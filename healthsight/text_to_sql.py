import os

from dotenv import load_dotenv
from google import genai

from schema_tool import get_table_schema
import time
from google.genai.errors import ServerError

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL")

client = genai.Client(api_key=api_key)


def generate_sql(question: str):

    schema_df = get_table_schema("inpatient_charges_2014")

    schema_text = schema_df[
        ["column_name", "data_type"]
    ].to_string(index=False)

    prompt = f"""
You are a healthcare data analyst.

Generate one BigQuery GoogleSQL query.

Table:
bigquery-public-data.medicare.inpatient_charges_2014

Available columns:
{schema_text}

Rules:
- Use only the provided table.
- Use only columns from the schema.
- Generate SELECT queries only.
- Do not modify data.
- Do not invent columns.
- Limit results to 10 rows.
- When calculating state-level average Medicare payments,
  weight average_medicare_payments by total_discharges.
- Return SQL only.
- Do not include markdown formatting.

Question:
{question}
"""

    response = None

    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            break

        except ServerError as e:
            if "503" not in str(e) or attempt == 3:
                raise

            wait_seconds = 5 * (2 ** attempt)

            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {wait_seconds} seconds..."
        )

            time.sleep(wait_seconds)

    return response.text.strip()

