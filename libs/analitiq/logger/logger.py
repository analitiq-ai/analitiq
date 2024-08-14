from typing import List, Dict, Any
import os
from pathlib import Path
import yaml
import logging.config
import logging

logger = logging.getLogger(__name__)

# Load the config file
# Get the directory of the current script
script_dir = Path(__file__).resolve().parent

# Get the base directory for Analitiq
base_dir = Path(__file__).resolve().parent.parent

# Get the base directory for project config
proj_config_dir = Path(__file__).resolve().parent.parent.parent

# Construct full path to the log config file
log_config_file_path = script_dir / "logger_config.yml"

# Construct full path to the project config file
proj_config_file_path = proj_config_dir / "project.yml"


def yaml_parse(file: Path) -> dict:
    """Parse a yaml file."""
    if not file.exists():
        logger.error("Config File not existing in %s", file)
        return {}
    with open(file, "rt") as f:
        cfg = yaml.safe_load(f.read())
    return cfg


def check_env_vars(project_config: Dict[str, Any]):
    """Check env Vars."""
    allowed_envs: List[str] = ["prod", "dev", "local"]
    env_var = ""
    if not proj_config.get("environment"):
        env_var = os.getenv("ENVIRONMENT")

    if env_var in allowed_envs:
        proj_config["environment"] = env_var
    else:
        logger.error("Environment not set or not valid. Setting to default = dev.")
        project_config["environment"] = "dev"
        os.environ["ENVIRONMENT"] = "dev"
    return proj_config


log_config = yaml_parse(log_config_file_path)
proj_config = yaml_parse(proj_config_file_path)

_log_dir = base_dir / "logs"

proj_config = check_env_vars(proj_config)


log_file_path = _log_dir / log_config.get("handlers").get("file").get("filename")
chat_log_file_path = os.path.join(_log_dir, log_config["handlers"]["chat_file"]["filename"])


log_config["handlers"]["file"]["filename"] = log_file_path
log_config["handlers"]["chat_file"]["filename"] = chat_log_file_path

# Configure the logging module with the config file
# logging.config.dictConfig(log_config)

# Get a logger object
logger = logging.getLogger(proj_config["environment"])
chat_logger = logging.getLogger("chat")

# Explicitly export the logger
__all__ = ["logger", "chat_logger"]
