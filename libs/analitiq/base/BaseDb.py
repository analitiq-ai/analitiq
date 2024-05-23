from sqlalchemy import inspect
from sqlalchemy import exc
from sqlalchemy.engine import Engine
from typing import List, Dict
import sqlalchemy as sa
from sqlalchemy.engine.url import URL
from functools import lru_cache
from langchain_community.utilities import SQLDatabase
import logging

CACHE_SIZE = 64
#{decode_data(password)}


class BaseDb:

    def __init__(self, params: Dict):
        self.db_params = params
        self.db_engine = self.create_db_engine()
        self.db = SQLDatabase(self.db_engine)
        self.dialect = ''

    @lru_cache(maxsize=CACHE_SIZE)
    def create_db_engine(self) -> Engine:
        """
        Create a SQLAlchemy database engine based on the specified parameters.

        :return: SQLAlchemy Engine object representing the database connection.
        """
        host = self.db_params['host']
        port = self.db_params['port']  # Default port is 5432 for PostgreSQL
        username = self.db_params['user']
        password = self.db_params['password']
        db_name = self.db_params['dbname']
        db_schemas = self.db_params['dbschemas']

        engine_options = {}

        if self.db_params['type'] == 'postgres':
            self.dialect = 'postgresql'
            driver = 'psycopg2'
            if db_schemas is not None:
                schemas_str = ",".join(db_schemas)
                engine_options['connect_args'] = {'options': f"-csearch_path={schemas_str}"}

            return sa.create_engine(f"{self.dialect}+{driver}://{username}:{password}@{host}:{port}/{db_name}", **engine_options)

        elif self.db_params['type'] == 'redshift':
            self.dialect = 'redshift'
            driver = 'redshift_connector'
            # build the sqlalchemy URL
            engine_options = {
                "sslmode": "allow",  # ensures certificate verification occurs for idp_host
            }
            url = URL.create(
                drivername=f"{self.dialect}+{driver}",  # indicate redshift_connector driver and self.dialect will be used
                host=host,  # Amazon Redshift host
                port=5439,  # Amazon Redshift port
                database=db_name,  # Amazon Redshift database
                username=username,  # Amazon Redshift username
                password=password  # Amazon Redshift password
            )

            return sa.create_engine(url, connect_args=engine_options)
        else:
            print(f"Unsupported database type {self.db_params['type']}")

    def get_db_engine(self):
        """
        Get the database engine used by the object.

        :return: The database engine used by the object.
        """
        return self.db_engine

    def get_db_object(self):
        """
        Retrieves the database object.

        :return: The database object.
        """
        return self.db

    def set_database(self):
        """
        Sets the database for the current profile.

        :return: None
        """
        profile = self.profile_configs['databases']

    def get_db_schemas(self) -> List[str]:
        """
        Get the database schemas.

        :return: The database schema.
        """
        return self.db_params['dbschemas']

    def get_schema_names(self) -> List[str]:
        """
        Retrieve the names of all schemas in the database.

        :return: A list of strings representing the names of all schemas in the database.
        :rtype: list[str]
        :raises SQLAlchemyError: If there is an error while retrieving the schema names.
        """
        try:
            inspector = sa.inspect(self.db_engine)
            return inspector.get_schema_names()
        except exc.SQLAlchemyError as e:
            raise e
        finally:
            # Clean up the engine
            self.engine.dispose()

    def get_tables_in_schema(self, db_schema):
        """
        Retrieve tables in the specified database schema.

        :param db_schema: The name of the database schema to retrieve tables from.
        :return: A list of table names in the specified schema.
        """
        # Create an inspector
        inspector = inspect(self.db_engine)

        # Retrieve tables with other schema
        return inspector.get_table_names(schema=db_schema)

    def get_schemas_and_tables(self, schema_list: List) -> Dict:
        """
        Fetches schemas, tables, and columns from the database.

        :return: A dictionary containing schema, table, and column details.
        """
        # Create an inspector
        inspector = inspect(self.db_engine)

        # Fetch schemas
        schemas = inspector.get_schema_names()

        # Filter out schemas that don't exist in schema_list
        schemas = [schema for schema in schemas if schema in schema_list]

        response = []
        for schema in schemas:
            if schema in ['cds_dds','cds', 'sd_stage']:
                continue

            tables = inspector.get_table_names(schema=schema)
            if len(tables) > 0:
                for table in tables:
                    columns = inspector.get_columns(table_name=table, schema=schema)
                    column_details = ', '.join(f"{schema}.{table}.{column['name']} ({column['type']})" for column in columns)
                    response.append(column_details)

        return response

    def run(self, sql, include_columns=True):

        try:
            result = self.db.run(sql, include_columns=True)
            return result
        finally:
            pass
