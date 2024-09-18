from analitiq.vectordb.keyword_extractions import extract_keywords


def test_extract_keywords():
    """Test if the function correctly extracts keywords."""
    text = "This is a test sentence for keyword extraction."
    expected_output = "test sentenc keyword extract"
    assert extract_keywords(text) == expected_output


def test_extract_keywords_empty_string():
    """Test if the function correctly handles an empty string."""
    text = ""
    expected_output = ""
    assert extract_keywords(text) == expected_output


def test_extract_keywords_no_keywords():
    """Test if the function correctly handles a string with no keywords."""
    text = "This is a test sentence with no keywords."
    expected_output = "test sentenc keyword"
    assert extract_keywords(text) == expected_output


def test_extract_keywords_with_punctuation():
    """Test if the function correctly handles a string with punctuation."""
    text = "This is a test sentence with punctuation!"
    expected_output = "test sentenc punctuat"
    assert extract_keywords(text) == expected_output


def test_extract_keywords_with_numbers():
    """Test if the function correctly handles a string with numbers."""
    text = "This is a test sentence with numbers 123."
    expected_output = "test sentenc number 123"
    assert extract_keywords(text) == expected_output


def test_extract_keywords_with_special_characters():
    """Test if the function correctly handles a string with special characters."""
    text = "This is a test sentence with special characters @#$."
    expected_output = "test sentenc special charact"
    assert extract_keywords(text) == expected_output