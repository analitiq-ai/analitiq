import pytest
from libs.analitiq.agents.sql.sql import Sql
from libs.analitiq.base.Database import DatabaseWrapper
from libs.analitiq.base.llm.BaseLlm import BaseLlm
from libs.analitiq.vectordb.weaviate import WeaviateHandler


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
