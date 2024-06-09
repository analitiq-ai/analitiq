import logging
from typing import Dict, Any
from pathlib import Path

from analitiq.base.ProfileLoader import ProfileLoader
from analitiq.base.ServicesLoader import ServicesLoader
from analitiq.utils.general import load_yaml
from langchain_community.utilities import SQLDatabase

class GlobalConfig:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """

        """
        if not self._initialized:

            self.core_config = self.load_config('libs/analitiq/core_config.yml')  # this is analitiq project.yml
            self.project_config = self.load_config('libs/project.yml')  # this is the users project.yml
            self.profiles = self.load_config('libs/profiles.yml')  # this is the users profiles.yml

            # Load and validate the Profile configuration
            profile_loader = ProfileLoader(self.profiles)
            self.profile_configs = profile_loader._validate_config(self.project_config['profile'])

            # Load Services
            self.services: Dict[str, Any] = {} #this is where project services from the YAML will be stored
            serv_loader = ServicesLoader()

            # load core services
            self.services.update(serv_loader.load_services_from_config(self.core_config, self.services))

            # load custom services created by users, if they exist
            self.services.update(serv_loader.load_services_from_config(self.project_config, self.services))

            # get the available services from the defined directory
            logging.info(f"[Service][Available]\n{self.services}")

            self._initialized = True

    def load_config(self, file_path: str):
        try:
            path = Path(file_path).resolve()
            print(f"Trying to load config from: {path}")
            _config = load_yaml(Path(file_path))
            return _config
        except Exception as e:
            print(f"{file_path} not in home directory")
            print(e)
            exit()

    def get_log_dir(self):
        print(self.project_config['config']['general'])
        return self.project_config['config']['general']['chat_log_dir']

    def get_log_filename(self):
        return self.project_config['config']['general']['session_uuid_file']
        # return self.project_config['config']['general']['latest_run_filename']

    def get_vdb_client(self, profile):
        if profile.type in ['weaviate']:
            from analitiq.storage.weaviate.weaviate_vs import WeaviateVS
            logging.info(f"VectorDB is set to {profile.type}")
            return
        else:
            print(f"Unsupported Vector DB type {profile.type}")

    def get_session_uuid_file(self):
        return self.project_config['config']['general']['session_uuid_file']

    def get_chat_log_dir(self):
        return self.project_config['config']['general']['chat_log_dir']

    def get_project_config_param(self, param_name: str):
        return self.project_config[param_name]

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


