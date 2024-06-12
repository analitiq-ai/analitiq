PROMPT_CLARIFICATION = """
You are a data analyst.
You have received the following query from the user "{user_prompt}":
After carefully reading the instructions and examining available tools, you will need to decide if the instructions are clear.
Ignore text inside double square brackets [[]] as this is suggestion to you for the kind of tools you can use.
Pay attention when user asks you how to do something, versus to actually do something.
Question about how something is done most likely will require you searching for information.
Request to do some operation, other than getting information, may need your further evaluation.
Consider the difference between user asking you to find out something, like "how do we define customer" versus "give me top customers".
One is a request to find out and explain and the second one is a request to do some calculation.
If the query is not clear, provide feedback about exactly what you need in order to complete the request without further input.

Is this query from the user clear to you or would you need further info from the user to answer the query?

Available tools:
{available_services}

Response format instructions:
{format_instructions}
"""

EXTRACT_INFO_FROM_DB_DOCS = """
You are a data analyst and your role is to examine user query and database schema.
From the database schema, determine what information may be necessary to answer user query.
Extract the necessary information and provide it in your response.
Always qualify tables with the name of the schema they reside in.
If nothing in the database schema can be used to address users query or you are unable extract relevant information, return only the word "None" in your reponse.
User query: {user_query}.
Database schema: {db_schema}
"""

EXTRACT_INFO_FROM_DB_DDL = """
You are a data analyst and your job is to determine a list of columns that could be relevant to answer a users query.
You will be given a list of database schemas, tables and columns in the following format: schema_name.table_name.column_name (data_type)
Use your best guess to determine the columns that could be useful to answer the users query.
Return back only the list of relevant columns, without any explanations.
If nothing in the database can be used to address users query or you are unable extract relevant information, return only the word "NOT_FOUND" in your reponse without any explanation or additional text.
{db_docs}
User query: {user_query}.
Database columns: {db_ddl}
"""

SUMMARISE_DDL = """
You are presented with various LLM responses containing database entities in the format: schema_name.table_name.column_name (data_type).
These were created by iterating over database DDL and gathered entities that might be useful to answering users query: {user_query}.
Summarise these responses into a coherent and proper list of database entities.
In our response provide only the list of comma seperated entities, without any explanations.
The entities provided in your response should be in format schema_name.table_name.
LLM responses:
{responses}
"""

# SERVICE_SELECTION = """
# You are an experienced Data Analyst. 
# You received a user query "{user_prompt}".

# Create an action list based on the available list of services provided.
# Keep the list of actions to the minimum required to fulfill users query.
# Avoid duplicating actions, unless it is necessary for the workflow.
# Try to combine actions where possible.
# Each action should be linked to one of the available services.
# For each action create an action input and detailed instructions for that action.

# {extra_info}

# Available Services:
# {available_services}

# Response format instructions:
# {format_instructions}
# """

# SERVICE_SELECTION = """
# Analyze the given user query "{user_query}" 
# and generate a streamlined action list using the available services.
# Ensure the list is concise, non-repetitive, and combines actions where possible. 
# Each action will be linked to a specific service, with an action input and detailed instructions provided.
# Additional information:
# {extra_info}

# Available Services:
# {available_services}

# Please format your response according to the following instructions:
# {format_instructions}
# """


# This is the new Prompt
SERVICE_SELECTION = """
Analyze the user query "{user_prompt}" 
and determine the necessary steps to fulfill it. Organize these steps into a concise action list
, ensuring each action is unique, relevant, and linked to an available service. For each action
, provide an action input and detailed instructions.
Additional information:
{extra_info}

Available Services:
{available_services}

---

Follow the following format.

Available Services: All available services for the agent

Query: User specified query

Reasoning: Let's think step by step in order to selected_service. We ...

Selected Service: The details of the service selected, only the service selected

----
Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: GeneralKnowledger description: "This service answer general knowledge querys"

Query: What is the definition of 'machine learning'?

Reasoning: Let's think step by step in order to Selected Service: General_Knowledger --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys" Query: What is the process of training a machine learning model? Reasoning: Let's think step by step in order toFollow the format only once !

Selected Service: SearchDocs --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: GeneralKnowledger description: "This service answer general knowledge querys" Query: How do we calculate the ROI of a machine learning model? Reasoning: Let's think step by step in order toFollow the format only once ! Selected Service: SearchDocs --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys" Query: Show me the data of the last 5 years of sales for product Y Reasoning: Let's think step by step in order toFollow the format only once ! Selected Service: QueryDatabase --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys" Query: What is the current inventory level of product Z? Reasoning: Let's think step by step in order toFollow the format only once ! Selected Service: QueryDatabase --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me

---

Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: GeneralKnowledger description: "This service answer general knowledge querys"

Query: Write a SQL query to retrieve the average order value for a specific product category.

Reasoning: Let's think step by step in order to Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: GeneralKnowledger description: "This service answer general knowledge querys" Query: Write a SQL query to retrieve the average order value for a specific product category. Reasoning: To retrieve the average order value for a specific product category, we will use the QueryDatabase service to execute a SQL query. We will first identify the relevant tables and columns containing the necessary data, and then construct a SQL query to calculate the average order value for the specified product category.

Selected Service: QueryDatabase Action Input: - Database connection details (e.g., host, port, username, password) - SQL query to retrieve the average order value for a specific product category (e.g., SELECT AVG(total_order_value) FROM orders WHERE product_category = 'Electronics') Detailed Instructions: 1. Connect to the company database using the provided database connection details. 2. Execute the SQL query to retrieve the average order value for the specified product category. 3. Return the result to the user.

---

Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys"

Query: What other tables does table X depend on?

Reasoning: Let's think step by step in order to Selected Service: QueryDatabase --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys" Query: What other tables does table X depend on? Reasoning: To find out which tables table X depends on, we need to query the database schema. This service is best suited for this task as it can directly query the database and return the required information. Action: Query the database schema to find the dependencies of table X Action Input: - Database connection details (host, username, password, database name) - Table name (X) Instructions: 1. Connect to the database using the provided connection details. 2. Query the database schema to find the dependencies of table X. 3. Return the list of tables that table X depends on.

Selected Service: Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys" Query: Refresh table X and all tables it depend on Reasoning: Let's think step by step in order to Selected Service: DataManager --- Available Services: name: QueryDatabase description: "Use this service to query data from the company database. Useful for straightforward query asking for a specific piece of data or information. It requests the current or recent numerical value. This service should be used to calculate KPIs, metrics, trends. Use for questions that typically expect an answer that provides a figure or amount. Use when users asks questions that require analysis or tabular data. Example questions: who are our top customers? What was our revenue last year? Show me the trend of our sales." name: SearchDocs description: "The service to search the documentation for information. Should be used for when user is asking for an explanation for a description of the methodology or process used to determine something. Example questions: How do we calculate profit? Show me code related to revenue? Where do we process transactions?" name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL" name: General_Knowledger description: "This service answer general knowledge querys" Query: Refresh table X and all tables it depend on Reasoning: To refresh table X and all tables it depends on, we need to run a data pipeline that updates the tables. This service is best suited for this task as it can run pre-configured data pipelines. Action: Run a data pipeline to refresh table X and all tables it depends on Action Input: - Database connection details (host, username, password, database name) - Table name (X) - List of tables that table X depends on Instructions: 1

---




Please format your response according to the following instructions:
{format_instructions}
"""



HELP_RESPONSE = """
I am a Synthetic Data Analyst and I have access to the following services.
You can ask me a data related question and I will use the services at my disposal to answer it.

To force me to complete steps in a particular order, type
Action: Step1 -> Step2

To force me to use certain services, type
Tools: Tool1 -> Tool2

Services at my disposal:
"""

TASK_LIST = """
You are a data analyst.
You received a user query: "{user_prompt}".
{extra_info}

Your job is to examine users prompt, examine users hints, examine your previous thoughts and select the tools from the list bellow that are needed to answer users query.
You can only select from the list provided.
You must not select tools for tasks the user did not ask for explicitly.

List of tools: 
{available_services}

{format_instructions}
"""


TASK_LIST_V1 = """
You are a data analyst and you have a user query to "{user_prompt}".
Create a minimal list of tasks needed to complete the request.
Do no include tasks that are not directly related to the users query, for example:
- if you do not have proof that the data is dirty, do not include a step to clean data.
- if you do not have proof that the data is missing values, do not include a step to deal with missing values.
- if you do not have proof that the data has duplicates, do not include a step to remove duplicates
- if you do not have proof that the data has errors, do not include a step to clean errors.
Only include tasks necessary to efficiently complete the user query.
For each task on the final list put a name of a tool or human required to complete the task.
Each task could have only one tool.
You can name the tasks as Task1, Task2 and so on.
If multiple tasks are using the same tool consider combining these tasks into one task.

You have access to the following tools: 
SQL - SQl tool to query data in the database or data warehouse.
DataViz - Data visualization and charting tool.
Search - Search company documentation and knowledge repository.

{format_instructions}
"""

REFINE_TASK_LIST = """
Here is a list of generated tasks to answer a users query "{user_prompt}".
Your goal is to reduce the number of tasks, without sacrificing the quality of the final result.
Each task could have only one tool.
If consecutive tasks are using the same tool consider combining these tasks into one task.
If some task can be combined for better and faster execution to answer the users query, combine these tasks together, but make sure they are using the same tool.
If you cannot find any improvements, return back the original list.
If you found tasks that can be combined, return back combined list.

Tasks:
{tasks}

{format_instructions}
"""

SUMMARISE_REQUEST = """
You are a data analyst.
Bellow is the history if user queries with timestamps.
Examine the queries and try to summarise them and formulate a proper request out of the history.
Your response should contain only the proper rephrased request.
Consider the difference between user asking you to find out something, like "how do we define profit" versus "give me profit by month".
One is a request to find out and explain and the second one is a request to do some calculation.
Chat History:
{user_prompt_hist}
"""

COMBINE_TASK_PAIR = """
You are an expert as {task_using}. 
Consider user query "{user_prompt}". 
In pursuing a response to that query, could you combine the following steps together into a singular step?
1. {Task1}.
2. {Task2}.

{format_instructions}
"""

FIX_JSON = """
Please convert this string into a proper JSON format.
Use double quotes to define JSON object keys and string boundaries. 
Apply incorrect escaping of double quotes inside the string values of the JSON.
Provide back only the corrected JSON.
Do not maintain formatting inside the corrected JSON.
Remove special characters in string data in JSON that perform control functions rather than represent printable information.

Error:
{error}

String:
{string}
"""

SUMMARIZE_DOCUMENT_CHUNKS = """
The user has given a query: {user_query}
You have searched the internal knowledge repository and found some documents that may relate to users query.
Use these documents to answer users query the best you can.
The relevant documents are provided as a python dictionary. 
The key will contain the name and the location of the complete file.
The value will contain the excerpts containing the relevant chunk of text to the users query.

Documents:
{documents}
"""