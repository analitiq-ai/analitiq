from sqlalchemy import inspect, exc, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine.url import URL
from functools import lru_cache
from langchain_community.utilities import SQLDatabase
import logging
from typing import List, Dict

CACHE_SIZE = 64


class DatabaseEngine:
    """
    The DatabaseEngine class is responsible for creating the engine based on the provided parameters.
    It uses the factory method pattern to create the appropriate engine based on the database type.

    Args:
        params (Dict): A dictionary containing the parameters for creating the engine.

    Attributes:
        params (Dict): A dictionary consisting of the parameters for creating the engine.
        engine (Engine): The created database engine.

    Raises:
        ValueError: If the provided database type is unsupported.

    """
    def __init__(self, params: Dict):
        self.params = params
        self.engine = self.create_engine()

    @lru_cache(maxsize=CACHE_SIZE)
    def create_engine(self):
        if self.params['type'] in ['postgres', 'postgresql']:
            return self._create_postgres_engine()
        elif self.params['type'] == 'redshift':
            return self._create_redshift_engine()
        else:
            raise ValueError(f"Unsupported database type {self.params['type']}")

    def _create_postgres_engine(self):
        engine_options = {}
        if self.params['db_schemas'] is not None:
            schemas_str = ",".join(self.params['db_schemas'])
            engine_options['connect_args'] = {'options': f"-csearch_path={schemas_str}"}
        return create_engine(
            f"postgresql+psycopg2://{self.params['user']}:{self.params['password']}@{self.params['host']}:{self.params['port']}/{self.params['dbname']}",
            **engine_options
        )

    def _create_redshift_engine(self):
        url = URL.create(
            drivername="redshift+redshift_connector",
            host=self.params['host'],
            port=5439,
            database=self.params['db_name'],
            username=self.params['username'],
            password=self.params['password']
        )
        return create_engine(url, connect_args={"sslmode": "allow"})


class DatabaseSession:
    """
    The DatabaseSession class is responsible for managing the database session.
    It uses the scoped session pattern to ensure that the same session is used within the same thread.

    This class is used as a context manager to manage the database session lifecycle.

    :param engine: The database engine to bind the session to.
    """
    def __init__(self, engine):
        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.Session = scoped_session(self.session_factory)

    def __enter__(self):
        self.session = self.Session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Session.remove()


class Database:
    """
    The Database class is responsible for running queries on the database.
    It uses the SQLDatabase class from the langchain_community.utilities module to run queries.

    :param engine: The database engine to use.
    :type engine: str
    """
    def __init__(self, engine):
        self.engine = engine
        self.db = SQLDatabase(self.engine)

    def run(self, sql, include_columns=True):
        try:
            result = self.db.run(sql, include_columns=include_columns)
            return result
        except Exception as e:
            raise e
        finally:
            self.engine.dispose()


class DatabaseWrapper:
    """
    The DatabaseWrapper class is the main class that uses the DatabaseEngine, DatabaseSession, and Database classes to perform database operations.
    It initializes these classes in its constructor and provides methods for getting schema names, tables in a schema, and schemas and tables.

    :param params: A dictionary containing parameters required to connect to the database.
    :type params: Dict
    """
    def __init__(self, params: Dict):
        self.params = params
        self.engine = DatabaseEngine(params).engine
        self.session = DatabaseSession(self.engine)
        self.db = Database(self.engine)

    def get_schema_names(self) -> List[str]:
        """
        Retrieves the names of the database schemas.

        :return: A list of strings representing the schema names.
        :rtype: list[str]
        """
        try:
            inspector = inspect(self.engine)
            return inspector.get_schema_names()
        except exc.SQLAlchemyError as e:
            raise e
        finally:
            self.engine.dispose()

    def get_tables_in_schema(self, db_schema):
        """
        Get the names of all tables in a given database schema.

        :param db_schema: The name of the database schema to retrieve table names from.
        :return: A list of table names in the specified database schema.
        """
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names(schema=db_schema)

        self.engine.dispose()

        return table_names

    def get_schemas_and_tables(self, target_schema_list: List) -> Dict:
        """
        Retrieve the schemas and tables from the database engine.

        :param target_schema_list: A list of schema names to consider.
        :type target_schema_list: List
        :return: A dictionary containing column details, grouped by schema and table.
        :rtype: Dict
        """
        inspector = inspect(self.engine)
        schemas = [schema for schema in inspector.get_schema_names() if schema in target_schema_list]
        response = []
        for schema in schemas:
            tables = inspector.get_table_names(schema=schema)
            if len(tables) > 0:
                for table in tables:
                    columns = inspector.get_columns(table_name=table, schema=schema)
                    column_details = ', '.join(f"{schema}.{table}.{column['name']} ({column['type']})" for column in columns)
                    response.append(column_details)

        self.engine.dispose()

        return response
