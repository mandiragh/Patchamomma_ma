from google.cloud import bigquery


PROJECT_ID = "healthsight-patchamomma"

client = bigquery.Client(project=PROJECT_ID)

MAX_BYTES = 100_000_000


def dry_run_query(sql: str):
    job_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
        maximum_bytes_billed=MAX_BYTES
    )

    query_job = client.query(
        sql,
        job_config=job_config
    )

    return query_job.total_bytes_processed


def run_query(sql: str):
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=MAX_BYTES
    )

    query_job = client.query(
        sql,
        job_config=job_config
    )

    return query_job.to_dataframe()

