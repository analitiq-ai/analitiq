"""Test the analitiq instances."""

import pytest
from analitiq.main import Analitiq
from dotenv import load_dotenv

@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv(".env", override=True)


@pytest.fixture(name="analitiq_instance")
def analitiq_instance_fixture(db_params, llm_params, vdb_params):
    """Return an Analitiq instance."""
    params = {
        "db_params": db_params,
        "llm_params": llm_params,
        "vdb_params": vdb_params,
    }
    return Analitiq(params)


@pytest.fixture(name="user_prompt")
def user_prompt_fixture():
    """Create a dummy User Prompt."""
    return "Bikes"


def test_analitiq_response(analitiq_instance, user_prompt):
    """Test the analitiq Response."""
    agent_responses = analitiq_instance.run(user_prompt)
    assert agent_responses

    for response in agent_responses.values():
        assert response
