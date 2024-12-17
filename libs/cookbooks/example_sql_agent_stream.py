import os
import sys
import asyncio
from analitiq.agents.sql.sql_agent import SQLAgent
from analitiq.main import Analitiq
from dotenv import load_dotenv

ENV_VARIABLES = ["COLLECTION_NAME", "VDB_HOST", "VDB_API_KEY", "LLM_MODEL_NAME",
                 "CREDENTIALS_PROFILE_NAME",
                 "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "REGION_NAME", "DB_NAME", "DB_DIALECT", "DB_HOST",
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
        "type": env_vars.get("DB_TYPE"),
        "name": env_vars.get("DB_NAME"),
        "dialect": env_vars.get("DB_DIALECT"),
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
        "collection_name": env_vars.get("COLLECTION_NAME"),
        "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
        "type": os.getenv("VDB_TYPE"),
        "host": env_vars.get("VDB_HOST"),
        "api_key": env_vars.get("VDB_API_KEY")
    }


async def main():
    add_to_sys_path()
    env_vars = load_env_variables()

    # Combine the variables into a dictionary
    params = {"db_params": define_db_params(env_vars),
              "llm_params": define_llm_params(env_vars),
              "vdb_params": define_vdb_params(env_vars)
              }

    # Create agents
    agents = [
        SQLAgent(key="sql_1")
    ]

    inst = Analitiq(agents, params)

    # Call the async arun method and iterate over the yielded results
    async for response in inst.arun(user_query="give me count of events by venue."):
        # Loop through all results and handle dataframes accordingly
        try:
            for key, result in response.items():
                print(f"Streaming result for agent key '{key}':")
                for content_type, content in result.items():
                    print(f"  {content_type}: {content}")
        except Exception as e:
            print(e)


# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())

