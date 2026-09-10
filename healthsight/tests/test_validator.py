from sql_validator import validate_sql


safe_sql = """
SELECT
  provider_state
FROM
  `bigquery-public-data.medicare.inpatient_charges_2014`
LIMIT 10
"""

unsafe_sql = """
DELETE FROM
  `bigquery-public-data.medicare.inpatient_charges_2014`
WHERE provider_state = 'MA'
"""


print("SAFE QUERY:")
print(validate_sql(safe_sql))

print("\nUNSAFE QUERY:")
print(validate_sql(unsafe_sql))

