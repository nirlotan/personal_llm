import streamlit_antd_components as sac
from utils.utils import *
from utils.lang_utils import *
from utils.prepare_prompt import prepare_system_prompt
import numpy as np


if 'init_complete' not in st.session_state:
    sv, categories, accounts, my_keys, lm = load()
    st.session_state['sv'] = sv
    st.session_state['categories'] = categories
    st.session_state['accounts'] = accounts
    st.session_state['my_api_keys'] = my_keys
    st.session_state['lm'] = lm
    st.session_state['init_complete'] = True
else:
    sv = st.session_state['sv']
    categories = st.session_state['categories']
    accounts = st.session_state['accounts']
    my_keys = st.session_state['my_api_keys']
    lm = st.session_state['lm']


if 'next_clicked' not in st.session_state:
    st.session_state['next_clicked'] = False
if 'categories_selected' not in st.session_state:
    st.session_state['categories_selected'] = False

if st.session_state.is_session_pc:
    categories_size = 25
    accounts_size = 18
else:
    categories_size = 18
    accounts_size = 12

ready_to_continue = False

accounts['pill_label'] = "**" + accounts['wikidata_label'] + "**" + "  \n(" + accounts['wikidata_desc'] + ")"

if not st.session_state['categories_selected']:
    st.markdown("### Let's set you a profile...")

    selected_categories = sac.chip(items=[sac.ChipItem(label=category) for category in categories]
             ,label='Select 3-5 of your preferred categories', description='Select 3 to 5 categories',
                                   size=categories_size, radius=28, color='grape', multiple=True)


    if len(selected_categories) > 5:
        st.error("Select no more than 5 categories")
    elif len(selected_categories) > 2:

        if "Next" == sac.buttons([
            sac.ButtonsItem(label='Next', color='green', icon="caret-right", )
        ], label="", size=categories_size, radius=28, index=None):

            st.session_state['categories_selected'] = True
            st.session_state['selected_categories'] = selected_categories
            st.rerun()



if st.session_state['categories_selected']:
    if 'category_index' not in st.session_state:
        st.session_state['category_index'] = 0
    if 'selected_accounts' not in st.session_state:
        st.session_state['selected_accounts'] = []

    if st.session_state['category_index'] < len(st.session_state['selected_categories']):


        current_category = st.session_state['selected_categories'][st.session_state['category_index']]
        accounts_in_category = accounts[accounts['category'] == current_category]['twitter_name'].unique().tolist()
        chip_items = [sac.ChipItem(label=account) for account in accounts_in_category]


        selected_accounts = sac.chip(
            items=chip_items,
            label=f'Select accounts to follow in {current_category} category:',
            align='left',
            size=accounts_size,
            radius=28,
            color='orange',
            multiple=True
        )

        if st.session_state['category_index'] == len(st.session_state['selected_categories']) - 1:
            st.session_state['chat_option'] = sac.checkbox(
                items=[
                    'Personalized Chat',
                    'Personalized Random',
                    'Not Personalized',
                ],
                label='Chat Option', index=[0], align='start'
            )

        if len(selected_accounts) > 0 and "Next" == sac.buttons([
                sac.ButtonsItem(label='Next', color='green', icon="caret-right")
            ], label="",size=accounts_size, radius=28, index=None):
            st.session_state['selected_accounts'].extend(selected_accounts)
            if st.session_state['category_index'] < len(st.session_state['selected_categories']) :
                st.session_state['category_index'] += 1
                st.rerun()
    else:
        un = accounts[accounts['twitter_name'].isin(st.session_state['selected_accounts'])]
        mean_vector = np.mean(np.stack(un['sv'].values), axis=0)
        with st.spinner("Wait for it...", show_time=True):
            persona_details = pd.read_pickle('data/persona_details_v2.pkl')
            persona_details.drop_duplicates(subset='screen_name', inplace=True)
            prepare_system_prompt(persona_details, mean_vector, st.session_state['chat_option'][0])
            st.session_state['clear_messages'] = True
            st.switch_page('pages/chat.py')