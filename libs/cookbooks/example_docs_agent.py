"""This is an example of how to search documents using search services."""

import os
from analitiq.factories.llm_factory import LlmFactory
from analitiq.agents.search_vdb.search_vdb import SearchVdb
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
import asyncio
from dotenv import load_dotenv
load_dotenv()

user_prompt = "bikes"

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

llm = LlmFactory.create_llm(llm_params)

vdb_params = {
    "type": "weaviate",
    "collection_name": "test",
    "host": os.getenv("WEAVIATE_URL"),
    "api_key": os.getenv("WEAVIATE_CLIENT_SECRET"),
}

vdb = VectorDatabaseFactory.create_database(vdb_params)

# Example of using the SQLGenerator class
agent = SearchVdb(llm, vdb=vdb, search_mode="hybrid")
result_generator = agent.arun(user_prompt)


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

