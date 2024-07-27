"""Functions for handling keyword extractions."""
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

nltk.download('punkt')
nltk.download('stopwords')

def extract_keywords(text: str) -> str:
    """Extract keywords using nlp technologys"""

    # split text by underscore
    tmp_text = text.replace("_", " ")
    tmp_text = word_tokenize(tmp_text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tmp_text if word.isalnum() and word not in stop_words]

    # Stemming
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    return " ".join(tokens)

if __name__ == '__main__':
    text = "SELECT sum(revenue_last_year) FROM tblPayments"
    print(extract_keywords(text))