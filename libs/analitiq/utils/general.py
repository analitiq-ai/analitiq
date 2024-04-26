import time
import logging

def retry(max_retries, wait_time):
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
    if response.Clear:
        return True
    elif not response.Clear and not chat_hist_exists:
        return True

    return False


def retry_response(max_retries, check_response):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            feedback = None  # Initialize feedback with None

            while retries < max_retries:
                try:
                    result, chat_hist_exists = func(*args, **kwargs, feedback=feedback) # Pass feedback to the function
                    if check_response(result, chat_hist_exists):
                        return result
                    logging.error(f"Retry {retries + 1} for {func.__name__} failed due to result {str(result)}")
                    retries += 1
                except Exception as e:
                    logging.error(f"Retry {retries + 1} for {func.__name__} failed due to response format {e}")
                    feedback = f"\nCheck your output and make sure it conforms to instructions! Your previous response created an error:\n{str(e)}"  # Update feedback with the latest exception
                    retries += 1
            else:
                logging.warning(f"Max retries of function {func} exceeded")
                return result
        return wrapper
    return decorator

