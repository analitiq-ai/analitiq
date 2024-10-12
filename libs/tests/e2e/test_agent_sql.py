import pytest
from analitiq.agents.sql.sql_agent import SQLAgent
from analitiq.main import Analitiq
from dotenv import load_dotenv


@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv(".env", override=True)


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
        SQLAgent(key="sql_1")
    ]

    return Analitiq(agents, params)

@pytest.mark.timeout(30)
def test_analitiq_agent(agent):
    """Test the sql agent e2e."""
    user_prompt = "show me sales by venue."
    response = agent.run(user_prompt)

    assert response

    if isinstance(response, str):
        assert response

