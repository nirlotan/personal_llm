import time

import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from streamlit.components import v1 as components
from utils.utils import get_user_intent, get_recommendation




# --- A dummy anchor to scroll to ---
scroll_to_bottom = """
    <div id="scroll-anchor"></div>
    <script>
        var anchor = document.getElementById("scroll-anchor");
        if (anchor) {
            anchor.scrollIntoView({behavior: "smooth"});
        }
    </script>
"""


def split_before_last_marker(text, marker="._."):
    before, _, _ = text.rpartition(marker)
    return before.strip()


if 'init_complete' not in st.session_state:
    st.switch_page('pages/cold_start.py')

openai_api_key = st.session_state['my_api_keys']["openai_api_key"]

class ChatSessionClass:
    def __init__(self,
                 system_message: str):
        st.session_state['system_message'] = system_message
        self.sv = st.session_state['sv']
        self.msgs = StreamlitChatMessageHistory(key="langchain_messages")
        self.msgs_len = len(self.msgs.messages)
        self.msgs.clear()
        self.chat_model = ChatOpenAI( api_key=openai_api_key,
                                      model="gpt-4o", # gpt-4o-mini
                                      temperature=0.5,
                                    )

        # --- Initialize session state variables ---
        st.session_state['last_system_message_time'] = time.time()

    def reset(self, system_message: str):
        # Re-call __init__ to reset attributes
        self.__init__(system_message)

    def get_messages_len(self):
        return self.msgs_len - 1

    def get_messages(self):
        return self.msgs.messages

    def inject_first_message(self, chain_with_history):
        if f"first_message_injected_{st.session_state['user_for_the_chat']}" not in st.session_state:
            injected_message = "Introduce yourself. Tell the user to feel free to ask you questions and guide the user to have a friendly chat with you, ask for recommendations and factual information questions."
            config = {"configurable": {"session_id": "any"}}
            response = chain_with_history.invoke({"sentence": injected_message}, config)
            # with st.chat_message("ai", avatar="🐼"):
            #     message_placeholder = st.empty()
            #     message_placeholder.write(response.content)
        st.session_state[f"first_message_injected_{st.session_state['user_for_the_chat']}"] = True
        return chain_with_history

    def modify_prompt_on_intent(self, user_prompt):
        user_intent = get_user_intent(user_prompt)
        if user_intent['intent'].value in ["Friendly Chat", "Recommendation", "Factual Information Request"]:
            st.session_state['chat_status'][user_intent['intent']] = 1

        if user_intent['intent'] == "Recommendation":
            if user_intent['topic']:
                rec_list = get_recommendation(self.sv, user_intent['topic'])
                extended_user_prompt = f"{user_prompt}._. If relevant, try to recommend from: {rec_list}, but try to suggest unique and interesting recommendations. Be specific and concise. Don't ramble and keep your answer to be under 100 words."
            else:
                extended_user_prompt = user_prompt + "._. Be specific and concise. Don't ramble and keep your answer to be under 100 words."
        elif user_intent['intent'] == "Factual Information Request":
            # st.toast("Factual Information Request")
            extended_user_prompt = user_prompt + "._. As part of providing the information requested, integrate your personal perspective, based on your topics of interest."
        else:
            extended_user_prompt = user_prompt + "._. Be specific and concise. Don't ramble and keep your answer to be under 100 words."
        return extended_user_prompt

    def chat_session(self):

        # --- LangChain setup ---
        prompt = ChatPromptTemplate.from_messages([
            ("system", st.session_state['system_message']),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{sentence}"),
        ])


        chain = prompt | self.chat_model

        chain_with_history = RunnableWithMessageHistory(
            chain,
            lambda session_id: self.msgs,
            input_messages_key="sentence",
            history_messages_key="history",
        )

        chain_with_history = self.inject_first_message(chain_with_history)
        components.html(scroll_to_bottom, height=0)

        self.msgs_len = len(self.msgs.messages) - 2

        # --- Render previous messages ---
        for msg in self.msgs.messages[1:]:
            avt = "🐨" if msg.type=="human" else "🐼"
            message = split_before_last_marker(msg.content) if msg.type=="human" else msg.content
            st.chat_message(msg.type, avatar=avt).write(message)
            # Re-scroll to bottom after new message
            components.html(scroll_to_bottom, height=0)

        # --- Handling User Prompt ---

        if user_prompt := st.chat_input(placeholder="Type your message:"):
            st.chat_message("human", avatar ="🐨").write(user_prompt)
            st.session_state['messages_timing'].append(round(time.time() - st.session_state['last_system_message_time']))

            extended_user_prompt = self.modify_prompt_on_intent(user_prompt)

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

                # Re-scroll to bottom after new message
                components.html(scroll_to_bottom, height=0)
                st.session_state['last_system_message_time'] = time.time()




