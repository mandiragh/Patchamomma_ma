import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from schema_tool import get_table_schema
from sql_validator import validate_sql
from bigquery_service import dry_run_query, run_query


load_dotenv()

MODEL = os.getenv(
    "ADK_MODEL",
    os.getenv("GEMINI_MODEL")
)



def inspect_medicare_schema() -> list[dict]:
    """
    Return the schema for the 2014 Medicare inpatient charges table.

    Use this before writing SQL so that table and column names
    are not invented.
    """

    df = get_table_schema("inpatient_charges_2014")

    return df[
        ["column_name", "data_type", "is_nullable"]
    ].to_dict(orient="records")


def validate_medicare_sql(sql: str) -> dict:
    """
    Validate a proposed Medicare BigQuery SQL query.

    Use this before executing SQL.
    """

    is_valid, message = validate_sql(sql)

    return {
        "valid": is_valid,
        "message": message,
    }


def execute_medicare_query(sql: str) -> dict:
    """
    Safely execute a read-only query against the approved
    Medicare inpatient dataset.

    The query is validated and dry-run before execution.
    """

    is_valid, message = validate_sql(sql)

    if not is_valid:
        return {
            "status": "rejected",
            "message": message,
        }

    bytes_processed = dry_run_query(sql)

    df = run_query(sql)

    return {
        "status": "success",
        "bytes_processed": int(bytes_processed),
        "rows": df.to_dict(orient="records"),
    }


root_agent = Agent(
    name="healthsight_agent",

    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(
            attempts=3
        ),
    ),

    instruction="""
You are HealthSight, a healthcare analytics agent.

You analyze the 2014 Medicare inpatient charges public dataset.

Your responsibilities:

1. Understand the user's healthcare analytics question.
2. Inspect the Medicare schema when necessary.
3. Generate valid BigQuery GoogleSQL.
4. Validate SQL before executing it.
5. Execute only safe read-only queries.
6. Explain the results clearly.

Important rules:

- Never invent table names or column names.
- Use only:
  bigquery-public-data.medicare.inpatient_charges_2014
- Only SELECT or WITH queries are allowed.
- Never modify data.
- Limit result sets to 10 rows unless necessary.
- For state-level average Medicare payments, weight
  average_medicare_payments by total_discharges.
- Clearly state that the dataset represents 2014 data.
- Do not provide medical diagnosis or patient-specific advice.
- Do not claim that observational data proves causation.
""",

    tools=[
        inspect_medicare_schema,
        validate_medicare_sql,
        execute_medicare_query,
    ],
)


app = App(
    name="adk_app",
    root_agent=root_agent,
)

