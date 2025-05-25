import os
from google import genai
from google.genai import types
import re

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
model = "gemini-1.5-flash"

generate_content_config = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_LOW_AND_ABOVE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_LOW_AND_ABOVE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_LOW_AND_ABOVE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_LOW_AND_ABOVE"),
    ],
    response_mime_type="text/plain",
    system_instruction=[types.Part.from_text(text="""
You are a helpful AI assistant that recommends movies based on the user's mood.
Respond with a list of 3-5 movies in the following format:

- Title (Genre) - IMDb: Rating : Short description
Example:
- Inception (Sci-Fi) - IMDb: 8.8 : A mind-bending thriller about dream invasion.
- Give some advice how to mood up.
""")]
)

def get_movie_recommendation(user_message: str) -> str:
    mood_keywords = ["sad", "depressed", "not feeling good", "anxious", "stress", "cheer up", "feeling low", "motivate me"]
    recommendation_keywords = ["recommend", "suggest", "movie", "film", "watch", "see"]

    user_message_lower = user_message.lower()

    mood_related = any(word in user_message_lower for word in mood_keywords)
    wants_movies = any(word in user_message_lower for word in recommendation_keywords)

    print("Mood related:", mood_related)
    print("Wants movies:", wants_movies)

    response_text = ""

    if mood_related and not wants_movies:
        print("Sending to mood advice mode.")
        mood_config = types.GenerateContentConfig(
            safety_settings=generate_content_config.safety_settings,
            response_mime_type="text/plain",
            system_instruction=[types.Part.from_text(text="""
You are a helpful AI assistant that provides emotional support and positive advice.
When a user is feeling sad, stressed, or down, respond with kind words and suggestions to lift their mood.
Do not recommend any movies in this case. Focus only on emotional encouragement, self-care, and positivity.
""")]
        )
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_message)])]
        for chunk in client.models.generate_content_stream(model=model, contents=contents, config=mood_config):
            print("Chunk:", chunk.text)
            response_text += chunk.text
    else:
        print("Sending to movie recommendation mode.")
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_message)])]
        for chunk in client.models.generate_content_stream(model=model, contents=contents, config=generate_content_config):
            print("Chunk:", chunk.text)
            response_text += chunk.text

    print("Final response text:", response_text)
    return response_text

def parse_response(response_text):
    movies = []
    lines = response_text.strip().split('\n')
    for line in lines:
        match = re.match(r"-\s*(.*?)\s*\((.*?)\)\s*-\s*IMDb:\s*(\d+\.?\d*)\s*:\s*(.*)", line)
        if match:
            title, genre, rating, description = match.groups()
            movies.append({
                "title": title.strip(),
                "genre": genre.strip(),
                "rating": rating.strip(),
                "description": description.strip()
            })
    return movies

# New Function to Get Movie Details (Example)
def get_movie_details(movie_title: str) -> str:
    # Simulating detailed response; you can integrate an API like OMDB here
    movie_details = {
        "Inception": "Inception (2010): Directed by Christopher Nolan, Inception is a mind-bending sci-fi thriller that explores the concept of shared dreams. The film stars Leonardo DiCaprio and features stunning visual effects. IMDb Rating: 8.8.",
        "The Matrix": "The Matrix (1999): Directed by the Wachowskis, The Matrix is a groundbreaking science fiction film that explores simulated reality. Keanu Reeves stars as Neo, who must decide whether to take the red pill or the blue pill. IMDb Rating: 8.7."
    }
    
    # Fallback if the movie is not found
    return movie_details.get(movie_title, "Sorry, I don't have more details on that movie.")

