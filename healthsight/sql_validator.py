import re


FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
}

ALLOWED_DATASET = "bigquery-public-data.medicare"


def validate_sql(sql: str):
    cleaned = sql.strip()

    upper_sql = cleaned.upper()

    if not (
        upper_sql.startswith("SELECT")
        or upper_sql.startswith("WITH")
    ):
        return False, "Only SELECT or WITH queries are allowed."

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            return False, f"Forbidden SQL keyword detected: {keyword}"

    if ALLOWED_DATASET not in cleaned:
        return False, "Query uses an unauthorized dataset."

    return True, "SQL is valid."

