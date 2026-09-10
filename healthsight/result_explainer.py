import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv("GEMINI_MODEL")


def explain_results(question, df):

    if df.empty:
        return "No data was returned for this question."

    # Only send a small result sample to Gemini
    result_text = df.head(10).to_string(index=False)

    prompt = f"""
You are HealthSight, a healthcare analytics assistant.

User question:
{question}

Query results:
{result_text}

Write a concise 2-3 sentence explanation.

Rules:
- Use only the supplied query results.
- Do not invent facts.
- Clearly mention that this is 2014 Medicare inpatient data.
- Do not make causal claims.
- Do not provide medical advice.
- Mention important limitations when relevant.
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            return response.text.strip()

        except ServerError:
            if attempt == 2:
                return (
                    "The data query completed successfully, "
                    "but the AI explanation is temporarily unavailable."
                )

            time.sleep(5 * (attempt + 1))
            