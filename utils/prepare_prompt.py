import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random
import time

def get_random_chat_choice():
    if len(st.session_state['remaining_chat_types']) == 0:
        st.error("No more chat types available for this session.")
        st.stop()
    st.session_state['chat_type'] = random.choice(st.session_state['remaining_chat_types'])
    return st.session_state['chat_type']


def clear_session_state_for_next_chat():
    st.session_state['remaining_chat_types'].remove(st.session_state['chat_type'])
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


def get_user_index_for_personalized_like_me(persona_details):
    sv_matrix = np.stack(persona_details['sv'].values)
    persona_details['similarity'] = cosine_similarity(sv_matrix, st.session_state['user_mean_vector'].reshape(1, -1)).flatten()
    if 'allow_debug' in st.session_state and st.session_state['allow_debug']:
        # Get top 10 positional indices sorted by similarity descending
        sorted_positions = np.argsort(-persona_details['similarity'].values)[:10]
        top_n = persona_details.iloc[sorted_positions].copy()

        st.subheader("Most Similar Users")
        st.caption("Expand a user to see their full details, then pick one and click the button below to start chatting.")

        for rank, (_, row) in enumerate(top_n.iterrows()):
            similarity_pct = row['similarity'] * 100
            with st.expander(f"#{rank + 1}  ·  {row['screen_name']}  ({similarity_pct:.1f}% similar)"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric(label="Similarity", value=f"{similarity_pct:.1f}%")
                with col2:
                    st.markdown(f"**Screen Name:** {row['screen_name']}")

                st.markdown("---")
                st.markdown("**Description:**")
                st.info(row.get('description', 'N/A'))

                follows_list = row.get('follows_list', [])
                if follows_list:
                    st.markdown("**Follows:**")
                    if isinstance(follows_list, list):
                        st.write(", ".join(str(f) for f in follows_list))
                    else:
                        st.write(str(follows_list))

        st.markdown("---")

        # Let the user pick which persona to chat with
        labels = [f"#{i + 1} — {row['screen_name']}" for i, (_, row) in enumerate(top_n.iterrows())]
        selected_label = st.selectbox("Select a user to chat with:", labels)
        selected_rank = labels.index(selected_label)

        # Only proceed when the user explicitly confirms
        if st.button("✅ Start Chat with Selected User", type="primary", use_container_width=True):
            return int(sorted_positions[selected_rank])

        # Halt the script so the page stays on the selection screen
        st.stop()

    else:
        return np.argmax(persona_details['similarity'].values)

def prepare_system_prompt(persona_details):
    user_description = ""

    st.session_state['chat_type'] = get_random_chat_choice()
        

    # prompt_base
    if st.session_state['chat_type'] in ["Personalized Like Me", "Personalized Random", "vanilla_with_prompt", "PERSONA_ref", "SPC_ref"]:
        with open("system_message/base_message.txt", "r", encoding="utf-8") as f:
            system_message = f.read()
    else:
        system_message = ""

    if st.session_state['chat_type'] in ["Personalized Like Me", "Personalized Random"]:
        if st.session_state['chat_type'] == "Personalized Like Me":
            selected_user_idx = get_user_index_for_personalized_like_me(persona_details)
        elif st.session_state['chat_type'] == "Personalized Random":
            selected_user_idx = random.randint(0, persona_details.shape[0] - 1)

        user_for_the_chat = persona_details.iloc[selected_user_idx]
        user_description += user_for_the_chat['description']

        st.session_state['user_for_the_chat'] = user_for_the_chat['screen_name']
        st.session_state['selected_user_similarity'] = user_for_the_chat['similarity']
        st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])
        st.session_state['selected_user_follow_list'] = user_for_the_chat['follows_list']
    elif st.session_state['chat_type'] in ["PERSONA_ref", "SPC_ref"]:
        # Deal with reference personas.
        import pandas as pd
        persona_description = pd.read_excel(f"data/{st.session_state['chat_type'].split('_')[0]}_selected_personas.xlsx")
        selected_user_idx = random.randint(0, persona_description.shape[0] - 1)
        user_for_the_chat = persona_description.iloc[selected_user_idx].astype(str)
        st.session_state['user_for_the_chat'] = user_for_the_chat['persona_id']
        user_description += user_for_the_chat['persona']
    else:
        st.session_state['user_for_the_chat'] = st.session_state['chat_type']
        st.session_state['selected_user_similarity'] = 0

    # Prepare the prompt
    final_prompt = system_message.replace("{character_description}", user_description)


    st.session_state['system_message'] = final_prompt

    return final_prompt
