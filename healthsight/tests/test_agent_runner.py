from agent_runner import run_healthsight_agent


question = (
    "Which states had the highest average "
    "Medicare inpatient payments?"
)


result = run_healthsight_agent(
    question
)


print("\nSTATUS:")
print(result["status"])


print("\nFINAL ANSWER:")
print(result["answer"])


print("\nTOOLS USED:")
print(result["tools_used"])


print("\nGENERATED SQL:")
print(result["sql"])


print("\nBYTES PROCESSED:")
print(result["bytes_processed"])


print("\nROWS:")
print(result["rows"][:3])

