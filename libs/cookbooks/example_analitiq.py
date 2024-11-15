"""
This is an example of how to query Analitiq for information.

Connection parameters can be defined manually or save as Environmental Variables.

params = {
    'db_params': {
        'name': 'prod_dw',
        'type': 'redshift',
        'host': 'xxxx',
        'username': 'smy_user',
        'password': '1234455',
        'port': 5439,
        'db_name': 'my_db',
        'db_schemas': ['schema1', 'schema2'],
        'threads': 4,
        'keepalives_idle': 240,
        'connect_timeout': 10
    },
    'llm_params': {
        'type': 'bedrock',
        'name': 'aws_llm',
        'api_key': None,
        'temperature': 0.0,
        'llm_model_name': 'anthropic.claude-v2',
        'credentials_profile_name': 'my_profile',
        'provider': 'anthropic',
        'aws_access_key_id': 'xxxxxx',
        'aws_secret_access_key': 'xxxxxxx',
        'region_name': 'eu-central-1'
    },
    'vdb_params': {
        'type': 'weaviate',
        'collection_name': 'test',
        'host': 'host_url',
        'api_key': 'host_api_key'
    }
}
"""
import os
from analitiq.main import Analitiq
from dotenv import load_dotenv

load_dotenv()

params = {
    'db_params': {
        "name": os.getenv("DB_NAME"),
        "dialect": os.getenv("DB_DIALECT"),
        "host": os.getenv("DB_HOST"),
        "username": os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
        "port": os.getenv("DB_PORT"),
        "db_name": os.getenv("DB_DB_NAME"),
        "db_schemas": os.getenv("DB_SCHEMAS").split(","),
        "threads": int(os.getenv("DB_THREADS")),
        "keepalives_idle": int(os.getenv("DB_KEEPALIVES_IDLE")),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT"))
    },
    'llm_params': {
        'type': 'bedrock',
        'name': 'aws_llm',
        'api_key': None,
        'temperature': 0.0,
        'llm_model_name': os.getenv("LLM_MODEL_NAME"),
        'credentials_profile_name': os.getenv("CREDENTIALS_PROFILE_NAME"),
        'provider': 'anthropic',
        'aws_access_key_id': os.getenv("AWS_ACCESS_KEY_ID"),
        'aws_secret_access_key': os.getenv("AWS_SECRET_ACCESS_KEY"),
        'region_name': os.getenv("REGION_NAME")
    },
    'vdb_params': {
        'type': 'weaviate',
        "collection_name": os.getenv("WEAVIATE_COLLECTION"),
        "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
        'host': os.getenv("WEAVIATE_URL"),
        'api_key': os.getenv("WEAVIATE_CLIENT_SECRET")
    }
}

user_prompt = "Show me events by venue."

a = Analitiq(params)
agent_responses = a.run(user_prompt)

for response in agent_responses.values():
    if response:
        print(response)


