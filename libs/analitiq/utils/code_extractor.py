import re
import json

class CodeExtractor:
    """
    Extracts code blocks from text that are fenced by triple backticks,
    according to a specified code language identifier.

    Methods:
        extract_code: Extracts the code block that matches a given language identifier.
    """

    def extract_code(self, code: str, text: str) -> str:
        """
        Extracts a code block from the provided text, based on the specified language.

        Args:
            code (str): A keyword that can be 'json', 'sql', or 'python', indicating
                        the type of code block to extract.
            text (str): The text containing the code block enclosed in triple backticks.

        Returns:
            str: The extracted code block as a string. If no matching block is found,
                 returns an empty string.

        Raises:
            ValueError: If the `code` parameter is not one of the expected keywords.
        """
        if code not in ['json', 'sql', 'python']:
            raise ValueError("Code parameter must be 'json', 'sql', or 'python'.")

        # Pattern to match code blocks that start with the specified code identifier
        pattern = rf"```{code}\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()
        else:
            return ""  # Return an empty string if no matching code block is found

    def CodeAndDictionaryExtractor(self, input_string):
        # Extract everything between the first { and the last }

        match = re.search(r'\{.*\}', input_string, re.DOTALL)
        if match:
            substring = match.group(0)
            # Remove newlines and tabs
            cleaned_string = substring.replace("\\n", " ").replace("\\t", " ")
            try:
                result_dict = json.loads(cleaned_string)
                return True, result_dict
            except json.JSONDecodeError as e:
                return False, str(e)
        else:
            return False, "No matching pattern found."
