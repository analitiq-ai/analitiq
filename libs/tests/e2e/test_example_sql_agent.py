import pytest
from libs.analitiq.agents.sql.sql import Sql
from analitiq.factories.relational_database_factory import RelationalDatabaseFactory
from analitiq.factories.llm_factory import LlmFactory
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv


@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv(".env", override=True)


@pytest.fixture(name="sql_agent")
def sql_agent_fixture(db_params, llm_params, vdb_params):
    """Set up the sql Agent."""
    db = RelationalDatabaseFactory.create_database(db_params)
    llm = LlmFactory.create_llm(llm_params)
    vdb = VectorDatabaseFactory.create_database(vdb_params)
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
