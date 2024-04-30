import time
import logging
import re

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
                    logging.error(f"Retry {retries + 1} for {func.__name__} failed due to {e}")
                    feedback = f"\nCheck your output and make sure it conforms to instructions! Your previous response created an error:\n{str(e)}"  # Update feedback with the latest exception
                    retries += 1
                    time.sleep(wait_time)
            else:
                logging.info(f"Max retries of function {func} exceeded")
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
