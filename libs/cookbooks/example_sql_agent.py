import os
import sys
from analitiq.agents.sql.sql import Sql
from analitiq.factories.relational_database_factory import RelationalDatabaseFactory
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.vectordb.weaviate.weaviate_handler import WeaviateHandler
from dotenv import load_dotenv

ENV_VARIABLES = ["WEAVIATE_COLLECTION", "WEAVIATE_URL", "WEAVIATE_CLIENT_SECRET", "LLM_MODEL_NAME",
                 "CREDENTIALS_PROFILE_NAME",
                 "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "REGION_NAME", "DB_NAME", "DB_TYPE", "DB_HOST",
                 "DB_USERNAME",
                 "DB_PASSWORD", "DB_PORT", "DB_DB_NAME", "DB_SCHEMAS", "DB_THREADS", "DB_KEEPALIVES_IDLE",
                 "DB_CONNECT_TIMEOUT"]


def add_to_sys_path():
    home_directory = os.environ.get("HOME")
    dynamic_path = f"{home_directory}/Documents/Projects/analitiq/libs/"
    sys.path.insert(0, dynamic_path)


def load_env_variables():
    load_dotenv()
    return {variable_name: os.getenv(variable_name) for variable_name in ENV_VARIABLES}


def define_db_params(env_vars):
    return {
        "name": env_vars.get("DB_NAME"),
        "type": env_vars.get("DB_TYPE"),
        "host": env_vars.get("DB_HOST"),
        "username": env_vars.get("DB_USERNAME"),
        "password": env_vars.get("DB_PASSWORD"),
        "port": env_vars.get("DB_PORT"),
        "db_name": env_vars.get("DB_DB_NAME"),
        "db_schemas": env_vars.get("DB_SCHEMAS").split(","),
        "threads": int(env_vars.get("DB_THREADS")),
        "keepalives_idle": int(env_vars.get("DB_KEEPALIVES_IDLE")),
        "connect_timeout": int(env_vars.get("DB_CONNECT_TIMEOUT"))
    }


def define_llm_params(env_vars):
    return {"type": "bedrock"
        , "name": "aws_llm"
        , "api_key": None
        , "temperature": 0.0
        , "llm_model_name": env_vars.get("LLM_MODEL_NAME")
        , "credentials_profile_name": env_vars.get("CREDENTIALS_PROFILE_NAME")
        , "provider": "anthropic"
        , "aws_access_key_id": env_vars.get("AWS_ACCESS_KEY_ID")
        , "aws_secret_access_key": env_vars.get("AWS_SECRET_ACCESS_KEY")
        , "region_name": env_vars.get("REGION_NAME")
            }


def define_vdb_params(env_vars):
    return {
        "collection_name": env_vars.get("WEAVIATE_COLLECTION"),
        "host": env_vars.get("WEAVIATE_URL"),
        "api_key": env_vars.get("WEAVIATE_CLIENT_SECRET")
    }


if __name__ == "__main__":
    add_to_sys_path()
    env_vars = load_env_variables()

    db_params = define_db_params(env_vars)
    llm_params = define_llm_params(env_vars)
    vdb_params = define_vdb_params(env_vars)

    db = RelationalDatabaseFactory.create_database(db_type="postgres", params=db_params)
    llm = BaseLlm(llm_params)
    vdb = WeaviateHandler(vdb_params)

    agent = Sql(db, llm, vdb=vdb)
    result_generator = agent.run("show me sales by venue.")

    print(str(result_generator))


