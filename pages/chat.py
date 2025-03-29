from utils.utils import *

from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI


import streamlit as st
import pandas as pd
from streamlit_extras.bottom_container import bottom
import streamlit_shadcn_ui as ui
import streamlit_antd_components as sac
from streamlit_javascript import st_javascript
from user_agents import parse
import time
import toml

with open( "styles.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

# if ['system_message'] not in st.session_state:
#     st.switch_page('pages/cold_start.py')
openai_api_key = st.secrets["openai_api_key"]
system_message = st.session_state['system_message']


user_prompt = False


sv = st.session_state['sv']
categories = st.session_state['categories']

config = toml.load("config.toml")

msgs = StreamlitChatMessageHistory(key="langchain_messages")
if 'clear_messages' in st.session_state and st.session_state['clear_messages']:
    msgs.clear()
    st.session_state['clear_messages'] = False
msgs_len = len(msgs.messages)
enable_feedback = False if msgs_len < config['minimal_number_of_messages'] else True

openai_api_key = st.secrets["openai_api_key"]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{sentence}"),
    ]
)


chain = prompt | ChatOpenAI(api_key=openai_api_key,
                            model="gpt-4o-mini",
                            temperature=1,
                            )
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,
    input_messages_key="sentence",
    history_messages_key="history",
)

last_user_prompt = ""
# Render current messages from StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

with bottom():
    bottom_columns = st.columns([3, 1],vertical_alignment='bottom')
    # Free text input option
    user_prompt = st.chat_input(placeholder="Type your message:")


    buttons_list = [
        sac.ButtonsItem(label="System Prompt", color='#25C3B0', icon="caret-right")
    ]
    if enable_feedback:
        buttons_list = buttons_list + [
            sac.ButtonsItem(label="I'm done, let's go to the feedback section", color='#25C3B0', icon="caret-right")
        ]
    next_button = sac.buttons(buttons_list, label="", index=None, color='violet', variant='filled')

    if next_button == "System Prompt":
        show_system_message()
    if next_button == "I'm done, let's go to the feedback section":
        st.session_state['clear_messages'] = True
        st.session_state['chat_messages'] = msgs.messages
        st.switch_page('pages/submit_feedback.py')


with st.container():
    if user_prompt:
        st.chat_message("human").write(user_prompt)

        topic, rec_list = get_recommendation(sv, user_prompt)
        if topic:
            extended_user_prompt = user_prompt + f" if relevant, try to recommend out of {rec_list}"
            st.toast(f"{topic}, {rec_list}")
        elif is_info_request(user_prompt):
            extended_user_prompt = user_prompt + ". Focus in your response in my topics of interest."
            st.toast("Info request")
        else:
            extended_user_prompt = user_prompt
            st.toast('No recommendation or info requested!')

        # Note: new messages are saved to history automatically by Langchain during run
        config = {"configurable": {"session_id": "any"}}
        response = chain_with_history.invoke({"sentence": extended_user_prompt}, config)

        with st.chat_message("ai"):
            message_placeholder = st.empty()  # Create a placeholder for the assistant's response
            length_of_wait = int(len(response.content)/40)
            for i in range(length_of_wait):  # Adjust the range for how long you want to show the "thinking" animation
                if i % 4 == 0:
                    message_placeholder.write("Typing")
                elif i % 4 == 1:
                    message_placeholder.write("Typing.")
                elif i % 4 == 2:
                    message_placeholder.write("Typing..")
                else:
                    message_placeholder.write("Typing...")
                time.sleep(0.5)  # Adjust the speed of the animation

            # After the delay, update the placeholder with the actual response
            message_placeholder.write(response.content)


