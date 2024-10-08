from typing import List, Dict, Any
import os
from pathlib import Path
import yaml
import logging.config

# Load the config file
# Get the directory of the current script
script_dir = Path(__file__).resolve().parent

# Get the base directory for Analitiq
base_dir = script_dir.parent

# Get the base directory for project config
proj_config_dir = base_dir.parent

# Construct full path to the log config file
log_config_file_path = script_dir / "logger_config.yml"

# Construct full path to the project config file
proj_config_file_path = proj_config_dir / "project.yml"


logger = logging.getLogger(__name__)

def yaml_parse(file: Path) -> dict:
    """Parse a yaml file."""
    if not file.exists():
        logger.error("Config File not existing in %s", file)
        return {}
    with open(file, "rt") as f:
        return yaml.safe_load(f) or {}


def check_env_vars(project_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check and set environment variables."""
    allowed_envs: List[str] = ["prod", "dev", "local"]
    env_var = project_config.get("environment") or os.getenv("ENVIRONMENT")

    if env_var not in allowed_envs:
        logger.error("Environment not set or not valid. Setting to default = dev.")
        env_var = "dev"
        os.environ["ENVIRONMENT"] = env_var

    project_config["environment"] = env_var
    return project_config


def setup_logging(log_config: Dict[str, Any], log_dir: Path):
    """Update log file paths and configure logging."""
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    log_config["handlers"]["file"]["filename"] = log_dir / log_config["handlers"]["file"]["filename"]
    log_config["handlers"]["chat_file"]["filename"] = log_dir / log_config["handlers"]["chat_file"]["filename"]

    logging.config.dictConfig(log_config)


log_config = yaml_parse(log_config_file_path)
proj_config = yaml_parse(proj_config_file_path)

if not proj_config:
    raise ValueError(f"proj_config is None. Check that project.yml file exists in {proj_config_file_path}.")

_log_dir = base_dir / "logs"
proj_config = check_env_vars(proj_config)

setup_logging(log_config, _log_dir)

# Get a logger object
logger = logging.getLogger(proj_config["environment"])
chat_logger = logging.getLogger("chat")

# Explicitly export the logger
__all__ = ["logger", "chat_logger"]