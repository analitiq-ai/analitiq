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

```python
from analitiq.services.sql.sql import Sql

instance = Sql()
response = instance.run("Who are our top 10 customers? Give me chart")
print(response)

print(response.content)  # DataFrame as JSON
print(response.metadata)  # Executed SQL and relevant tables
```

