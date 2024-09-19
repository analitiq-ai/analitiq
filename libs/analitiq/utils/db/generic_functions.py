def extract_table_name_from_string(input_string: str) -> str:
    """Extract 'table_name' from the given string by splitting the text by commas,
    taking the first occurrence, and then splitting by dots to take the second occurrence.
    Gets output from db.get_schemas_and_tables(schema_name)

    Args:
    ----
        input_string (str): The input string containing the table name information.

    Returns:
    -------
        str: Extracted table name.

    """
    # Split the string by comma and take the first occurrence
    first_part = input_string.split(",")[0]

    # Split the first part by dot and take the second occurrence
    schema_table = first_part.split(".")[0] + "." + first_part.split(".")[1]

    return schema_table
