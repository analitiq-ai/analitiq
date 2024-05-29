# SQL Service

The SQL service, part of the `analitiq` framework, empowers users to interact with databases through natural language prompts. By leveraging advanced natural language processing (NLP) techniques, this service interprets user inputs to determine relevant database tables, generate SQL queries accordingly, and execute these queries. The results are returned as pandas DataFrames, making data analysis and visualization tasks more accessible to users without deep SQL expertise.

## Purpose

The SQL service is designed to bridge the gap between natural language queries and SQL, enabling users to extract and analyze data from databases by simply describing their data retrieval needs in plain English. This eliminates the need for intricate SQL knowledge and speeds up the data retrieval process, making it ideal for quick insights and iterative data exploration.

## How It Works

The service operates through several steps:
1. **Table Identification**: From the user's natural language prompt, the service identifies relevant tables within the database.
2. **Query Generation**: It then translates the prompt into a structured SQL query using the identified tables.
3. **Query Execution**: The SQL query is executed against the database, and the results are fetched.
4. **Result Transformation**: Finally, the results are converted into a pandas DataFrame for easy manipulation, analysis, or visualization.

## Inputs and Outputs

### Inputs
- **User Prompt (str)**: A natural language description of the data retrieval or analysis task.

### Outputs
- **Response Object**: Contains the query result set as a pandas DataFrame and metadata including executed SQL and relevant tables.
1. response.content = pandas dataframe of the result
2. response.metadata = metadata, such as SQL that has been executed.
```python
metadata={
    "chart_type": "Pie"
}
```

## Example Usage

You may need to add directory for Analitiq to your Python path.
Here is an example:
```python
import os
import sys
# Get the home directory
home_directory = os.environ['HOME']
# Dynamically construct the path
dynamic_path = f'{home_directory}/Documents/Projects/analitiq/libs/'
sys.path.insert(0, dynamic_path)
```
We need 3 things for SQL service to work with:
1. Database
2. Large Language Model
3. VectorDB (for searching documentation for better SQL results)

```python
from sql import Sql
from analitiq.base.BaseDb import BaseDb
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.base.vectordb.weaviate.weaviate_vs import WeaviateHandler

user_prompt = "Please give me revenues by month."

db_params = {'name': 'prod_dw'
    , 'type': 'redshift'
    , 'host': 'xxxx'
    , 'user': 'smy_user'
    , 'password': '1234455'
    , 'port': 5439
    , 'dbname': 'my_db'
    , 'dbschemas': ['schema1', 'schema2']
    , 'threads': 4
    , 'keepalives_idle': 240
    , 'connect_timeout': 10}
db = BaseDb(db_params)

llm_params = {'type': 'bedrock'
    , 'name': 'aws_llm'
    , 'api_key': None
    , 'temperature': 0.0
    , 'llm_model_name': 'anthropic.claude-v2'
    , 'credentials_profile_name': 'my_profile'
    , 'provider': 'anthropic'
    , 'aws_access_key_id': 'xxxxxx'
    , 'aws_secret_access_key': 'xxxxxxx'
    , 'region_name': 'eu-central-1'}
llm = BaseLlm(llm_params)

vdb = WeaviateHandler('https://12345.weaviate.network', 'xxxxxxx', 'my_project')

# Example of using the SQLGenerator class
sql_gen = Sql("Please give me revenues by month.", db, llm, vector_db=vdb)
result = sql_gen.run()
print(result)

```

