import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from adk_app.agent import root_agent


APP_NAME = "healthsight"
USER_ID = "healthsight_user"


async def _run_agent(question: str):

    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=question)
        ],
    )

    final_text = ""

    tool_calls = []

    executed_sql = None

    query_rows = []

    bytes_processed = None


    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
    ):

        # =================================================
        # CAPTURE TOOL CALLS
        # =================================================

        try:

            function_calls = event.get_function_calls()

            for call in function_calls:

                tool_calls.append(call.name)

                # Capture SQL sent to BigQuery execution tool
                if call.name == "execute_medicare_query":

                    if call.args:

                        executed_sql = call.args.get(
                            "sql"
                        )

        except Exception:
            pass


        # =================================================
        # CAPTURE TOOL RESPONSES
        # =================================================

        try:

            function_responses = (
                event.get_function_responses()
            )

            for response in function_responses:

                if (
                    response.name
                    == "execute_medicare_query"
                ):

                    tool_result = (
                        response.response or {}
                    )


                    # Some ADK versions/tools may wrap
                    # results inside {"result": {...}}
                    if (
                        isinstance(tool_result, dict)
                        and "result" in tool_result
                        and isinstance(
                            tool_result["result"],
                            dict,
                        )
                    ):

                        tool_result = (
                            tool_result["result"]
                        )


                    if isinstance(
                        tool_result,
                        dict,
                    ):

                        if (
                            tool_result.get("status")
                            == "success"
                        ):

                            query_rows = (
                                tool_result.get(
                                    "rows",
                                    [],
                                )
                            )

                            bytes_processed = (
                                tool_result.get(
                                    "bytes_processed"
                                )
                            )

        except Exception:
            pass


        # =================================================
        # CAPTURE FINAL AGENT RESPONSE
        # =================================================

        try:

            if event.is_final_response():

                if (
                    event.content
                    and event.content.parts
                ):

                    final_text = "".join(
                        part.text or ""
                        for part
                        in event.content.parts
                    )

        except Exception:
            pass


    # Remove duplicate tool names while preserving order
    unique_tools = list(
        dict.fromkeys(tool_calls)
    )


    return {
        "status": "success",
        "answer": final_text,
        "tools_used": unique_tools,
        "sql": executed_sql,
        "rows": query_rows,
        "bytes_processed": bytes_processed,
    }


# =========================================================
# PUBLIC RUNNER
# =========================================================

def run_healthsight_agent(question: str):

    try:

        return asyncio.run(
            _run_agent(question)
        )


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except Exception as e:

        error_text = str(e)


        # -------------------------------------------------
        # GEMINI QUOTA
        # -------------------------------------------------

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):

            return {
                "status": "quota_exceeded",
                "answer": (
                    "The HealthSight Agent is temporarily "
                    "unavailable because the Gemini API "
                    "quota has been reached."
                ),
                "tools_used": [],
                "sql": None,
                "rows": [],
                "bytes_processed": None,
            }


        # -------------------------------------------------
        # GEMINI TEMPORARILY UNAVAILABLE
        # -------------------------------------------------

        if (
            "503" in error_text
            or "UNAVAILABLE" in error_text
        ):

            return {
                "status": "model_unavailable",
                "answer": (
                    "The Gemini model is temporarily "
                    "unavailable. Please try again shortly."
                ),
                "tools_used": [],
                "sql": None,
                "rows": [],
                "bytes_processed": None,
            }


        # -------------------------------------------------
        # OTHER ERRORS
        # -------------------------------------------------

        return {
            "status": "error",
            "answer": (
                f"Agent execution failed: {error_text}"
            ),
            "tools_used": [],
            "sql": None,
            "rows": [],
            "bytes_processed": None,
        }

    