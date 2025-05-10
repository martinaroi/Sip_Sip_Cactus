import re
from typing import Optional

def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2 format.
    
    Args:
        text (str): Text to escape
        
    Returns:
        str: Escaped text safe for MarkdownV2
    """
    # Characters that must be escaped in MarkdownV2
    SPECIAL_CHARS = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', 
                    '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = text
    for char in SPECIAL_CHARS:
        escaped_text = escaped_text.replace(char, f"\\{char}")
    return escaped_text

import unicodedata
def preprocess_string(text):
            """
            Preprocess text by removing diacritics and normalizing for comparison.
            
            Args:
                text (str): Input text to preprocess
            
            Returns:
                str: Normalized text without diacritics
            """
            # Normalize unicode characters and remove diacritics
            normalized = unicodedata.normalize('NFKD', text)
            # Remove non-ASCII characters (this will remove diacritics)
            ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
            # Convert to lowercase for case-insensitive comparison
            return ascii_text.lower().strip()