import os
from pathlib import Path
import yaml
import logging.config

allowed_envs = ["prod", "dev", "local"]

# Load the config file
# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Get the base directory for Analitiq
base_dir = Path(__file__).resolve().parent.parent

# Get the base directory for project config
proj_config_dir = Path(__file__).resolve().parent.parent.parent

# Construct full path to the log config file
log_config_file_path = os.path.join(script_dir, "logger_config.yml")

# Construct full path to the project config file
proj_config_file_path = os.path.join(proj_config_dir, "project.yml")


with open(log_config_file_path, "rt") as f:
    log_config = yaml.safe_load(f.read())

with open(proj_config_file_path, "rt") as f:
    proj_config = yaml.safe_load(f.read())

if not proj_config.get("environment"):
    env_var = os.getenv("ENVIRONMENT")

    if env_var in allowed_envs:
        proj_config["environment"] = env_var
    else:
        raise EnvironmentError(
            "Environment not set or not valid. Please set to one of {}".format(allowed_envs)
        )

_log_dir = os.path.join(base_dir, "logs")

log_file_path = os.path.join(_log_dir, log_config["handlers"]["file"]["filename"])
chat_log_file_path = os.path.join(_log_dir, log_config["handlers"]["chat_file"]["filename"])

print(f"Log file path: {log_file_path}")
print(f"Log file path for chat: {chat_log_file_path}")

log_config["handlers"]["file"]["filename"] = log_file_path
log_config["handlers"]["chat_file"]["filename"] = chat_log_file_path

# Configure the logging module with the config file
logging.config.dictConfig(log_config)

# Get a logger object
logger = logging.getLogger(proj_config["environment"])
chat_logger = logging.getLogger("chat")

# Explicitly export the logger
__all__ = ["logger", "chat_logger"]
