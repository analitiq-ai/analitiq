import pandas as pd
from typing import Tuple, Optional
from analitiq.logger.logger import logger, chat_logger
from analitiq.base.BaseResponse import BaseResponse
from analitiq.utils.code_extractor import CodeExtractor
from analitiq.agents.sql.schema import SQL
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.exc import DatabaseError
from analitiq.agents.sql.prompt import RETURN_RELEVANT_TABLE_NAMES, TEXT_TO_SQL_PROMPT
from langchain_core.exceptions import OutputParserException


class Sql:
    """Handles SQL query generation and execution against the database using LLM integration.

    This class provides methods to load DDL into a vector database, get relevant tables,
    check relevant tables, get database documentation schema, execute SQL queries, search DDL vectors,
    get SQL from LLM, glue document chunks, and run the SQL agent.
    """

    def __init__(self, db, llm, vdb=None):
        """Initialize the SQL Agent.

        SQL Agent writes SQL and executes the SQL against the database.
        After that SQL Agent returns the result.

        Args:
        ----
            db (RelationalDatabaseFactory): An instance of RelationalDatabaseFactory class representing the database connection.
            llm: A parameter representing llm (unknown data type).
            vdb (optional): An optional parameter representing vdb (unknown data type).

        """
        logger.info("SQL Agent Started.")
        self.user_prompt: Optional[str] = None
        self.db = db  # Database connection
        self.llm = llm  # Language model to generate SQL queries
        self.vdb = vdb  # Optional vector database for additional data context
        self.relevant_tables = ""  # Placeholder for relevant table names
        self.response = BaseResponse(self.__class__.__name__)  # Initialize response object

    def execute_sql(self, sql: str) -> Tuple[bool, Optional[pd.DataFrame]]:
        """Executes the given SQL query and returns the result as a DataFrame.

        Args:
        ----
            sql (str): The SQL query to be executed.

        Returns:
        -------
            Tuple[bool, Optional[pd.DataFrame]]: A tuple containing a boolean indicating success, and the result as a DataFrame or an error message.

        """
        chat_logger.info(f"{sql}")  # Log the SQL query being executed
        try:
            # Execute the SQL query and store the result in a DataFrame
            result = pd.read_sql(sql, self.db.engine)
            if result.empty:
                chat_logger.info("SQL executed successfully, but result is empty.")
            else:
                chat_logger.info(f"SQL executed successfully. Converted to DataFrame. {result}")

            return True, result
        except DatabaseError as e:
            # Handle SQL execution errors
            chat_logger.error(f"Error executing SQL. {e!s}")
            return False, str(e)

    def get_sql_from_llm(self, docs_ddl: Optional[str] = None, docs_schema: Optional[str] = None) -> str:
        """Generates SQL from the LLM (Language Model) based on provided DDL and schema documentation.

        Args:
        ----
            docs_ddl (str, optional): DDL documentation. Defaults to None.
            docs_schema (str, optional): Schema documentation. Defaults to None.

        Returns:
        -------
            str: Generated SQL code.

        Raises:
        ------
            ValueError: If no SQL code is returned.

        """
        # Format DDL documentation if provided
        if docs_ddl:
            docs_ddl = """I will provide a list of tables and columns for you to use to create an SQL query between the tags [DDL_START] and [DDL_END].
            Use only these tables and columns.
            Make sure you qualify schema for each table when creating the SQL.
            Please use only the specified table names, schemas, and column names in any queries or operations. 
            Any deviation from the provided schema will be considered incorrect. 
            Strictly adhere to the provided definitions.
            [DDL_START]
            {docs_ddl_placeholder}
            [DDL_END]
            """.format(docs_ddl_placeholder="\n".join(docs_ddl))

        # Format schema documentation if provided
        if docs_schema:
            docs_schema = """Here is some additional documentation that you may find useful to make your SQL more accurate:
            {docs_schema_placeholder}
            """.format(docs_schema_placeholder="\n".join(docs_schema))

        # Set up the parser and prompt for generating SQL
        parser = JsonOutputParser(pydantic_object=SQL)

        prompt = PromptTemplate(
            template=TEXT_TO_SQL_PROMPT,
            input_variables=["user_prompt"],
            partial_variables={
                "dialect": self.db.params["type"],
                "docs_ddl": docs_ddl,
                "docs_schema": docs_schema,
                "top_k": 100,
                "format_instructions": parser.get_format_instructions(),
            },
        )

        chat_logger.info(f"Human: {prompt.format(user_prompt=self.user_prompt)}")

        try:
            # Invoke the LLM to generate SQL
            response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
        except Exception as e:
            # Handle LLM invocation errors
            chat_logger.error(f"Error invoking LLM: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}")

        chat_logger.info(f"Assistant: {response}")

        if not response.get("SQL_Code"):
            # Raise an error if no SQL code is returned
            msg = "No SQL Code returned"
            raise ValueError(msg)

        return response

    def resubmit_for_correction(self, docs_ddl: str, sql: str, error_message: str, max_retries: int = 3) -> str:
        """Resubmits the prompt, DDL, generated SQL, and error to the LLM for correction.

        Args:
        ----
            docs_ddl (str): The DDL documentation used to generate the SQL.
            sql (str): The SQL query that caused the error.
            error_message (str): The error message received when executing the SQL.
            max_retries (int, optional): Maximum number of retries for correction. Defaults to 3.

        Returns:
        -------
            str: Corrected SQL code.

        """
        response: dict = None
        retries = 0

        # Create the correction prompt with the error message and DDL
        correction_prompt = f"""
        The following SQL query resulted in an error when executed:
        [SQL]
        {sql}
        [ERROR]
        {error_message}
        
        Based on the DDL documentation provided between the tags [DDL_START] and [DDL_END], please correct the SQL query.
        [DDL_START]
        {docs_ddl}
        [DDL_END]
        """

        parser = JsonOutputParser(pydantic_object=SQL)

        prompt = PromptTemplate(
            template=correction_prompt,
            input_variables=[],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
            },
        )

        chat_logger.info(f"Human: {correction_prompt}")

        try:
            # Retry the correction process up to max_retries times
            while retries < max_retries:
                response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
                if response.get("SQL_Code"):
                    break
                retries += 1
                chat_logger.info(f"Retrying correction: attempt {retries}")
            chat_logger.info(f"Assistant: {response}")
        except OutputParserException as e:
            # Handle output parsing errors and extract SQL code if available
            extractor = CodeExtractor()
            extracted_code = extractor.extract_code(str(e), 'sql')
            response = {'SQL_Code': extracted_code}

        if not response.get("SQL_Code"):
            # Raise an error if no corrected SQL code is returned
            msg = "No corrected SQL code returned"
            raise ValueError(msg)

        return response["SQL_Code"]

    @staticmethod
    def parse_sql_from_error(error_message: str) -> Optional[str]:
        """Attempts to parse the corrected SQL from the error message if available.

        Args:
        ----
            error_message (str): The error message containing the suggested SQL correction.

        Returns:
        -------
            Optional[str]: The parsed corrected SQL code if available, otherwise None.

        """
        import re

        # Use regex to extract SQL code from the error message
        match = re.search(r"```sql\n(.*?)\n```", error_message, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def glue_document_chunks(documents):
        """Glues document chunks into a single coherent document.

        Args:
        ----
            documents: The documents to be glued.

        Returns:
        -------
            List[str]: A list of glued documents.

        """
        glued_documents = []
        for document in documents:
            # Get document chunks and join them with new lines
            chunks = document.get("document_chunks", [])
            glued_text = "\n\n".join(chunks)  # Ensure each chunk starts on a new line
            glued_documents.append(glued_text)
        return glued_documents

    @staticmethod
    def format_ddl_chunks(input_data: list) -> str:
        # Format DDL chunks for easy interpretation by LLM
        output = []
        schema_name = input_data[0]['document_name'].split('.')[-2]
        output.append(f"Database Schema: {schema_name}\n")
        for item in input_data:
            table_name = item['document_name'].split('.')[-1]
            columns = item['document_chunks'][0]
            output.append(f"Table name: {table_name}\nColumn names: {columns})\n")
        return ''.join(output)

    def _set_result(
            self,
            result: pd.DataFrame,
            sql: Optional[str] = None,
            explanation: Optional[str] = None,
    ):
        """Sets the result of the SQL execution into the response object.

        Args:
        ----
            result (pd.DataFrame): The result of the SQL execution.
            sql (str, optional): The SQL query executed. Defaults to None.
            explanation (str, optional): Explanation of the result. Defaults to None.

        """
        # Set the content of the response as a DataFrame
        self.response.set_content(result, "dataframe")
        if result.empty:
            # Add metadata if the query produced no results
            self.response.add_text_to_metadata(
                "The query produced no result. Please review your query and SQL generated based on it and fine-tune your instructions."
            )
        else:
            # Add explanation and SQL query to metadata
            self.response.add_text_to_metadata(f"\n{explanation}")
            if sql:
                self.response.add_text_to_metadata(f"\n```\n{sql}\n```")

    def __get_ddl_from_vdb(self, user_prompt):
        # Set up filter to search for relevant DDL documents in vector database
        filter_list = [
            {"property": "document_tags", "operator": "contains_any", "value": ["ddl"]}
        ]

        # Add schema-specific filters
        for schema in self.db.params["db_schemas"]:
            filter_list.append({"property": "document_name", "operator": "like", "value": f"*{schema}*"} )

        filter_expression = {
            "and": filter_list
        }

        # Search the vector database using the filter expression
        return self.vdb.search_filter(user_prompt, filter_expression, ['document_name'])

    def run(self, user_prompt: str) -> BaseResponse:
        """Main method to run the SQL agent based on the user's prompt.

        Args:
        ----
            user_prompt (str): The user's query.

        Returns:
        -------
            BaseResponse: The response from the SQL agent.

        """
        self.user_prompt = user_prompt

        chat_logger.info(f"Human: {user_prompt}")
        logger.info(f"[Sql Agent] Query: {user_prompt}")

        # Get DDL documents from vector database
        docs_ddl = self.__get_ddl_from_vdb(user_prompt)

        if not docs_ddl or docs_ddl == "ANALYTQ___NO_ANSWER":
            logger.info("No relevant DDL documents in VDB located.")
        if docs_ddl:
            logger.info(f"DDL documents found: {len(docs_ddl)}")

            # Format the DDL chunks for LLM input
            docs_ddl_formatted = self.format_ddl_chunks(docs_ddl)

        docs_schema = None
        docs_schema_formatted: str = None

        if not docs_ddl and not docs_schema:
            # If no supporting documents are found, return an appropriate response
            self.response.add_text_to_metadata("No supporting documents found in Vector DB to query data.")
            return self.response

        try:
            # Generate SQL from LLM based on provided DDL and schema
            response = self.get_sql_from_llm(docs_ddl_formatted, docs_schema_formatted)
            sql = response["SQL_Code"]
        except RuntimeError as e:
            # Handle errors during SQL generation
            self.response.add_text_to_metadata(str(e))
            return self.response

        if sql:
            logger.info(f"SQL: {sql}")
            try:
                # Execute the generated SQL
                success, result = self.execute_sql(sql)
            except Exception as e:
                # Handle SQL execution errors
                self.response.add_text_to_metadata(str(e))
                return self.response

            if not success:
                # Resubmit the SQL for correction if the execution fails
                corrected_sql = self.resubmit_for_correction(docs_ddl_formatted, sql, result)
                logger.info(f"Corrected SQL: {corrected_sql}")
                success, result = self.execute_sql(corrected_sql)

                if not success:
                    # Parse SQL from the error message if the correction also fails
                    parsed_sql = self.parse_sql_from_error(result)
                    if parsed_sql:
                        logger.info(f"Parsed SQL from error message: {parsed_sql}")
                        success, result = self.execute_sql(parsed_sql)

            if success:
                # Set the result in the response object
                self._set_result(result, sql, response["Explanation"])
            else:
                # Add error message to metadata if execution fails
                self.response.add_text_to_metadata(result)

        return self.response

    async def arun(self, user_prompt: str):
        """Async method to run the SQL agent with streaming capability based on the user's prompt.

        Args:
        ----
            user_prompt (str): The user's query.

        Yields:
        -------
            dict: Intermediate results or final response from the SQL agent.

        """
        self.user_prompt = user_prompt

        chat_logger.info(f"Human: {user_prompt}")
        logger.info(f"[Sql Agent] Query: {user_prompt}")

        # Get DDL documents from vector database
        docs_ddl = self.__get_ddl_from_vdb(user_prompt)

        if not docs_ddl or docs_ddl == "ANALYTQ___NO_ANSWER":
            logger.info("No relevant DDL documents in VDB located.")
        if docs_ddl:
            logger.info(f"DDL documents found: {len(docs_ddl)}")
            yield {"content": f"DDL Documents found: {len(docs_ddl)}"}

            # Format the DDL chunks for LLM input
            docs_ddl_formatted = self.format_ddl_chunks(docs_ddl)

        docs_schema = None
        docs_schema_formatted: str = None

        if not docs_ddl and not docs_schema:
            # If no supporting documents are found, yield an appropriate response
            self.response.add_text_to_metadata("No supporting documents found in Vector DB to query data.")
            yield self.response.to_json()
            return

        try:
            # Generate SQL from LLM based on provided DDL and schema
            response = self.get_sql_from_llm(docs_ddl_formatted, docs_schema_formatted)
            sql = response["SQL_Code"]
        except RuntimeError as e:
            # Handle errors during SQL generation
            self.response.add_text_to_metadata(str(e))
            yield self.response.to_json()
            return

        if sql:
            yield {"content": f"Here is the SQL that was used:\n ```\n{sql}\n```"}
            logger.info(f"SQL: {sql}")
            try:
                # Execute the generated SQL
                success, result = self.execute_sql(sql)
            except Exception as e:
                # Handle SQL execution errors
                self.response.add_text_to_metadata(str(e))
                yield self.response.to_json()
                return

            if not success:
                # Resubmit the SQL for correction if the execution fails
                corrected_sql = self.resubmit_for_correction(docs_ddl_formatted, sql, result)
                logger.info(f"Corrected SQL: {corrected_sql}")
                success, result = self.execute_sql(corrected_sql)

                if not success:
                    # Parse SQL from the error message if the correction also fails
                    parsed_sql = self.parse_sql_from_error(result)
                    if parsed_sql:
                        logger.info(f"Parsed SQL from error message: {parsed_sql}")
                        success, result = self.execute_sql(parsed_sql)

            if success:
                # Set the result in the response object
                self._set_result(result, sql, response["Explanation"])
                yield self.response.to_json()
            else:
                # Add error message to metadata if execution fails
                self.response.add_text_to_metadata(result)
                yield self.response.to_json()