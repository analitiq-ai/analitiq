"""This is an example of how to search documents using search services."""

import os
from analitiq.agents.search_vdb.vdb_agent import VDBAgent
from analitiq.main import Analitiq
from dotenv import load_dotenv
load_dotenv()


llm_params = {"type": "bedrock"
    , "name": "aws_llm"
    , "api_key": None
    , "temperature": 0.0
    , "llm_model_name": os.getenv("LLM_MODEL_NAME")
    , "credentials_profile_name": os.getenv("CREDENTIALS_PROFILE_NAME")
    , "provider": "anthropic"
    , "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID")
    , "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY")
    , "region_name": os.getenv("REGION_NAME")}


vdb_params = {
    "type": "weaviate",
    "collection_name": os.getenv("COLLECTION_NAME"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "host": os.getenv("VDB_HOST"),
    "api_key": os.getenv("VDB_API_KEY"),
}


if __name__ == "__main__":

    params = {
        "llm_params": llm_params,
        "vdb_params": vdb_params
    }

    # Create agents
    agents = [
        VDBAgent(key="vdb_1")
    ]

    inst = Analitiq(agents, params)

    # Run the pipeline
    response = inst.run(user_query="catid")

    sql = response.get_result_sql('vdb_1')
    text = response.get_result_text('vdb_1')
    result = response.get_result_data('vdb_1')

    if text:
        print(text)
    if sql:
        print(sql)
    if result:
        print(result)

