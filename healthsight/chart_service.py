import pandas as pd


def get_chart_config(df: pd.DataFrame):
    if df.empty:
        return None

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    text_columns = df.select_dtypes(exclude="number").columns.tolist()

    if not numeric_columns or not text_columns:
        return None

    x_column = text_columns[0]
    y_column = numeric_columns[-1]

    return {
        "x": x_column,
        "y": y_column,
        "type": "bar",
    }

