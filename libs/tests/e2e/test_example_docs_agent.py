"""Test the docs Agent."""
import pytest
import os
import asyncio
from libs.analitiq.base.llm.BaseLlm import BaseLlm
from libs.analitiq.agents.search_vdb.search_vdb import SearchVdb
from libs.analitiq.vectordb.weaviate import WeaviateHandler

from libs.tests.e2e import helpers

# Liste der erforderlichen Umgebungsvariablen
REQUIRED_ENV_VARS = [
    "WEAVIATE_URL",
    "WEAVIATE_CLIENT_SECRET",
    "LLM_MODEL_NAME",
    "CREDENTIALS_PROFILE_NAME",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "REGION_NAME"
]

@pytest.fixture(name="env_vars")
def env_vars_fixture():
    """Set the variables and return dict."""
    helpers.check_env_vars(REQUIRED_ENV_VARS)
    return {
        "WV_URL": os.getenv("WEAVIATE_URL"),
        "WV_CLIENT_SECRET": os.getenv("WEAVIATE_CLIENT_SECRET"),
        "LLM_MODEL_NAME": os.getenv("LLM_MODEL_NAME"),
        "CREDENTIALS_PROFILE_NAME": os.getenv("CREDENTIALS_PROFILE_NAME"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "REGION_NAME": os.getenv("REGION_NAME")
    }

# Fixture für die LLM-Parameter
@pytest.fixture(name="llm_params")
def llm_params_fixture(env_vars):
    """Set the LLM Params for creating LLM Connection."""
    return {
        "type": "bedrock",
        "name": "aws_llm",
        "api_key": None,
        "temperature": 0.0,
        "llm_model_name": env_vars["LLM_MODEL_NAME"],
        "credentials_profile_name": env_vars["CREDENTIALS_PROFILE_NAME"],
        "provider": "anthropic",
        "aws_access_key_id": env_vars["AWS_ACCESS_KEY_ID"],
        "aws_secret_access_key": env_vars["AWS_SECRET_ACCESS_KEY"],
        "region_name": env_vars["REGION_NAME"]
    }

# Fixture für die VDB-Parameter
@pytest.fixture(name="vdb_params")
def vdb_params_fixture(env_vars):
    """Set the vdb params."""
    return {
        "collection_name": "bikmo",
        "host": env_vars["WV_URL"],
        "api_key": env_vars["WV_CLIENT_SECRET"],
    }

# Fixture für die Suche
@pytest.fixture(name="search")
def search(llm_params, vdb_params):
    """Fixture for setting up the SearchVdB."""
    llm = BaseLlm(llm_params)
    vdb = WeaviateHandler(vdb_params)
    return SearchVdb(llm, vdb=vdb, search_mode="hybrid")

def test_analitiq_search(search):
    """Test the analitiq Search function."""
    user_prompt = "Please give me revenues by month."
    result_generator = search.arun(user_prompt)

    assert result_generator

    async def process_results():
        async for result in result_generator:
            if isinstance(result, str):
                assert result
            else:
                assert result

    asyncio.run(process_results())
