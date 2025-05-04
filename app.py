import streamlit as st 
import pickle
import pandas as pd 
import requests

def fetch_movie_details(movie_id):
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=916ed8867edce6717dda3cffd517274c&language=en-US')
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

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_details = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_details.append(fetch_movie_details(movie_id))
    return recommended_details

movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))

st.title('Movie Recommender System')

selected_movie_name = st.selectbox(
    'How would you like to be contacted?',
    movies['title'].values)

if st.button('Recommend'):
    details_list = recommend(selected_movie_name)
    cols = st.columns(5)
    
    for idx, col in enumerate(cols):
        with col:
            details = details_list[idx]
            st.image(details['poster_url'])
            st.markdown(f"**{details['title']}**")
            st.caption(f"*{details['tagline']}*")
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
