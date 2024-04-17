import logging

import langchain
langchain.debug = True

from analitiq.base.BaseService import BaseResponse
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.BaseMemory import BaseMemory
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import List, Optional
import pandas as pd

from analitiq.services.sql.prompt import (
    RETURN_RELEVANT_TABLE_NAMES,
    TEXT_TO_SQL_PROMPT
)


class Table(BaseModel):
    TableName: str = Field(description="The name of the table")
    Columns: List[str] = Field(description="A list of relevant columns in the table")


class Tables(BaseModel):
    TableList: List[Table] = Field(description="A list of relevant tables from the list of all tables in a database")


class SQL(BaseModel):
    Code: str = Field(description="Only SQL code goes here")
    Explanation: Optional[str] = Field(description="Explanation about the SQL, if necessary.")


class Sql():
    """Handles SQL query generation and execution against database. Useful when user would like to query data.

    This class integrates natural language processing to identify relevant database tables
    and generate SQL queries that are then executed against a database. The results are returned
    as data frames for further analysis or display.
    """

    def __init__(self) -> None:
        self.db = GlobalConfig().get_database()
        self.llm = GlobalConfig().get_llm()

    def get_tables(self) -> List[str]:
        """Retrieves a list of usable table names from the database.

        Returns:
            List[str]: A list of table names.
        """
        return self.db.get_usable_table_names()

    def get_relevant_tables(self, user_prompt: str) -> List[str]:
        """Determines the relevant tables based on the user's prompt using AI.

        Args:
            user_prompt (str): The user's prompt.

        Returns:
            List[str]: A list of relevant table names.
        """
        table_names_in_db = ",".join(self.get_tables())

        parser = PydanticOutputParser(pydantic_object=Tables)
        prompt = PromptTemplate(
            template=RETURN_RELEVANT_TABLE_NAMES,
            input_variables=["user_prompt"],
            partial_variables={"table_names_in_db": table_names_in_db, "format_instructions": parser.get_format_instructions()},
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt})
        logging.info(f"Get relevant tables.\nInput: {user_prompt}.\nResponse: {response}")

        return response.TableList

    def get_sql2(self, user_prompt: str, relevant_tables: List[Tables]) -> str:

        logging.info(f"[Node: SQL->get_sql2]\nInput: {user_prompt}")

        parser = PydanticOutputParser(pydantic_object=SQL)
        prompt = PromptTemplate(
            template=TEXT_TO_SQL_PROMPT,
            input_variables=["user_prompt"],
            partial_variables={
                "dialect": self.db.dialect,
                "table_info": str(relevant_tables),
                "top_k": 100,  # TODO this should be from config
                "schema_name": "sample_data",  # TODO this should be from config
                "format_instructions": parser.get_format_instructions()},
        )

        logging.info(f"[Node: SQL->get_sql2]\nInput: {user_prompt}")

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt})
        logging.info(f"[Node: SQL->get_sql2]\nResponse: {response}")
        exit()

        return response.Code


    def get_sql(self, user_prompt: str, tables_to_use: List[str]) -> str:
        """Converts a user prompt into an SQL query using specified tables.

        Args:
            user_prompt (str): The user prompt.
            tables_to_use (List[str]): Tables to use for constructing the query.

        Returns:
            str: The constructed SQL query.
        """
        try:
            tables_to_use_str = ",".join(tables_to_use)
        except Exception as e:
            print(f"Error processing tables: {e}")
            tables_to_use_str = ""

        system = TEXT_TO_SQL_PROMPT
        prompt = ChatPromptTemplate.from_messages(
            [("system", system), ("human", "{input}")]
        ).partial(dialect=self.db.dialect)

        def parse_final_answer(output: str) -> str:
            cleaned_code = output.split("Final answer: ")[1].replace('sql', '').replace('`', '').strip()
            return cleaned_code

        try:
            query_chain = create_sql_query_chain(self.llm, self.db, prompt=prompt) | parse_final_answer
            query = query_chain.invoke({
                "question": user_prompt,
                "table_info": tables_to_use_str,
                'top_k': 100,
                "schema_name": "sample_data"
            })
        except:
            query_chain = create_sql_query_chain(self.llm, self.db, prompt=prompt)
            query = query_chain.invoke({
                "question": user_prompt,
                "table_info": tables_to_use_str,
                'top_k': 100,
                "schema_name": "sample_data"
            })
        finally:
            logging.info(f"sql compiled: {query}")

        return query

    def run_sql(self, sql: str, convert_to_df=True) -> pd.DataFrame:
        """Executes an SQL query against the database.

        Args:
            sql (str): The SQL query to execute.
            convert_to_df (bool): Whether to convert the result to a DataFrame.

        Returns:
            pd.DataFrame: The query result as a DataFrame.
        """
        try:
            result = self.db.run(sql, include_columns=True)
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return pd.DataFrame()

        if convert_to_df:
            try:
                # check if we need to import Decimal lib
                if 'Decimal(' in result:
                    from decimal import Decimal #TODO, this should not be necessary, but cannot figure out a better way

                if ' datetime.' in result:
                    import datetime #TODO, this should not be necessary, but cannot figure out a better way

                result_df = pd.DataFrame(eval(result))
                return result_df
            except Exception as e:
                print(f"Could not convert query result to dataframe: {e}")
                # return empty data frame
                return pd.DataFrame()
        else:
            return result

    def run(self, user_prompt: str, **kwargs) -> BaseResponse:
        """Executes the full process from interpreting a user prompt to SQL query generation and execution.

        Args:
            user_prompt (str): The user's input prompt intended to generate a SQL query.

        Returns:
            Response: An object containing the query result set as a DataFrame in the content attribute
                      and additional metadata such as executed SQL and relevant tables.
        """
        # Identify relevant tables based on the user's prompt
        relevant_tables = self.get_relevant_tables(user_prompt)

        # Generate an SQL query from the user's prompt using the identified relevant tables
        sql_query = self.get_sql2(user_prompt, relevant_tables)

        logging.info(sql_query) ## TODO if the query returns an error, we need to re-try

        # Execute the generated SQL query and receive the result as a DataFrame
        result_df = self.run_sql(sql_query)

        # Check if the DataFrame is empty, return empty string instead
        if result_df.empty:
            result_df_json_str = ''

        # Convert the DataFrame to a JSON string with "split" orientation for better portability
        result_df_json_str = result_df.to_json(orient="split")

        # Package the result and metadata into a Response object
        response = BaseResponse(
            content=result_df_json_str,
            metadata={
                "relevant_tables": relevant_tables,
                "sql": sql_query,
                "format": 'dataframe',
                "unpack_format": 'split' # this is helpful to let other services understand how to format this Data frame.
            }
        )

        # Save the response to memory
        memory = BaseMemory()
        memory.log_service_message(response, 'SQL')
        memory.save_to_file()

        return response

