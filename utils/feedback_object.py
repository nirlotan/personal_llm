import json

import firebase_admin
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
from firebase_admin import credentials, db
from datetime import datetime

class FeedbackObject():
    def __init__(self):
        if not firebase_admin._apps:
            firebase_json = st.session_state['my_api_keys']['freebase_certificate']
            cred = credentials.Certificate(json.loads(firebase_json))
            # Initialize the Firebase app
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://socialai-00007-default-rtdb.firebaseio.com/'  # Use your own database URL here
            })

        # Reference to the Firebase Realtime Database
        self.ref = db.reference("/survey_results_10", app=firebase_admin.get_app(),
                           url="https://socialai-00007-default-rtdb.firebaseio.com/")
        self.survey_data = {}

    def submit_feedback(self):
        self.ref.push(self.survey_data)

    def feedback_form(self):
        questions = pd.read_csv('data/questionnaire.csv')

        responses = []

        for i, question in questions.iterrows():
            responses.append(
                sac.rate(label=question['label'], description=question['description'], value=0.0, align='start',
                         key=f'q{i}'))

        if 'system_message' not in st.session_state:
            st.session_state['system_message'] = None

        txt = st.text_area("Additional Feedback (Optional)",
                           key="my_text")

        self.survey_data = {
            "experiment_start_time": st.session_state['experiment_start_time'],
            "date_time": str(datetime.now()),
            "unique_session_id": st.session_state['unique_session_id'],
            "user_selected_categories": st.session_state['selected_categories'],
            "user_selected_accounts": st.session_state['selected_accounts'],
            "user_selected_for_chat": st.session_state['user_for_the_chat'],
            "chat_type": st.session_state['chat_type'],
            "selected_user_similarity": st.session_state['selected_user_similarity'],
            "system_message": st.session_state['system_message'],
            "chat": [f"{d.type}: {d.content}" for d in st.session_state['chat_messages']],
            "messages_timing": st.session_state['messages_timing'],
            "user_feedback": {questions['short_label'].iloc[index]: value for index, value in enumerate(responses)},
            "free_text_feedback": txt
        }

        if 0 in responses:
            st.caption("You must provide your feedback on all categories in order to proceed.")
        return responses