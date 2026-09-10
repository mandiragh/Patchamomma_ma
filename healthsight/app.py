import pandas as pd
import streamlit as st

from text_to_sql import generate_sql
from sql_validator import validate_sql
from bigquery_service import dry_run_query, run_query
from chart_service import get_chart_config
from result_explainer import explain_results
from agent_runner import run_healthsight_agent


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="HealthSight",
    page_icon="🏥",
    layout="wide",
)

# =========================================================
# GOOGLE CLOUD INSPIRED THEME
# =========================================================

st.markdown(
    """
    <style>

    /* Main app background */
    .stApp {
        background:
            linear-gradient(
                135deg,
                #F8FBFF 0%,
                #EEF4FF 45%,
                #FFFDF5 100%
            );
    }

    /* Main content width/padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Main headings */
    h1 {
        color: #4285F4 !important;
        font-weight: 700 !important;
    }

    h2, h3 {
        color: #202124 !important;
        font-weight: 600 !important;
    }

    /* Normal text */
    p, label {
        color: #3C4043;
    }

    /* Primary buttons */
    div.stButton > button[kind="primary"] {
        background-color: #4285F4;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #3367D6;
        color: white;
        border: none;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(66,133,244,0.25);
    }

    /* Secondary / example buttons */
    div.stButton > button:not([kind="primary"]) {
        background-color: white;
        color: #4285F4;
        border: 1px solid #DADCE0;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    div.stButton > button:not([kind="primary"]):hover {
        border-color: #4285F4;
        color: #3367D6;
        background-color: #F1F6FF;
    }

    /* Text input */
    div[data-baseweb="input"] {
        border-radius: 10px;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #4285F4 !important;
        box-shadow: 0 0 0 1px #4285F4 !important;
    }

    /* Radio button selected color */
    div[role="radiogroup"] input:checked + div {
        background-color: #4285F4 !important;
        border-color: #4285F4 !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: rgba(255,255,255,0.92);
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #E8EAED;
        box-shadow: 0 2px 8px rgba(60,64,67,0.08);
    }

    /* Dataset/container cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255,255,255,0.85);
        border-radius: 14px;
    }

    /* Expanders */
    details {
        background-color: rgba(255,255,255,0.90);
        border-radius: 10px;
        border: 1px solid #E8EAED;
    }

    /* Success message */
    div[data-testid="stAlert"][data-baseweb="notification"] {
        border-radius: 10px;
    }

    /* Download button */
    div.stDownloadButton > button {
        background-color: #0F9D58;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
    }

    div.stDownloadButton > button:hover {
        background-color: #0B8043;
        color: white;
        border: none;
    }

    /* Divider */
    hr {
        border-color: #DADCE0 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_value(value, column_name):
    """
    Format KPI values based on the column name.
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
    """
    Convert SQL-style names into readable labels.
    """

    return (
        str(column_name)
        .replace("_", " ")
        .strip()
        .title()
    )


def show_kpi_cards(df, bytes_processed=None):
    """
    Display three KPI cards for a query result.
    """

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

    # -----------------------------------------------------
    # KPI 1
    # -----------------------------------------------------

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
                value=f"{len(df):,}",
            )

    # -----------------------------------------------------
    # KPI 2
    # -----------------------------------------------------

    with metric2:

        if numeric_columns:

            metric_column = numeric_columns[-1]

            st.metric(
                label=friendly_column_name(
                    metric_column
                ),
                value=format_value(
                    df.iloc[0][metric_column],
                    metric_column,
                ),
            )

        else:

            st.metric(
                label="Rows Returned",
                value=f"{len(df):,}",
            )

    # -----------------------------------------------------
    # KPI 3
    # -----------------------------------------------------

    with metric3:

        if bytes_processed is not None:

            processed_mb = (
                bytes_processed
                / 1024
                / 1024
            )

            st.metric(
                label="Query Scan",
                value=f"{processed_mb:.2f} MB",
            )

        else:

            st.metric(
                label="Rows Returned",
                value=f"{len(df):,}",
            )


def show_visualization(df):
    """
    Create a visualization when the returned data
    contains compatible categorical and numeric fields.
    """

    chart_config = get_chart_config(df)

    if not chart_config:
        return

    x_column = chart_config["x"]
    y_column = chart_config["y"]

    if (
        x_column not in df.columns
        or y_column not in df.columns
    ):
        return

    st.markdown("## Visualization")

    chart_df = df[
        [
            x_column,
            y_column,
        ]
    ].copy()

    chart_df = chart_df.set_index(
        x_column
    )

    st.bar_chart(
        chart_df,
        use_container_width=True,
    )


def show_data_notes():
    """
    Shared dataset and interpretation notes.
    """

    with st.expander(
        "Data & Interpretation Notes"
    ):

        st.write(
            "• The current HealthSight MVP uses the "
            "Medicare Inpatient Charges 2014 dataset."
        )

        st.write(
            "• Results represent historical Medicare "
            "inpatient data and should not be interpreted "
            "as current healthcare conditions."
        )

        st.write(
            "• Covered charges should not automatically "
            "be interpreted as actual hospital costs."
        )

        st.write(
            "• HealthSight is designed for analytics "
            "and research, not medical diagnosis."
        )

        st.write(
            "• AI-generated SQL is subject to validation "
            "before BigQuery execution."
        )


# =========================================================
# SESSION STATE
# =========================================================

if "question_input" not in st.session_state:
    st.session_state.question_input = ""


# =========================================================
# HEADER
# =========================================================

st.title("🏥 HealthSight")

st.subheader(
    "AI-Powered Healthcare Data Analytics"
)

st.write(
    "Ask questions about Medicare inpatient utilization "
    "and payment data using plain English."
)


# =========================================================
# DATASET INFORMATION
# =========================================================

with st.container(border=True):

    col1, col2, col3 = st.columns(3)

    with col1:

        st.caption("DATASET")
        st.write(
            "Medicare Inpatient Charges 2014"
        )

    with col2:

        st.caption("DATA PLATFORM")
        st.write(
            "Google BigQuery"
        )

    with col3:

        st.caption("ACCESS MODE")
        st.write(
            "Read-only Analytics"
        )


st.caption(
    "Public 2014 Medicare inpatient data is used for "
    "demonstration and analytical research. Results "
    "should not be interpreted as current healthcare conditions."
)


# =========================================================
# EXAMPLE QUESTIONS
# =========================================================

st.markdown("### Try an Example")

example_questions = {

    "Highest Payments":
        "Which states had the highest average Medicare "
        "inpatient payments?",

    "Top Hospitals":
        "Which hospitals had the highest total inpatient "
        "discharges in 2014?",

    "Common DRGs":
        "What were the most common inpatient DRGs?",

    "MA vs NY":
        "Compare Medicare inpatient payments between "
        "Massachusetts and New York.",
}


example_cols = st.columns(4)

for index, (label, example_question) in enumerate(
    example_questions.items()
):

    with example_cols[index]:

        if st.button(
            label,
            use_container_width=True,
            key=f"example_button_{index}",
        ):

            st.session_state.question_input = (
                example_question
            )


# =========================================================
# ANALYSIS MODE
# =========================================================

st.markdown("### Analysis Mode")

analysis_mode = st.radio(
    "Choose how HealthSight should analyze your question:",
    options=[
        "Standard Analytics",
        "HealthSight Agent",
    ],
    horizontal=True,
    key="analysis_mode",
)


if analysis_mode == "Standard Analytics":

    st.caption(
        "⚡ Fast, controlled Text-to-SQL analytics with "
        "deterministic validation and BigQuery execution."
    )

else:

    st.caption(
        "🤖 Agentic analysis using Google ADK with dynamic "
        "tool selection, schema inspection, validation, "
        "and protected BigQuery execution."
    )


# =========================================================
# QUESTION INPUT
# =========================================================

st.markdown("### Ask HealthSight")

question = st.text_input(
    "Ask a healthcare data question:",
    placeholder=(
        "Which states had the highest average "
        "Medicare inpatient payments?"
    ),
    key="question_input",
)


analyze = st.button(
    "Analyze",
    type="primary",
    use_container_width=True,
    key="analyze_button",
)


# =========================================================
# ANALYSIS PIPELINE
# =========================================================

if analyze:

    # =====================================================
    # EMPTY QUESTION
    # =====================================================

    if not question.strip():

        st.warning(
            "Please enter a healthcare analytics question."
        )


    # =====================================================
    # HEALTHSIGHT AGENT MODE
    # =====================================================

    elif analysis_mode == "HealthSight Agent":

        with st.spinner(
            "HealthSight Agent is reasoning and using its tools..."
        ):

            result = run_healthsight_agent(
                question
            )


        status = result.get(
            "status",
            "error",
        )


        # =================================================
        # AGENT SUCCESS
        # =================================================

        if status == "success":

            st.success(
                "HealthSight Agent completed the analysis."
            )

            agent_answer = result.get(
                "answer",
                "No response was returned.",
            )

            tools_used = result.get(
                "tools_used",
                [],
            )

            agent_sql = result.get(
                "sql"
            )

            rows = result.get(
                "rows",
                [],
            )

            bytes_processed = result.get(
                "bytes_processed"
            )

            agent_df = pd.DataFrame(
                rows
            )


            # =============================================
            # AGENT INSIGHT
            # =============================================

            st.markdown(
                "## Agent Insight"
            )

            with st.container(
                border=True
            ):

                st.write(
                    agent_answer
                )


            # =============================================
            # STRUCTURED QUERY RESULTS
            # =============================================

            if not agent_df.empty:

                # -----------------------------------------
                # KPI CARDS
                # -----------------------------------------

                st.markdown(
                    "## At a Glance"
                )

                show_kpi_cards(
                    agent_df,
                    bytes_processed,
                )


                # -----------------------------------------
                # VISUALIZATION
                # -----------------------------------------

                show_visualization(
                    agent_df
                )


                # -----------------------------------------
                # RESULTS
                # -----------------------------------------

                st.markdown(
                    "## Results"
                )

                st.dataframe(
                    agent_df,
                    use_container_width=True,
                    hide_index=True,
                )


                # -----------------------------------------
                # CSV DOWNLOAD
                # -----------------------------------------

                csv_data = (
                    agent_df
                    .to_csv(index=False)
                    .encode("utf-8")
                )

                st.download_button(
                    label=(
                        "⬇️ Download Agent Results as CSV"
                    ),
                    data=csv_data,
                    file_name=(
                        "healthsight_agent_results.csv"
                    ),
                    mime="text/csv",
                    key="download_agent_results",
                )

            else:

                st.info(
                    "The agent completed its response "
                    "without returning tabular query results."
                )


            # =============================================
            # ACTUAL AGENT ACTIVITY
            # =============================================

            st.markdown(
                "## Agent Activity"
            )


            if tools_used:

                unique_tools = list(
                    dict.fromkeys(
                        tools_used
                    )
                )

                for tool in unique_tools:

                    if tool == "inspect_medicare_schema":

                        st.write(
                            "✅ Inspected Medicare dataset schema"
                        )

                    elif tool == "validate_medicare_sql":

                        st.write(
                            "✅ Validated generated SQL"
                        )

                    elif tool == "execute_medicare_query":

                        st.write(
                            "✅ Executed protected BigQuery query"
                        )

                    else:

                        st.write(
                            f"✅ {friendly_column_name(tool)}"
                        )

            else:

                st.info(
                    "The agent answered without calling "
                    "an external data tool."
                )


            # =============================================
            # AGENT WORKFLOW
            # =============================================

            with st.expander(
                "How the HealthSight Agent Worked"
            ):

                st.write(
                    "HealthSight uses Google ADK to "
                    "determine which tools are required "
                    "for the user's question."
                )

                if tools_used:

                    st.write(
                        "**Actual tool sequence:**"
                    )

                    st.write(
                        " → ".join(
                            tools_used
                        )
                    )

                else:

                    st.write(
                        "No data tools were invoked "
                        "for this request."
                    )


            # =============================================
            # AGENT GENERATED SQL
            # =============================================

            if agent_sql:

                with st.expander(
                    "View Agent Generated SQL"
                ):

                    st.code(
                        agent_sql,
                        language="sql",
                    )


            # =============================================
            # AGENT QUERY INFORMATION
            # =============================================

            if not agent_df.empty:

                with st.expander(
                    "Agent Query Information"
                ):

                    query_col1, query_col2 = (
                        st.columns(2)
                    )


                    with query_col1:

                        st.metric(
                            "Rows Returned",
                            f"{len(agent_df):,}",
                        )


                    with query_col2:

                        if bytes_processed is not None:

                            processed_mb = (
                                bytes_processed
                                / 1024
                                / 1024
                            )

                            st.metric(
                                "Data Processed",
                                f"{processed_mb:.2f} MB",
                            )

                        else:

                            st.metric(
                                "Data Processed",
                                "N/A",
                            )


                    if bytes_processed is not None:

                        st.write(
                            f"**Estimated bytes processed:** "
                            f"{bytes_processed:,}"
                        )


            # =============================================
            # AGENT GOVERNANCE
            # =============================================

            with st.expander(
                "Agent Safety & Governance"
            ):

                st.write(
                    "• Dataset access is restricted to "
                    "the approved Medicare public dataset."
                )

                st.write(
                    "• Data-changing SQL operations are blocked."
                )

                st.write(
                    "• SQL is validated before BigQuery execution."
                )

                st.write(
                    "• BigQuery query-processing limits "
                    "are enforced."
                )

                st.write(
                    "• Results use historical 2014 Medicare "
                    "inpatient data."
                )

                st.write(
                    "• HealthSight is intended for analytics "
                    "and research, not medical diagnosis."
                )


            show_data_notes()


        # =================================================
        # GEMINI QUOTA EXCEEDED
        # =================================================

        elif status == "quota_exceeded":

            st.warning(
                result.get(
                    "answer",
                    "The Gemini API quota has been reached."
                )
            )

            st.info(
                "You can switch to Standard Analytics "
                "while Agent Mode is unavailable."
            )


        # =================================================
        # MODEL UNAVAILABLE
        # =================================================

        elif status == "model_unavailable":

            st.warning(
                result.get(
                    "answer",
                    "The Gemini model is temporarily unavailable."
                )
            )

            st.info(
                "Please try again shortly or use "
                "Standard Analytics mode."
            )


        # =================================================
        # OTHER AGENT ERROR
        # =================================================

        else:

            st.error(
                result.get(
                    "answer",
                    "The HealthSight Agent encountered an error."
                )
            )


    # =====================================================
    # STANDARD ANALYTICS MODE
    # =====================================================

    else:

        with st.spinner(
            "HealthSight is analyzing the data..."
        ):

            try:

                # =========================================
                # 1. GENERATE SQL
                # =========================================

                sql = generate_sql(
                    question
                )


                # =========================================
                # 2. VALIDATE SQL
                # =========================================

                is_valid, validation_message = (
                    validate_sql(
                        sql
                    )
                )


                if not is_valid:

                    st.error(
                        "The generated query did not pass "
                        f"the safety checks: "
                        f"{validation_message}"
                    )

                    st.stop()


                # =========================================
                # 3. BIGQUERY DRY RUN
                # =========================================

                bytes_processed = dry_run_query(
                    sql
                )


                processed_mb = (
                    bytes_processed
                    / 1024
                    / 1024
                )


                # =========================================
                # 4. EXECUTE QUERY
                # =========================================

                df = run_query(
                    sql
                )


                if df.empty:

                    st.warning(
                        "The query completed successfully, "
                        "but no matching records were found."
                    )

                    st.stop()


                # =========================================
                # 5. EXPLAIN RESULTS
                # =========================================

                explanation = explain_results(
                    question,
                    df,
                )


                st.success(
                    "Analysis completed successfully."
                )


                # =========================================
                # KEY INSIGHT
                # =========================================

                st.markdown(
                    "## Key Insight"
                )

                with st.container(
                    border=True
                ):

                    st.write(
                        explanation
                    )


                # =========================================
                # KPI CARDS
                # =========================================

                st.markdown(
                    "## At a Glance"
                )

                show_kpi_cards(
                    df,
                    bytes_processed,
                )


                # =========================================
                # VISUALIZATION
                # =========================================

                show_visualization(
                    df
                )


                # =========================================
                # RESULTS TABLE
                # =========================================

                st.markdown(
                    "## Results"
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )


                # =========================================
                # CSV DOWNLOAD
                # =========================================

                csv_data = (
                    df.to_csv(
                        index=False
                    )
                    .encode("utf-8")
                )


                st.download_button(
                    label="⬇️ Download Results as CSV",
                    data=csv_data,
                    file_name="healthsight_results.csv",
                    mime="text/csv",
                    key="download_standard_results",
                )


                # =========================================
                # PIPELINE TRACE
                # =========================================

                with st.expander(
                    "How HealthSight Answered"
                ):

                    st.write(
                        "✅ Medicare schema provided to Gemini"
                    )

                    st.write(
                        "✅ Natural-language question "
                        "converted to SQL"
                    )

                    st.write(
                        "✅ SQL safety validation passed"
                    )

                    st.write(
                        "✅ BigQuery dry run passed"
                    )

                    st.write(
                        f"✅ Estimated query scan: "
                        f"{processed_mb:.2f} MB"
                    )

                    st.write(
                        "✅ BigQuery query executed successfully"
                    )

                    st.write(
                        "✅ Results interpreted and summarized"
                    )


                # =========================================
                # GENERATED SQL
                # =========================================

                with st.expander(
                    "View Generated SQL"
                ):

                    st.code(
                        sql,
                        language="sql",
                    )


                # =========================================
                # QUERY INFORMATION
                # =========================================

                with st.expander(
                    "Query Information"
                ):

                    query_col1, query_col2 = (
                        st.columns(2)
                    )


                    with query_col1:

                        st.metric(
                            "Rows Returned",
                            f"{len(df):,}",
                        )


                    with query_col2:

                        st.metric(
                            "Data Processed",
                            f"{processed_mb:.2f} MB",
                        )


                    st.write(
                        f"**Estimated bytes processed:** "
                        f"{bytes_processed:,}"
                    )

                    st.write(
                        f"**Validation status:** "
                        f"{validation_message}"
                    )


                # =========================================
                # DATA NOTES
                # =========================================

                show_data_notes()


            # =============================================
            # STANDARD ANALYTICS ERROR
            # =============================================

            except Exception as e:

                st.error(
                    "HealthSight was unable to "
                    "complete the analysis."
                )

                with st.expander(
                    "Technical Details"
                ):

                    st.exception(
                        e
                    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "HealthSight • Patchamomma 2026 • "
    "Google BigQuery + Gemini + Google ADK + "
    "Python + Streamlit"
)

