from typing import List, Dict, Any
import os
from pathlib import Path
import yaml
import logging
import logging.config


def yaml_parse(file: Path) -> dict:
    """Parse a yaml file."""
    if not file.exists():
        print(f"Config File not existing in {file}")
        return {}
    with open(file, "rt") as f:
        return yaml.safe_load(f) or {}

def check_environment(project_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check and set environment variables."""
    allowed_envs: List[str] = ["prod", "dev", "local"]
    env_var = project_config.get("environment") or os.getenv("ENVIRONMENT")

    if env_var not in allowed_envs:
        print("Environment not set or not valid. Setting to default = dev.")
        env_var = "dev"
        os.environ["ENVIRONMENT"] = env_var

    project_config["environment"] = env_var
    return project_config

def initialize_logging():
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

    def setup_logging(log_config: Dict[str, Any], log_dir: Path):
        """Update log file paths and configure logging."""
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        file_handlers = ["file", "chat_file"]
        for handler in file_handlers:
            if handler in log_config.get("handlers", {}):
                log_config["handlers"][handler]["filename"] = log_dir / log_config["handlers"][handler]["filename"]

        try:
            logging.config.dictConfig(log_config)
        except ValueError as e:
            logger.error("Error configuring logging: %s", e)
            raise

    log_config = yaml_parse(log_config_file_path)
    proj_config = yaml_parse(proj_config_file_path)

    if not proj_config:
        raise ValueError(f"proj_config is None. Check that project.yml file exists in {proj_config_file_path}.")


    _log_dir = base_dir / "logs"

    proj_config = check_environment(proj_config)

    setup_logging(log_config, _log_dir)

    # Get a logger object
    main_logger = logging.getLogger(proj_config["environment"])
    chat_logger = logging.getLogger("chat")

    return main_logger, chat_logger

# Explicitly export the logger
__all__ = ["initialize_logging"]
