import streamlit as st

from text_to_sql import generate_sql
from sql_validator import validate_sql
from bigquery_service import dry_run_query, run_query
from chart_service import get_chart_config
from result_explainer import explain_results


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="HealthSight",
    page_icon="🏥",
    layout="wide",
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def format_value(value, column_name):
    """
    Format values for KPI cards based on the column name.
    """

    column_name = column_name.lower()

    if any(
        word in column_name
        for word in ["payment", "charge", "cost", "amount"]
    ):
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)

    if any(
        word in column_name
        for word in ["discharge", "count", "total"]
    ):
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)

    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def friendly_column_name(column_name):
    return (
        column_name
        .replace("_", " ")
        .strip()
        .title()
    )


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("HealthSight")

st.subheader(
    "AI-Powered Healthcare Data Analytics"
)

st.write(
    "Ask questions about Medicare inpatient utilization "
    "and payment data using plain English."
)


# ---------------------------------------------------------
# DATASET INFORMATION
# ---------------------------------------------------------

with st.container(border=True):

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("DATASET")
        st.write("Medicare Inpatient Charges 2014")

    with col2:
        st.caption("DATA PLATFORM")
        st.write("Google BigQuery")

    with col3:
        st.caption("ACCESS MODE")
        st.write("Read-only Analytics")


st.caption(
    "Public 2014 Medicare inpatient data is used for demonstration "
    "and analytical research. Results should not be interpreted as "
    "current healthcare conditions."
)


# ---------------------------------------------------------
# EXAMPLE QUESTIONS
# ---------------------------------------------------------

st.markdown("### Try an example")

example_questions = {
    "Highest Medicare Payments":
        "Which states had the highest average Medicare inpatient payments?",

    "Top Hospitals":
        "Which hospitals had the highest total inpatient discharges in 2014?",

    "Common DRGs":
        "What were the most common inpatient DRGs?",

    "MA vs NY":
        "Compare Medicare inpatient payments between Massachusetts and New York.",
}


example_cols = st.columns(4)

for index, (label, example_question) in enumerate(
    example_questions.items()
):
    with example_cols[index]:

        if st.button(
            label,
            use_container_width=True,
            key=f"example_{index}",
        ):
            st.session_state["question"] = example_question


# ---------------------------------------------------------
# QUESTION INPUT
# ---------------------------------------------------------

st.markdown("### Ask HealthSight")

if "question" not in st.session_state:
    st.session_state["question"] = ""


question = st.text_input(
    "Ask a healthcare data question:",
    value=st.session_state["question"],
    placeholder=(
        "Which states had the highest average "
        "Medicare inpatient payments?"
    ),
)

st.session_state["question"] = question


analyze = st.button(
    "Analyze",
    type="primary",
    use_container_width=True,
)


# ---------------------------------------------------------
# ANALYSIS PIPELINE
# ---------------------------------------------------------

if analyze:

    if not question.strip():

        st.warning(
            "Please enter a healthcare analytics question."
        )

    else:

        with st.spinner(
            "HealthSight is analyzing the data..."
        ):

            try:

                # -------------------------------------------------
                # 1. GENERATE SQL
                # -------------------------------------------------

                sql = generate_sql(question)


                # -------------------------------------------------
                # 2. VALIDATE SQL
                # -------------------------------------------------

                is_valid, validation_message = validate_sql(sql)

                if not is_valid:

                    st.error(
                        "The generated query did not pass "
                        f"the safety checks: {validation_message}"
                    )

                    st.stop()


                # -------------------------------------------------
                # 3. BIGQUERY DRY RUN
                # -------------------------------------------------

                bytes_processed = dry_run_query(sql)


                # -------------------------------------------------
                # 4. EXECUTE QUERY
                # -------------------------------------------------

                df = run_query(sql)


                if df.empty:

                    st.warning(
                        "The query completed successfully, "
                        "but no matching records were found."
                    )

                    st.stop()


                # -------------------------------------------------
                # 5. RESULT EXPLANATION
                # -------------------------------------------------

                explanation = explain_results(
                    question,
                    df,
                )


                st.success(
                    "Analysis completed successfully."
                )


                # -------------------------------------------------
                # KEY INSIGHT
                # -------------------------------------------------

                st.markdown("## Key Insight")

                with st.container(border=True):

                    st.write(explanation)


                # -------------------------------------------------
                # KPI CARDS
                # -------------------------------------------------

                st.markdown("## At a Glance")

                text_columns = (
                    df.select_dtypes(
                        exclude="number"
                    ).columns.tolist()
                )

                numeric_columns = (
                    df.select_dtypes(
                        include="number"
                    ).columns.tolist()
                )


                metric1, metric2, metric3 = st.columns(3)


                with metric1:

                    if text_columns:

                        first_text_column = text_columns[0]

                        st.metric(
                            label=(
                                f"Top "
                                f"{friendly_column_name(first_text_column)}"
                            ),
                            value=str(
                                df.iloc[0][first_text_column]
                            ),
                        )

                    else:

                        st.metric(
                            label="Rows Returned",
                            value=len(df),
                        )


                with metric2:

                    if numeric_columns:

                        metric_column = numeric_columns[-1]

                        st.metric(
                            label=(
                                friendly_column_name(
                                    metric_column
                                )
                            ),
                            value=format_value(
                                df.iloc[0][metric_column],
                                metric_column,
                            ),
                        )

                    else:

                        st.metric(
                            label="Rows Returned",
                            value=len(df),
                        )


                with metric3:

                    processed_mb = (
                        bytes_processed
                        / 1024
                        / 1024
                    )

                    st.metric(
                        label="Query Scan",
                        value=f"{processed_mb:.2f} MB",
                    )


                # -------------------------------------------------
                # VISUALIZATION
                # -------------------------------------------------

                chart_config = get_chart_config(df)

                if chart_config:

                    st.markdown("## Visualization")

                    chart_df = df[
                        [
                            chart_config["x"],
                            chart_config["y"],
                        ]
                    ].copy()

                    chart_df = chart_df.set_index(
                        chart_config["x"]
                    )

                    st.bar_chart(
                        chart_df,
                        use_container_width=True,
                    )


                # -------------------------------------------------
                # RESULTS TABLE
                # -------------------------------------------------

                st.markdown("## Results")

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )


                # -------------------------------------------------
                # DOWNLOAD
                # -------------------------------------------------

                csv_data = df.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="Download Results as CSV",
                    data=csv_data,
                    file_name="healthsight_results.csv",
                    mime="text/csv",
                )


                # -------------------------------------------------
                # PIPELINE TRACE
                # -------------------------------------------------

                with st.expander(
                    "How HealthSight Answered"
                ):

                    st.write(
                        "✓ Medicare schema provided to Gemini"
                    )

                    st.write(
                        "✓ Natural-language question converted to SQL"
                    )

                    st.write(
                        "✓ SQL safety validation passed"
                    )

                    st.write(
                        "✓ BigQuery dry run passed"
                    )

                    st.write(
                        f"✓ Estimated query scan: "
                        f"{processed_mb:.2f} MB"
                    )

                    st.write(
                        "✓ BigQuery query executed successfully"
                    )

                    st.write(
                        "✓ Results interpreted and summarized"
                    )


                # -------------------------------------------------
                # SQL TRANSPARENCY
                # -------------------------------------------------

                with st.expander(
                    "View Generated SQL"
                ):

                    st.code(
                        sql,
                        language="sql",
                    )


                # -------------------------------------------------
                # QUERY DETAILS
                # -------------------------------------------------

                with st.expander(
                    "Query Information"
                ):

                    st.write(
                        f"Estimated bytes processed: "
                        f"{bytes_processed:,}"
                    )

                    st.write(
                        f"Estimated MB processed: "
                        f"{processed_mb:.2f}"
                    )

                    st.write(
                        f"Rows returned: "
                        f"{len(df):,}"
                    )

                    st.write(
                        f"Validation status: "
                        f"{validation_message}"
                    )


                # -------------------------------------------------
                # LIMITATIONS
                # -------------------------------------------------

                with st.expander(
                    "Data & Interpretation Notes"
                ):

                    st.write(
                        "• The current MVP uses the "
                        "Medicare Inpatient Charges 2014 dataset."
                    )

                    st.write(
                        "• Results represent historical Medicare "
                        "inpatient data and should not be treated "
                        "as current healthcare conditions."
                    )

                    st.write(
                        "• HealthSight is designed for analytics "
                        "and research, not medical diagnosis."
                    )

                    st.write(
                        "• AI-generated SQL is validated before "
                        "BigQuery execution."
                    )


            except Exception as e:

                st.error(
                    "HealthSight was unable to complete "
                    "the analysis."
                )

                with st.expander(
                    "Technical Details"
                ):

                    st.exception(e)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "HealthSight • Patchamomma 2026 • "
    "BigQuery + Gemini + Python + Streamlit"
)

