"""Test the analitiq instances."""
import pytest
from analitiq.main import Analitiq

@pytest.fixture(name="analitiq_instance")
def analitiq_instance_fixture():
    """Return an Analitiq instance."""
    return Analitiq()

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
