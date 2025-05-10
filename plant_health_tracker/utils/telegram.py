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
