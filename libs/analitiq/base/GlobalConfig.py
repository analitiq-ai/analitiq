from analitiq.logger.logger import logger
from typing import Dict, Any
from pathlib import Path
import os
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
        """ """
        if not self._initialized:
            self.project_config = self.load_config(
                "project.yml"
            )  # this is the users project.yml
            self.profiles: Dict = None
            self.profile_configs: Dict = None

            # Load Services
            serv_loader = ServicesLoader()

            # This is where project services from the YAML will be stored
            self.services: Dict[str, Any] = serv_loader.load_services_from_config(
                self.project_config
            )

            if not self.services:
                msg = "The 'Available Services' dictionary is empty!"
                raise ValueError(msg)

            # get the available services from the defined directory
            logger.info(f"[Services][Available] {self.services}")

            self._initialized = True

    def load_profiles(self):
        if not self.profiles:
            # check if the file is in .analitiq directory of the user
            home_dir = os.path.expanduser("~")
            filename = "profiles.yml"
            full_path = home_dir + f"/.analitiq/{filename}"

            if os.path.isfile(full_path):
                self.profiles = self.load_config(full_path)
            else:
                self.profiles = self.load_config(filename)

            # Load and validate the Profile configuration
            profile_loader = ProfileLoader(self.profiles)
            self.profile_configs = profile_loader._validate_config(
                self.project_config["profile"]
            )

    def load_config(self, file_path: str):
        try:
            path = Path(file_path).resolve()
            _config = load_yaml(Path(file_path))
            logger.info(f"Loaded config: {path}")
            return _config
        except Exception as e:
            logger.info(f"{file_path} not in home directory")
            raise e

    def get_log_dir(self):
        return self.project_config["config"]["general"]["log_dir"]

    def get_log_filename(self):
        return self.project_config["config"]["general"]["latest_run_filename"]

    def get_session_uuid_file(self):
        return self.project_config["config"]["general"]["session_uuid_file"]

    def get_chat_log_dir(self):
        return self.project_config["config"]["general"]["chat_log_dir"]
