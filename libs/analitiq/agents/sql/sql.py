import pandas as pd
from typing import List, Tuple, Optional
from analitiq.logger.logger import logger, chat_logger
from analitiq.base.BaseResponse import BaseResponse
from analitiq.utils.code_extractor import CodeExtractor
from analitiq.base.Database import DatabaseWrapper
from analitiq.agents.sql.schema import Table, Tables, SQL, TableCheck
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.exc import DatabaseError
from analitiq.agents.sql.prompt import RETURN_RELEVANT_TABLE_NAMES, TEXT_TO_SQL_PROMPT
from analitiq.utils.document_processor import string_to_chunk

MAX_ITERATIONS = 5
DB_DESCRIPTION_METADATA_PARAM = "document_name"
DB_DESCRIPTION_METADATA_VALUE = "schema.yml"
CONTEXT_MAX_TOKENS = 100000
CHUNK_OVERLAP = 200
VECTOR_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class Sql:
    """Handles SQL query generation and execution against the database using LLM integration.

    This class provides methods to load DDL into a vector database, get relevant tables,
    check relevant tables, get database documentation schema, execute SQL queries, search DDL vectors,
    get SQL from LLM, glue document chunks, and run the SQL agent.
    """

    def __init__(self, db: DatabaseWrapper, llm, vdb=None):
        """Initializes the SQL Agent. SQL Agent writes SQL and executes the SQL against the database. After that SQL Agent returns the result.

        Args:
        ----
            db (DatabaseWrapper): An instance of DatabaseWrapper class representing the database connection.
            llm: A parameter representing llm (unknown data type).
            vdb (optional): An optional parameter representing vdb (unknown data type).

        """
        logger.info("SQL Agent Started.")
        self.user_prompt: Optional[str] = None
        self.db = db
        self.llm = llm
        self.vdb = vdb  # TODO this should be double checked as it is not same as search example.
        self.relevant_tables = ""
        self.response = BaseResponse(self.__class__.__name__)

    @staticmethod
    def _extract_table_name(input_string: str) -> str:
        """Extracts 'table_name' from the given string by splitting the text by commas, taking the first occurrence, and then splitting by dots to take the second occurrence.

        Args:
        ----
            input_string (str): The input string containing the table name information.

        Returns:
        -------
            str: Extracted table name.

        """
        # Split the string by comma and take the first occurrence
        first_part = input_string.split(",")[0]

        # Split the first part by dot and take the second occurrence
        schema_table = first_part.split(".")[0] + "." + first_part.split(".")[1]

        return schema_table

    def load_ddl_into_vdb(self) -> int:
        """Loads DDL (Data Definition Language) into the Vector Database (VDB).

        Notes
        -----
            - SQLAlchemy returns DDL as a list of tables in schema [] with every object in list being comma separated list of columns.
            - Analitiq stores the DDL in vector DB using metadata to identify source of the data:
                - content=DDL for 1 table,
                - source='host/database',
                - document_type='ddl',
                - document_name='schema.table'

        Returns
        -------
            List[str]: A list of responses after loading DDL into VDB.

        """
        response = []
        metadata = {}

        metadata["source"] = f"{self.db.params['host']}/{self.db.params['db_name']}"

        document_type = "ddl"
        for schema_name in self.db.params["db_schemas"]:
            # for some reason ddl is a one item list []
            ddl = self.db.get_schemas_and_tables(schema_name)
            logger.info(f"Received DDL for {len(ddl)} tables in schema {schema_name}")
            # Do not log this unless you really need to. This could be huge
            # logger.info(f"DDL for {schema_name}: {ddl}")

            # Check if DDL in VDB
            meta_parameters = [("document_name", schema_name), ("document_type", document_type)]
            filter_expression = {
                "and": [
                    {"property": "document_name", "operator": "like", "value": schema_name},
                    {"property": "document_type", "operator": "=", "value": document_type}
                ]
            }
            response = self.vdb.count_with_filter(filter_expression)

            loaded_chunk_counter = 0
            if response.total_count and response.total_count > 0:
                logger.info(f"[VDB] Found {response.total_count} ddl documents for schema {schema_name}.")
                # TODO add checking here for when it was last loaded

            else:  # if the DDL does not exist in VDB, we load it
                chunks = []

                for table_ddl in ddl:
                    metadata["document_name"] = self._extract_table_name(table_ddl)
                    metadata["document_type"] = "ddl"
                    chunk = string_to_chunk(table_ddl, metadata)
                    chunks.append(chunk)
                    loaded_chunk_counter += + 1

                chunks_loaded = self.vdb.load_chunks(chunks)

                logger.info(f"Loaded {counter} chunks for schema {schema_name} into Vector Database.")

        return loaded_chunk_counter

    def get_relevant_tables(self, ddl: str, docs: Optional[str] = None) -> List[Table]:
        """Retrieves relevant tables based on the provided DDL and documentation.

        Args:
        ----
            ddl (str): The Data Definition Language of the database.
            docs (str, optional): Additional database documentation. Defaults to None.

        Returns:
        -------
            List[Table]: A list of relevant tables.

        """
        docs = f"Database Documentation:\n{docs}\n" if docs else ""

        parser = PydanticOutputParser(pydantic_object=Tables)
        prompt = PromptTemplate(
            template=RETURN_RELEVANT_TABLE_NAMES,
            input_variables=["user_prompt"],
            partial_variables={
                "ddl": ddl,
                "db_docs": docs,
                "format_instructions": parser.get_format_instructions(),
            },
        )
        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
        logger.info(f"Relevant Tables: {response.to_json()}")
        chat_logger.info(f"Assistant: List of tables believed to be relevant - {response.to_json()}")

        schema_dict = {}

        for table in response.TableList:
            check_result = self.check_relevant_table(table.SchemaName, table.TableName)
            if check_result.Required:
                if table.SchemaName not in schema_dict:
                    schema_dict[table.SchemaName] = []
                schema_dict[table.SchemaName].append(table)

        return self._format_relevant_tables(schema_dict)

    @staticmethod
    def _format_relevant_tables(schema_dict: dict) -> str:
        """Formats the relevant tables into a readable string format.

        Args:
        ----
            schema_dict (dict): Dictionary containing schema and table information.

        Returns:
        -------
            str: Formatted string of relevant tables.

        """
        output_lines = []
        for schema, tables in schema_dict.items():
            output_lines.append(f"- Schema: {schema}")
            for table in tables:
                output_lines.append(f"  - Table: {schema}.{table.TableName}")
                column_details = ", ".join(
                    f"{column.ColumnName} ({column.DataType})" for column in table.Columns
                )
                output_lines.append(f"    - Columns: {column_details}")
        return "\n".join(output_lines)

    def check_relevant_table(self, schema_name: str, table_name: str) -> TableCheck:
        """Checks if the specified table is relevant to the user's query.

        Args:
        ----
            schema_name (str): The schema name.
            table_name (str): The table name.

        Returns:
        -------
            TableCheck: Result of the table relevance check.

        """
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
                "format_instructions": parser.get_format_instructions(),
            },
        )
        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)
        return response

    def get_db_docs_schema(self, query: str) -> Optional[str]:
        """Retrieves the database schema documentation relevant to the given query.

        Args:
        ----
            query (str): The user query.

        Returns:
        -------
            Optional[str]: The relevant database schema documentation, if available.

        """
        if not self.vdb:
            return None

        filter_expression = {
            "and": [
                {"property": DB_DESCRIPTION_METADATA_PARAM, "operator": "=", "value": DB_DESCRIPTION_METADATA_VALUE}
            ]
        }

        response = self.vdb.search_with_filter(
            query, filter_expression, ["document_name", "document_type"]
        )

        if not response:
            logger.info(
                f"[VectorDB] No objects returned that match search query in {DB_DESCRIPTION_METADATA_PARAM}: {DB_DESCRIPTION_METADATA_VALUE}."
            )
            return None

        logger.info(f"[VDB] Context Documents found: {len(response)}")

        # response = self.llm.extract_info_from_db_docs(self.user_prompt, response)

        # chat_logger.info(f"LLM: {response}")
        # self.response.add_text_to_metadata(response)

        # logger.info(f"LLM Info from Documents: {response}")

        # if 'ANALITQ___NO_ANSWER' in response:
        #    return None

        return response

    def execute_sql(self, sql: str) -> Tuple[bool, Optional[pd.DataFrame]]:
        """Executes the given SQL query and returns the result as a DataFrame.

        Args:
        ----
            sql (str): The SQL query to be executed.

        Returns:
        -------
            Tuple[bool, Optional[pd.DataFrame]]: A tuple containing a boolean indicating success, and the result as a DataFrame or an error message.

        """
        chat_logger.info(f"{sql}")
        try:
            result = pd.read_sql(sql, self.db.engine)
            if result.empty:
                chat_logger.info("SQL executed successfully, but result is empty.")
            else:
                chat_logger.info(f"SQL executed successfully. Converted to DataFrame. {result}")

            return True, result
        except DatabaseError as e:
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
        if docs_ddl:
            docs_ddl = """Bellow is a list of relevant tables and columns for you to use to create an SQL query.
            Make sure you use only the available database tables and columns.
            Each table is prepended with a schema name like this schema_name.table.name
            {docs_ddl_placeholder}
            """.format(docs_ddl_placeholder="\n".join(docs_ddl))
        if docs_schema:
            docs_schema = """Here is some additional documentation that you may find useful to make your SQL more accurate:
            {docs_schema_placeholder}
            """.format(docs_schema_placeholder="\n".join(docs_schema))

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

        response = self.llm.llm_invoke(self.user_prompt, prompt, parser)

        chat_logger.info(f"Assistant: {response}")

        if not response.get("SQL_Code"):
            msg = "No SQL Code returned"
            raise ValueError(msg)

        return response

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
            chunks = document.get("document_chunks", [])
            glued_text = "\n\n".join(chunks)  # Ensure each chunk starts on a new line
            glued_documents.append(glued_text)
        return glued_documents

    def _set_result(self, result: pd.DataFrame, sql: Optional[str] = None, explanation: Optional[str] = None):
        """Sets the result of the SQL execution into the response object.

        Args:
        ----
            result (pd.DataFrame): The result of the SQL execution.
            sql (str, optional): The SQL query executed. Defaults to None.
            explanation (str, optional): Explanation of the result. Defaults to None.

        """
        self.response.set_content(result, "dataframe")
        if result.empty:
            self.response.add_text_to_metadata(
                "The query produced no result. Please review your query and SQL generated based on it and fine-tune your instructions."
            )
        else:
            self.response.add_text_to_metadata(f"\n{explanation}")
            if sql:
                self.response.add_text_to_metadata(f"\n```\n{sql}\n```")

    def __get_ddl_from_vdb(self, user_prompt):
        # Build filters for Weaviate DB to use to find DB Schemas
        schema_filters = []
        for schema in self.db.params["db_schemas"]:
            schema_filters.append({"property": "document_name", "operator": "like", "value": schema})

        filter_expression = {
            "and": [
                {"property": "document_type", "operator": "=", "value": "ddl"},
                {
                    "or": schema_filters
                }
            ]
        }

        return self.vdb.search_with_filter(user_prompt, filter_expression, ["document_name"])

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

        docs_schema = self.get_db_docs_schema(user_prompt)
        docs_schema_formatted: str = None

        if not docs_schema or docs_schema == "ANALYTQ___NO_ANSWER":
            # logger.info("No relevant documents in VDB located.", docs)
            docs_schema = None
        if docs_schema:
            logger.info(f"Context Documents found: {len(docs_schema)}")
            docs_schema_formatted = self.glue_document_chunks(docs_schema)

            if "```" in docs_schema:
                extractor = CodeExtractor()
                sql = extractor.extract_code(docs_schema, "sql")
                if sql:
                    success, result = self.execute_sql(sql)
                    if success:
                        self._set_result(result, None, docs_schema)
                        return self.response

        # Check if DDL is already loaded in Vector DB
        self.load_ddl_into_vdb()

        docs_ddl = self.__get_ddl_from_vdb(user_prompt)

        # self.relevant_tables = self.get_relevant_tables(ddl, docs_schema)
        # chat_logger.info(f"Assistant: List of relevant tables and columns.\n{self.relevant_tables}")

        # self.response.add_text_to_metadata(f"Relevant tables: {self.relevant_tables}")
        # self.response.set_metadata({"relevant_tables": self.relevant_tables})

        # if we do not have ddl_docs docs_schema and context, there is little point trying to create SQL.

        docs_ddl_formatted: str = None

        if not docs_ddl and not docs_schema:
            self.response.add_text_to_metadata("No supporting documents found in Vector DB to query data.")
            return self.response

        if docs_ddl:
            logger.info(f"DDL Documents found: {len(docs_ddl)}")
            docs_ddl_formatted = self.glue_document_chunks(docs_ddl)

        try:
            response = self.get_sql_from_llm(docs_ddl_formatted, docs_schema_formatted)
            sql = response["SQL_Code"]
        except RuntimeError as e:
            self.response.add_text_to_metadata(str(e))
            return self.response

        if sql:
            pass

        logger.info(f"SQL: {sql}")

        success, result = self.execute_sql(sql)

        if success:
            self._set_result(result, sql, response["Explanation"])
        else:
            self.response.add_text_to_metadata(result)

        return self.response

    async def arun(self, user_prompt: str) -> BaseResponse:
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

        docs_schema = self.get_db_docs_schema(user_prompt)

        if not docs_schema or docs_schema == "ANALYTQ___NO_ANSWER":
            # logger.info("No relevant documents in VDB located.", docs)
            docs_schema = None
        if docs_schema:
            msg = f"Context Documents found: {len(docs_schema)}"
            yield {"content": msg}
            docs_schema_formatted = self.glue_document_chunks(docs_schema)

            if "```" in docs_schema:
                extractor = CodeExtractor()
                sql = extractor.extract_code(docs_schema, "sql")
                if sql:
                    success, result = self.execute_sql(sql)
                    if success:
                        self._set_result(result, None, docs_schema)
                        yield self.response.to_json()
                        return

        # Check if DDL is already loaded in Vector DB
        self.load_ddl_into_vdb()

        docs_ddl = self.__get_ddl_from_vdb(user_prompt)

        # self.relevant_tables = self.get_relevant_tables(ddl, docs_schema)
        # chat_logger.info(f"Assistant: List of relevant tables and columns.\n{self.relevant_tables}")

        # self.response.add_text_to_metadata(f"Relevant tables: {self.relevant_tables}")
        # self.response.set_metadata({"relevant_tables": self.relevant_tables})

        # if we do not have ddl_docs docs_schema and context, there is little point trying to create SQL.

        if not docs_ddl and not docs_schema:
            self.response.add_text_to_metadata("No supporting documents found in Vector DB to query data.")
            yield self.response.to_json()

            return

        if docs_ddl:
            msg = f"DDL Documents found: {len(docs_ddl)}"
            yield {"content": msg}
            docs_ddl_formatted = self.glue_document_chunks(docs_ddl)

        try:
            response = self.get_sql_from_llm(docs_ddl_formatted, docs_schema_formatted)
            sql = response["SQL_Code"]
        except RuntimeError as e:
            self.response.add_text_to_metadata(str(e))

            yield self.response.to_json()
            return

        if sql:
            msg = f"Here is the SQL that was used:\n ```\n{sql}\n```"
            yield {"content": msg}

        logger.info(f"SQL: {sql}")

        success, result = self.execute_sql(sql)

        if success:
            self._set_result(result.to_markdown(), sql, response["Explanation"])
        else:
            self.response.add_text_to_metadata(str(result))

        yield self.response.to_json()
