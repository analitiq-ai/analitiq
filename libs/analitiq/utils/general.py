import time
from analitiq.logger.logger import initialize_logging
logger, chat_logger = initialize_logging()
import re

import yaml
from typing import Dict, Any

logger, chat_logger = initialize_logging()

def retry(max_retries, wait_time):
    """Decorator to retry a function with specified maximum retries and wait time between retries.

    :param max_retries: The maximum number of retries.
    :param wait_time: The wait time (in seconds) between retries.
    :return: The decorated function.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            feedback = None  # Initialize feedback with None

            while retries < max_retries:
                try:
                    result = func(*args, **kwargs, feedback=feedback)  # Pass feedback to the function
                    return result
                except Exception as e:
                    logger.error(f"Retry {retries + 1} for {func.__name__} failed due to {e}")
                    # Update feedback with the latest exception
                    feedback = (
                        f"\nCheck your output and make sure it conforms to instructions! "
                        f"Your previous response created an error:\n{e!s}"
                    )
                    retries += 1
                    time.sleep(wait_time)
            logger.info(f"Max retries of function {func} exceeded")
            msg = f"Max retries of function {func} exceeded"
            raise Exception(msg)

        return wrapper

    return decorator


def extract_hints(text):
    """Extract hints from the given text.

    :param text: The input text.
    :return: A tuple containing the cleaned prompt and the extracted hints.
    :rtype: tuple[str, str]
    """
    # Regular expression to find all instances of text within double square brackets
    pattern = r"\[\[(.*?)\]\]"

    # Find all matches and join them with a space
    hints = " ".join(re.findall(pattern, text))

    # Remove the bracketed text from the original string
    cleaned_prompt = re.sub(pattern, "", text).strip()

    return cleaned_prompt, hints


def load_yaml(file_path: str) -> Dict[str, Any]:
    """Load a YAML file and return the parsed configurations.

    :param file_path: The path to the YAML file.
    :return: A dictionary containing the loaded configurations.
    :raises ValueError: If the file is empty.
    :raises FileNotFoundError: If the file does not exist.
    """
    # Create a Path object for the file you want to check

    if file_path.exists():
        with open(file_path, "r") as f:
            configs = yaml.safe_load(f)
            if configs is None or configs == {}:
                msg = f"The file is empty: {file_path}"
                raise ValueError(msg)
    else:
        msg = f"The file does not exist: {file_path}"
        raise FileNotFoundError(msg)

    return configs


def flatten(lst):
    """Flatten a nested list.

    :param lst: The nested list to be flattened.
    :type lst: list
    :return: The flattened list.
    :rtype: list
    """
    output = []
    if isinstance(lst, list):
        for i in lst:
            if isinstance(i, list):
                output.extend(flatten(i))
            else:
                output.append(i)
    else:
        output.append(lst)

    return output


def remove_bracket_contents(text):
    return re.sub(r"\[\[.*?\]\]", "", text)
