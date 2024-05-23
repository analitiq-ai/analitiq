import re
import json

class CodeExtractor:
    """
    Extracts code blocks from text that are fenced by triple backticks,
    according to a specified code language identifier.

    Methods:
        extract_code: Extracts the code block that matches a given language identifier.
    """

    def extract_code(self, text: str, code: str) -> str:
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
        try:
            match = re.search(pattern, text, re.DOTALL)
        except Exception as e:
            self.logger.error(f"Error extracting SQL from text: {str(e)}")

        if match and len(match.group(1).strip()) > 5:
            return match.group(1).strip()
        else:
            return None  # Return an empty string if no matching code block is found

    def CodeAndDictionaryExtractor(self, input_string):
        """
        :param input_string: a string containing the input data
        :return: a tuple indicating success of extraction and the extracted dictionary or an error message

        This method extracts the content between the first '{' and the last '}' in the given input string. It first searches for a substring enclosed in curly braces using regular expression
        * pattern matching. The extracted substring is then cleaned by replacing newline and tab characters with a space.

        If the cleaned substring can be successfully parsed as a JSON dictionary, the method returns a tuple with the first element being True indicating successful extraction, and the second
        * element being the parsed dictionary. If the parsing fails, the method returns a tuple with the first element being False indicating extraction failure, and the second element being
        * the error message.

        If no matching pattern is found in the input string, the method returns a tuple with the first element being False, and the second element being a "No matching pattern found." error
        * message.
        """

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
