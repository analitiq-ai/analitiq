TEXT_TO_SQL_PROMPT = """
You are a Data Analyst with a lot of experience in writing {dialect} queries in SQL.
You have received the following user request: {user_prompt}.
Your job is to create a proper SQL query for {dialect}.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per {dialect}.
You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question.
Quality each table name with a schema name, like this: schema_name.table_name.

# Important considerations
Write an initial draft of the query. Then double check the {dialect} query for common mistakes, including:
- Using only columns that exist in each table
- Pay attention to use date('now') function to get the current date, if the question involves "today"
- Pay attention to which column is in which table
- Not using columns that do not exist in the table
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins
- Keep in mind that underlying granular data may be very large. Try to obtain a summarized set of data from the database, but granular enough to answer the input question.

{docs_ddl}

{docs_schema}

# Response format instructions:
Make sure the SQL complies with {dialect} standard.
{format_instructions}
"""

RETURN_RELEVANT_TABLE_NAMES = """
You are a detail oriented data analyst.
Bellow is a database structure for your reference
Your goal is to select names of tables and queries that could be used to answer a query "{user_prompt}".
Return the names of all the SQL tables and columns that might be relevant to answering the query.
Do not return empty table names or empty column names.
Do not return table names and column names that do not exist in the Database Structure provided to you.
{db_docs}
Database Structure:\n
{ddl}

{format_instructions}
"""

FIX_SQL = """
You are an SQL expert with specialty in {dialect}.
The following SQL generates an error.
Please examine this SQL, fix it so it can be executed and return it back.

sql:
{sql}

Error:
{error}
"""


FIX_RESPONSE = """
You were asked to crete an SQL to address a user query: {user_prompt}.
Your response resulted in an error.
I will provide you our chat history between the tags CHAT_HISTORY_START and CHAT_HISTORY_END.
Please examine the chat history and correct your response by addressing the error that is provided after it.
Prompts from user are identified with "Human:".
Your responses are identified with "Assistant:".
I will provide you format requirements between tags RESPONSE_INSTRUCTIONS_START and RESPONSE_INSTRUCTIONS_END in which I expect you to provide your response.
Please follow these instructions carefully.

CHAT_HISTORY_START
{chat_hist}
CHAT_HISTORY_END

RESPONSE_INSTRUCTIONS_START
Your corrected response should be a properly formatted JSON.
Use double quotes to define JSON object keys and string boundaries.
Apply incorrect escaping of double quotes inside the string values of the JSON.
Do not add new line or tab characters.

{format_instructions}
RESPONSE_INSTRUCTIONS_END
"""
