import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gzip
import shutil

# --- Google Drive Download Helpers ---
def download_file_from_google_drive(file_id, destination):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)

# --- Ensure similarity.pkl is available ---
SIMILARITY_FILE_ID = '1u_GB-EfOVKdXx3hmU_CZfNPO8QcD1BLa'
SIMILARITY_FILE_PATH = 'similarity.pkl'
SIMILARITY_GZ_PATH = 'similarity.pkl.gz'

if not os.path.exists(SIMILARITY_FILE_PATH):
    if os.path.exists(SIMILARITY_GZ_PATH):
        with gzip.open(SIMILARITY_GZ_PATH, 'rb') as f_in:
            with open(SIMILARITY_FILE_PATH, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        download_file_from_google_drive(SIMILARITY_FILE_ID, SIMILARITY_FILE_PATH)

# --- Load data ---
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open(SIMILARITY_FILE_PATH, 'rb'))

# --- TMDB API Function ---
session = requests.Session()

def fetch_movie_details(movie_id):
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=916ed8867edce6717dda3cffd517274c&language=en-US'
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            'poster_url': "https://image.tmdb.org/t/p/w500/" + data.get('poster_path', ''),
            'title': data.get('title', 'N/A'),
            'tagline': data.get('tagline', 'N/A'),
            'overview': data.get('overview', 'N/A'),
            'language': data.get('original_language', 'N/A'),
            'release_date': data.get('release_date', 'N/A'),
            'status': data.get('status', 'N/A'),
            'budget': data.get('budget', 'N/A'),
            'revenue': data.get('revenue', 'N/A'),
            'adult': data.get('adult', False),
            'genres': ', '.join([genre['name'] for genre in data.get('genres', [])]),
            'production_companies': ', '.join([company['name'] for company in data.get('production_companies', [])]),
            'rating': f"{data.get('vote_average', 'N/A')} ({data.get('vote_count', 0)} votes)"
        }
    except requests.exceptions.RequestException:
        st.warning("Failed to fetch movie details. Please try again later.")
        return {
            'poster_url': '',
            'title': 'Unavailable',
            'tagline': '',
            'overview': 'Could not retrieve movie details.',
            'language': 'N/A',
            'release_date': 'N/A',
            'status': 'N/A',
            'budget': 0,
            'revenue': 0,
            'adult': False,
            'genres': 'N/A',
            'production_companies': 'N/A',
            'rating': 'N/A'
        }

# --- Recommendation Function ---
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_details = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_details.append(fetch_movie_details(movie_id))
    return recommended_details

# --- Streamlit UI ---
st.title('🎬 Movie Recommender System')

selected_movie_name = st.selectbox('Select a movie you like:', movies['title'].values)

if st.button('Recommend'):
    details_list = recommend(selected_movie_name)
    cols = st.columns(5)

    for idx, col in enumerate(cols):
        with col:
            details = details_list[idx]
            if details['poster_url']:
                st.image(details['poster_url'])
            st.markdown(f"**{details['title']}**")
            st.caption(details['tagline'])
            st.write(f"**Overview:** {details['overview']}")
            st.write(f"**Language:** {details['language'].upper()}")
            st.write(f"**Release Date:** {details['release_date']}")
            st.write(f"**Status:** {details['status']}")
            st.write(f"**Budget:** ${details['budget']:,}")
            st.write(f"**Revenue:** ${details['revenue']:,}")
            st.write(f"**Adult Content:** {'Yes' if details['adult'] else 'No'}")
            st.write(f"**Genres:** {details['genres']}")
            st.write(f"**Production Companies:** {details['production_companies']}")
            st.write(f"**Ratings:** {details['rating']}")
