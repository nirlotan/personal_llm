import os

import streamlit as st
import streamlit_antd_components as sac
from utils.utils import load, session_init
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

session_init()

st.markdown("""

### Personal Chat Experiment
#### The Impact of Personalization on Large Language Models (LLMs)
Hey there, and thanks for participating!

You’re taking part in a study exploring how personalization affects the way people interact with large language models (LLMs).

**The experiment has the following parts:**  \n
> 1.	Pick a few topics you’re interested in, and social media accounts for each topic.
> 2.	You'll be asked to chat with **two seperate language models**.
> 3.	After chatting **with each of the models** you'll be asked a few questions about the experience.

Everything is completely anonymous, and your responses will only be used for research.

By clicking "Start" below, you agree to participate in this study.

**We appreciate your time and contribution!**
""", unsafe_allow_html=True)

next_button = sac.buttons([
    sac.ButtonsItem(label='Start', color='#25C3B0', icon="caret-right")
], label="", index=None, color='violet', variant='filled')

if next_button == "Start":
    st.session_state['clear_messages'] = True
    st.switch_page('pages/cold_start.py')
