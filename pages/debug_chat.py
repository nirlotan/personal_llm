from utils.utils import *
from utils.lang_utils import *
import time
import numpy as np
import pandas as pd
import random

def clear_session_state_for_debug_chat():
    st.session_state['system_message'] = None
    st.session_state['chat_status'] = {"Friendly Chat": 0,
                                       "Recommendation": 0,
                                       "Factual Information Request" : 0
                                        }
    st.session_state['chat_type'] = None
    st.session_state['clear_messages'] = True
    st.session_state['last_system_message_time'] = time.time()
    st.session_state['confirm3'] = None
    st.session_state['chat_messages'] = None
    st.session_state['messages_timing'] = []
    st.session_state['user_for_the_chat'] = None
    st.session_state['user_embeddings'] = None
    st.session_state['selected_user_similarity'] = None
    st.session_state["selected_categories"] = None
    st.session_state["selected_accounts"] = None
    # Remove init_complete from session state entirely
    if 'init_complete' in st.session_state:
        del st.session_state['init_complete']

def prepare_system_message_for_debug(chat_type):
    """Prepare system message for debug mode (no cold start)"""
    # For vanilla, no system message
    if chat_type == "vanilla":
        return ""
    
    # Load base message for other types
    with open("system_message/base_message.txt", "r", encoding="utf-8") as f:
        system_message = f.read()
    
    user_description = ""
    
    # For reference personas (PERSONA_ref, SPC_ref)
    if chat_type in ["PERSONA_ref", "SPC_ref"]:
        persona_description = pd.read_excel(f"data/{chat_type.split('_')[0]}_selected_personas.xlsx")
        selected_user_idx = random.randint(0, persona_description.shape[0] - 1)
        user_for_the_chat = persona_description.iloc[selected_user_idx].astype(str)
        st.session_state['user_for_the_chat'] = user_for_the_chat['persona_id']
        user_description = user_for_the_chat['persona']
    # For Personalized Random (without cold start data)
    elif chat_type == "Personalized Random":
        persona_details = pd.read_pickle('data/persona_details_v2.pkl')
        persona_details.drop_duplicates(subset='screen_name', inplace=True)
        selected_user_idx = random.randint(0, persona_details.shape[0] - 1)
        user_for_the_chat = persona_details.iloc[selected_user_idx]
        user_description = user_for_the_chat['description']
        st.session_state['user_for_the_chat'] = user_for_the_chat['screen_name']
        st.session_state['selected_user_similarity'] = 0
        st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])
    
    # Prepare final prompt
    final_prompt = system_message.replace("{character_description}", user_description)
    return final_prompt


session_init()
check_pc_mobile()
#clear_session_state_for_debug_chat()
st.session_state['clear_messages'] = True

# Custom CSS for card-based layout matching the reference HTML
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        margin-bottom: 50px;
        font-weight: 500;
        letter-spacing: -0.5px;
        text-align: center;
        color: #1d1d1f;
    }
    
    .card-grid {
        display: flex;
        gap: 24px;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 50px;
    }
    
    .card {
        background: #fff;
        width: 220px;
        height: 240px;
        padding: 30px 20px;
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: pointer;
        border: 1px solid rgba(0,0,0,0.03);
        text-decoration: none;
        color: inherit;
    }
    
    .card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
    }
    
    .emoji {
        font-size: 2.8rem;
        margin-bottom: 20px;
        display: block;
    }
    
    .card h3 {
        font-size: 1.15rem;
        margin-bottom: 12px;
        font-weight: 600;
        line-height: 1.2;
        text-align: center;
    }
    
    .card p {
        font-size: 0.95rem;
        color: #6e6e73;
        line-height: 1.4;
        font-weight: 400;
        text-align: center;
    }
    
    .vanilla { 
        background: linear-gradient(180deg, #e1f0ff 0%, #ffffff 60%); 
    }
    .personalized-me { 
        background: linear-gradient(180deg, #e4f5e9 0%, #ffffff 60%); 
    }
    .personalized-random { 
        background: linear-gradient(180deg, #f1e6f7 0%, #ffffff 60%); 
    }
    .persona-ref { 
        background: linear-gradient(180deg, #fff2e0 0%, #ffffff 60%); 
    }
    .spc-ref { 
        background: linear-gradient(180deg, #ffe0e0 0%, #ffffff 60%); 
    }
    
    @media (max-width: 768px) {
        .card-grid {
            flex-direction: column;
            align-items: center;
        }
        .card {
            width: 100%;
            max-width: 320px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-title">Welcome to PersonaChat</h1>', unsafe_allow_html=True)

# Create card grid
st.markdown('<div class="card-grid">', unsafe_allow_html=True)

# Card definitions with emojis, titles, and descriptions
cards = [
    ("vanilla", "🤖", "Vanilla", "Experience standard AI assistance."),
    ("Personalized Like Me", "🪞", "Personalized Like Me", "Chat that mirrors your style."),
    ("Personalized Random", "🎲", "Personalized Random", "Unexpected, varied responses."),
    ("PERSONA_ref", "🎭", "PERSONA_ref", "Adopt a specific persona."),
    ("SPC_ref", "✨", "SPC_ref", "Special reference mode."),
]

# Create columns for cards
cols = st.columns(5)

st.session_state['allow_debug'] = True

for idx, (chat_type, emoji, title, description) in enumerate(cards):
    with cols[idx]:
        card_class = chat_type.lower().replace(" ", "-")
        if st.button(f"{emoji}\n\n**{title}**\n\n{description}", key=chat_type, use_container_width=True):
            st.session_state['chat_type'] = chat_type            

            st.session_state['remaining_chat_types'] = [chat_type]
            # If "Personalized Like Me" is selected, go through cold start
            if chat_type == "Personalized Like Me":
                # clear the system_message and redirect to cold_start
                st.session_state['system_message'] = None
                st.session_state['clear_messages'] = True
                st.switch_page('pages/cold_start.py')
            else:
                # For all other options, prepare system message and skip cold start
                st.session_state['system_message'] = prepare_system_message_for_debug(chat_type)
                st.session_state['clear_messages'] = True
                st.switch_page('pages/chat.py')

st.markdown('</div>', unsafe_allow_html=True)