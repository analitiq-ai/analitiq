PROMPT_CLARIFICATION = """
You are a data analyst.
You have received the following query from the user {user_prompt}:
Is this query from the user clear to you or would you need further info from the user to answer the query?
If the query is not clear, provide feedback about exactly what you need in order to complete the request without further input.
{format_instructions}
"""

SERVICE_SELECTION = """
You are a leader of a data team with multiple tools called services at your disposal. 
You received a user query:
{user_prompt}

Examine the list of the services required to fulfill the query that you have earlier identified and match this list of required services against the list of available services.
You can only match required services to the list of available services.
User may specify for you in the query the actions needed to be taken in the order they need to be taken. Example: actions: query data -> analyse.
You would need to select a tool to match each action.
Your response should contain only available services
User can force you to use only specific services by adding to the query word 'tool' and adding service dependency, like this: tools: sql->chart

Available Services:
{available_services}

Required Services:
{required_services}

{format_instructions}
"""

SERVICE_DEPENDENCY = """
You are a leader of a data team. You received a user query:
{user_prompt}

You have already selected a list of services to use to fulfill users query.
You now need to construct a dependency dictionary from the selected services in the order needed to execute them to answer the users query.
Pay particular attention to the inputs and the outputs of each service as some services take inputs from previous services.
The inputs and outputs formats are defined in the list of available services.
You need to make sure in your dependency dictionary that if Service B runs after Service A, then service A produces output in a format in which service B can process it.

Follow these rules:
-If services can run in parallel, do not make them dependant on each other. For example, chart does not have to depend on the analyze service.
-If a service depends on another service, its' inputs must match the output of the service on which it depends. Check the service info input and output parameters for this.
-Services can be reused in the dependency JSON, if needed
-Use example dependency JSON for an example of how to structure dependency between nodes
-Once you complete the dependency JSON, double check that the inputs of the service can accept the outputs of dependencies services.

Please respond with only a dictionary of service names as nodes as per example provided.
Do not add numbering or bullets.
Return a properly formatted json.

Selected services as a list of service names:
{selected_services}

Available Services in JSON format:
{available_services}

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
If multiple tasks are using the same tool consider combining these tasks into one task.

You have access to the following tools: 
SQL - SQl tool to query data in the database or data warehouse.
DataViz - Data visualization and charting tool.
VectorStore - Access and search vector store database that has company documentation and processes and operations.

{format_instructions}
"""

REFINE_TASK_LIST = """
Here is a list of generated tasks to answer a users query {user_prompt}.
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
User has given to you the following queries during a chat.
Put yourself in place of the user who has given you the queries, examine the queries and try to formulate a coherent request out of them.
Return back in your response only the formulated request.
Queries:
{user_prompt_hist}
{user_prompt}
"""


