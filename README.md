# App Deployment
This chat app for ChatGPT has a frontend in React and a backend in Python using FastApi to communicate with the front end.
- Frontend is all in directory `/frontend`
- Backend is all in the directory `/app`

The app is running in Docker so docker-compose is available in the home directory of the app.

## First Time / One-Time Setup
Note: the python requirements.txt lists CUDA as a required package. CUDA supports only Intel-based GPUs. So, installing on a Mac will lead to some hardware incompatibility issues.

### Install Git
On a fresh EC2 instance, install requirements with the following commands:

```bash
# install Git
sudo yum update -y
sudo yum install git -y
git --version # verify Git installation

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo chkconfig docker on # make Docker auto-start
sudo usermod -a -G docker ec2-user
docker --version # verify Docker installation

# Install Docker Compose
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version # verify Docker Compose installation
```

### GitHub PAT Token

To authenticate with GitHub, create a Personal Identification Token (PAT) in your GitHub settings.

If the PAT token is expired, update the remote URL using the new PAT token:
```
git remote set-url origin https://<username>:<NEW_PAT_TOKEN>@github.com/key2market/analitiq.git
```

### Cloning the Repo
```
git clone --branch dev https://{YOUR USERNAME}:{PAT}@github.com/key2market/analitiq analitiq
```

## ENV Variables
Before building the docker image, we need to set up some environmental variables needed by the app. The `.env` file should reside in the root directory. The root directory also has an `.env.template` file which can be copied and used as a template.

### Required Variables
The following variables from `.env` file are essential for the app's core function and should be set up before Docker is built:
- ENVIRONMENT=dev
- HOST={IP OF THE HOST} 
- OPENAI_API_KEY={KEY}
- FASTAPI_HOST=localhost
- FASTAPI_PORT={PORT}
- SECRET_KEY=XXXX
- ALGORITHM=HS256
- ACCESS_TOKEN_EXPIRE_MINUTES=30
- CHROMA_DB_HOST={IP}
- CHROMA_DB_PORT={PORT}
- VECTOR_STORE_CONTEXT_COLLECTION=table-schema
- EMBEDDING_MODEL=local:sentence-transformers/all-MiniLM-L6-v2

The app uses a centralised Postgres server sitting on AWS RDS, however, for local testing, it is fine to deploy a local Postgres db and fill in the parameters for the local server
- POSTGRES_USER=
- POSTGRES_PASSWORD=
- POSTGRES_DB=
- POSTGRES_HOST=
- POSTGRES_PORT=

### Optional Variables
Some variables in the `.env` file are not required for local development and are only needed for the production environment. They can be left blank:
- MAIL_USERNAME= 
- MAIL_PASSWORD=
- MAIL_FROM=
- MAIL_PORT=
- MAIL_SERVER=
- MAIL_STARTTLS=FALSE
- MAIL_SSL_TLS=True

- AWS_REGION=
- AWS_ACCESS_KEY_ID=
- AWS_SECRET_ACCESS_KEY=
- AWS_SESSION_TOKEN=
- AWS_SAGEMAKER_LLM_ENDPOINT=
- AWS_SAGEMAKER_LLM_ENDPOINT_COMP_NAME=


### Build Docker
After the `.env` file has been set up properly, the app can be deployed:
```
docker-compose up -d # run in background mode
```

### Add DB Connection
One of the functions of the app is to connect to a database and query data.
Once a new user is created or a user signs in, if there is no DB connection saved for the user from a previous session, the app will ask for DB credentials.
![image](assets/images/db_connection.png)

you can use the following connections for sample DB
- POSTGRES_HOST=analitiq-db.cw1g0qte5un7.eu-central-1.rds.amazonaws.com
- POSTGRES_PORT=5432
- POSTGRES_USER=analitiq_pg
- POSTGRES_PASSWORD=yNgjV9mrJsCFGRAFV345e5v
- POSTGRES_DB=postgres

### Query the Data
Once the DB connection has been set up, you can query the Analyst.
![image](assets/images/query.png)


