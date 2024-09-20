"""This is an example of how to search documents using search services."""

import os


from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.agents.search_vdb.search_vdb import SearchVdb
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
import asyncio
from dotenv import load_dotenv

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_CLIENT_SECRET = os.getenv("WEAVIATE_CLIENT_SECRET")

LLM_MODEL_NAME=os.getenv("LLM_MODEL_NAME")
CREDENTIALS_PROFILE_NAME=os.getenv("CREDENTIALS_PROFILE_NAME")
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME=os.getenv("REGION_NAME")

if not WEAVIATE_URL or not WEAVIATE_CLIENT_SECRET:
    msg = "Environment Variables not set. Please set variables!"
    raise KeyError(msg)

user_prompt = "Please give me revenues by month."

llm_params = {"type": "bedrock"
    , "name": "aws_llm"
    , "api_key": None
    , "temperature": 0.0
    , "llm_model_name": LLM_MODEL_NAME
    , "credentials_profile_name": CREDENTIALS_PROFILE_NAME
    , "provider": "anthropic"
    , "aws_access_key_id": AWS_ACCESS_KEY_ID
    , "aws_secret_access_key": AWS_SECRET_ACCESS_KEY
    , "region_name": REGION_NAME}

llm = BaseLlm(llm_params)

vdb_params = {
    "type": "weaviate",
    "collection_name": "test",
    "host": WEAVIATE_URL,
    "api_key": WEAVIATE_CLIENT_SECRET,
}

vdb = VectorDatabaseFactory.create_database(vdb_params)

# Example of using the SQLGenerator class
agent = SearchVdb(llm, vdb=vdb, search_mode="hybrid")
result_generator = agent.arun("Bikes")


async def process_results():
    async for result in result_generator:
        if isinstance(result, str):
            print(result)
            pass  # Print incremental results
        else:
            print(result)
            pass  # Capture the final BaseResponse object


# Run the async function
asyncio.run(process_results())

