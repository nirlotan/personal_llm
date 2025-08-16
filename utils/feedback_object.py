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
            firebase_json = st.session_state.get('my_api_keys', {}).get('freebase_certificate')
            if not firebase_json:
                raise ValueError("Firebase certificate not found in session state")

            cred = credentials.Certificate(json.loads(firebase_json))
            firebase_admin.initialize_app(cred, {
                'databaseURL': st.session_state['my_api_keys']['firebase_db_url']
            })

        self.ref = db.reference(st.session_state['my_api_keys']['experiment_feedback_path'],
                                app=firebase_admin.get_app(),
                                url=st.session_state['my_api_keys']['firebase_db_url'])
        self.survey_data = {}

    def _safe_get_session_value(self, key, default=None):
        """Safely get a value from session state with a default fallback."""
        return st.session_state.get(key, default)

    def _format_chat_messages(self, messages):
        """Safely format chat messages, handling None or empty cases."""
        if not messages:
            return []
        return [f"{getattr(d, 'type', 'unknown')}: {getattr(d, 'content', '')}" for d in messages]

    def submit_feedback(self):
        self.ref.push(self.survey_data)

    def feedback_form(self):
        questions = pd.read_csv('data/questionnaire.csv')
        responses = []

        for i, question in questions.iterrows():
            responses.append(
                sac.rate(label=question['label'], description=question['description'], value=0.0, align='start',
                         key=f'q{i}'))

        txt = st.text_area("Additional Feedback (Optional)", key="my_text")

        # Build survey data with safe defaults
        self.survey_data = {
            "experiment_start_time": self._safe_get_session_value('experiment_start_time'),
            "date_time": str(datetime.now()),
            "unique_session_id": self._safe_get_session_value('unique_session_id'),
            "user_selected_categories": self._safe_get_session_value('selected_categories', []),
            "user_selected_accounts": self._safe_get_session_value('selected_accounts', []),
            "user_selected_for_chat": self._safe_get_session_value('user_for_the_chat'),
            "chat_type": self._safe_get_session_value('chat_type'),
            "selected_user_similarity": self._safe_get_session_value('selected_user_similarity'),
            "system_message": self._safe_get_session_value('system_message'),
            "chat": self._format_chat_messages(self._safe_get_session_value('chat_messages')),
            "messages_timing": self._safe_get_session_value('messages_timing', {}),
            "user_feedback": {questions['short_label'].iloc[index]: value for index, value in enumerate(responses)},
            "free_text_feedback": txt
        }

        if 0 in responses:
            st.caption("You must provide your feedback on all categories in order to proceed.")
        return responses