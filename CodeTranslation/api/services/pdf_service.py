"""
PDF Code Extraction Service
Extracts code snippets from PDF documents
"""

import logging
import re
from pathlib import Path
from typing import List
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_code_from_pdf(pdf_path: str) -> str:
    """
    Extract code content from a PDF file

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted code as string

    Raises:
        Exception if PDF cannot be processed
    """
    try:
        logger.info(f"Extracting code from PDF: {pdf_path}")

        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            num_pages = len(pdf_reader.pages)

            logger.info(f"PDF has {num_pages} pages")

            # Extract text from all pages
            all_text = ""
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                all_text += text + "\n"

            logger.info(f"Extracted {len(all_text)} characters from PDF")

            # Try to identify and extract code blocks
            # Look for common code patterns
            code_content = extract_code_patterns(all_text)

            if not code_content.strip():
                # If no code patterns found, return all text
                code_content = all_text

            logger.info(f"Extracted code content: {len(code_content)} characters")

            return code_content.strip()

    except Exception as e:
        logger.error(f"Error extracting code from PDF: {str(e)}", exc_info=True)
        raise Exception(f"Failed to extract code from PDF: {str(e)}")


def extract_code_patterns(text: str) -> str:
    """
    Extract code patterns from text

    Args:
        text: Text content to search

    Returns:
        Extracted code snippets
    """
    # Look for code between common delimiters
    code_blocks = []

    # Pattern 1: Code between ``` markers
    markdown_code = re.findall(r'```[\w]*\n(.*?)\n```', text, re.DOTALL)
    code_blocks.extend(markdown_code)

    # Pattern 2: Indented code blocks (4+ spaces)
    indented_code = re.findall(r'(?:^    .+$)+', text, re.MULTILINE)
    code_blocks.extend(indented_code)

    # Pattern 3: Code with common keywords (class, def, function, etc.)
    keyword_patterns = [
        r'(?:public|private|protected)?\s*class\s+\w+.*?\{.*?\}',  # Java/C++ classes
        r'def\s+\w+\(.*?\):.*?(?=\n(?!\s))',  # Python functions
        r'function\s+\w+\(.*?\)\s*\{.*?\}',  # JavaScript functions
        r'fn\s+\w+\(.*?\)\s*\{.*?\}',  # Rust functions
        r'func\s+\w+\(.*?\)\s*\{.*?\}',  # Go functions
    ]

    for pattern in keyword_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        code_blocks.extend(matches)

    if code_blocks:
        return '\n\n'.join(code_blocks)

    # If no patterns match, return original text
    return text


def validate_pdf_file(filename: str, file_size: int, max_size: int) -> None:
    """
    Validate uploaded PDF file

    Args:
        filename: Name of the file
        file_size: Size of the file in bytes
        max_size: Maximum allowed file size in bytes

    Raises:
        ValueError if validation fails
    """
    # Check file extension
    if not filename.lower().endswith('.pdf'):
        raise ValueError("Only PDF files are allowed")

    # Check file size
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValueError(f"File too large. Maximum size is {max_size_mb}MB")

    if file_size == 0:
        raise ValueError("Empty file uploaded")

    logger.info(f"PDF file validation passed: {filename} ({file_size / 1024:.2f} KB)")