import streamlit as st


@st.dialog("See Similar Accounts", width="large")
def show_similar(sv, sv_vector):
    st.write(sv.get_similar(sv_vector)[['name','screen_name','description','similarity','twitter_id']])
    return



from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@st.dialog("See Similar Users", width="large")
def find_most_similar(mean_vector, persona_details, top_n=5):
    # Let's assume mean_vector is a 1D numpy array
    # And persona_details['sv'] contains 1D numpy arrays as well

    # Step 1: Stack the vectors from the 'sv' column into a 2D numpy array
    sv_matrix = np.stack(persona_details['sv'].values)

    # Step 2: Compute cosine similarity between mean_vector and all rows in sv_matrix
    # Reshape mean_vector to 2D for sklearn
    similarities = cosine_similarity(sv_matrix, mean_vector.reshape(1, -1)).flatten()

    if top_n > 1:
        persona_details['similarity'] = similarities
        top_5 = persona_details.nlargest(top_n, 'similarity')
        st.table(top_5[['screen_name','location','description','url','similarity']])
    elif top_n == 1:
        most_similar_idx = np.argmax(similarities)
        most_similar_user = persona_details.iloc[most_similar_idx]
        if type(most_similar_user['image'])==str:
            st.image(most_similar_user['image'], caption=most_similar_user['screen_name'], width=150)
        st.markdown(f"### {most_similar_user['screen_name']}")
        st.markdown(f"[{most_similar_user['url']}](%s)" % most_similar_user['url'])
        st.markdown(f"{most_similar_user['description']}")
        st.markdown(f"{most_similar_user['location']}")
        st.markdown(f"#### Additional SV info:")
        st.markdown(f"{most_similar_user['persona_description']}")

