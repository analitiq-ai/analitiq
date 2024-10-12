"""This is an example of how to search documents using search services."""

import os
import asyncio
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
    "collection_name": os.getenv("WEAVIATE_COLLECTION"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "host": os.getenv("WEAVIATE_URL"),
    "api_key": os.getenv("WEAVIATE_CLIENT_SECRET"),
}


async def main():

    params = {
        "llm_params": llm_params,
        "vdb_params": vdb_params
    }

    # Create agents
    agents = [
        VDBAgent(key="vdb_1")
    ]

    inst = Analitiq(agents, params)
    final_res = None

    # Call the async arun method and iterate over the yielded results
    async for res in inst.arun(user_query="catid"):
        if isinstance(res, dict):
            print(f"Intermediate result: {res}")
        else:
            print(f"Final results:")
            final_res = res

    # Process final results once after the async loop
    if final_res:
        for key, result in final_res.results.items():
            print(f"Results for key '{key}':")
            for result_type, value in result.items():
                if result_type == 'data' and isinstance(value, pd.DataFrame):
                    print(f"  {result_type}: {value.to_json(orient='split')}")
                else:
                    print(f"  {result_type}: {value}")


# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())


