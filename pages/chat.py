# --- Imports ---
from langchain.chains import LLMChain
import streamlit as st
import streamlit_antd_components as sac
from utils.chat_object import ChatSessionClass
from utils.utils import *
from streamlit_extras.bottom_container import bottom

if 'init_complete' not in st.session_state:
    st.switch_page('pages/cold_start.py')

if not st.session_state['messages_timing']:
    st.session_state['messages_timing'] = []

@st.dialog("Conversation with a Language Model")
def chat_popup():
    st.write(f"Next, you’ll chat with a large language model, exchanging a few messages.")
    st.write(f"**This is the first chatbot out of 2 chatbos.**")
    st.write(f"Try to complete these tasks:  \n 1. Have a **casual conversation,**  \n 2. Ask for **recommendations,**  \n 3. Request **factual information.**")
    st.write(f"You can pass to the next phase after trying all these types of interactions, of after a minimal number of messages.")
    st.badge("**Suggestion:** Try to exchange opinions with the chatbot!", icon="💡", color="green")
    st.badge("**Note:** Read the chatbot messages!", icon="👉", color="orange")
    if st.button("Confirm"):
        st.session_state.confirm3 = True
        st.rerun()

@st.dialog("We're almost there...")
def second_chat_popup():
    st.write(f"**One more chat** (with a different bot), and after getting your feedback on this bot - you are done!")
    if st.button("Confirm"):
        st.session_state.second_chat_confirm = True
        st.rerun()

if "confirm3" not in st.session_state:
    chat_popup()
elif "second_chat_confirm" not in st.session_state and len(st.session_state['remaining_chat_types'])==1:
    second_chat_popup()

if 'chat_status' not in st.session_state:
    st.session_state['chat_status'] = {"Friendly Chat": 0,
                                       "Recommendation": 0,
                                       "Factual Information Request" : 0
                                        }

# Things to clean between chats:
# - st.session_state['chat_status']

if "first_chat" not in st.session_state:
    st.session_state['first_chat'] = ChatSessionClass(st.session_state['system_message'])
st.session_state['first_chat'].chat_session()

# Dynamic button options
buttons_list = []

with bottom():
    app_config = toml.load("config.toml")
    chat_status_indexes = [i for i, (k, v) in enumerate(st.session_state['chat_status'].items()) if v == 1]

    #msgs_len = st.session_state['first_chat'].get_messages_len()
    msgs_len = int(len(st.session_state['first_chat'].msgs.messages)/2) - 1
    if (msgs_len < app_config['minimal_number_of_messages']):
        if st.session_state.is_session_pc:
            sac.checkbox(
                items=[
                    'Friendly Chat',
                    'Recommendation',
                    'Factual Information Request',
                ],
                label=f'You need to write {int(app_config["minimal_number_of_messages"] - msgs_len)} more messages to move to the next phase.<br>Try to complete the following tasks:',
                index=chat_status_indexes, align='left', size='lg', disabled=True
            )

    enable_feedback = msgs_len >= app_config['minimal_number_of_messages']

    if enable_feedback:
        # Inject custom CSS to style the button
        st.markdown("""
            <style>
            div.stButton > button {
                position: fixed;
                bottom: 5%;
                left: 50%;
                transform: translateX(-50%);
                background-color: purple;
                color: white;
                padding: 12px 24px;
                font-size: 18px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.25);
                z-index: 9999;
            }
            </style>
        """, unsafe_allow_html=True)

        # Use regular Streamlit button
        if st.button("✨ You can keep chatting. Whenever you are done, click here in order to continue"):
            st.session_state['clear_messages'] = True
            st.session_state['chat_messages'] = st.session_state['first_chat'].get_messages()
            st.switch_page('pages/submit_feedback.py')