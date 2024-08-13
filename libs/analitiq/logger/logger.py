from typing import ClassVar, List
import os
from pathlib import Path
import yaml
import logging.config

class LoggerConfigurator:
    """A class to configure and setup loggers.

    Attributes
    ----------
        ALLOWED_ENVS (list): List of allowed environments.
        LOG_CONFIG_FILE_NAME (str): Name of the log config file.
        PROJ_CONFIG_FILE_NAME (str): Name of the project config file.

    """

    ALLOWED_ENVS: ClassVar[List[str]] = ["prod", "dev", "local"]
    LOG_CONFIG_FILE_NAME = "logger_config.yml"
    PROJ_CONFIG_FILE_NAME = "project.yml"

    def __init__(self, script_dir, base_dir, proj_config_dir):
        """Initialize the LoggerConfigurator."""
        self.script_dir = script_dir
        self.base_dir = base_dir
        self.proj_config_dir = proj_config_dir
        self.log_config = None
        self.proj_config = None
        self.logger = None
        self.chat_logger = None

    def load_configs(self):
        """Load the log and project configurations from their respective files."""
        log_config_file_path = os.path.join(self.script_dir, self.LOG_CONFIG_FILE_NAME)
        proj_config_file_path = os.path.join(self.proj_config_dir, self.PROJ_CONFIG_FILE_NAME)

        with open(log_config_file_path, "rt") as f:
            self.log_config = yaml.safe_load(f.read())

        with open(proj_config_file_path, "rt") as f:
            self.proj_config = yaml.safe_load(f.read())

    def set_environment(self):
        """Set the environment based on the project configuration or environment variable."""
        if not self.proj_config.get("environment"):
            env_var = os.getenv("ENVIRONMENT")

            if env_var in self.ALLOWED_ENVS:
                self.proj_config["environment"] = env_var
            else:
                msg = "Environment not set or not valid. Please set to one of {}".format(self.ALLOWED_ENVS)
                raise EnvironmentError(msg)

    def configure_log_paths(self):
        """Configure the log paths based on the log configuration and project directory."""
        _log_dir = os.path.join(self.base_dir, "logs")

        log_file_path = os.path.join(_log_dir, self.log_config["handlers"]["file"]["filename"])
        chat_log_file_path = os.path.join(_log_dir, self.log_config["handlers"]["chat_file"]["filename"])

        self.log_config["handlers"]["file"]["filename"] = log_file_path
        self.log_config["handlers"]["chat_file"]["filename"] = chat_log_file_path

    def configure_logging(self):
        """Configure the logging module based on the log configuration."""
        logging.config.dictConfig(self.log_config)

        self.logger = logging.getLogger(self.proj_config["environment"])
        self.chat_logger = logging.getLogger("chat")

    def get_loggers(self):
        """Return the configured loggers."""
        return self.logger, self.chat_logger

# Usage
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    base_dir = Path(__file__).resolve().parent.parent
    proj_config_dir = Path(__file__).resolve().parent.parent.parent.parent

    configurator = LoggerConfigurator(script_dir, base_dir, proj_config_dir)
    configurator.load_configs()
    configurator.set_environment()
    configurator.configure_log_paths()
    configurator.configure_logging()
    logger, chat_logger = configurator.get_loggers()