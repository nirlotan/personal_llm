import streamlit as st
import streamlit_antd_components as sac
from utils.utils import load
from streamlit_javascript import st_javascript
from user_agents import parse
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

st.markdown("""

### Experiment Overview – The Impact of Personalization on Large Language Models (LLM)

Hello and welcome,  
Thank you for agreeing to participate in an experiment examining the effect of personalization on the user experience with Large Language Models (LLMs).

The experiment consists of three stages:

1. **Selecting Interests** – In this stage, you will be asked to choose a few topics that interest you, and then select some social media accounts related to those topics — accounts you would be happy to follow.  
2. **Conversation with a Language Model** – Next, you will engage in a conversation with a large language model, exchanging at least a few messages. During the conversation, feel free to explore a variety of interactions, such as asking for a recommendation, searching for a piece of information, or just casual chatting.  
3. **Feedback on the Experience** – At the end of the conversation, you will be asked to complete a short questionnaire, consisting of 7 rating questions on a scale of 1 to 5, aimed at evaluating your experience interacting with the model.

Participation in the experiment is anonymous, and all collected data will be used for research purposes only.

#### The experiment will be conducted in English

**Thank you very much for your cooperation and participation!**
""", unsafe_allow_html=True)

try:
    # check user agent to suppress non-mandatory parts when running on mobile
    ua_string = st_javascript("""window.navigator.userAgent;""")
    user_agent = parse(ua_string)
    st.session_state.is_session_pc = user_agent.is_pc
except:
    st.session_state.is_session_pc = True





next_button = sac.buttons([
    sac.ButtonsItem(label='Start', color='#25C3B0', icon="caret-right")
], label="", index=None, color='violet', variant='filled')

load()

if next_button == "Start":
    st.session_state['clear_messages'] = True
    st.switch_page('pages/cold_start.py')
