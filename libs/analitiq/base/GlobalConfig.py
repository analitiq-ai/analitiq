import logging
from typing import Dict, Any
from pathlib import Path

from analitiq.base.ProfileLoader import ProfileLoader
from analitiq.base.ServicesLoader import ServicesLoader
from analitiq.utils.general import load_yaml

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

            self.core_config = self.load_config('analitiq/core_config.yml')  # this is analitiq project.yml
            self.project_config = self.load_config('project.yml')  # this is the users project.yml
            self.profiles = self.load_config('profiles.yml')  # this is the users project.yml

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
            _config = load_yaml(Path(file_path))
            print(f"Loaded config: {path}")
            return _config
        except Exception as e:
            print(f"{file_path} not in home directory")
            exit()

    def get_log_dir(self):
        return self.project_config['config']['general']['log_dir']

    def get_log_filename(self):
        return self.project_config['config']['general']['latest_run_filename']

    def get_session_uuid_file(self):
        return self.project_config['config']['general']['session_uuid_file']

    def get_chat_log_dir(self):
        return self.project_config['config']['general']['chat_log_dir']

