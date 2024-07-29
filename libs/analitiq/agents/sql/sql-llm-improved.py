import logging
import pandas as pd
import os
import re
from typing import List, Tuple, Optional
from analitiq.utils.general import split_list_of_ddl
from analitiq.base.BaseResponse import BaseResponse
from analitiq.utils.code_extractor import CodeExtractor
from analitiq.base.Database import DatabaseWrapper
from analitiq.agents.sql.schema import Table, Column, Tables, SQL, TableCheck
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.exc import DatabaseError

from analitiq.agents.sql.prompt import (
    RETURN_RELEVANT_TABLE_NAMES,
    TEXT_TO_SQL_PROMPT,
    FIX_SQL,
    FIX_RESPONSE
)

MAX_ITERATIONS = 5
DB_DOCS_NAME = "schema.sql"
CONTEXT_MAX_TOKENS = 100000
CHUNK_OVERLAP = 200

"""
TODO How do you reconcile:
VDB docs with info about tables in schemas.
schemas which Analitiq has access to.
Schemas that are defined in configuration.

Perhaps what we should do is to limit the schemas to only the ones that are defined in config, and if the documents have additional info, we disregard it?
"""


# Logging setup
def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.propagate = False

    # Clear the logfile content
    with open(log_file, "w") as log_file:
        pass

    return logger

class Sql:
    """Handles SQL query generation and execution against the database using LLM integration."""

    def __init__(self, db: DatabaseWrapper, llm, vdb=None):
        self.chat_logger = setup_logger(__name__, self._get_chat_log_file_path())
        self.exe_logger = setup_logger('execution_logger', self._get_execution_log_file_path())
        print("SQL Agent Started.")
        self.user_prompt: Optional[str] = None
        self.db = db
        self.llm = llm
        self.vdb = vdb # TODO this should be double checked as it is not same as search example.
        self.relevant_tables = ""
        self.response = BaseResponse(self.__class__.__name__)


    @staticmethod
    def _get_chat_log_file_path() -> str:
        return f"{os.path.dirname(os.path.abspath(__file__))}/logs/latest_chat.log"

    @staticmethod
    def _get_execution_log_file_path() -> str:
        return f"{os.path.dirname(os.path.abspath(__file__))}/logs/latest_run.log"

    def _log_prompt(self, prompt_as_txt: str, is_history: bool):
        if is_history:
            self.chat_logger.info(f"[[PROMPT_WITH_CHAT_HISTORY_START]]\n\n{prompt_as_txt}\n\n[[PROMPT_WITH_CHAT_HISTORY_END]]")
        else:
            self.chat_logger.info(f"Human: {prompt_as_txt}")

    def get_ddl(self) -> List[str]:
        schema_name = self.db.params['db_schemas'][0]

        ddl = self.db.get_schemas_and_tables(schema_name) # TODO for now it takes only 1 schema
        self.exe_logger.info(f"DDL for {schema_name}: {ddl}")
        result = split_list_of_ddl(ddl, 5000)
        if len(result) > 1:
            responses = []
            for chunk in result:
                combined_text = ', '.join(chunk)
                response = self.llm.extract_info_from_db_ddl(self.user_prompt, chunk)
                if 'NOT_FOUND' not in response:
                    responses.append(response)
            return self.llm.summ_info_from_db_ddl(self.user_prompt, '. '.join(responses))
        return ', '.join(ddl)

    def get_relevant_tables(self, docs: str = None) -> List[Table]:
        ddl = self.get_ddl()
        docs = f"Database Documentation:\n{docs}\n" if docs else ''
        parser = PydanticOutputParser(pydantic_object=Tables)
        prompt = PromptTemplate(
            template=RETURN_RELEVANT_TABLE_NAMES,
            input_variables=["user_prompt"],
            partial_variables={
                "ddl": ddl,
                "db_docs": docs,
                "format_instructions": parser.get_format_instructions()
            }
        )
        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
        self.exe_logger.info(f"Relevant Tables: {response.to_json()}")
        self.chat_logger.info(f"Assistant: List of tables believed to be relevant - {response.to_json()}")

        schema_dict = {}
        for table in response.TableList:
            check_result = self.check_relevant_table(table.SchemaName, table.TableName)
            if check_result.Required:
                if table.SchemaName not in schema_dict:
                    schema_dict[table.SchemaName] = []
                schema_dict[table.SchemaName].append(table)

        self.relevant_tables = self._format_relevant_tables(schema_dict)
        self.chat_logger.info(f"Assistant: List of relevant tables and columns.\n{self.relevant_tables}")
        self.response.add_text_to_metadata(f"Relevant tables: {self.relevant_tables}")
        self.response.set_metadata({"relevant_tables": self.relevant_tables})

    @staticmethod
    def _format_relevant_tables(schema_dict: dict) -> str:
        output_lines = []
        for schema, tables in schema_dict.items():
            output_lines.append(f"- Schema: {schema}")
            for table in tables:
                output_lines.append(f"  - Table: {schema}.{table.TableName}")
                column_details = ', '.join(f"{column.ColumnName} ({column.DataType})" for column in table.Columns)
                output_lines.append(f"    - Columns: {column_details}")
        return "\n".join(output_lines)

    def check_relevant_table(self, schema_name: str, table_name: str) -> TableCheck:
        sql = f"SELECT * FROM {schema_name}.{table_name} LIMIT 5"
        result = self.db.run(sql, include_columns=True)
        parser = PydanticOutputParser(pydantic_object=TableCheck)
        prompt = PromptTemplate(
            template="You are a data analyst. You received user query: {user_prompt}.\n"
                     "Does the table {schema_name}.{table_name} contain the data that might be relevant to answer the user's query? "
                     "Below is some data from the table: \n {data_sample}. \n {format_instructions}.",
            input_variables=["user_prompt"],
            partial_variables={
                "schema_name": schema_name,
                "table_name": table_name,
                "data_sample": result,
                "format_instructions": parser.get_format_instructions()
            }
        )
        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
        return response

    def get_db_docs(self) -> Optional[str]:
        if not self.vdb:
            return None

        response = self.vdb.search_vector_database_with_filter('revenue', "source", DB_DOCS_NAME)

        if not response:
            self.chat_logger.info(f"[VectorDB] No objects returned that match search parameter {DB_DOCS_NAME}.")
            return None
        else:
            self.exe_logger.info(f"Documents from VDB: {response}")

        self.exe_logger.info(f"Documents obtained: {response}")

        response = self.llm.extract_info_from_db_docs(self.user_prompt, response)
        self.chat_logger.info(f"LLM: {response}")
        self.response.add_text_to_metadata(response)

        self.exe_logger.info(f"LLM Info from Documents: {response}")

        if 'ANALITQ___NO_ANSWER' in response:
            return None

        return response

    def execute_sql(self, sql: str) -> Tuple[bool, Optional[pd.DataFrame]]:
        self.chat_logger.info(f"{sql}")
        try:
            result = pd.read_sql(sql, self.db.engine)
            if result.empty:
                self.chat_logger.info("SQL executed successfully, but result is empty.")
            else:
                self.chat_logger.info(f"SQL executed successfully. Converted to DataFrame. {result}")
            self.response.add_text_to_metadata(f"```\n{sql}\n```")
            return True, result
        except DatabaseError as e:
            self.chat_logger.error(f"Error executing SQL. {str(e)}")
            return False, str(e)

    def get_sql_from_llm(self, iteration_num: int) -> str:
        parser = JsonOutputParser(pydantic_object=SQL)
        if iteration_num > 0:
            chat_hist = self._remove_bracket_contents(self._get_chat_hist(1))
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
            response = self._prep_llm_invoke(prompt, parser, is_hist)
            if not response.get('SQL_Code'):
                raise ValueError("No SQL Code returned")
            return response
        except Exception as e:
            self.chat_logger.error(f"Error getting LLM response. {str(e)}")
            if iteration_num < MAX_ITERATIONS:
                return self.get_sql_from_llm(iteration_num + 1)
            else:
                raise RuntimeError("Maximum retry attempts reached for SQL generation.")

    def _prep_llm_invoke(self, prompt, parser, is_history: bool = False):
        prompt_as_txt = prompt.format(user_prompt=self.user_prompt)
        self._log_prompt(prompt_as_txt, is_history)
        try:
            response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
            self.chat_logger.info(f"Assistant: {response}")
            return response
        except Exception as e:
            self.chat_logger.error(f"LLM response error: {str(e)}")
            return self._handle_llm_failure(e)

    def _handle_llm_failure(self, exception):
        extractor = CodeExtractor()
        try:
            success, result = extractor.CodeAndDictionaryExtractor(str(exception))
            if success and result:
                return result
            return None
        except Exception as e:
            self.chat_logger.error(f"LLM code extractor error: {str(e)}")
            return None

    def _get_chat_hist(self, num_sections: int = 5) -> str:
        with open(self._get_chat_log_file_path(), 'r') as file:
            content = file.read()

        start_tag = '[[PROMPT_WITH_CHAT_HISTORY_START]]'
        end_tag = '[[PROMPT_WITH_CHAT_HISTORY_END]]'
        pattern = re.compile(re.escape(start_tag) + '.*?' + re.escape(end_tag), re.DOTALL)
        modified_content = re.sub(pattern, '', content)

        return modified_content

    def _remove_bracket_contents(self, text: str) -> str:
        return re.sub(r'\[[^]]*\]', '', text)

    def run(self, user_prompt: str) -> BaseResponse:
        self.user_prompt = user_prompt
        self.chat_logger.info(f"Human: {user_prompt}")
        self.exe_logger.info(f"[Sql Agent] Query: {user_prompt}")
        docs = self.get_db_docs()

        if docs and "```" in docs:
            extractor = CodeExtractor()
            sql = extractor.extract_code(docs, 'sql')
            if sql:
                success, result = self.execute_sql(sql)
                if success:
                    self._set_result(result, None, docs)
                    return self.response

        self.get_relevant_tables(docs)

        try:
            response = self.get_sql_from_llm(0)
            sql = response['SQL_Code']
        except RuntimeError as e:
            self.response.add_text_to_metadata(str(e))
            return self.response

        self.exe_logger.info(f"SQL: {sql}")

        for _ in range(MAX_ITERATIONS):
            success, result = self.execute_sql(sql)
            if success:
                self._set_result(result, sql, response['Explanation'])
                break
            else:
                try:
                    response = self.get_sql_from_llm(1)
                    sql = response['SQL_Code']
                except RuntimeError as e:
                    self.response.add_text_to_metadata(str(e))

        return self.response

    def _set_result(self, result: pd.DataFrame, sql: Optional[str] = None, explanation: Optional[str] = None):
        self.response.set_content(result, 'dataframe')
        if result.empty:
            self.response.add_text_to_metadata("The query produced no result. Please review your query and SQL generated based on it and fine-tune your instructions.")
        else:
            self.response.add_text_to_metadata(f"\n{explanation}")
            if sql:
                self.response.add_text_to_metadata(f"\n```\n{sql}\n```")
