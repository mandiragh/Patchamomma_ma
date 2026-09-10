# HealthSight

HealthSight is an AI-powered healthcare analytics application that allows users to explore public Medicare inpatient data using natural-language questions instead of writing SQL.

The application combines Google Gemini, Google ADK, BigQuery, Streamlit, and Cloud Run to provide governed, explainable, and self-service healthcare analytics. It supports both a deterministic analytics workflow and an agentic workflow that can inspect schema, validate SQL, execute protected BigQuery queries, and return results with explanations and visualizations.

## Live Demo

HealthSight is deployed on Google Cloud Run and is publicly accessible at:
Link: https://healthsight-285849155638.us-east1.run.app/ 


## Project Overview

Healthcare administrators, analysts, researchers, and operational teams often depend on technical staff to write SQL and retrieve information from large healthcare datasets. HealthSight reduces this dependency by allowing users to ask questions in plain English and receive structured analytical results.

Example questions include:

- Which states had the highest average Medicare inpatient payments?
- Which hospitals had the highest total inpatient discharges in 2014?
- What were the most common inpatient DRGs?
- Compare Medicare inpatient payments between Massachusetts and New York.

The current MVP uses the public Medicare Inpatient Charges 2014 dataset in Google BigQuery.

## Key Features

### Natural-Language Analytics

Users can ask healthcare data questions in plain English. Gemini interprets the request and generates GoogleSQL for BigQuery.

### Two Analysis Modes

HealthSight provides two execution approaches:

**Standard Analytics**

A deterministic workflow designed for predictable and efficient analysis:

1. Receive the user question.
2. Generate SQL with Gemini.
3. Validate the SQL.
4. Perform a BigQuery dry run.
5. Enforce a query-processing limit.
6. Execute the query.
7. Return structured results.
8. Generate a concise explanation.

**HealthSight Agent**

An agentic workflow built with Google ADK. The agent can dynamically determine which tools are required for a request, including:

- Medicare schema inspection
- SQL validation
- Protected BigQuery query execution

This mode also exposes the actual tool sequence used during analysis.

### Schema-Aware Query Generation

HealthSight can inspect the BigQuery table schema before executing analysis. This helps reduce invalid queries caused by invented or incorrect column names.

### Healthcare-Specific Analytical Rules

The application includes domain-aware guidance for healthcare analytics. For example, state-level Medicare payment comparisons use discharge-weighted aggregation rather than a simple average across provider and DRG rows.

HealthSight also distinguishes covered charges from actual hospital costs and avoids presenting historical data as current healthcare conditions.

### SQL Safety Controls

AI-generated SQL is validated before execution.

The current safety layer:

- Allows read-only analytical queries using `SELECT` or `WITH`
- Rejects data-changing statements such as `DELETE`, `UPDATE`, `INSERT`, `DROP`, `ALTER`, and `CREATE`
- Restricts queries to the approved Medicare dataset
- Revalidates SQL before protected execution

The safety validator is designed as an MVP guardrail and should not be treated as a replacement for production-grade SQL parsing, access control, and database governance.

### BigQuery Cost Protection

Before a query executes, HealthSight performs a BigQuery dry run to estimate the amount of data that will be processed.

The application also uses a maximum-bytes-billed limit to reduce the risk of unexpectedly expensive AI-generated queries.

### Explainable Results

HealthSight provides:

- Natural-language insight
- KPI cards
- Dynamic visualizations
- Query result tables
- Generated SQL
- Query-processing information
- CSV export
- Agent tool activity when Agent Mode is used

## Architecture

```text
User
  |
  v
Streamlit Web Interface
  |
  v
Analysis Mode
  |
  +-------------------------------+
  |                               |
  v                               v
Standard Analytics          HealthSight Agent
  |                               |
  v                               v
Gemini Text-to-SQL          Google ADK
  |                               |
  v                               v
SQL Validator               Tool Selection
  |                               |
  v                         Schema Inspection
BigQuery Dry Run                  |
  |                               v
  v                         SQL Validation
Query Cost Limit                  |
  |                               v
  v                         Protected BigQuery
BigQuery Execution                Execution
  |                               |
  +---------------+---------------+
                  |
                  v
           Query Results
                  |
                  v
        Pandas / Result Layer
                  |
                  v
 Streamlit Results, KPIs, Charts,
 SQL Transparency and CSV Export
```

## Google Cloud Architecture

HealthSight uses the following Google Cloud services:

| Service | Purpose |
| --- | --- |
| Google BigQuery | Stores and analyzes the public Medicare dataset |
| Gemini API | Natural-language understanding, Text-to-SQL generation, and result explanation |
| Google ADK | Agent orchestration and tool execution |
| Cloud Run | Hosts the Streamlit application |
| Secret Manager | Stores the Gemini API key securely |
| IAM / Service Accounts | Controls application permissions |
| Cloud Build | Builds the application container during deployment |
| Artifact Registry | Stores the container image used by Cloud Run |

Additional technologies:

| Technology | Purpose |
| --- | --- |
| Python | Core application language |
| Streamlit | Web interface |
| Pandas | Query result handling |
| Docker | Application packaging |
| `google-cloud-bigquery` | BigQuery client integration |
| `google-genai` | Gemini API integration |

## Dataset

HealthSight currently uses:

```text
bigquery-public-data.medicare.inpatient_charges_2014
```

The table includes fields such as:

- `drg_definition`
- `provider_id`
- `provider_name`
- `provider_city`
- `provider_state`
- `total_discharges`
- `average_covered_charges`
- `average_total_payments`
- `average_medicare_payments`

The dataset represents historical Medicare inpatient information from 2014.

HealthSight clearly communicates this limitation in the interface so users do not interpret the results as current healthcare conditions.

## Repository Structure

```text
healthsight/
├── app.py
├── agent_runner.py
├── bigquery_service.py
├── chart_service.py
├── result_explainer.py
├── schema_tool.py
├── sql_validator.py
├── text_to_sql.py
├── prompts.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── adk_app/
│   ├── __init__.py
│   └── agent.py
└── tests/
    ├── __init__.py
    ├── eval_questions.json
    ├── test_agent_runner.py
    ├── test_analytics_eval.py
    ├── test_bigquery.py
    ├── test_gemini_connection.py
    ├── test_pipeline.py
    ├── test_safety.py
    ├── test_schema.py
    ├── test_text_to_sql.py
    └── test_validator.py
```

Actual filenames may vary slightly as the project evolves.

## Local Setup

### Prerequisites

- Python 3.13
- Google Cloud CLI
- Access to a Google Cloud project
- Gemini API key
- BigQuery API access

### 1. Clone the repository

```bash
git clone <https://github.com/mandiragh/Patchamomma_ma>
cd healthsight
```

### 2. Create a virtual environment

```bash
python3.13 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project healthsight-patchamomma
```

### 5. Create the local environment file

Create a `.env` file in the project directory:

```text
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=your_standard_model
ADK_MODEL=your_agent_model
```

Do not commit `.env` or API credentials to Git.

### 6. Run the application locally

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

## Environment Variables

HealthSight expects the following environment variables:

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Gemini API authentication |
| `GEMINI_MODEL` | Model used by the standard analytics workflow |
| `ADK_MODEL` | Model used by the Google ADK agent |

For Cloud Run, the Gemini API key is stored in Google Secret Manager rather than included directly in the source code or container image.

## Cloud Run Deployment

The application is containerized with Docker and deployed to Google Cloud Run.

A dedicated runtime service account is used:

```text
healthsight-runner@healthsight-patchamomma.iam.gserviceaccount.com
```

The runtime account is configured with only the permissions needed by the application, including BigQuery job execution and access to the Gemini secret.

Example deployment command:

```bash
gcloud run deploy healthsight \
  --source . \
  --project healthsight-patchamomma \
  --region us-east1 \
  --service-account healthsight-runner@healthsight-patchamomma.iam.gserviceaccount.com \
  --set-secrets="GEMINI_API_KEY=healthsight-gemini-api-key:latest" \
  --set-env-vars="GEMINI_MODEL=${GEMINI_MODEL_VALUE},ADK_MODEL=${ADK_MODEL_VALUE}" \
  --allow-unauthenticated
```

The application should never store API keys directly in GitHub, the Dockerfile, or source code.

## Testing and Evaluation

HealthSight includes tests for:

- SQL validation
- BigQuery connectivity
- Schema discovery
- Gemini connectivity
- Text-to-SQL generation
- End-to-end query execution
- ADK agent execution
- Safety behavior
- Analytical correctness

### Safety Evaluation

The current MVP safety test suite evaluates:

- Safe `SELECT` queries
- Safe `WITH` queries
- Rejection of `DELETE`
- Rejection of `UPDATE`
- Rejection of `DROP`
- Rejection of unauthorized datasets

Current safety test result:

```text
6/6 tests passed
Safety score: 100%
```

This result applies to the current defined test cases and should not be interpreted as proof of complete production security.

### Analytical Evaluation

Representative questions are evaluated for:

- Use of real schema fields
- SQL validity
- BigQuery dry-run success
- Appropriate healthcare aggregation logic
- Correct interpretation of covered charges and payments
- Safe handling of user requests

Analytical evaluation may be constrained by Gemini API quota limits during development.

## Security and Governance

HealthSight follows several defensive design principles:

- Read-only query enforcement
- Approved-dataset restriction
- SQL validation before execution
- Revalidation inside the protected execution tool
- BigQuery dry runs before execution
- Maximum query-processing limits
- Secret Manager for API credentials
- Dedicated Cloud Run runtime identity
- Historical-data disclaimers
- No medical diagnosis or patient-specific recommendations

For a production healthcare environment, additional controls would be required, including stronger SQL parsing, role-based access control, audit logging, data classification, PHI protections, dataset-level IAM, row-level security, and organizational compliance requirements.

## Current Scope

The current MVP focuses on one curated public healthcare dataset.

It is not:

- A clinical decision-support system
- An electronic health record system
- A patient-level diagnostic application
- A PHI-enabled production healthcare platform
- A replacement for healthcare analysts or clinical professionals

The MVP is intended to demonstrate the architecture and value of governed, agent-assisted healthcare analytics.

## Future Roadmap

Potential future enhancements include:

- Multi-dataset discovery and routing
- Additional CMS datasets
- Medicare outpatient and provider analytics
- Claims and hospital operations data
- Healthcare semantic catalog
- Cross-dataset joins
- FHIR-compatible data integration
- Enterprise authentication
- Role-based access control
- Row-level security
- Query audit trails
- Saved analytical sessions
- Automated data-quality checks
- More advanced healthcare KPI libraries
- Production-grade SQL parsing and policy enforcement

The long-term vision is for HealthSight to connect to an approved catalog of healthcare datasets so users can ask questions without needing to know which database, table, or field contains the answer.

## Design Philosophy

HealthSight is not intended to be only a generic Text-to-SQL application.

The project focuses on four areas:

1. Healthcare-aware analytical logic
2. Governed AI-generated query execution
3. Transparent and explainable analytics
4. Agentic tool orchestration where it provides value

The goal is to make healthcare analytics easier for non-technical users while maintaining clear controls around data access, SQL execution, query cost, and interpretation.

## Project Status

The current MVP includes:

- Natural-language healthcare analytics
- Gemini Text-to-SQL generation
- Google ADK agent mode
- BigQuery integration
- Schema inspection
- SQL validation
- Query dry runs and processing limits
- Healthcare-specific aggregation guidance
- Result explanations
- KPI cards
- Dynamic charts
- CSV export
- SQL transparency
- Agent activity display
- Cloud Run deployment
- Secret Manager integration
- Automated safety testing

## Project Context

HealthSight was developed as part of the Patchamomma 2026 build program.

The project demonstrates how Google Cloud and generative AI technologies can be combined to build a governed self-service analytics experience for healthcare data.

## Disclaimer

HealthSight currently analyzes public historical Medicare inpatient data from 2014. It is intended for demonstration, analytics, research, and educational purposes only.

The application does not provide medical advice, diagnosis, treatment recommendations, or patient-specific clinical guidance.


## Acknowledgment and AI Assistance

HealthSight was conceived, designed, and implemented by the project author. AI tools, including ChatGPT, Claude, and Google Gemini, were used to support brainstorming, coding, debugging, and documentation during development.