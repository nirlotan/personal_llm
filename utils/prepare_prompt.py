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


def prepare_system_prompt(persona_details):
    user_description = ""

    st.session_state['chat_type'] = get_random_chat_choice()

    sv_matrix = np.stack(persona_details['sv'].values)
    persona_details['similarity'] = cosine_similarity(sv_matrix, st.session_state['user_mean_vector'].reshape(1, -1)).flatten()

    if st.session_state['chat_type'] == "Personalized Like Me":
        selected_user_idx = np.argmax(persona_details['similarity'].values)
    elif st.session_state['chat_type'] == "Personalized Random":
        selected_user_idx = random.randint(0, persona_details.shape[0] - 1)

    user_for_the_chat = persona_details.iloc[selected_user_idx]
    user_description += user_for_the_chat['description']

    st.session_state['user_for_the_chat'] = user_for_the_chat['screen_name']
    st.session_state['selected_user_similarity'] = user_for_the_chat['similarity']
    st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])

    # Prepare the prompt
    with open("system_message/base_message3.txt", "r", encoding="utf-8") as f:
        system_message = f.read()

    final_prompt = system_message.replace("{character_description}", user_description)

    # else:
    #     st.session_state['user_embeddings'] = np.zeros(100)
    #     final_prompt = ""

    st.session_state['system_message'] = final_prompt

    return final_prompt
