import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import streamlit_antd_components as sac



def prepare_system_prompt(persona_details, mean_vector, chat_option):
    user_description = ""

    if chat_option == "Personalized Chat":
        sv_matrix = np.stack(persona_details['sv'].values)
        persona_details['similarity'] = cosine_similarity(sv_matrix, mean_vector.reshape(1, -1)).flatten()
        most_similar_idx = np.argmax(persona_details['similarity'].values)
        user_for_the_chat = persona_details.iloc[most_similar_idx]
        user_description += user_for_the_chat['description']
        #user_description += f"Your alias is: {user_for_the_chat['screen_name']}.\n"
        #if user_for_the_chat['location']:
        #    user_description += f"You are from {user_for_the_chat['location']}. "
        #user_description += f"You describe youself as: {user_for_the_chat['description']}.\n"
        #user_description += f"Additional details: {user_for_the_chat['persona_description']}.\n"

        st.session_state['user_for_the_chat'] = user_for_the_chat['screen_name']
        st.session_state['selected_user_similarity'] = user_for_the_chat['similarity']
        st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])
        st.session_state['is_personalized_chat'] = True

        # Prepare the prompt
        with open("system_message/base_message.txt", "r", encoding="utf-8") as f:
            system_message = f.read()

        final_prompt = system_message.replace("{character_description}", user_description)

    else:
        st.session_state['user_embeddings'] = np.zeros(100)
        final_prompt = ""

    st.session_state['system_message'] = final_prompt

    return final_prompt
