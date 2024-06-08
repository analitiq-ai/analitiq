import logging
import sys

console = True  # Set this to True to enable console debugging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a console handler and set the level to DEBUG
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Create a file handler and set the level to INFO
file_handler = logging.FileHandler(filename='analitiq/latest_run.log', encoding='utf-8', mode='w')
file_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])', datefmt='%d/%m/%Y %I:%M:%S %p')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the console handler to the logger based on the debug parameter
debug = False  # Set this to True to enable console debugging
if debug:
    console_handler.setLevel(logging.DEBUG)
else:
    console_handler.setLevel(logging.INFO)

# Add the file handler to the logger
logger.addHandler(file_handler)

if console:
    # Add the console handler to the logger
    logger.addHandler(console_handler)

# Explicitly export the logger
__all__ = ['logger']