import os
import pandas as pd
from socialvec.socialvec import SocialVec
import streamlit as st
from typing import Optional, Literal
from enum import Enum
import numpy as np
import dspy
import toml
from langchain.chains import LLMChain
from streamlit_javascript import st_javascript
from user_agents import parse
import uuid
from datetime import datetime

categories_file_path = os.path.join("data","popular_accounts_manually_validated_with_sv.xlsx")

@st.cache_resource(show_spinner="Initial loading. Please wait...")
def load():
    sv = SocialVec()
    categories = pd.ExcelFile(categories_file_path).sheet_names
    accounts = pd.DataFrame()
    for sheet in categories:
        df_rec = pd.read_excel(categories_file_path, sheet_name=sheet)
        df_rec = df_rec[df_rec['use']==1]
        df_rec['category'] = sheet
        accounts = pd.concat([accounts,df_rec])

    accounts['sv'] = accounts['sv'].apply(lambda x: np.fromstring(str(x).strip('[]'), sep=' '))
    df_dbpedia = pd.read_csv('data/dbpedia_types.csv')
    sv.entities = pd.merge(sv.entities,df_dbpedia, on='screen_name', how='left')

    accounts = accounts[['twitter_screen_name','twitter_user_id','twitter_name','use','twitter_desc','wikidata_label','wikidata_desc','wikidata_desc_np','category','sv']]

    my_keys = toml.load("/etc/secrets/keys.toml")
    lm = dspy.LM('openai/gpt-4o', api_key=my_keys["openai_api_key"]) #openai/gpt-4o-mini

    return sv, categories, accounts, my_keys, lm

def session_init():
    if 'init_complete' not in st.session_state:
        sv, categories, accounts, my_keys, lm = load()

        st.session_state['sv'] = sv
        st.session_state['categories'] = categories
        st.session_state['accounts'] = accounts
        st.session_state['my_api_keys'] = my_keys
        st.session_state['lm'] = lm
        st.session_state['experiment_start_time'] = str(datetime.now())
        st.session_state['messages_timing'] = []
        st.session_state['number_of_feedbacks_provided'] = 0
        st.session_state['remaining_chat_types'] = my_keys['types_of_chat_list'].copy()
        st.session_state['recommendation_topics'] = []
        st.session_state['init_complete'] = True

        set_user_guid()

def set_user_guid():
    if 'unique_session_id' not in st.session_state:
        if "PROLIFIC_PID" in st.query_params:
            st.session_state['user_from_prolific'] = True
            st.session_state['unique_session_id'] = f"{st.query_params['PROLIFIC_PID']}__{st.query_params['STUDY_ID']}__{st.query_params['SESSION_ID']}"
        else:
            st.session_state['unique_session_id'] = str(uuid.uuid4())
    return

def check_pc_mobile():
    try:
        # check user agent to suppress non-mandatory parts when running on mobile
        ua_string = st_javascript("""window.navigator.userAgent;""")
        user_agent = parse(ua_string)
        st.session_state.is_session_pc = user_agent.is_pc
    except:
        st.session_state.is_session_pc = True

def check_if_same_type(user_id, type):
    try:
        if type in st.session_state['sv'].entities[st.session_state['sv'].entities['twitter_id'] == user_id].iloc[0]['dbpedia_types']:
            return True
        else:
            return False
    except:
        pass

def safe_get_similar(sv, user_embeddings,x):
    try:
        return sv.get_similarity(user_embeddings, x)
    except:
        return 0

def new_get_similar(sv, user_embeddings: str, topic: str, topn: int = 10):
    """
    This function returns the topn similar entities for a given entity
    """

    topic_subset = sv.entities[sv.entities['topic'] == topic].copy()

    topic_subset['similarity'] = topic_subset['screen_name'].apply(lambda x: safe_get_similar(sv,user_embeddings,x))
    topic_subset.sort_values('similarity', ascending=False, inplace=True)
    return topic_subset.head(topn)['name'].to_list()

# Define Intent Enum
class UserIntent(str, Enum):
    FRIENDLY_CHAT = "Friendly Chat"
    RECOMMENDATION = "Recommendation"
    INFO_REQUEST = "Factual Information Request"
    OTHER = "Other"


class ClassifyUserIntent(dspy.Signature):
    """
    Classify a sentence into a single intent type.
    Recommendation may be explicit, for example if the user asked you about something you like or did.
    If you are not sure between "Info Request" and "Recommendation", the intent will be "Recommendation"
    If the intent is 'Recommendation', a related topic is also returned.

    """

    sentence: str = dspy.InputField()
    intent: UserIntent = dspy.OutputField()
    topic: Optional[Literal['Tournament', 'SocietalEvent', 'SportsEvent', 'TelevisionStation',
       'Broadcaster', 'BroadcastNetwork', 'Film', 'Scientist',
       'Publisher', 'Museum', 'Venue', 'GovernmentAgency', 'Place',
       'Sport', 'SportsLeague', 'BaseballTeam', 'SportsTeam',
       'AmericanFootballTeam', 'BasketballTeam', 'SportsClub', 'Band',
       'Musical', 'Artist', 'MusicalArtist', 'PokerPlayer', 'VoiceActor',
       'TelevisionShow', 'NascarDriver', 'MotorsportRacer', 'Race',
       'RacingDriver', 'Automobile', 'Cyclist', 'FormulaOneRacer',
       'Cricketer', 'Coach', 'GridironFootballPlayer',
       'AmericanFootballPlayer', 'CollegeCoach', 'Comedian', 'Actor',
       'Skater', 'FigureSkater', 'WinterSportPlayer', 'SoccerPlayer',
       'Youtuber', 'Writer', 'Economist', 'AdultActor', 'School',
       'EducationalInstitution', 'University', 'Presenter', 'RadioHost',
       'Journalist', 'TelevisionHost', 'PoliticalParty', 'BusinessPerson',
       'Airport', 'Boxer', 'Magazine', 'Chef', 'Model',
       'PeriodicalLiterature', 'Newspaper', 'WrittenWork', 'Athlete',
       'RadioProgram', 'Beverage', 'Hotel', 'Dancer', 'Convention',
       'Game', 'MartialArtist', 'Software', 'VideoGame', 'Airline',
       'HockeyTeam', 'MovieDirector', 'FictionalCharacter',
       'BaseballPlayer', 'ComicsCreator', 'BasketballPlayer', 'Astronaut',
       'FashionDesigner', 'Fashion', 'Restaurant', 'TennisPlayer',
       'Swimmer', 'IceHockeyPlayer', 'Politician', 'Wrestler',
       'GolfPlayer', 'RecordLabel']] = dspy.OutputField()

def get_user_intent(sentence):
    with dspy.context(lm=st.session_state['lm']):
        classify = dspy.Predict(ClassifyUserIntent)
        result = classify(sentence=sentence)
    return result

def get_recommendation(sv, topic):
    user_sv = st.session_state["user_embeddings"]
    similar = new_get_similar(sv, user_sv, topic, topn=7)
    return similar

@st.dialog("System Message", width="large")
def show_system_message():
    st.code(st.session_state['system_message'],wrap_lines=True)