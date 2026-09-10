from sql_validator import validate_sql


test_cases = [
    {
        "name": "Safe SELECT",
        "sql": """
        SELECT provider_state, SUM(total_discharges)
        FROM `bigquery-public-data.medicare.inpatient_charges_2014`
        GROUP BY provider_state
        """,
        "expected": True,
    },
    {
        "name": "Safe WITH query",
        "sql": """
        WITH state_data AS (
            SELECT provider_state, total_discharges
            FROM `bigquery-public-data.medicare.inpatient_charges_2014`
        )
        SELECT *
        FROM state_data
        LIMIT 10
        """,
        "expected": True,
    },
    {
        "name": "Reject DELETE",
        "sql": """
        DELETE FROM `bigquery-public-data.medicare.inpatient_charges_2014`
        WHERE provider_state = 'MA'
        """,
        "expected": False,
    },
    {
        "name": "Reject UPDATE",
        "sql": """
        UPDATE `bigquery-public-data.medicare.inpatient_charges_2014`
        SET provider_state = 'NY'
        WHERE provider_state = 'MA'
        """,
        "expected": False,
    },
    {
        "name": "Reject DROP",
        "sql": """
        DROP TABLE `bigquery-public-data.medicare.inpatient_charges_2014`
        """,
        "expected": False,
    },
    {
        "name": "Reject unauthorized dataset",
        "sql": """
        SELECT *
        FROM `some-other-project.private_dataset.patient_data`
        LIMIT 10
        """,
        "expected": False,
    },
]


passed = 0

print("\nHealthSight Safety Evaluation")
print("=" * 50)


for test in test_cases:

    valid, message = validate_sql(
        test["sql"]
    )

    success = valid == test["expected"]

    if success:
        passed += 1
        result = "PASS"
    else:
        result = "FAIL"

    print(
        f"{result:<5} | "
        f"{test['name']:<30} | "
        f"{message}"
    )


print("=" * 50)

print(
    f"Result: {passed}/{len(test_cases)} tests passed"
)

percentage = (
    passed
    / len(test_cases)
    * 100
)

print(
    f"Safety score: {percentage:.0f}%"
)

