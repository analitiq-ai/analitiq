# Profiles Configuration (`profiles.yml`) for Analitiq

The file `profiles.yml` has all of your sensitive connection information, such as your API keys and DB credentials, so treat it with respect. This file can be placed in one of the two locations:
1. in the `.analitiq` directory inside your users home directory
2. in the root directory of your project

We recommend the 1st option so it is out of the way and not accidentally picked up by `git`.
> **_NOTE:_**  If you choose to keep profiles.yml file in your project directory, make sure to add it to your gitignore.

## Sample File
Here is how the `profiles.yml` should look like:
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
## Sections
The sections present in the `profiles.yaml` are divided into 3 groups:
1. Database connections
2. LLM API connections
3. Vector Database connections

We first start with the name of the profile as a root identifier. In our example it is creatively named `test`. Each set of configurations begins under profile identifier.
At the next level, we put `connections`: This section is designed to establish and configure various types of connections.

### Databases
The `connections.databases` subsection configures database connections. Each connection is defined as a list item.
- `name`: Identifier for the connection.
- `type`: Defines the type of the database. In the provided example it's a postgres database.
- `host`: The hostname or IP address where the database is located.
- `user`: The username used to access the database.
- `password`: The password associated with the username.
- `port`: The port number to connect to the database.
- `db_name`: The name of the database to connect to.
- `db_schema`: A list containing the database schemas that can be used by Analitiq.
- `threads`: Number of threads to use.
- `keepalives_idle`: The idle interval before the connection is dropped. The default value is 240 seconds.
- `connect_timeout`: Connection timeout value in seconds. The default is 10 seconds.

### LLMs
The `connections.llms` section is used to configure different Large Language Model connections.

- `name`: The name of the llm connection.
- `type`: The type of service providing the llm, such as openai or mistral.
- `api_key`: The key used to authenticate with the service.
- `llm_model_name`: The specific model to be used, provided by the llm service.

### Vector Databases
The `connections.vector_dbs` section configures connections to vector databases.

- `name`: The name to identify the vector database connection.
- `type`: The type of service that provides vector databases.
- `host`: The host address of the vector database service.
- `api_key`: The API key for the vector databases service.
- `usage`: This section defines the default connections out of the many that were configured in the previous sections.
- `databases`: The name of the database connection to use by default.
- `llms`: The name of the llm connection to be used by default.
- `vector_dbs`: The name of the default vector database connection.

## Usage
The usage section specifies which db connection, LLM connection and vector database connection to use in a particular environment.
This way, you can have dedicated `profiles.yml` files in each of the local/dev/integr/prod environments and define which connection each environment uses in the `usage` section.
```yaml
  usage:
    databases: prod_dw
    llms: aws_llm
    vector_dbs: prod_vdb
```

## Example
Let's look at some examples. Let's say when I run Analitiq locally, I want to use OpenAI. And when I upload it to production server, I want to use Bedrock.
I will set up my connections in `profiles.yml` in the following way:
```yaml
prod:
  connections:
    databases:
      - name: prod_db
        type: postgres
        host: xxxx
        user: xxxx
        password: xxxx
        port: 5432
        dbname: postgres
        dbschema: sample_data
        threads: 4
        keepalives_idle: 240 # default 240 seconds
        connect_timeout: 10 # default 10 seconds
        # search_path: public # optional, not recommended
    
    llms:
      - name: aws_llm
        type: bedrock
        credentials_profile_name: bedrock
        region_name: eu-central-1
        provider: anthropic
        llm_model_name: anthropic.claude-v2
        temperature: 0.0
        aws_access_key_id: xxxxx
        aws_secret_access_key: xxxxx
  usage:
    databases: prod_db
    llms: aws_llm

local:
  connections:
    databases:
      - name: local_db
        type: postgres
        host: xxxx
        user: xxxx
        password: xxxx
        port: 5432
        dbname: postgres
        dbschema: sample_data
        threads: 4
        keepalives_idle: 240 # default 240 seconds
        connect_timeout: 10 # default 10 seconds
        # search_path: public # optional, not recommended

    llms:
      - name: openai_llm
        type: openai
        api_key: xxxx
        temperature: 0.0
        llm_model_name: gpt-3.5-turbo
  usage:
    databases: local_db
    llms: openai_llm
```

on my local machine, I would have `project.py` file with the following configuration
```yaml
name: 'analitiq'
version: '0.1'
profile: 'local'
config_version: 2
```
and the production server will have `project.py` file with the following configuration
```yaml
name: 'analitiq'
version: '0.1'
profile: 'prod'
config_version: 2
```

Now, I can move the project files between my prod environment and local and Analitiq will use different run configurations in each environment.
