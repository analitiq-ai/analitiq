import json
import logging
import pandas as pd
import os
import re
from typing import List
from analitiq.utils.general import split_list_of_ddl
from analitiq.base.BaseResponse import BaseResponse
from analitiq.utils.code_extractor import CodeExtractor
from analitiq.base.Database import DatabaseWrapper

from analitiq.services.sql.schema import Table, Column, Tables, SQL, TableCheck
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.exc import DatabaseError

from analitiq.services.sql.prompt import (
    RETURN_RELEVANT_TABLE_NAMES,
    TEXT_TO_SQL_PROMPT,
    FIX_SQL,
    FIX_RESPONSE
)

# Maximum iterations for all loops to LLM
max_iterations = 5
db_docs_name = "schema"  # this is the identifier of the name of the DB schema doc
context_max_tokens = 100000
chunk_overlap = 200

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
    execute_sql: Executes SQL queries and returns results as a DataFrame.
    get_sql_from_llm: Parses and handles responses from the LLM.
    run: Orchestrates the process from prompt interpretation to SQL query execution.
    """

    """Class to generate and execute SQL queries using prompts submitted to an LLM, with logging and retries."""

    def __init__(self, db: DatabaseWrapper, llm, vdb=None):
        self.user_prompt: str = None
        self.db = db
        self.llm = llm
        self.vdb = vdb

        self.relevant_tables = ""
        self.response = BaseResponse(self.__class__.__name__)
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.get_log_file_path())
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
        logger.propagate = False

        # clear the logfile content
        with open(self.get_log_file_path(), "w") as log_file:
            pass

        return logger

    def get_log_file_path(self):
        return f"{os.path.dirname(os.path.abspath(__file__))}/logs/latest_run.log"

    def _format_prompt(self, prompt, is_history):
        formatted_prompt = prompt.format(user_prompt=self.user_prompt)
        if is_history:
            return "\n\t".join(formatted_prompt.splitlines())
        return formatted_prompt

    def _log_prompt(self, prompt_as_txt, is_history):

        if is_history:
            self.logger.info(f"[[PROMPT_WITH_CHAT_HISTORY_START]]\n\n{prompt_as_txt}\n\n[[PROMPT_WITH_CHAT_HISTORY_END]]")
        else:
            self.logger.info(f"Human: {prompt_as_txt}")

    def get_ddl(self, docs) -> List[str]:
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
        ddl = self.db.get_schemas_and_tables(self.db.params['db_schemas'])

        result = split_list_of_ddl(ddl, 5000)

        if len(result) > 1:
            responses = []
            for i, chunk in enumerate(result):
                combined_text = ', '.join(chunk)
                response = self.llm.extract_info_from_db_ddl(self.user_prompt, chunk, docs)
                if 'NOT_FOUND' in response:
                    continue

                responses.append(response)

            response = self.llm.summ_info_from_db_ddl(self.user_prompt, '. '.join(responses))
            return response

        return ', '.join(ddl)

    def get_relevant_tables(self, docs: str = None) -> List[str]:
        """
        Determines tables from the docs relevant to the given user prompt using AI.

        Returns:
            List[Table]: A list of relevant Table objects.
        """
        ddl = self.get_ddl(docs)

        if docs:
            docs = f"Database Documentation:\n{docs}\n"
        else:
            docs = ''
        parser = PydanticOutputParser(pydantic_object=Tables)
        prompt = PromptTemplate(
            template=RETURN_RELEVANT_TABLE_NAMES,
            input_variables=["user_prompt"],
            partial_variables={
                "ddl": ddl
                , "db_docs": docs
                , "format_instructions": parser.get_format_instructions()
            }
        )

        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)


        self.logger.info(f"Assistant:\nList of tables believed to be relevant - {response.to_json()}")

        schema_dict = {}
        # Organize tables by schema
        for table in response.TableList:

            # first check if table is needed
            check_result = self.check_relevant_table(table.SchemaName, table.TableName)

            if check_result.Required is True:
                if table.SchemaName not in schema_dict:
                    schema_dict[table.SchemaName] = []
                schema_dict[table.SchemaName].append(table)

        if not schema_dict:
            return

        # Format the output string
        output_lines = []
        for schema, tables in schema_dict.items():
            output_lines.append(f"- Schema: {schema}")
            for table in tables:
                output_lines.append(f"  - Table: {schema}.{table.TableName}")
                column_details = ', '.join(f"{column.ColumnName} ({column.DataType})" for column in table.Columns)
                output_lines.append(f"    - Columns: {column_details}")

        self.relevant_tables = "\n".join(output_lines)
        self.logger.info(f"Assistant:\nList of relevant tables and columns.\n{self.relevant_tables}")
        self.response.add_text_to_metadata(f"Relevant tables: {self.relevant_tables}")

        self.response.set_metadata({"relevant_tables": self.relevant_tables})

        return True

    def check_relevant_table(self, schema_name, table_name):
        limit = 5

        sql = f"SELECT * FROM {schema_name}.{table_name} LIMIT {limit}"
        result = self.db.db.run(sql, include_columns=True)

        parser = PydanticOutputParser(pydantic_object=TableCheck)
        prompt = PromptTemplate(
            template="You are a data analys. You received user query: {user_prompt}.\nDoes the table {schema_name}.{table_name} contain the data that might be relevant to answer the users query? Bellow is some data from the table: \n {data_sample}. \n {format_instructions}.",
            input_variables=["user_prompt"],
            partial_variables={"schema_name": schema_name,
                               "table_name": table_name,
                               "data_sample": result,
                               "format_instructions": parser.get_format_instructions()
                               }
        )

        #prompt_as_string = prompt.format(user_prompt=self.user_prompt)

        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)

        return response

    def prep_llm_invoke(self, prompt, parser, is_history: bool = False):

        prompt_as_txt = self._format_prompt(prompt, is_history)
        self._log_prompt(prompt_as_txt, is_history)

        """Invoke the LLM with a given prompt and parser."""
        try:
            response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
            self.logger.info(f"Assistant:\n{response}")
            return response
        except Exception as e:
            self.logger.error(f"LLM response error: {str(e)}")
            return self._handle_llm_failure(e)

    def _handle_llm_failure(self, exception):
        result = self._extract_error_details(exception)
        if result:
            return result
        return self._attempt_llm_recovery(exception, result)

    def _extract_error_details(self, exception):
        extractor = CodeExtractor()
        try:
            success, result = extractor.CodeAndDictionaryExtractor(str(exception))
            if success and result:
                return result
            return None
        except Exception as e:
            self.logger.error(f"LLM code extractor error: {str(e)}")
            return None

    def _attempt_llm_recovery(self, exception, result):
        a = AnalitiqLLM()
        response = a.llm_fix_json(str(exception), result)

        try:
            response_dict = json.loads(response)
            return response_dict
        except Exception as e:
            self.logger.error(f"Could not extract dictionary from response {response}.\n{str(e)}")
            raise RuntimeError("Failed to recover from LLM error.") from e


    def get_sql_from_llm(self, iteration_num: int) -> str:
        """Generate SQL from LLM based on the user prompt and handle retries with error logging."""
        parser = JsonOutputParser(pydantic_object=SQL)

        if iteration_num > 0:
            chat_hist = remove_bracket_contents(self._get_chat_hist(1))
            prompt = PromptTemplate(
                template=FIX_RESPONSE,
                input_variables=["user_prompt"],
                partial_variables={
                    "chat_hist": chat_hist,
                    "format_instructions": parser.get_format_instructions()
                }
            )

            is_hist = True
        else:
            prompt = PromptTemplate(
                template=TEXT_TO_SQL_PROMPT,
                input_variables=["user_prompt"],
                partial_variables={
                    "dialect": self.db.params['type'],
                    "table_info": self.relevant_tables,
                    "top_k": 100,
                    "format_instructions": parser.get_format_instructions()
                }
            )
            is_hist = False

        try:
            response = self.prep_llm_invoke(prompt, parser, is_hist)
            if not response.get('SQL_Code'):
                raise ValueError("Human: No SQL Code returned")
            return response
        except Exception as e:
            self.logger.error(f"Human: Error getting LLM response. {str(e)}")
            if iteration_num < 5:
                return self.get_sql_from_llm(iteration_num + 1)
            else:
                raise RuntimeError("Human: Maximum retry attempts reached for SQL generation.")

    def _get_chat_hist(self, num_sections: int = 5):
        with open(self.get_log_file_path(), 'r') as file:
            content = file.read()

        start_tag = '[[PROMPT_WITH_CHAT_HISTORY_START]]'
        end_tag = '[[PROMPT_WITH_CHAT_HISTORY_END]]'

        # Define the pattern to find text between tags
        pattern = re.compile(re.escape(start_tag) + '.*?' + re.escape(end_tag), re.DOTALL)

        # Remove the text between tags
        modified_content = re.sub(pattern, '', content)

        return modified_content

    def get_db_docs(self):

        # If connection to VectorDB did not initialise, return None
        if not self.vdb:
            return None

        response = self.vdb.get_many_like("document_name", db_docs_name)

        if not response:
            self.logger.info(f"[VectorDB] No objects returned that match search parameter {db_docs_name}.")
            return None

        # Initialize an empty string to hold the formatted content
        document_dict = {}
        formatted_documents_string = ""

        for obj in response.objects:
            document_name = obj.properties['document_name']
            document_content = obj.properties['content']
            # Check if the document_name already exists in the dictionary
            if document_name in document_dict:
                # Append the content to the existing list
                document_dict[document_name].append(document_content)
            else:
                # Create a new list with the content
                document_dict[document_name] = [document_content]

            # Use the dictionary to print the formatted document contents

        for document_name, content_list in document_dict.items():
            formatted_content = "\n".join(content_list)
            formatted_documents_string += f"Document name: {document_name}\nDocument content:\n{formatted_content}\n\n"

        response = self.llm.extract_info_from_db_docs(self.user_prompt, formatted_documents_string)
        self.logger.info(f"LLM: {response}")
        self.response.add_text_to_metadata(response)

        if response == 'None':
            return None

        return response

    def execute_sql(self, sql: str, convert_to_df=True):
        """Execute SQL and log the process, handling errors and retries."""
        self.logger.info({sql})
        try:
            if convert_to_df:
                result = pd.read_sql(sql, self.db.engine)
                if result.empty:
                    self.logger.info(f"Human: SQL executed successfully, but result is empty.")
                else:
                    self.logger.info(f"Human: SQL executed successfully.\nConverted to DataFrame. {result}")
            else:
                result = self.db.run(sql, include_columns=True)
                self.logger.info("Human: SQL executed successfully.")

            self.response.add_text_to_metadata(f"```\n{sql}\n```")
            return True, result
        except DatabaseError as e:
            self.logger.error(f"Human: Error executing SQL.\n{str(e)}")
            return False, str(e)

    def _set_result(self, result: pd.DataFrame, sql: str = None, explanation: str = None):
        self.response.set_content(result, 'dataframe')
        if result.empty:
            self.response.add_text_to_metadata("\nThe query produced no result. Please review your query and SQL generated based on it and fine-tune your instructions.")
        else:
            self.response.add_text_to_metadata(f"\n{explanation}")
            if sql:
                self.response.add_text_to_metadata(f"\n```\n{sql}\n```")

    def run(self, user_prompt: str = None):
        """Executes the full process from interpreting a user prompt to SQL query generation and execution.

       Args:
           user_prompt (str): The user's input prompt intended to generate a SQL query.

       Returns:
           Response: An object containing the query result set as a DataFrame in the content attribute
                     and additional metadata such as executed SQL and relevant tables.
       """
        self.user_prompt = user_prompt
        self.logger.info(f"Human: {user_prompt}")
        docs = self.get_db_docs()

        if docs:
            # we check if DB doc already has SQL as some LLMs tend to do that.
            if "```" in docs:
                extractor = CodeExtractor()
                sql = extractor.extract_code(docs, 'sql')
                if sql:
                    success, result = self.execute_sql(sql)
                    if success:
                        self._set_result(result, None, docs)  # Since SQL already is in the document reponse, we do not need to add it to the response.
                        return self.response

        # Identify relevant tables based on the user's prompt
        self.get_relevant_tables(docs)

        """Process the prompt to generate and execute SQL, handling all logging and retries."""
        try:
            response = self.get_sql_from_llm(0)
            sql = response['SQL_Code']
        except RuntimeError as e:
            return str(e)

        for _ in range(max_iterations):
            success, result = self.execute_sql(sql)
            if success:
                self._set_result(result, sql, response['Explanation'])
                break  # terminate the loop on successful execution of SQL
            else:
                try:
                    # here we artificially set iteration to be at 1 to let the system know that this is post error run and trigger chat history.
                    response = self.get_sql_from_llm(1)
                    sql = response['SQL_Code']
                except RuntimeError as e:
                    self.response.add_text_to_metadata(str(e))

        return self.response

