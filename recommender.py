import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load movies and ratings
movies = pd.read_csv('data/movies.csv')
ratings = pd.read_csv('data/ratings.csv')
tags = pd.read_csv('data/tags.csv')

# Compute average ratings
avg_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()
avg_ratings.columns = ['movieId', 'rating']

# Merge ratings into movies
movies = movies.merge(avg_ratings, on='movieId', how='left')

tag_df = tags.groupby('movieId')['tag'].apply(lambda x: ', '.join(set(x.dropna().astype(str)))).reset_index()
tag_df.columns = ['movieId', 'tags']
movies = movies.merge(tag_df, on='movieId', how='left')

# Extract year from title
movies['year'] = movies['title'].apply(
    lambda x: int(re.search(r'\((\d{4})\)', x).group(1)) if re.search(r'\((\d{4})\)', x) else None
)
movies['year'] = pd.to_numeric(movies['year'], errors='coerce')

# Prepare combined text
movies['combined'] = movies['title'] + ' ' + movies['genres'].str.replace('|', ' ', regex=False)

# TF-IDF vectorization
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(movies['combined'])
similarity = cosine_similarity(tfidf_matrix)

def get_recommendations(title, top_n=50, alpha=0.5, beta=0.5):
    title = title.lower().strip()
    if title not in movies['title'].str.lower().values:
        return []

    idx = movies[movies['title'].str.lower() == title].index[0]
    sim_scores = list(enumerate(similarity[idx]))

    scored_recommendations = []
    for i, sim in sim_scores:
        if i == idx:
            continue  # skip the same movie
        rating = movies.iloc[i]['rating']
        norm_rating = rating / 5.0 if pd.notnull(rating) else 0  # normalize and handle missing
        final_score = alpha * sim + beta * norm_rating
        scored_recommendations.append((i, final_score))

    # Sort by final score
    scored_recommendations = sorted(scored_recommendations, key=lambda x: x[1], reverse=True)
    top_indices = [i for i, score in scored_recommendations[:top_n]]

    # Prepare result DataFrame
    recommendations = movies.iloc[top_indices][['title', 'genres', 'year', 'rating', 'tags']].copy()


    # Round rating to 1 decimal
    recommendations['rating'] = recommendations['rating'].round(1)
    recommendations = recommendations.sort_values(by='rating', ascending=False)
    return recommendations.to_dict(orient='records')
