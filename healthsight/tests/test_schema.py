from schema_tool import get_tables, get_table_schema


print("Available Medicare tables:")
print(get_tables())

print("\nSchema for inpatient_charges_2014:")
print(get_table_schema("inpatient_charges_2014"))