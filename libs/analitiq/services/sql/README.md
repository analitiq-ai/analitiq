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
- **Tables to Use (List[str])** *(optional)*: Specific tables to be used for constructing the SQL query, if known in advance.

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

```python
user_prompt = 'Show me total sales by category.'

# Optionally, specify relevant tables if known
tables_to_use = ['sales_data']

sql_service = Sql()
relevant_tables = sql_service.get_relevant_tables(user_prompt)
sql_query = sql_service.prompt2sql(user_prompt, relevant_tables)

# Execute the generated SQL query and get results as a DataFrame
result_df = sql_service.execute_sql(sql_query)

# For demonstration, print the resulting DataFrame
print(result_df)

# Running the full process in one step
response = sql_service.run(user_prompt)
print(response.content)  # DataFrame as JSON
print(response.metadata)  # Executed SQL and relevant tables
```

## Example async usage
```python
from utils import db_utils
from analitiq.services.sql.base import Sql
import os
import asyncio
import json

async def main():
    user_prompt = "What is our commission per venue?"
    db_eng = db_utils.create_db_engine('postgresql', 'psycopg2', os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_PORT"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"), os.getenv("POSTGRES_DB"), 'sample_data')
    agent = Sql()

    result = agent.run(user_prompt)
    print(result.metadata['sql'])
    
    # If you want to format the resulting Data Frame
    df_formatted = df.to_json(orient="split")
    
    print(df_formatted)

asyncio.run(main())
```