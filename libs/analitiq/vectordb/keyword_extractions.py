"""Functions for handling keyword extractions."""

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.data import find


def is_resource_downloaded(resource):
    """Check if resource is already downloaded."""
    try:
        find(resource)
        return True
    except LookupError:
        return False


# Check if 'punkt' and 'stopwords' are downloaded
punkt_downloaded = is_resource_downloaded("tokenizers/punkt")
stopwords_downloaded = is_resource_downloaded("corpora/stopwords")

# Download only if not already downloaded
if not punkt_downloaded:
    nltk.download("punkt")

if not stopwords_downloaded:
    nltk.download("stopwords")


def extract_keywords(text: str) -> str:
    """Extract keywords using nlp technologys."""
    tmp_text = text.replace("_", " ")
    tmp_text = word_tokenize(tmp_text.lower())
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tmp_text if word.isalnum() and word not in stop_words]

    # Stemming
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    return " ".join(set(tokens))


if __name__ == "__main__":
    text = "SELECT sum(revenue_last_year) FROM tblPayments"
    print(extract_keywords(text))
