import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
from utils.utils import *
from utils.temp_utils import *
import streamlit_shadcn_ui as ui
import numpy as np

from streamlit_extras.bottom_container import bottom

sv, categories, accounts, indices = load()
st.session_state['sv'] = sv
st.session_state['categories'] = categories
ready_to_continue = False

accounts['pill_label'] = "**" + accounts['wikidata_label'] + "**" + "  \n(" + accounts['wikidata_desc'] + ")"


st.markdown("#### Let's set you a profile...")
#selected_categories = st.multiselect("Select Categories", categories, max_selections= 5)
#selected_categories = st.pills("Select Categories", categories, selection_mode="multi")
selected_categories = sac.chip(items=[sac.ChipItem(label=category) for category in categories]
         ,label='Select you preferred categoties', description='Select up to 5 categories',  align='center',
                               size='md', radius=20, variant='outline',multiple=True)

if len(selected_categories) > 5:
    st.error("Select no more than 5 categories")
elif len(selected_categories) > 0:
    st.session_state['selected_categories'] = selected_categories
    accounts_for_selection = []

    for category in selected_categories:
        accounts_in_category = accounts[accounts['category']==category]['twitter_name'].unique().tolist()
        accounts_for_selection.extend([accounts_in_category[i] for i in indices])

    random.seed(76)

    # Make a copy so original list isn't altered
    shuffled_accounts = accounts_for_selection.copy()
    random.shuffle(shuffled_accounts)

    chip_items = [sac.ChipItem(label=account) for account in shuffled_accounts]

    selected_accounts = sac.chip(items=chip_items,
                                 label = 'Now select accounts that you find interesting', description = 'at least 2 and up to 7 accounts',
                                 align='center', size='sm', radius=20,
                                 color='grape', variant='outline',multiple=True)

    if len(selected_accounts) < 2:
        st.success("Please select at least 2 accounts")
        st.divider()
    else:
        st.divider()

        un = accounts[accounts['twitter_name'].isin(selected_accounts)]
        mean_vector = np.mean(np.stack(un['sv'].values), axis=0)
        with st.spinner("Wait for it...", show_time=True):
            persona_details = pd.read_pickle('data/persona_details_v2.pkl')
            persona_details.drop_duplicates(subset='screen_name', inplace=True)


        # Prepare the prompt
        with open("system_message/base_message.txt", "r", encoding="utf-8") as f:
            system_message = f.read()

        chat_option = st.radio(label="",label_visibility='hidden', options=["Personalized chat - user like me",
                                                                            "Personalized chat - random user",
                                                                            "Chat with standard LLM"],
                                    index=0)

        if chat_option == "Personalized chat - user like me":
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


        elif chat_option == "Personalized chat - random user":
            user_for_the_chat = persona_details.sample().iloc[0]
            system_message += f"You describe youself as: {user_for_the_chat['description']}.\n"
            system_message += f"Additional details about you: {user_for_the_chat['persona_description']}.\n"


        st.session_state['system_message'] = system_message
        st.session_state['user_embeddings'] = np.array(user_for_the_chat['sv'])
        ready_to_continue = True


        cols = st.columns(5)
        if cols[0].button("Closest User", use_container_width=True):
            find_most_similar(mean_vector, persona_details, top_n=1)
        if cols[1].button("Top 5 closest users", use_container_width=True):
            find_most_similar(mean_vector, persona_details, top_n=5)
        if cols[2].button("Similarity", use_container_width=True):
            show_similar(sv, mean_vector)

        if cols[3].button("System Message", use_container_width=True):
            show_system_message()



with bottom():
    bottom_cols = st.columns([2,3])
    with bottom_cols[0]:
        if ready_to_continue:
            next_button = sac.buttons([
                sac.ButtonsItem(label='Go to chat',color='#25C3B0', icon="caret-right")
                ],label="",index=None,color='violet',variant='filled')

            if next_button == "Go to chat":
                st.session_state['clear_messages'] = True
                st.switch_page('pages/chat.py')

    with bottom_cols[1].expander("📝 Still to do:", expanded=False):
        """
        
        * Cherry pick some of the accounts we show (e.g.: Donald Trump in the politicians)
        * improve the socialvec info snippets (There are some inconcistencies)
        * Decide about the user's pictures/description/text they wrote
        """
        pass