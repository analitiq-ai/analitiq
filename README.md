# Analitiq
Analitiq is a Framework for managin your data using LLMs. Analitiq can be extended with your own services written in python. These custom services can address your unique tasks for managing your data and they can function as part of the overall analytical engine of Analitiq.
![image](assets/images/Analitiq_Diagram.png)

Analitiq currently supports the following LLM models
- ChatGPT
- Mistral
- Bedrock (AWS)

Analitiq currently integrates with the following vectorDBs
- Weaviate
- ChromaDB
## Quick Start
1. Clone the repo
2. Set up `profiles.yml` in root directory. The file `profiles.yml` has all of your sensitive info, such as your API keys and DB credentials, so treat it with respect. Under `uses` you can define which connections should be used for the current deployment. 
Ideally, you would have different `profiles.yml` for your prod and dev instances.
```yaml
test:
  connections:
    databases:
      - name: prod_dw
        type: postgres
        host: xxxxx
        user: xxxx
        password: 'xxxxx'
        port: 5432
        dbname: sample_db
        dbschema: sample_schema
        threads: 4
        keepalives_idle: 240 # default 240 seconds
        connect_timeout: 10 # default 10 seconds
        # search_path: public # optional, not recommended
    llms:
      - name: prod_llm
        type: openai
        api_key: xxxxxx
        temperature: 0.0
        llm_model_name: gpt-3.5-turbo
      - name: dev_llm
        type: mistral
        api_key: xxxxxx
      - name: aws_llm
        type: bedrock
        credentials_profile_name: my_profile
        provider: anthropic
        llm_model_name: anthropic.claude-v2:1
        temperature: 0.0
    vector_dbs:
      - name: prod_vdb
        type: weaviate
        host: example.com
        api_key: xxxxx

  usage:
    databases: prod_dw
    llms: aws_llm
    vector_dbs: prod_vdb
```
3. Set up `project.yml` in root directory. The file `project.yml` has all of your project data, such as where the logs are stored. Most importantly, `project.yml` defines where your custom Services are located so Analitiq can pick them up and use them to manage your data.
```yaml
name: 'analitiq'
version: '0.1'
profile: 'test'
config_version: 2

config:
  general:
    chat_log_dir: "chats" # this is where we save our chat logs.
    sql_dir: "analysis" # this is where the ETL SQLs are being saved and managed
    services_dir: "custom_services"
    session_uuid_file: 'session_uuid.txt' # Where session identifier is being recorded. When session is reset, it is like beginning of a new chat topic and new log file will be created.
    target_path: "target"
    message_lookback: 5 # when LLM has no clue about users request, or users request relates to some item in chat history, how far back (in number of messages) should the LLM look in the current session chat log
  vectordb:
    doc_chunk_size: 2000
    doc_chunk_overlap: 200

services:
  - name: ChartService
    description: "Use this service to generate script for APEX charts to visualize data"
    path: "custom_services/chart/chart.py"
    class: "Chart"
    method: "run"
    inputs: "dataframe as serialized json"
    outputs: "javascript that is used by the frontend to visualize data"
```
5. Run the example file `example.py` (located in the root directory.)

## UI
The app interface can be extended with a UI, such as streamlit app.
![image](assets/images/query.png)