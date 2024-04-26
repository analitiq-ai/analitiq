from sqlalchemy import inspect
from sqlalchemy import exc
from sqlalchemy.engine import Engine
from typing import List, Optional
import sqlalchemy as sa
from functools import lru_cache

CACHE_SIZE = 64
#{decode_data(password)}

@lru_cache(maxsize=CACHE_SIZE)
def create_db_engine(dialect: str, driver: str, host: str, port: int, username: str, password: str, db_name: str, db_schema: str = None) -> Engine:
    engine_options = {}
    if db_schema is not None:
        engine_options['connect_args'] = {'options': f"-csearch_path={db_schema}"}

    return sa.create_engine(f"{dialect}+{driver}://{username}:{password}@{host}:{port}/{db_name}", **engine_options)


def get_schema_names(engine: Engine) -> List[str]:
    try:
        inspector = sa.inspect(engine)
        return inspector.get_schema_names()
    except exc.SQLAlchemyError as e:
        raise e


def get_tables_in_schema(engine, db_schema):

    # Create an inspector
    inspector = inspect(engine)

    # Retrieve tables with other schema
    return inspector.get_table_names(schema=db_schema)


def get_schemas_and_tabes(engine: Engine) -> str:
    # Create an inspector
    inspector = inspect(engine)

    # Fetch schemas, tables, and columns
    schemas = inspector.get_schema_names()

    prompt = ""
    for schema in schemas:
        prompt += f"- Schema: {schema}\n"
        tables = inspector.get_table_names(schema=schema)
        for table in tables:
            prompt += f"  - Table: {table}\n    - Columns: "
            columns = inspector.get_columns(table_name=table, schema=schema)
            column_details = ', '.join(f"{column['name']} ({column['type']})" for column in columns)
            prompt += f"{column_details}\n"

    return prompt