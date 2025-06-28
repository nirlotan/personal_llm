import streamlit as st
from st_pages import add_page_title, get_nav_from_toml

st.set_page_config(layout="wide")
with open( "styles.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)
# Importing stylesheet
#st.markdown('<style>' + open('./style.css').read() + '</style>', unsafe_allow_html=True)
# Hides Streamlit's default menu and footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# If you want to use the no-sections version, this
# defaults to looking in .streamlit/pages.toml, so you can
# just call `get_nav_from_toml()`
nav = get_nav_from_toml(".streamlit/pages.toml")

pg = st.navigation(nav)

pg.run()