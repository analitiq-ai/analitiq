import json
import logging
from analitiq.utils import db_utils
from analitiq.base.BaseService import BaseResponse
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.BaseMemory import BaseMemory
from analitiq.utils.code_extractor import CodeExtractor
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser
from typing import List, Optional
import pandas as pd
from analitiq.utils.general import *


from analitiq.services.sql.prompt import (
    RETURN_RELEVANT_TABLE_NAMES,
    TEXT_TO_SQL_PROMPT,
    FIX_SQL
)


class Column(BaseModel):
    ColumnName: str = Field(description="The name of the column.")
    DataType: str = Field(description="Data type of the column.")


class Table(BaseModel):
    SchemaName: str = Field(description="The schema where this table resides.")
    TableName: str = Field(description="The name of the table.")
    Columns: List[Column] = Field(description="A list of relevant columns in the table.")


class Tables(BaseModel):
    TableList: List[Table] = Field(description="A list of relevant tables from the list of all tables in a database")


class SQL(BaseModel):
    SQL_Code: str = Field(description="Only SQL code goes in here.")
    Explanation: str = Field(description="Any text or explanation other than SQL code.")


class Sql:
    """Handles SQL query generation and execution against database. Useful when user would like to query data.

    This class integrates natural language processing to identify relevant database tables
    and generate SQL queries that are then executed against a database. The results are returned
    as data frames for further analysis or display.
    Manages SQL query generation and execution using LLMs for enhanced interaction with databases.

    Methods:
    __init__: Constructor to initialize database and LLM configurations.
    get_tables: Retrieves usable table names from the database.
    get_relevant_tables: Identifies relevant tables based on user input.
    get_sql2: Generates SQL queries based on user input.
    get_sql: Converts a user prompt into an SQL query using specified tables.
    run_sql: Executes SQL queries and returns results as a DataFrame.
    get_sql_from_llm: Parses and handles responses from the LLM.
    run: Orchestrates the process from prompt interpretation to SQL query execution.
    """

    def __init__(self, user_prompt) -> None:
        self.db = GlobalConfig().get_database()
        self.llm = GlobalConfig().get_llm()
        self.user_prompt = user_prompt
        self.relevant_tables = ""
        self.metadata = {
            "text": "",
            "relevant_tables": self.relevant_tables,
            "sql": "",
            "format": 'dataframe',
            "unpack_format": 'split' # this is helpful to let other services understand how to format this Data frame.
        }

    def get_ddl(self) -> List[str]:
        """Retrieves a list of usable table names from the database.

        Returns:
            str: A list of table names.
        Example:
            Database Structure:
                - Schema: Sales
                  - Table: Orders
                    - Columns: order_id (INTEGER), order_date (DATE), customer_id (INTEGER), total_amount (DECIMAL)
                  - Table: Customers
                    - Columns: customer_id (INTEGER), name (VARCHAR(255)), address (VARCHAR(255)), phone_number (VARCHAR(25))
                - Schema: HR
                  - Table: Employees
                    - Columns: employee_id (INTEGER), name (VARCHAR(255)), position (VARCHAR(100)), salary (DECIMAL)
                  - Table: Departments
                    - Columns: department_id (INTEGER), department_name (VARCHAR(100)), manager_id (INTEGER)

        """

        # Fetch all schemas (If your database supports schemas)
        ddl = db_utils.get_schemas_and_tabes(GlobalConfig().get_db_engine())

        return ddl

    def get_relevant_tables(self) -> List[str]:
        """
        Determines tables relevant to the given user prompt using AI.

        Returns:
            List[Table]: A list of relevant Table objects.
        """
        ddl = self.get_ddl()

        parser = PydanticOutputParser(pydantic_object=Tables)
        prompt = PromptTemplate(
            template=RETURN_RELEVANT_TABLE_NAMES,
            input_variables=["user_prompt"],
            partial_variables={"ddl": ddl
                ,"format_instructions": parser.get_format_instructions()}
        )

        prompt_as_string = prompt.format(user_prompt=self.user_prompt)

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": self.user_prompt})

        logging.info(f"[Node:SQL][Get relevant tables].\nInput: {self.user_prompt}.\nResponse: {response}")

        schema_dict = {}
        # Organize tables by schema
        for table in response.TableList:
            if table.SchemaName not in schema_dict:
                schema_dict[table.SchemaName] = []
            schema_dict[table.SchemaName].append(table)

        # Format the output string
        output_lines = []
        for schema, tables in schema_dict.items():
            output_lines.append(f"- Schema: {schema}")
            for table in tables:
                output_lines.append(f"  - Table: {schema}.{table.TableName}")
                column_details = ', '.join(f"{column.ColumnName} ({column.DataType})" for column in table.Columns)
                output_lines.append(f"    - Columns: {column_details}")

        self.relevant_tables = "\n".join(output_lines)
        self.metadata['relevant_tables'] = self.relevant_tables

        return True

    def parse_sql_from_string(self, llm_output: str):
        """
        Attempts to extract SQL from LLM textual putput.
        :param llm_output:
        :return:

        Example:
        Here is the fixed SQL:

        ```sql
        SELECT "name", SUM("sales_amount") AS "total_sales"
        FROM sample_data.sales
        GROUP BY "name"
        ORDER BY "total_sales" DESC
        LIMIT 10
        ```

        I made the following changes:

        - Replaced "customer" with "name", since the error indicates "customer" does not exist as a column. I assumed "name" is the correct column with customer names.
        - Kept the rest of the query the same - summing the sales_amount per name, ordering by total sales descending, and limiting to the top 10 rows.

        Let me know if you have any other questions!
        """
        if '```sql' in llm_output:
            # Example usage:
            extractor = CodeExtractor()
            extracted_code = extractor.extract_code('sql', llm_output)
            logging.info(f"Extracted SQL from output: {extracted_code}")

        return extracted_code

    def get_sql_primary(self, error: dict = None) -> str:
        """
       Generates a SQL query from the user prompt and relevant tables information.

       Args:
           error (Optional[dict]): Error message from the previous attempt, if any.

       Returns:
           str: Generated SQL query.
       """

        logging.info(f"[Node:SQL][get_sql_primary]\nInput: {self.user_prompt}")

        feedback = ""

        if error:
            feedback = f"""
            Your previous response generated an error that is listed bellow. Please fix this the error and provide a valid SQL.
            Previous response:\n
            {error['response']}
            
            Error:\n
            {error['error']}
            """
        # Set up a parser + inject instructions into the prompt template.
        parser = JsonOutputParser(pydantic_object=SQL)

        prompt = PromptTemplate(
            template=TEXT_TO_SQL_PROMPT,
            input_variables=["user_prompt"],
            partial_variables={
                "dialect": self.db.dialect,
                "table_info": self.relevant_tables,
                "top_k": 100,  # TODO this should be from config
                "schema_name": "sample_data",  # TODO this should be from config
                "feedback": feedback,
                "format_instructions": parser.get_format_instructions()
            },
        )

        response = {}

        table_chain = prompt | self.llm | parser
        try:
            response = table_chain.invoke({"user_prompt": self.user_prompt})
        except Exception as e:
            logging.error(f"[Node: SQL][get_sql_primary]\n Error parsing response: {e}")
            try:
                response['SQL_Code'] = self.parse_sql_from_string(str(e))
            except Exception as e:
                logging.error(f"[Node: SQL][get_sql_primary]\n Error extracting SQL: {e}")
                return False

        logging.info(f"[Node: SQL][get_sql_primary]Response:\n{response}")

        return response


    def get_sql_failover(self, last_error: dict = None) -> str:
        """
        This is a failover function to extract SQL from LLM response, in case more structured approach does not work. Converts a user prompt into an SQL query using specified tables.

        Returns:
            str: The constructed SQL query.
        """

        system = TEXT_TO_SQL_PROMPT
        prompt = ChatPromptTemplate.from_messages(
            [("system", system), ("human", "{input}")]
        ).partial(dialect=self.db.dialect)

        def parse_final_answer(output: str) -> str:
            extractor = CodeExtractor()
            extracted_code = extractor.extract_code('sql', output)
            return extracted_code

        try:
            query_chain = create_sql_query_chain(self.llm, self.db, prompt=prompt) | parse_final_answer
            query = query_chain.invoke({
                "question": self.user_prompt,
                "table_info": self.relevant_tables,
                'top_k': 100,
                "schema_name": "sample_data"
            })
        except:
            query_chain = create_sql_query_chain(self.llm, self.db, prompt=prompt)
            query = query_chain.invoke({
                "question": self.user_prompt,
                "table_info": self.relevant_tables,
                'top_k': 100,
                "schema_name": "sample_data"
            })
        finally:
            logging.info(f"[Node: SQL][SQL]: {query}")

        return query


    def convert_to_df(self, result):
        """
        Converts result of running SQL to dataframe.
        :param result:
        :return:
        """
        try:
            # check if we need to import Decimal lib
            if 'Decimal(' in result:
                from decimal import Decimal #TODO, this should not be necessary, but cannot figure out a better way

            if ' datetime.' in result:
                import datetime #TODO, this should not be necessary, but cannot figure out a better way

            result_df = pd.DataFrame(eval(result))
            return result_df
        except Exception as e:
            logging.error(f"Could not convert query result to dataframe: {e}")
            # return empty data frame
            return pd.DataFrame()

    def execute_sql(self, sql: str, convert_to_df=True) -> (bool, pd.DataFrame or str):
        """
        Executes an SQL query and optionally converts the result to a DataFrame.
        This method now returns a tuple indicating success and either the DataFrame or error message.

        Args:
            sql (str): The SQL query to execute.
            convert_to_df (bool): Whether to convert the result to a DataFrame.

        Returns:
            tuple: (success (bool), DataFrame or error message (str))
        """
        try:
            result = self.db.run(sql, include_columns=True)
            if convert_to_df:
                return True, self.convert_to_df(result)
            return True, result
        except Exception as e:
            logging.error(f"Error executing SQL: {e}")
            return False, str(e)

    def get_sql_from_llm(self, error: dict = {}, iters: int = 5):
        """
        Parses and processes the response from a Large Language Model (LLM).

        This function is designed to interpret the JSON response from an LLM, extracting relevant information and converting it into a structured format that can be used by other parts of the application. It handles specific response formats and converts them into a more usable or readable form.

        Args:
            error (dict): Error that has been passed from previous iteration.
            iters (dict): Number of iterations to run.

        Returns:
            dict: A dictionary containing the processed and simplified version of the LLM's response. The structure of this dictionary will depend on the specific requirements of the application.

        Raises:
            ValueError: If the response does not contain expected keys or is in an unexpected format.
            TypeError: If the input is not a dictionary as expected.

        """

        for attempt in range(iters):  # Loop up to x times
            logging.info(f"[Node: SQL][Attempt {attempt}]")

            # first, we try the usual way to generate the SQL
            try:
                # Generate an SQL query, passing the last error if one occurred
                llm_response = self.get_sql_primary(error)
                return llm_response
            except Exception as e:
                # Log and prepare the error for the next attempt
                logging.error(f"[Node: SQL][SQL Error]: {e}")
                error = {'error': e}  # Set the error for the next iteration

        for attempt in range(iters):  # Loop up to x times

            # first, we try the usual way to generate the SQL
            try:
                # Generate an SQL query, passing the last error if one occurred
                llm_response = self.get_sql_failover(error)
            except Exception as e:
                # Log and prepare the error for the next attempt
                logging.error(f"[Node: SQL] Cannot generate SQL from LLM: {e}")
                error = {'error': e}  # Set the error for the next iteration

            error = {'response': llm_response}

            try:
                # Attempt to parse the SQL query as JSON
                result = json.loads(llm_response)
                logging.info(f"[Node: SQL] Successfully parsed JSON:", result)

            except json.JSONDecodeError as e:
                # Log and prepare the error for the next attempt
                logging.error(f"[Node: SQL] Cannot load SQL: {e}")
                error = {'error': e}  # Set the error for the next iteration
            except Exception as general_error:
                # Handle any other types of exceptions that might occur
                logging.error(f"Unexpected error: {general_error}")
                error = {'error': general_error}  # Set the error for the next iteration

        # If the loop completes without a successful parse, handle the failure case
        logging.error(f"Failed to parse JSON after many attempts: {llm_response}")
        return None  # Or raise an Exception, depending on your error handling strategy

    def iterate_sql_get_and_exec(self, iters: int = 5):
        attempts = 0
        error = {}
        while attempts < iters:
            # Generate an SQL query from the user's prompt using the identified relevant tables
            llm_response = self.get_sql_from_llm(error)

            success, result = self.execute_sql(llm_response['SQL_Code'])

            if success:
                self.metadata['sql'] = llm_response['SQL_Code']
                self.metadata['text'] = llm_response['Explanation']
                logging.info(f"[Node: SQL][SQL Success][Iteration {attempts}]: {result}")
                return result
            else:
                # Log the error and attempt to fix the SQL
                logging.info(f"[Node: SQL][SQL Error][Iteration {attempts}]: {result}")
                error = {'response': llm_response['SQL_Code'], 'error': result}
                attempts += 1

    def run(self, user_prompt: str, **kwargs) -> BaseResponse:
        """Executes the full process from interpreting a user prompt to SQL query generation and execution.

        Args:
            user_prompt (str): The user's input prompt intended to generate a SQL query.

        Returns:
            Response: An object containing the query result set as a DataFrame in the content attribute
                      and additional metadata such as executed SQL and relevant tables.
        """
        self.user_prompt = user_prompt

        # Identify relevant tables based on the user's prompt
        self.get_relevant_tables()

        # Execute the generated SQL query and receive the result as a DataFrame
        result_df = self.iterate_sql_get_and_exec(5)

        # Check if the DataFrame is empty, return empty string instead
        if result_df.empty:
            response = BaseResponse(
                content=None,
                metadata=self.metadata
            )
        else:
            response = BaseResponse(
                content=result_df,
                metadata=self.metadata
            )

        # Save the response to memory
        memory = BaseMemory()
        memory.log_service_message(response, 'SQL')
        memory.save_to_file()

        return response

