from text_to_sql import generate_sql
from sql_validator import validate_sql
from bigquery_service import dry_run_query, run_query


question = (
    "Which states had the highest average "
    "Medicare inpatient payments?"
)

print("\nQuestion:")
print(question)

sql = generate_sql(question)

print("\nGenerated SQL:")
print(sql)

is_valid, message = validate_sql(sql)

print("\nValidation:")
print(message)

if not is_valid:
    raise ValueError("Generated SQL failed validation.")

bytes_processed = dry_run_query(sql)

print("\nDry run successful.")
print(f"Estimated bytes processed: {bytes_processed:,}")

df = run_query(sql)

print("\nResults:")
print(df)

