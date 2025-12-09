"""
Initialize utils module.
"""

from utils.logger import get_logger, setup_logging
from utils.pdf_handler import (
    create_cover_letter_pdf,
    extract_text_from_pdf,
    get_pdf_page_count,
    merge_pdfs,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "merge_pdfs",
    "extract_text_from_pdf",
    "get_pdf_page_count",
    "create_cover_letter_pdf",
]
