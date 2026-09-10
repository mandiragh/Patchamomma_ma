import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

if not model_name:
    raise ValueError("GEMINI_MODEL not found in .env")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=model_name,
    contents="Reply with exactly: Gemini connection successful"
)

print(response.text)