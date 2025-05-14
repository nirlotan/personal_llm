import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import streamlit_antd_components as sac



def prepare_system_prompt(persona_details, mean_vector, chat_option):
    # Prepare the prompt
    with open("system_message/base_message.txt", "r", encoding="utf-8") as f:
        system_message = f.read()

    if chat_option == "Personalized Chat":
        sv_matrix = np.stack(persona_details['sv'].values)
        persona_details['similarity'] = cosine_similarity(sv_matrix, mean_vector.reshape(1, -1)).flatten()
        most_similar_idx = np.argmax(persona_details['similarity'].values)
        user_for_the_chat = persona_details.iloc[most_similar_idx]
        system_message += "\n\nAdditional info about yourself:\n"
        system_message += f"You alias is: {user_for_the_chat['screen_name']}.\n"
        if user_for_the_chat['location']:
            system_message += f"You are from {user_for_the_chat['location']}. "
        system_message += f"You describe youself as: {user_for_the_chat['description']}.\n"
        system_message += f"Additional details: {user_for_the_chat['persona_description']}.\n"

        st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])
        st.session_state['is_personalized_chat'] = True

    elif chat_option == "Personalized Random":
        user_for_the_chat = persona_details.sample().iloc[0]
        system_message += f"You describe youself as: {user_for_the_chat['description']}.\n"
        system_message += f"Additional details about you: {user_for_the_chat['persona_description']}.\n"
        st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])
        st.session_state['is_personalized_chat'] = True

    else:
        st.session_state['user_embeddings'] = np.zeros(100)

    st.session_state['system_message'] = system_message
