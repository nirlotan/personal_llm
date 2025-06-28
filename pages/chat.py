# --- Imports ---
import time
import streamlit_antd_components as sac
from streamlit_extras.bottom_container import bottom
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from utils.utils import *
import streamlit.components.v1 as components

def split_before_last_marker(text, marker="._."):
    before, _, _ = text.rpartition(marker)
    return before.strip()

if 'init_complete' not in st.session_state:
    st.switch_page('pages/cold_start.py')

# --- Configuration ---
openai_api_key = st.session_state['my_api_keys']["openai_api_key"]
app_config = toml.load("config.toml")


@st.dialog("Conversation with a Language Model")
def chat_popup():
    st.write(f"Next, you’ll chat with a large language model, exchanging a few messages.")
    st.write(f"Try interacting with the model by:  \n 1. having a **casual conversation,**  \n 2. asking for **recommendations,**  \n 3. and looking up **actual information.**")
    st.badge("**Suggestion:** Try asking the bot: _'Tell me about yourself_'...", icon="💡", color="green")
    if st.button("Confirm"):
        st.session_state.confirm3 = True
        st.rerun()

if 'chat_status' not in st.session_state:
    st.session_state['chat_status'] = {"Friendly Chat": 0,
                                       "Recommendation": 0,
                                       "Factual Information Request" : 0
                                        }

# --- Load session data ---

if 'system_message' not in st.session_state:
    st.switch_page('pages/cold_start.py')
system_message = st.session_state['system_message']

sv = st.session_state['sv']

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

if "confirm3" not in st.session_state:
    chat_popup()

if 'injected_first_message' not in st.session_state:
    injected_message = "Introduce yourself. Tell the user to feel free to ask you questions and guide the user to have a friendly chat with you, ask for recommendations and factual information questions."
    config = {"configurable": {"session_id": "any"}}
    response = chain_with_history.invoke({"sentence": injected_message}, config)
    with st.chat_message("ai", avatar="🐼"):
        message_placeholder = st.empty()
        message_placeholder.write(response.content)
    st.session_state['injected_first_message'] = True

if 'last_system_message_time' not in st.session_state:
    st.session_state['last_system_message_time'] = time.time()

# --- Add a dummy anchor and scroll to it ---
scroll_to_bottom = """
    <div id="scroll-anchor"></div>
    <script>
        var anchor = document.getElementById("scroll-anchor");
        if (anchor) {
            anchor.scrollIntoView({behavior: "smooth"});
        }
    </script>
"""
components.html(scroll_to_bottom, height=0)


# --- Render previous messages ---
for msg in msgs.messages[1:]:
    avt = "🐨" if msg.type=="human" else "🐼"
    message = split_before_last_marker(msg.content) if msg.type=="human" else msg.content
    st.chat_message(msg.type, avatar=avt).write(message)

    # Re-scroll to bottom after new message
    components.html(scroll_to_bottom, height=0)

# --- Handling User Prompt ---

if user_prompt := st.chat_input(placeholder="Type your message:"):
    st.chat_message("human", avatar ="🐨").write(user_prompt)
    st.session_state['messages_timing'].append(round(time.time() - st.session_state['last_system_message_time']))

    extended_user_prompt = user_prompt + "._. Be concise (under 100 words)"

    user_intent = get_user_intent(user_prompt)
    if user_intent['intent'].value in ["Friendly Chat", "Recommendation", "Factual Information Request"]:
        st.session_state['chat_status'][user_intent['intent']]=1

    #st.toast(user_intent['intent'])
    if user_intent['intent']=="Recommendation":
        if user_intent['topic']:
            rec_list = get_recommendation(sv, user_intent['topic'])
            extended_user_prompt = f"{user_prompt}._. If relevant, try to recommend from: {rec_list}, but try to suggest unique and interesting recommendations. Be concise (under 100 words)."
            #st.toast(f"{user_intent['topic']}, {rec_list}")

    elif user_intent['intent'] == "Factual Information Request":
        #st.toast("Factual Information Request")
        extended_user_prompt = user_prompt + "._. When you provide the information requested, consider your personal perspective based on your topics of interest and emphasize it if relevant."

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


with bottom():

    st.write(st.session_state['messages_timing'])

    # Dynamic button options
    st.caption("Complete the following tasks in order to be able to move to the next step:")
    buttons_list = []
    chat_status_indexes = [i for i, (k, v) in enumerate(st.session_state['chat_status'].items()) if v == 1]

    if st.session_state.is_session_pc:
        sac.checkbox(
            items=[
                'Friendly Chat',
                'Recommendation',
                'Factual Information Request',
            ],
            label='Complete the following tasks in order to be able to move to the next step:', index=chat_status_indexes, align='left', size='lg', disabled=True
        )

    enable_feedback = msgs_len >= app_config['minimal_number_of_messages'] or all(
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
