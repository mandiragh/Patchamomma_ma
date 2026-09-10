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

schema_df = get_table_schema("inpatient_charges_2014")

schema_text = schema_df[
    ["column_name", "data_type"]
].to_string(index=False)

question = "Which states had the highest average Medicare inpatient payments?"

prompt = f"""
You are a healthcare data analyst.

Generate one BigQuery GoogleSQL query that answers the user's question.

Table:
bigquery-public-data.medicare.inpatient_charges_2014

Available columns:
{schema_text}

Rules:
- Use only the table and columns provided above.
- Use GoogleSQL.
- Generate a SELECT query only.
- Do not modify data.
- Do not invent columns.
- Limit output to 10 rows.
- When calculating state-level average Medicare payments,
  use total_discharges as the weight.
- Do not use a simple AVG(average_medicare_payments)
  when aggregating across provider/DRG rows.
- Return only SQL.
- Do not include ```sql or other markdown formatting.

User question:
{question}
"""

response = None

for attempt in range(3):
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        break

    except ServerError as e:
        if attempt == 2:
            raise

        print("Gemini is temporarily busy. Retrying...")
        time.sleep(10)


print("\nGenerated SQL:\n")
print(response.text)