"""Functions for handling keyword extractions."""

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.data import find


def is_resource_downloaded(resource):
    """
    Checks if a resource has been downloaded.

    :param resource: The resource to be checked.
    :return: True if the resource has been downloaded, False otherwise.
    """
    try:
        find(resource)
        return True
    except LookupError:
        return False


punkt_downloaded = is_resource_downloaded("tokenizers/punkt")
stopwords_downloaded = is_resource_downloaded("corpora/stopwords")

if not punkt_downloaded:
    nltk.download("punkt")

if not stopwords_downloaded:
    nltk.download("stopwords")


def extract_keywords(text: str) -> str:
    """
    Extracts keywords from a provided text string.

    This function performs several transformations on the input text to isolate the most relevant keywords. The
    processing includes tokenization, removing any stop words from the English language (as defined by the NLTK corpus),
    and applying the Porter Stemming algorithm.

    Parameters:
    ----------
    text : str
        The input text from which to extract keywords.

    Returns:
    -------
    str
        The extracted keywords, returned as a space-separated string. In the case that the same keyword is extracted
        multiple times from the text, it is only included once in the output. The order of the keywords in the
        output does not reflect their original order in the input text.

    Example:
    -------
    >>> extract_keywords("This_ is a sample text, which has repeated text and some other_text...")
    'sampl text repeat'

    Notes:
    -----
    - Internally, underscores in the input string are replaced with spaces prior to tokenization.
    - Only alphanumeric tokens that do not appear in the NLTK English stop words list are considered keywords.
    - The Porter Stemming algorithm is applied to all potential keywords prior to inclusion in the final output string.

    """

    tmp_text = text.replace("_", " ")
    tmp_text = word_tokenize(tmp_text.lower())
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tmp_text if word.isalnum() and word not in stop_words]

    # Stemming
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    return " ".join(set(tokens))
