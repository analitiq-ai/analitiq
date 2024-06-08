import time
from analitiq.logger import logger
import re
import yaml
from typing import Dict, Any

def retry(max_retries, wait_time):
    """
    Decorator to retry a function with specified maximum retries and wait time between retries.

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
                    result = func(*args, **kwargs, feedback=feedback) # Pass feedback to the function
                    return result
                except Exception as e:
                    logger.error(f"Retry {retries + 1} for {func.__name__} failed due to {e}")
                    feedback = f"\nCheck your output and make sure it conforms to instructions! Your previous response created an error:\n{str(e)}"  # Update feedback with the latest exception
                    retries += 1
                    time.sleep(wait_time)
            else:
                logger.info(f"Max retries of function {func} exceeded")
                raise Exception(f"Max retries of function {func} exceeded")
        return wrapper
    return decorator


def is_response_clear(response, chat_hist_exists):
    """
    Checks if the response is clear based on the provided response object and chat history existence.

    :param response: An object representing the response.
    :param chat_hist_exists: A boolean indicating if the chat history exists.
    :return: True if the response is clear, False otherwise.
    """
    if response.Clear:
        return True
    elif not response.Clear and not chat_hist_exists:
        return True

    return False

def extract_hints(text):
    """
    Extracts hints from the given text.

    :param text: The input text.
    :return: A tuple containing the cleaned prompt and the extracted hints.
    :rtype: tuple[str, str]
    """
    # Regular expression to find all instances of text within double square brackets
    pattern = r"\[\[(.*?)\]\]"

    # Find all matches and join them with a space
    hints = ' '.join(re.findall(pattern, text))

    # Remove the bracketed text from the original string
    cleaned_prompt = re.sub(pattern, '', text).strip()

    return cleaned_prompt, hints

def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Loads the configuration file.

    Parameters:
    - config_path (str): The path to the configuration YAML file.

    Returns:
    - List[Type]: A list of instantiated service classes.
    """
    # Create a Path object for the file you want to check
    if file_path.exists():
        with open(file_path, 'r') as f:
            configs = yaml.safe_load(f)
    else:
        raise FileNotFoundError(f"The file does not exist: {file_path}")

    return configs

def flatten(lst):
    """
    Flatten a nested list.

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
    return re.sub(r'\[\[.*?\]\]', '', text)


def split_list_of_ddl(ddl_list, max_chunk: int = 5000, seperator: str = ','):
    """
    Split List of DDL

    Split the given list of DDL (Data Definition Language) statements into chunks of columns without exceeding a maximum chunk size.

    :param ddl_list: The list of DDL statements to be split.
    :param max_chunk: The maximum size (in characters) of each chunk. Default is 5000.
    :param seperator: The separator used to combine the DDL statements into one large text string. Default is ','.
    :return: A list of chunks, each containing a subset of the columns.

    """
    # Combine all items into one large text string
    combined_text = seperator.join(ddl_list)

    # Split the combined text by commas to get individual columns
    columns = [col.strip() for col in combined_text.split(seperator)]

    # Create chunks of columns without exceeding max_chunk size
    chunks = []
    current_chunk = []
    current_chunk_size = 0

    for col in columns:
        col_length = len(col)

        # If adding this column exceeds max_chunk, start a new chunk
        if current_chunk_size + col_length > max_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_chunk_size = 0

        # Add the column to the current chunk
        current_chunk.append(col)
        current_chunk_size += col_length

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
