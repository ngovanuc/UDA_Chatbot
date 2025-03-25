import re
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.utils.function_calling import convert_to_openai_tool


def convert_pydantic_models(pydantic_models: List) -> List:
    """
    Converts a list of Pydantic models to OpenAI tools and removes the 'parameters' field from each.

    Args:
        pydantic_models (List): A list of Pydantic models to be converted.

    Returns:
        List: A list of dictionaries representing the OpenAI tools without the 'parameters' field.
    """
    tools = []
    for function in pydantic_models:
        tools.append(convert_to_openai_tool(function))
    return tools


def preprocessing(text: str) -> str:
    """
    Preprocesses the input text by replacing all newline characters with spaces.

    Args:
        text (str): The input text to be preprocessed.

    Returns:
        str: The processed text with newline characters replaced by spaces.
    """
    text = text.replace("\n", " ")
    return text


def extract_text_from_pdf(file_path: str) -> str:
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    data = [preprocessing(d.page_content) for d in documents]
    return " ".join(data)


def remove_pattern_from_content(content: str, pattern: str) -> str:
    """
    Removes all occurrences of a specified pattern from the given content using a regular expression
    and returns the cleaned content with leading and trailing whitespace removed.

    Args:
        content (str): The original string content to be processed.
        pattern (str): The regular expression pattern to be removed from the content.

    Returns:
        str: The processed content with the specified pattern removed and leading/trailing whitespace stripped.
    """
    cleaned_content = re.sub(pattern, "", content)
    return cleaned_content.strip()


def is_valid_email(email):
    """Check if the email is a valid format."""

    # Regular expression for validating an Email

    regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$"

    # If the string matches the regex, it is a valid email
    match = re.match(regex, email)

    if match:
        return match.group()
    else:
        return None


# Hàm kiểm tra định dạng số điện thoại Việt Nam
def is_vietnamese_phone_number(text: str) -> Optional[str]:
    """
    Checks if the given text is a valid phone number.
    """
    phone_number_checker = r"(\+84|0084|0)[235789][0-9]{8}"
    match = re.search(phone_number_checker, text)
    if match:
        return match.group()
    else:
        return None
