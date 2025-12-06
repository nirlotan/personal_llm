from utils.utils import *
from utils.lang_utils import *
import time

import numpy as np

def clear_session_state_for_debug_chat():
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
    st.session_state["selected_categories"] = None
    st.session_state["selected_accounts"] = None


session_init()
check_pc_mobile()
clear_session_state_for_debug_chat()
st.session_state['clear_messages'] = True

system_message = ""


st.session_state['chat_type'] = st.selectbox("select chat type:",options=["", "vanilla","Personalized Like Me", "Personalized Random", "Personalized Random", "PERSONA_ref","SPC_ref"])
#if "chat_type" in st.query_params:
if st.session_state["chat_type"] != "":
    st.session_state['system_message'] = system_message
    st.session_state['init_complete'] = True
    st.switch_page('pages/chat.py')