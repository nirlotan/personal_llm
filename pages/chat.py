# --- Imports ---
import os
import time
import toml
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
import streamlit_shadcn_ui as ui
from streamlit_extras.bottom_container import bottom
from streamlit_javascript import st_javascript
from user_agents import parse

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

from utils.utils import *

def split_before_last_marker(text, marker="._."):
    before, _, _ = text.rpartition(marker)
    return before.strip()

# --- Styles ---
with open("styles.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

# --- Configuration ---
try:
    openai_api_key = st.secrets["openai_api_key"]
except:
    openai_api_key = os.environ.get('openai_api_key')

app_config = toml.load("config.toml")

if 'chat_status' not in st.session_state:
    st.session_state['chat_status'] = {"Friendly Chat": 0,
                                       "Recommendation": 0,
                                       "Info Request" : 0
                                        }


# --- Load session data ---

if 'system_message' not in st.session_state:
    st.switch_page('pages/cold_start.py')
system_message = st.session_state['system_message']

sv = st.session_state['sv']
categories = st.session_state['categories']

# --- Set up message history ---
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if st.session_state.get('clear_messages', False):
    msgs.clear()
    st.session_state['clear_messages'] = False

# Check if feedback option should be enabled
msgs_len = len(msgs.messages)

# --- LangChain setup ---
prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{sentence}"),
])

chat_model = ChatOpenAI(
    api_key=openai_api_key,
    model="gpt-4o-mini",
    temperature=0.5,
)

chain = prompt | chat_model
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,
    input_messages_key="sentence",
    history_messages_key="history",
)

# --- Render previous messages ---
for msg in msgs.messages:
    avt = "🐨" if msg.type=="human" else "🐼"
    message = split_before_last_marker(msg.content) if msg.type=="human" else msg.content
    st.chat_message(msg.type, avatar=avt).write(message)

# --- Bottom input section ---
with bottom():
    bottom_columns = st.columns([3, 1], vertical_alignment='bottom')

    # User free text input
    user_prompt = st.chat_input(placeholder="Type your message:")

# --- Handling User Prompt ---
with st.container():
    if user_prompt:
        st.chat_message("human", avatar ="🐨").write(user_prompt)

        if st.session_state['is_personalized_chat']:
            user_intent = get_user_intent(user_prompt)
            if user_intent['intent'].value in ["Friendly Chat", "Recommendation", "Info Request"]:
                st.session_state['chat_status'][user_intent['intent']]=1

            #st.toast(user_intent['intent'])
            if user_intent['intent']=="Recommendation":
                if user_intent['topic']:
                    rec_list = get_recommendation(sv, user_intent['topic'])
                    extended_user_prompt = f"{user_prompt}._. If relevant, try to recommend from: {rec_list}. Be concise (under 100 words)."
                    #st.toast(f"{user_intent['topic']}, {rec_list}")

            elif user_intent['intent'] == "Info Request":
                extended_user_prompt = user_prompt + "._. After providing the information requested provide some personal perspective based on my topics of interest."
            else:
                extended_user_prompt = user_prompt + "._. Be concise (under 100 words)"
        # Not personalized chat
        else:
            extended_user_prompt = user_prompt + "._. Be concise (under 100 words)"

        # Generate model response
        config = {"configurable": {"session_id": "any"}}
        response = chain_with_history.invoke({"sentence": extended_user_prompt}, config)

        # Simulate typing animation
        with st.chat_message("ai", avatar ="🐼"):
            message_placeholder = st.empty()
            length_of_wait = int(len(response.content) / 40)
            for i in range(length_of_wait):
                dots = "." * (i % 4)
                message_placeholder.write(f"Typing{dots}")
                time.sleep(0.5)
            message_placeholder.write(response.content)


with bottom():

    # Dynamic button options
    buttons_list = []
    chat_status_indexes = [i for i, (k, v) in enumerate(st.session_state['chat_status'].items()) if v == 1]

    sac.checkbox(
        items=[
            'Friendly Chat',
            'Recommendation',
            'Info Request',
        ],
        label='', index=chat_status_indexes, align='left', size='lg', disabled=True
    )

    enable_feedback = msgs_len >= app_config['minimal_number_of_messages'] and all(
        v == 1 for v in st.session_state['chat_status'].values())
    if enable_feedback:
        buttons_list.append(
            sac.ButtonsItem(label="I'm done, let's go to the feedback section", color='#25C3B0', icon="caret-right")
        )

    next_button = sac.buttons(buttons_list, label="", index=None, color='violet', variant='filled')

    if next_button == "System Prompt":
        show_system_message()
    elif next_button == "I'm done, let's go to the feedback section":
        st.session_state['clear_messages'] = True
        st.session_state['chat_messages'] = msgs.messages
        st.switch_page('pages/submit_feedback.py')
