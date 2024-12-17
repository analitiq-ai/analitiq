"""Create Parameters to use for e2e Variables and reuse in each E2E test."""

import os
import pytest

from tests.helpers import helpers


ENV_VARIABLES = [
    "COLLECTION_NAME",
    "VDB_HOST",
    "VDB_API_KEY",
    "LLM_MODEL_NAME",
    "LLM_CREDENTIALS_PROFILE_NAME",
    "LLM_AWS_ACCESS_KEY_ID",
    "LLM_AWS_SECRET_ACCESS_KEY",
    "LLM_REGION_NAME",
    "DB_TYPE",
    "DB_NAME",
    "DB_DIALECT",
    "DB_HOST",
    "DB_USERNAME",
    "DB_PASSWORD",
    "DB_PORT",
    "DB_SCHEMAS",
    "DB_THREADS",
    "DB_KEEPALIVES_IDLE",
    "DB_CONNECT_TIMEOUT",
]


@pytest.fixture(name="env_vars")
def env_vars_fixture():
    """Set the variables and return dict."""
    helpers.check_env_vars(ENV_VARIABLES)
    return {variable_name: os.getenv(variable_name) for variable_name in ENV_VARIABLES}


@pytest.fixture(name="db_params")
def db_params_fixture(env_vars):
    """Set the database parameters."""
    return {
        "name": env_vars.get("DB_NAME"),
        "type": env_vars.get("DB_TYPE"),
        "dialect": env_vars.get("DB_DIALECT"),
        "host": env_vars.get("DB_HOST"),
        "username": env_vars.get("DB_USERNAME"),
        "password": env_vars.get("DB_PASSWORD"),
        "port": env_vars.get("DB_PORT"),
        "db_name": env_vars.get("DB_NAME"),
        "db_schemas": env_vars.get("DB_SCHEMAS").split(","),
        "threads": int(env_vars.get("DB_THREADS")),
        "keepalives_idle": int(env_vars.get("DB_KEEPALIVES_IDLE")),
        "connect_timeout": int(env_vars.get("DB_CONNECT_TIMEOUT")),
    }


@pytest.fixture(name="llm_params")
def llm_params_fixture(env_vars):
    """Set the llm parameters."""
    return {
        "type": "bedrock",
        "name": "aws_llm",
        "api_key": None,
        "temperature": 0.0,
        "llm_model_name": env_vars.get("LLM_MODEL_NAME"),
        "credentials_profile_name": env_vars.get("LLM_CREDENTIALS_PROFILE_NAME"),
        "provider": "anthropic",
        "aws_access_key_id": env_vars.get("LLM_AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": env_vars.get("LLM_AWS_SECRET_ACCESS_KEY"),
        "region_name": env_vars.get("LLM_REGION_NAME"),
    }


@pytest.fixture(name="vdb_params")
def vdb_params_fixture(env_vars):
    """Set the vdb Parameters."""
    return {
        "collection_name": env_vars.get("COLLECTION_NAME"),
        "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
        "type": "weaviate",
        "host": env_vars.get("VDB_HOST"),
        "api_key": env_vars.get("VDB_API_KEY"),
    }
