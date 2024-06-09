from analitiq.logger import logger
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

<<<<<<< HEAD
            self.core_config = self.load_config('libs/analitiq/core_config.yml')  # this is analitiq project.yml
            self.project_config = self.load_config('libs/project.yml')  # this is the users project.yml
            self.profiles = self.load_config('libs/profiles.yml')  # this is the users profiles.yml
=======
            self.project_config = self.load_config('project.yml')  # this is the users project.yml
            self.profiles: Dict = None
            self.profile_configs: Dict = None

            # Load Services
            serv_loader = ServicesLoader()

            # This is where project services from the YAML will be stored
            self.services: Dict[str, Any] = serv_loader.load_services_from_config(self.project_config)

            # get the available services from the defined directory
            logger.info(f"[Services][Available] {self.services}")

            self._initialized = True

    def load_profiles(self):
        if not self.profiles:
            self.profiles = self.load_config('profiles.yml')  # this is the users project.yml
>>>>>>> c7c08acdbcba4904187810782f616754c92535a6

            # Load and validate the Profile configuration
            profile_loader = ProfileLoader(self.profiles)
            self.profile_configs = profile_loader._validate_config(self.project_config['profile'])

    def load_config(self, file_path: str):
        try:
            path = Path(file_path).resolve()
            _config = load_yaml(Path(file_path))
            logger.info(f"Loaded config: {path}")
            return _config
        except Exception as e:
<<<<<<< HEAD
            print(f"{file_path} not in home directory")
            print(e)
            exit()
=======
            logger.info(f"{file_path} not in home directory")
            raise e
>>>>>>> c7c08acdbcba4904187810782f616754c92535a6

    def get_log_dir(self):
        print(self.project_config['config']['general'])
        return self.project_config['config']['general']['chat_log_dir']

    def get_log_filename(self):
        return self.project_config['config']['general']['session_uuid_file']
        # return self.project_config['config']['general']['latest_run_filename']

    def get_session_uuid_file(self):
        return self.project_config['config']['general']['session_uuid_file']

    def get_chat_log_dir(self):
        return self.project_config['config']['general']['chat_log_dir']

