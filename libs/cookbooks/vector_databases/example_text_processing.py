"""This is an example of how to load documents into VectorDB before allowing analitiq access them.
"""

import pathlib

from dotenv import load_dotenv

from analitiq.vectordb import keyword_extractions

load_dotenv()

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
FILE_DIR = pathlib.Path(CURRENT_DIR / "example_test_files")
FILES = [file for file in FILE_DIR.iterdir() if file.is_file()]
for file in FILES:
    with open(file, "r") as f:
        text = f.read()
    print(keyword_extractions.extract_keywords(text))
    print("----------------Done with it next --------------")
