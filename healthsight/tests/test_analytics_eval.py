from text_to_sql import generate_sql
from sql_validator import validate_sql
from bigquery_service import dry_run_query


test_cases = [
    {
        "id": 1,
        "question": (
            "Which states had the highest average Medicare "
            "inpatient payments?"
        ),
        "expected_logic": (
            "Should group by provider_state and calculate a "
            "discharge-weighted average using total_discharges."
        ),
    },
    {
        "id": 2,
        "question": (
            "Which hospitals had the highest total inpatient "
            "discharges in 2014?"
        ),
        "expected_logic": (
            "Should group by provider/hospital and SUM(total_discharges)."
        ),
    },
    {
        "id": 3,
        "question": (
            "What were the most common inpatient DRGs?"
        ),
        "expected_logic": (
            "Should group by drg_definition and SUM(total_discharges)."
        ),
    },
    {
        "id": 4,
        "question": (
            "Compare Medicare inpatient payments between "
            "Massachusetts and New York."
        ),
        "expected_logic": (
            "Should filter provider_state to MA and NY and compare "
            "Medicare payments, preferably using discharge weighting."
        ),
    },
    {
        "id": 5,
        "question": (
            "Which states had the highest average covered charges?"
        ),
        "expected_logic": (
            "Should group by provider_state and compare covered charges. "
            "Should not describe covered charges as hospital costs."
        ),
    },
]


print("\n")
print("=" * 70)
print("HealthSight Analytical Evaluation")
print("=" * 70)


for test in test_cases:

    print(f"\nTEST {test['id']}")
    print("-" * 70)

    print("QUESTION:")
    print(test["question"])

    print("\nEXPECTED ANALYTICAL LOGIC:")
    print(test["expected_logic"])

    try:

        sql = generate_sql(
            test["question"]
        )

        print("\nGENERATED SQL:")
        print(sql)

        valid, message = validate_sql(
            sql
        )

        print("\nVALIDATION:")
        print(
            f"{valid} - {message}"
        )

        if valid:

            bytes_processed = dry_run_query(
                sql
            )

            print(
                f"Dry run: PASS "
                f"({bytes_processed:,} bytes)"
            )

        else:

            print(
                "Dry run: NOT RUN"
            )

    except Exception as e:

        print(
            f"\nERROR: {e}"
        )


print("\n")
print("=" * 70)
print("Evaluation complete.")
print("=" * 70)

