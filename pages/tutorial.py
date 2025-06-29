import os

import streamlit as st
import streamlit_antd_components as sac
from utils.utils import load, set_user_guid
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import time
with st.spinner("Loading... Please wait..."):
    sv, categories, accounts, my_keys, lm = load()

#gif_placeholder.empty()

st.session_state['sv'] = sv
st.session_state['categories'] = categories
st.session_state['accounts'] = accounts
st.session_state['my_api_keys'] = my_keys
st.session_state['lm'] = lm
st.session_state['messages_timing'] = []
st.session_state['number_of_feedbacks_provided'] = 0
set_user_guid()
st.session_state['init_complete'] = True

st.markdown("""

### Personal Chat Experiment
#### The Impact of Personalization on Large Language Models (LLMs)
Hey there, and thanks for participating!

You’re taking part in a study exploring how personalization affects the way people interact with large language models (LLMs).

**The experiment has three parts:**  \n
> 1.	Pick a few topics you’re interested in, and social media accounts for each topic.
> 2.	Chat with a language model.
> 3.	Share your thoughts about the experience.

Everything is completely anonymous, and your responses will only be used for research.

**We appreciate your time and contribution!**
""", unsafe_allow_html=True)



next_button = sac.buttons([
    sac.ButtonsItem(label='Start', color='#25C3B0', icon="caret-right")
], label="", index=None, color='violet', variant='filled')

if next_button == "Start":
    st.session_state['clear_messages'] = True
    st.switch_page('pages/cold_start.py')