import pytest
import os
from libs.analitiq.agents.sql.sql import Sql
from libs.analitiq.base.Database import DatabaseWrapper
from libs.analitiq.base.llm.BaseLlm import BaseLlm
from libs.analitiq.vectordb.weaviate import WeaviateHandler

from libs.tests.e2e import helpers

ENV_VARIABLES = ["WEAVIATE_COLLECTION", "WEAVIATE_URL", "WEAVIATE_CLIENT_SECRET", "LLM_MODEL_NAME",
                 "CREDENTIALS_PROFILE_NAME",
                 "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "REGION_NAME", "DB_NAME", "DB_TYPE", "DB_HOST",
                 "DB_USERNAME",
                 "DB_PASSWORD", "DB_PORT", "DB_DB_NAME", "DB_SCHEMAS", "DB_THREADS", "DB_KEEPALIVES_IDLE",
                 "DB_CONNECT_TIMEOUT"]


@pytest.fixture(name="env_vars")
def env_vars_fixture():
    """Set and check the env vars."""
    helpers.check_env_vars(ENV_VARIABLES)
    return {variable_name: os.getenv(variable_name) for variable_name in ENV_VARIABLES}


@pytest.fixture(name="db_params")
def db_params_fixture(env_vars):
    """Set the database parameters."""
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


@pytest.fixture(name="llm_params")
def llm_params_fixture(env_vars):
    """Set the llm parameters."""
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


@pytest.fixture(name="vdb_params")
def vdb_params_fixture(env_vars):
    """Set the vdb Parameters."""
    return {
        "collection_name": env_vars.get("WEAVIATE_COLLECTION"),
        "host": env_vars.get("WEAVIATE_URL"),
        "api_key": env_vars.get("WEAVIATE_CLIENT_SECRET")
    }

@pytest.fixture(name="sql_agent")
def sql_agent_fixture(db_params, llm_params, vdb_params):
    """Set up the sql Agent."""
    db = DatabaseWrapper(db_params)
    llm = BaseLlm(llm_params)
    vdb = WeaviateHandler(vdb_params)
    return Sql(db, llm, vdb=vdb)


def test_analitiq_sql_agent(sql_agent):
    """Test the sql agent e2e."""
    user_prompt = "show me sales by venue."
    result_generator = sql_agent.run(user_prompt)

    assert result_generator

    for result in result_generator:
        if isinstance(result, str):
            assert result
        else:
            assert result
