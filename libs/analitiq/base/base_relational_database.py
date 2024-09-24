from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
from sqlalchemy import inspect
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session
from pandas import read_sql, DataFrame
from langchain_community.utilities import SQLDatabase


class BaseRelationalDatabase(ABC):
    """Abstract base class for relational databases."""

    def __init__(self, params: Dict):
        self.params = params
        self.engine = self.create_engine()
        self.session = self.create_session()
        self.db = self.create_db()

    @abstractmethod
    def create_engine(self):
        """Create and return a SQLAlchemy engine."""

    def create_session(self):
        """Create a scoped session bound to the engine."""
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        session = scoped_session(session_factory)
        return session

    def create_db(self):
        """Create an SQLDatabase instance for query execution."""
        return SQLDatabase(self.engine)

    def get_schema_names(self) -> List[str]:
        """Retrieve the names of the database schemas."""
        try:
            inspector = inspect(self.engine)
            return inspector.get_schema_names()
        except SQLAlchemyError as e:
            raise e
        finally:
            self.engine.dispose()

    def get_tables_in_schema(self, db_schema: str) -> List[str]:
        """Get the names of all tables in a specific database schema."""
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names(schema=db_schema)
        self.engine.dispose()
        return table_names

    def get_schemas_and_tables(self, target_schema_list: List[str]) -> List[str]:
        """Retrieve the schemas and tables from the database engine."""
        inspector = inspect(self.engine)
        schemas = [schema for schema in inspector.get_schema_names() if schema in target_schema_list]
        response = []
        for schema in schemas:
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                columns = self.get_table_columns(table_name=table, schema=schema)
                column_details = ", ".join(
                    f"{schema}.{table}.{column['name']} ({column['type']})" for column in columns
                )
                response.append(column_details)
        self.engine.dispose()
        return response

    def get_table_columns(self, table_name: str, schema: str) -> List[Dict]:
        """Retrieve column metadata for a given table and schema."""
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name, schema=schema)
        return columns

    @staticmethod
    def get_numeric_columns(columns: List[Dict]) -> Dict[str, str]:
        """Return a dictionary of numeric columns and their data types."""
        numeric_types = (
            "INTEGER",
            "FLOAT",
            "NUMERIC",
            "DECIMAL",
            "REAL",
            "DOUBLE",
            "BIGINT",
            "SMALLINT",
        )
        numeric_columns = {
            col["name"]: str(col["type"])
            for col in columns
            if any(str(col["type"]).upper().startswith(num_type) for num_type in numeric_types)
        }
        return numeric_columns

    def get_row_count(self, schema_name: str, table_name: str) -> int:
        """Get the row count for a specific table."""
        sql = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
        with self.engine.connect() as connection:
            result = connection.execute(sql)
            count = result.scalar()
        return count

    def get_summary_statistics(
        self, schema_name: str, table_name: str, column_name: str
    ) -> Tuple[float, float, float]:
        """Get summary statistics (min, max, avg) for a numeric column."""
        sql = f"""
            SELECT 
                MIN({column_name}) AS min_val, 
                MAX({column_name}) AS max_val, 
                AVG({column_name}) AS avg_val
            FROM {schema_name}.{table_name}
        """
        with self.engine.connect() as connection:
            result = connection.execute(sql)
            min_val, max_val, avg_val = result.fetchone()
        return min_val, max_val, avg_val

    def execute_sql(self, sql: str) -> Tuple[bool, Optional[DataFrame]]:
        """Execute the given SQL query and return the result as a DataFrame."""
        try:
            result = read_sql(sql, self.engine)
            return True, result
        except DatabaseError:
            return False, None

    def run(self, sql: str, include_columns: bool = True):
        """Execute a query using the SQLDatabase utility."""
        try:
            result = self.db.run(sql, include_columns=include_columns)
            return result
        except Exception as e:
            raise e
        finally:
            self.engine.dispose()
