import streamlit as st
import streamlit_antd_components as sac
import firebase_admin
from firebase_admin import credentials, db
import json
import pandas as pd
from streamlit_extras.bottom_container import bottom

if 'init_complete' not in st.session_state:
    st.switch_page('pages/cold_start.py')

# Initialize session state for the button
if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False

# Function to handle button click
def on_button_click():
    st.session_state.button_clicked = True  # Set the button as clicked

if not firebase_admin._apps:
    firebase_json = st.session_state['my_api_keys']['freebase_certificate']
    cred = credentials.Certificate(json.loads(firebase_json))
    # Initialize the Firebase app
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://socialai-00007-default-rtdb.firebaseio.com/'  # Use your own database URL here
    })

# Reference to the Firebase Realtime Database
ref = db.reference("/survey_results", app=firebase_admin.get_app(),
                   url="https://socialai-00007-default-rtdb.firebaseio.com/")  # This is where survey results will be stored

# Display the button with streamlit_shadcn_ui
if not st.session_state.button_clicked:

    questions = pd.read_csv('data/questionnaire.csv')

    responses = []

    for i, question in questions.iterrows():
        responses.append(
            sac.rate(label=question['label'], description=question['description'], value=0.0, align='start',
                     key=f'q{i}'))

    if 'system_message' not in st.session_state:
        st.session_state['system_message'] = None

    survey_data = {questions['label'].iloc[index]: value for index, value in enumerate(responses)}
    survey_data.update({"profile": st.session_state['system_message'],
                        "chat": [f"{d.type}: {d.content}" for d in st.session_state['chat_messages']]})
    # [f"{d.type}: {d.content}" for d in survey_data["chat"]]

    with bottom():
        next_button = sac.buttons([
            sac.ButtonsItem(label='Submit Survey', color='#25C3B0', icon="send")
        ], label="", index=None, color='violet', variant='filled')

        if next_button == 'Submit Survey':
            # Save survey results to Firebase (generating a new key under 'survey_results')
            ref.push(survey_data)
            on_button_click()
            st.success("Thank you for submitting the survey!")

else:
    st.error("Survey can only be sumbitted once.")
# Button to submit the survey
