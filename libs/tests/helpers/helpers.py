import os
from typing import List


def check_env_vars(required_env_vars: List[str]):
    """Check if env vars are correctly set."""
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        msg = f"following Env vars are missing: {', '.join(missing_vars)}"
        raise KeyError(msg)
