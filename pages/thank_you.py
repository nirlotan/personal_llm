import streamlit as st

st.markdown("<div style='text-align: center;'><h3>Thank you very much for your participation!</h3></div>", unsafe_allow_html=True)
st.balloons()

def redirect_button(url, text):
    cols = st.columns(3)
    cols[1].markdown(
        f'<a href="{url}" target="_blank"><button text-align="center" font-size="20px">{text}</button></a>',
        unsafe_allow_html=True,
    )

if 'user_from_prolific' in st.session_state:
    redirect_button(f"https://app.prolific.com/submissions/complete?cc={st.session_state['my_api_keys']['prolific_approval']}",
                    "Click here to be redirected to Prolific to get your credit")
