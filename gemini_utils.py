# import re
# import os
# import google.generativeai as genai

# def get_mood_based_movies(mood: str):
#     genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
#     model = genai.GenerativeModel("gemini-1.5-flash")

#     prompt = f"""
#     You are a helpful AI assistant that provides movie recommendations based on the user's mood.

#     Mood: {mood}

#     Suggest 5 movies. For each movie, provide the following:
#     - Title
#     - Genre(s)
#     - IMDb Rating (approximate)
#     - 1-2 sentence description

#     Be concise but informative.
#     """

#     response = model.generate_content(prompt)

#     print("Gemini Response Text:", response.text)

#     movie_details = []

#     # ✅ Final robust regex: handles "Genre" or "Genre(s)", optional tilde (~), flexible spaces and multiline
#     movie_pattern = re.compile(
#         r"\d+\.\s*\*\*Title:\*\*\s*(?P<title>.+?)\s*"
#         r"\*\*Genre(?:\(s\))?:\*\*\s*(?P<genre>.+?)\s*"
#         r"\*\*IMDb Rating:\*\*\s*~?(?P<rating>[\d.]+)\s*"
#         r"\*\*Description:\*\*\s*(?P<description>.+?)(?=\n\d+\.|\Z)",
#         re.DOTALL
#     )

#     matches_list = list(movie_pattern.finditer(response.text))
#     print("Number of matches:", len(matches_list))

#     for match in matches_list:
#         movie_details.append({
#             'title': match.group('title').strip(),
#             'genre': match.group('genre').strip(),
#             'rating': match.group('rating').strip(),
#             'description': match.group('description').strip()
#         })

#     print("Parsed Movie Details:", movie_details)
#     return movie_details[:3]





