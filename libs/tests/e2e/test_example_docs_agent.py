"""Test the docs Agent."""

import pytest
import asyncio
from libs.analitiq.base.llm.BaseLlm import BaseLlm
from libs.analitiq.agents.search_vdb.search_vdb import SearchVdb
from libs.analitiq.vectordb.weaviate import WeaviateHandler

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
