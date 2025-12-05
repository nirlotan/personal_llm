# Personal LLM Application – High Level Documentation

## Overview
This application is an interactive, research-oriented web app built with Streamlit. It explores the impact of personalization on user interactions with large language models (LLMs). The app guides users through a three-part process: selecting interests, chatting with a personalized LLM, and providing feedback.

## Main Features
1. **User Onboarding & Personalization**
   - Users select 3–5 topics of interest from a curated list.
   - For each topic, users pick several social media accounts they find interesting.
   - The app builds a user profile and computes a personalized embedding vector based on these selections.

2. **Personalized Chat with LLM**
   - Users engage in a chat with an LLM (OpenAI GPT-4o-mini via LangChain).
   - The system prompt is dynamically generated to reflect the user's selected interests and the persona of a real social media account.
   - The chat interface supports friendly conversation, recommendations, and factual information requests, with intent detection.

3. **Feedback Collection**
   - After chatting, users complete a feedback survey about their experience.
   - Survey results and chat logs are stored anonymously in Firebase for research analysis.

## Architecture & Key Components
- **Streamlit Frontend**: Multi-page app with onboarding (`tutorial.py`, `cold_start.py`), chat (`chat.py`), and feedback (`submit_feedback.py`).
- **Data Handling**: Loads and processes account and persona data from Excel/CSV/Pickle files in the `data/` directory.
- **Personalization Logic**: Computes user embedding vectors and finds the most similar persona for prompt generation.
- **LLM Integration**: Uses LangChain and OpenAI APIs to manage chat history and generate responses.
- **Session State**: Stores user selections, embeddings, chat history, and system prompts in Streamlit's session state for a seamless experience.
- **Feedback Storage**: Integrates with Firebase to store survey results and chat logs.

## Data Files
- `data/popular_accounts_manually_validated_with_sv.xlsx`: Main source of account and topic data, including precomputed embeddings.
- `data/persona_details_v2.pkl`: Persona details for prompt personalization.
- `data/questionnaire.csv`: Survey questions for feedback.

## How It Works
1. **Onboarding**: Users select interests and accounts, which are used to compute a personalized profile.
2. **Prompt Generation**: The app finds the most similar persona and generates a system prompt for the LLM.
3. **Chat**: Users interact with the LLM, which responds in character, using the personalized prompt.
4. **Feedback**: Users rate their experience and submit feedback, which is stored for research.

## Technologies Used
- Python, Streamlit, Pandas, Numpy, Scikit-learn
- LangChain, OpenAI API
- Firebase (for feedback storage)

## Research Context
This app is designed for a study on how personalization affects LLM-based conversations. All data is handled anonymously, and user privacy is prioritized.


---
