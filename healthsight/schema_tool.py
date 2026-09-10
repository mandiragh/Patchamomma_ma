from bigquery_service import run_query


DATASET = "bigquery-public-data.medicare"


def get_tables():
    sql = f"""
    SELECT
      table_name,
      table_type
    FROM
      `{DATASET}.INFORMATION_SCHEMA.TABLES`
    ORDER BY
      table_name
    """

    return run_query(sql)


def get_table_schema(table_name: str):
    sql = f"""
    SELECT
      column_name,
      data_type,
      is_nullable
    FROM
      `{DATASET}.INFORMATION_SCHEMA.COLUMNS`
    WHERE
      table_name = '{table_name}'
    ORDER BY
      ordinal_position
    """

    return run_query(sql)