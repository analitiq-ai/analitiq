# pylint: disable=redefined-outer-name

"""Test the docs Agent."""

import pytest
import asyncio
from analitiq.factories.llm_factory import LlmFactory
from libs.analitiq.agents.search_vdb.search_vdb import SearchVdb
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv

@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Load environment variables from .env file."""
    load_dotenv(".env", override=True)

@pytest.fixture(name="search")
def search(llm_params, vdb_params):
    """Fixture for setting up the SearchVdB."""
    llm = LlmFactory.create_llm(llm_params)
    vdb = VectorDatabaseFactory.create_database(vdb_params)
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
