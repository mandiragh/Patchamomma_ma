from bigquery_service import run_query


query = """
SELECT
  provider_state,
  SUM(total_discharges) AS total_discharges,
  ROUND(
    SUM(average_medicare_payments * total_discharges)
    / SUM(total_discharges),
    2
  ) AS weighted_avg_medicare_payment
FROM
  `bigquery-public-data.medicare.inpatient_charges_2014`
WHERE
  total_discharges > 0
GROUP BY
  provider_state
ORDER BY
  weighted_avg_medicare_payment DESC
LIMIT 10
"""

df = run_query(query)

print(df)