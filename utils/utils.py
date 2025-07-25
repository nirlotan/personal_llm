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
        st.session_state['remaining_chat_types'] = ['Personalized Random', 'Personalized Like Me']
        set_user_guid()
        st.session_state['init_complete'] = True


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

def new_get_similar(sv, input: str, etype: str, topn: int = 10):
    """
    This function returns the topn similar entities for a given entity

    Parameters
    ----------
    input : twitter user id or username
    by : 'userid', 'username' or vector default is username
    topn : requested numner of similar entities

    Returns
    -------
    Pandas dataframe with the top n similar entities details

    """

    if isinstance(input, int) or (isinstance(input, str) and input.isdigit()):
        input = sv.validate_userid(input)
    elif isinstance(input, str):
        input = sv.validate_username(input)
    elif isinstance(input, np.ndarray):
        input = input

    sim = sv.sv.wv.most_similar(input, topn=50000)

    similar = pd.DataFrame(sim, columns=['twitter_id', 'similarity'])
    similar = pd.merge(similar, sv.entities, on='twitter_id', how='left')
    similar = similar.dropna(subset=['dbpedia_types'])

    similar['dbpedia_types'] = similar['dbpedia_types'].apply(lambda x: str(x))# if type(x) == str else x)
    filtered_similar = similar[similar['dbpedia_types'].apply(lambda x: etype in x)]

    return filtered_similar



class ClassifyRecommend(dspy.Signature):
    """Classify if a sentence contains a request for recommendation or not (even explicitly), or if the user asked you about something you like
       and on which topic from a predefined list of topics"""

    sentence: str = dspy.InputField()
    is_recommendation: bool = dspy.OutputField()
    topic: Literal['TennisTournament', 'Mountain', 'TelevisionStation', 'FilmFestival', 'Scientist', 'Building', 'SpaceMission', 'IceHockeyLeague', 'Sport', 'Album', 'Musical', 'ShoppingMall', 'PokerPlayer', 'VoiceActor', 'RadioStation', 'NascarDriver', 'Single', 'SoccerLeague', 'MotorsportSeason', 'CanadianFootballLeague', 'CyclingRace', 'FormulaOneTeam', 'Theatre', 'Racecourse', 'ComedyGroup', 'Cardinal', 'Cricketer', 'Coach', 'Artist', 'Skater', 'TennisLeague', 'SoccerManager', 'Youtuber', 'Writer', 'AdultActor', 'School', 'BadmintonPlayer', 'MotorsportRacer', 'HorseRace', 'Presenter', 'Skier', 'AmusementParkAttraction', 'Anime', 'PoliticalParty', 'SoftballLeague', 'FootballLeagueSeason', 'RaceTrack', 'Journalist', 'Religious', 'MusicalArtist', 'Race', 'BusinessPerson', 'Olympics', 'Cinema', 'Airport', 'Election', 'Boxer', 'River', 'MusicGenre', 'ScreenWriter', 'BaseballTeam', 'Chef', 'SoccerTournament', 'ClassicalMusicArtist', 'SnookerPlayer', 'BeautyQueen', 'RadioHost', 'PeriodicalLiterature', 'RugbyLeague', 'SportsClub', 'EducationalInstitution', 'ChristianBishop', 'GolfCourse', 'AustralianFootballTeam', 'GridironFootballPlayer', 'RadioProgram', 'VolleyballPlayer', 'SnookerChamp', 'CollegeCoach', 'MusicalWork', 'ArtistDiscography', 'Food', 'Venue', 'Hotel', 'Dancer', 'Publisher', 'Convention', 'Insect', 'Tournament', 'Comedian', 'MartialArtist', 'Bank', 'Software', 'Broadcaster', 'AcademicJournal', 'Airline', 'RugbyPlayer', 'MixedMartialArtsLeague', 'HockeyTeam', 'MovieDirector', 'TelevisionShow', 'CricketTeam', 'Village', 'ProgrammingLanguage', 'BaseballPlayer', 'ComicsCreator', 'Museum', 'Library', 'GovernmentAgency', 'BasketballPlayer', 'Bodybuilder', 'Astronaut', 'FashionDesigner', 'FigureSkater', 'Winery', 'SpeedwayRider', 'Place', 'Restaurant', 'Newspaper', 'HollywoodCartoon', 'TennisPlayer', 'Fashion', 'Legislature', 'RugbyClub', 'SportsLeague', 'SoccerPlayer', 'Cleric', 'SportFacility', 'WrittenWork', 'Film', 'TelevisionHost', 'WomensTennisAssociationTournament', 'GolfTournament', 'Bird', 'BasketballTeam', 'SoccerClubSeason', 'AmericanFootballTeam', 'Surfer', 'HistoricBuilding', 'HistoricPlace', 'LacrosseLeague', 'Cyclist', 'NationalFootballLeagueEvent', 'Automobile', 'Producer', 'VideoGame', 'FictionalCharacter', 'SoccerClub', 'SocietalEvent', 'University', 'DartsPlayer', 'SportsEvent', 'Architect', 'ComicsCharacter', 'Swimmer', 'NCAATeamSeason', 'IceHockeyPlayer', 'BaseballLeague', 'Bridge', 'FormulaOneRacer', 'Politician', 'Game', 'Artwork', 'Beverage', 'Economist', 'Manga', 'Wrestler', 'SportsTeam', 'Magazine', 'BroadcastNetwork', 'Brewery', 'RacingDriver', 'Mayor', 'SportsManager', 'BeachVolleyballPlayer', 'AmericanFootballLeague', 'Curler', 'Lake', 'Model', 'CyclingTeam', 'WrestlingEvent', 'Book', 'AmericanFootballPlayer', 'WinterSportPlayer', 'Actor', 'Athlete', 'GolfPlayer', 'Gymnast', 'RecordLabel', 'MemberOfParliament', 'ArchitecturalStructure', 'Band', 'Governor', 'Rocket', 'Congressman', 'BasketballLeague'] = dspy.OutputField()

class ClassifyInfoRequest(dspy.Signature):
    """Classify if a sentence contains a request for general knowledge or factual information (not personal information)"""

    sentence: str = dspy.InputField()
    is_info_request: bool = dspy.OutputField()


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
    topic: Optional[Literal[
        'TennisTournament', 'Mountain', 'TelevisionStation', 'FilmFestival', 'Scientist', 'Building', 'SpaceMission', 'IceHockeyLeague', 'Sport', 'Album', 'Musical', 'ShoppingMall', 'PokerPlayer', 'VoiceActor', 'RadioStation', 'NascarDriver', 'Single', 'SoccerLeague', 'MotorsportSeason', 'CanadianFootballLeague', 'CyclingRace', 'FormulaOneTeam', 'Theatre', 'Racecourse', 'ComedyGroup', 'Cardinal', 'Cricketer', 'Coach', 'Artist', 'Skater', 'TennisLeague', 'SoccerManager', 'Youtuber', 'Writer', 'AdultActor', 'School', 'BadmintonPlayer', 'MotorsportRacer', 'HorseRace', 'Presenter', 'Skier', 'AmusementParkAttraction', 'Anime', 'PoliticalParty', 'SoftballLeague', 'FootballLeagueSeason', 'RaceTrack', 'Journalist', 'Religious', 'MusicalArtist', 'Race', 'BusinessPerson', 'Olympics', 'Cinema', 'Airport', 'Election', 'Boxer', 'River', 'MusicGenre', 'ScreenWriter', 'BaseballTeam', 'Chef', 'SoccerTournament', 'ClassicalMusicArtist', 'SnookerPlayer', 'BeautyQueen', 'RadioHost', 'PeriodicalLiterature', 'RugbyLeague', 'SportsClub', 'EducationalInstitution', 'ChristianBishop', 'GolfCourse', 'AustralianFootballTeam', 'GridironFootballPlayer', 'RadioProgram', 'VolleyballPlayer', 'SnookerChamp', 'CollegeCoach', 'MusicalWork', 'ArtistDiscography', 'Food', 'Venue', 'Hotel', 'Dancer', 'Publisher', 'Convention', 'Insect', 'Tournament', 'Comedian', 'MartialArtist', 'Bank', 'Software', 'Broadcaster', 'AcademicJournal', 'Airline', 'RugbyPlayer', 'MixedMartialArtsLeague', 'HockeyTeam', 'MovieDirector', 'TelevisionShow', 'CricketTeam', 'Village', 'ProgrammingLanguage', 'BaseballPlayer', 'ComicsCreator', 'Museum', 'Library', 'GovernmentAgency', 'BasketballPlayer', 'Bodybuilder', 'Astronaut', 'FashionDesigner', 'FigureSkater', 'Winery', 'SpeedwayRider', 'Place', 'Restaurant', 'Newspaper', 'HollywoodCartoon', 'TennisPlayer', 'Fashion', 'Legislature', 'RugbyClub', 'SportsLeague', 'SoccerPlayer', 'Cleric', 'SportFacility', 'WrittenWork', 'Film', 'TelevisionHost', 'WomensTennisAssociationTournament', 'GolfTournament', 'Bird', 'BasketballTeam', 'SoccerClubSeason', 'AmericanFootballTeam', 'Surfer', 'HistoricBuilding', 'HistoricPlace', 'LacrosseLeague', 'Cyclist', 'NationalFootballLeagueEvent', 'Automobile', 'Producer', 'VideoGame', 'FictionalCharacter', 'SoccerClub', 'SocietalEvent', 'University', 'DartsPlayer', 'SportsEvent', 'Architect', 'ComicsCharacter', 'Swimmer', 'NCAATeamSeason', 'IceHockeyPlayer', 'BaseballLeague', 'Bridge', 'FormulaOneRacer', 'Politician', 'Game', 'Artwork', 'Beverage', 'Economist', 'Manga', 'Wrestler', 'SportsTeam', 'Magazine', 'BroadcastNetwork', 'Brewery', 'RacingDriver', 'Mayor', 'SportsManager', 'BeachVolleyballPlayer', 'AmericanFootballLeague', 'Curler', 'Lake', 'Model', 'CyclingTeam', 'WrestlingEvent', 'Book', 'AmericanFootballPlayer', 'WinterSportPlayer', 'Actor', 'Athlete', 'GolfPlayer', 'Gymnast', 'RecordLabel', 'MemberOfParliament', 'ArchitecturalStructure', 'Band', 'Governor', 'Rocket', 'Congressman', 'BasketballLeague'
    ]] = dspy.OutputField()

def get_user_intent(sentence):
    with dspy.context(lm=st.session_state['lm']):
        classify = dspy.Predict(ClassifyUserIntent)
        result = classify(sentence=sentence)
    return result

def get_recommendation(sv, topic):
    user_sv = st.session_state["user_embeddings"]
    similar = new_get_similar(sv, user_sv, topic).head(10)
    return similar['name'].tolist()

def is_info_request(sentence):
    with dspy.context(lm=st.session_state['lm']):
        classify = dspy.Predict(ClassifyInfoRequest)
        result = classify(sentence=sentence)
        if result.is_info_request:
            return True
        else:
            return False

@st.dialog("System Message", width="large")
def show_system_message():
    st.code(st.session_state['system_message'],wrap_lines=True)