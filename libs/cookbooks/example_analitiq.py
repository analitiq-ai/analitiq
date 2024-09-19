"""This is an example of how to query Analitiq for information."""

from analitiq.main import Analitiq

user_prompt = "Bikes"

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
        'collection_name': 'bikmo',
        'host': WV_URL,
        'api_key': WV_CLIENT_SECRET
    }
}

a = Analitiq(params)
agent_responses = a.run(user_prompt)

for response in agent_responses.values():
    if response:
        pass


