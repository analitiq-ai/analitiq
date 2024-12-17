# pylint: disable=redefined-outer-name

"""Test the docs Agent."""

import pytest
import asyncio
from analitiq.main import Analitiq
from analitiq.agents.search_vdb.vdb_agent import VDBAgent
from dotenv import load_dotenv

@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv("/Users/kirillandriychuk/Documents/Projects/analitiq-ai/.env", override=True)

@pytest.fixture(name="agent")
def agent_fixture(db_params, llm_params, vdb_params):
    """Set up the sql Agent."""
    params = {
        "db_params": db_params,
        "llm_params": llm_params,
        "vdb_params": vdb_params,
    }
    # Create agents
    agents = [
        VDBAgent(key="sql_1")
    ]

    return Analitiq(agents, params)

@pytest.mark.timeout(30)
def test_analitiq_agent(agent):
    """Test the sql agent e2e."""
    user_prompt = "catid"
    result = agent.run(user_prompt)

    assert result

    if isinstance(result, str):
        assert result


def test_analitiq_search_async(agent):
    """Test the analitiq Search function."""
    user_prompt = "catid"
    responses = agent.arun(user_prompt)

    assert responses

    async def process_results():
        async for response in responses:
            if isinstance(response, str):
                assert response
            else:
                assert response

    asyncio.run(process_results())
