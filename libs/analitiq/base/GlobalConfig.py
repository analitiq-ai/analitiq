import logging
from typing import Dict, Any
import yaml
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from analitiq.base.ProfileLoader import ProfileLoader
from analitiq.base.ServicesLoader import ServicesLoader


class GlobalConfig:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """
        profile_configs will have the loaded profile configuration
        Example:
        {'databases': DatabaseConnection(type='postgres', name='prod_dw', host='rds.amazonaws.com', user='', password='', dbname='my_db'),
        'llms': LLMConnection(type='openai', name='prod_llm', api_key='11111', temperature=0.0, llm_model_name='gpt-3.5-turbo'),
        'vector_dbs': VectorDBConnection(type='weaviate', name='prod_vdb', host='https://1111-sandbox-ffff.weaviate.network', api_key='sk-11111')
        }

        """
        if not self._initialized:

            self.core_config = self.load_yaml(Path('analitiq/core_config.yml')) #this is analitiq project.yml
            self.project_config = self.load_yaml(Path('project.yml')) #this is the users project.yml

            # Load and validate the Profile configuration
            profile_loader = ProfileLoader(file_path='profiles.yml')
            self.profile_configs = profile_loader.load_and_validate_config(self.project_config['profile'])

            # Load Services
            self.services: Dict[str, Any] = {} #this is where project services from the yml will be stored
            serv_loader = ServicesLoader()
            # load core services
            self.services.update(serv_loader.load_services_from_config(self.core_config, self.services))
            # load custom services created by users, if they exist
            self.services.update(serv_loader.load_services_from_config(self.project_config, self.services))
            # get the available services from the defined directory
            logging.info(f"\n\nAvailable services:\n{self.services}")

            self.llm = self.set_llm(self.profile_configs['llms'])  # Placeholder for llm instance
            self.database = None
            #self.database = self.set_database()  # Placeholder for database instance
            self.vdb = None
            self._initialized = True

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        Loads the configuration file.

        Parameters:
        - config_path (str): The path to the configuration YAML file.

        Returns:
        - List[Type]: A list of instantiated service classes.
        """
        # Create a Path object for the file you want to check
        if file_path.exists():
            with open(file_path, 'r') as f:
                configs = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"The file does not exist: {file_path}")

        return configs

    def set_llm(self, profile):
        if profile.type == 'openai':
            from langchain_openai import ChatOpenAI
            logging.info(f"LLM is set to {profile.type}")
            return ChatOpenAI(openai_api_key=profile.api_key, temperature=profile.temperature, model_name=profile.llm_model_name)
        elif profile.type == 'mistral':
            from langchain_mistralai.chat_models import ChatMistralAI
            logging.info(f"LLM is set to {profile.type}")
            return ChatMistralAI(mistral_api_key=profile.llm_api_key)
        elif profile.type == 'bedrock':
            from langchain_community.llms import Bedrock
            logging.info(f"LLM is set to {profile.type}")
            return Bedrock(
                credentials_profile_name=profile.credentials_profile_name,
                provider=profile.provider,
                model_id=profile.llm_model_name,
                model_kwargs={"temperature": profile.temperature},
                streaming=False
            )

    def get_llm(self):
        return self.llm

    def set_database(self):
        profile = self.profile_configs['databases']
        if profile.type in ['postgres', 'redshift']:
            from analitiq.utils import db_utils
            db_engine = db_utils.create_db_engine('postgresql', 'psycopg2', profile.host, profile.port, profile.user, profile.password, profile.dbname, profile.dbschema)
            logging.info(f"Database is set to {profile.type}")
            return SQLDatabase(db_engine)
        else:
            print(f"Unsupported database type {profile.type}")

    def get_database(self):
        if self.database is None:
            self.database = self.set_database()

        return self.database

    def set_vdb(self, profile):

        if profile.type in ['weaviate']:
            from analitiq.storage.weaviate.weaviate_vs import WeaviateVS
            logging.info(f"VectorDB is set to {profile.type}")
            return WeaviateVS(self.get_project_name(), profile.host, profile.api_key)
        else:
            print(f"Unsupported Vector DB type {profile.type}")

    def get_vdb(self):
        return self.vdb

    def get_session_uuid_file(self):
        return self.project_config['config']['general']['session_uuid_file']

    def get_chat_log_dir(self):
        return self.project_config['config']['general']['chat_log_dir']

    def get_project_name(self):
        return self.project_config['name']

    def get_config_general_param(self, param_name):
        """
        Returns value of a configuration parameter from General configuration
        :param param_name:
        :return:
        """
        return self.project_config['config']['general'][param_name]

    def get_config_vectordb_param(self, param_name):
        """
        Returns value of a configuration parameter from vectordb configuration
        :param param_name:
        :return:
        """
        return self.project_config['config']['vectordb'][param_name]