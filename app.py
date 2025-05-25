from flask import Flask, render_template, request,jsonify
import re
import pandas as pd
from recommender import get_recommendations 
# from gemini_utils import get_mood_based_movies
from movie_ai import get_movie_recommendation,parse_response, get_movie_details


app = Flask(__name__)
# Load movies data
movies_df = pd.read_csv('data/movies.csv')

# Extract year from the title using regex
movies_df['year'] = movies_df['title'].apply(lambda x: re.search(r'\((\d{4})\)', x).group(1) if re.search(r'\((\d{4})\)', x) else None)
movies_df['year'] = pd.to_numeric(movies_df['year'], errors='coerce')

# Load ratings and calculate average rating per movie
ratings_df = pd.read_csv('data/ratings.csv')
avg_ratings = ratings_df.groupby('movieId')['rating'].mean().reset_index()
avg_ratings.columns = ['movieId', 'avg_rating']

# Merge with movies
movies_df = pd.merge(movies_df, avg_ratings, on='movieId', how='left')
# Load tags data and combine tags per movie
tags_df = pd.read_csv('data/tags.csv')
tags_agg = tags_df.groupby('movieId')['tag'].apply(lambda tags: ', '.join(tags.unique())).reset_index()
tags_agg.columns = ['movieId', 'tags']

# Merge tags into movies_df
movies_df = pd.merge(movies_df, tags_agg, on='movieId', how='left')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mood', methods=['GET'])
def mood_page():
    return render_template('mood.html')

@app.route('/no')
def home():
    return render_template("mood.html")

@app.route('/get_mood_recommendations', methods=['POST'])
def get_mood_recommendations():
    data = request.get_json()
    mood = data.get("mood", "")
    if not mood:
        return jsonify({"recommendations": []})
    
    try:
        raw_response = get_movie_recommendation(mood)
        print("Gemini Response:\n", raw_response)
        recommendations = parse_response(raw_response)
        if recommendations:
            return jsonify({"type": "recommendations", "data": recommendations})
        else:
            return jsonify({"type": "mood", "message": raw_response})

    except Exception as e:
        print("Error:", e)
        return jsonify({"recommendations": []})
    
@app.route('/get_movie_details', methods=['POST'])
def get_movie_details_route():
    data = request.get_json()
    movie_title = data.get("movie_title", "")
    if not movie_title:
        return jsonify({"detail": "Please provide a movie title."})
    
    try:
        details = get_movie_details(movie_title)
        return jsonify({"detail": details})
    except Exception as e:
        print("Error:", e)
        return jsonify({"detail": "Error fetching movie details."})

# @app.route('/get_recommendations', methods=['POST'])
# def get_general_recommendations():
#     mood = request.json.get('mood')
#     if not mood:
#         return jsonify({'error': 'Mood is required'}), 400

#     recommendations = get_mood_based_movies(mood)
#     print("Recommendations:", recommendations)
#     return jsonify({'recommendations': recommendations})
def parse_response(response_text):
    # Basic example assuming Gemini returns a bullet list format
    movies = []
    for line in response_text.split('\n'):
        if '-' in line:
            match = re.match(r"-\s*(.*) \((.*)\) - IMDb: (.*?)\s*:\s*(.*)", line)
            if match:
                title, genre, rating, description = match.groups()
                movies.append({
                    "title": title.strip(),
                    "genre": genre.strip(),
                    "rating": rating.strip(),
                    "description": description.strip()
                })
    return movies

@app.route('/recommend-by-genre', methods=['GET', 'POST'])
def recommend_by_genre():
    if request.method == 'POST':
        genre = request.form.get('genre')
        page = int(request.form.get('page', 1))
        filter_by = request.form.get('filter', 'rating')  # Default to 'rating'
        movies_per_page = 7

        # Filter movies by genre
        filtered_movies = movies_df[
            (movies_df['genres'].str.contains(genre, case=False, na=False)) &
            (movies_df['year'] > 2000)
        ]

        # Remove movies with missing years
        filtered_movies = filtered_movies.dropna(subset=['year'])

        # Sort based on the selected filter (rating or year)
        if filter_by == 'rating':
            filtered_movies['avg_rating'] = pd.to_numeric(filtered_movies['avg_rating'], errors='coerce')
            filtered_movies = filtered_movies.sort_values(by='avg_rating',  ascending=False)
        elif filter_by == 'year':
            filtered_movies = filtered_movies.sort_values(by='year', ascending=False)


        # Round ratings to 2 decimal place
        filtered_movies['avg_rating'] = filtered_movies['avg_rating'].round(4)

        # Paginate
        start = (page - 1) * movies_per_page
        end = start + movies_per_page
        movies_to_display = filtered_movies.iloc[start:end]

        has_more = len(filtered_movies) > end

        return render_template(
            'genre_recommendations.html',
            recommendations=movies_to_display.to_dict(orient='records'),
            genre=genre,
            page=page,
            has_more=has_more,
            filter=filter_by  # Passing the selected filter to the template
        )

    # When GET, render form
    genres = sorted(set(g.strip() for sublist in movies_df['genres'].dropna().str.split('|') for g in sublist))
    return render_template('select_genre.html', genres=genres)

@app.route('/recommend-by-movie', methods=['GET', 'POST'])
def recommend_by_movie():
    if request.method == 'POST':
        movie_name = request.form.get('movie')
        page = int(request.form.get('page', 1))
        filter_by = request.form.get('filter', 'rating')  # Default to 'rating'
        movies_per_page = 7

        all_recommendations = get_recommendations(movie_name)

        # Sort based on the selected filter (rating or year)
        if filter_by == 'rating':
            all_recommendations = sorted(all_recommendations, key=lambda x: x.get('avg_rating', 0), reverse=True)
        elif filter_by == 'year':
            all_recommendations = sorted(all_recommendations, key=lambda x: x.get('year', 0), reverse=True)

        for movie in all_recommendations:
            if 'avg_rating' in movie and movie['avg_rating'] is not None:
                movie['avg_rating'] = round(movie['avg_rating'], 3)
        # Pagination logic
        start = (page - 1) * movies_per_page
        end = start + movies_per_page
        movies_to_display = all_recommendations[start:end]
        has_more = len(all_recommendations) > end

        return render_template(
            'movie_recommendations.html',
            recommendations=movies_to_display,
            input_movie=movie_name,
            page=page,
            has_more=has_more,
            filter=filter_by  # Passing the selected filter to the template
        )

    # If GET request, return the list of all movies for the user to select from
    all_movies = pd.read_csv('data/movies.csv')['title'].dropna().unique().tolist()
    return render_template('select_movie.html', movies=sorted(all_movies))

if __name__ == '__main__':
    app.run(debug=True)
