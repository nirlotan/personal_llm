import streamlit as st
import streamlit_antd_components as sac
from utils.feedback_object import FeedbackObject
from utils.prepare_prompt import clear_session_state_for_next_chat, prepare_system_prompt
from utils.chat_object import ChatSessionClass
import pandas as pd

if 'init_complete' not in st.session_state:
    st.switch_page('pages/cold_start.py')

# Initialize session state for the button
# if "button_clicked" not in st.session_state:
#     st.session_state.button_clicked = False
#
# Function to handle button click
# def on_button_click():
#     st.session_state.button_clicked = True  # Set the button as clicked

@st.dialog("Feedback")
def feedback_popup():
    st.write(f"Now please share with us your feedback about your experience chatting with this specific chatbot.")
    if st.button("Confirm"):
        st.session_state.confirm4 = True
        st.rerun()

if "confirm4" not in st.session_state:
    feedback_popup()

fo = FeedbackObject()

response = fo.feedback_form()

if len(response) > 0:
    next_button = sac.buttons([
        sac.ButtonsItem(label='Submit Survey', color='#25C3B0', icon="send")
    ], label="", index=None, color='violet', variant='filled')

    if next_button == 'Submit Survey':
        # Save survey results to Firebase (generating a new key under 'survey_results')
        fo.submit_feedback()
        #on_button_click()

        clear_session_state_for_next_chat()
        if len(st.session_state['remaining_chat_types']) > 0:
            persona_details = pd.read_pickle('data/persona_details_v2.pkl')
            persona_details.drop_duplicates(subset='screen_name', inplace=True)
            new_system_message = prepare_system_prompt(persona_details)
            st.session_state['clear_messages'] = True
            st.session_state['first_chat'].reset(new_system_message)
            st.switch_page('pages/chat.py')
        else:
            st.success("Thank you for submitting the survey!")
            st.balloons()
            st.switch_page('pages/thank_you.py')

#else:
#    st.error("Survey can only be sumbitted once.")
# Button to submit the survey
