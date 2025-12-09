"""
Utility functions for PDF operations.
"""

from pathlib import Path
from typing import Optional

import PyPDF2
from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def merge_pdfs(pdf_files: list[Path], output_path: Path) -> None:
    """
    Merge multiple PDF files into one.
    
    Args:
        pdf_files: List of PDF file paths
        output_path: Output merged PDF path
    """
    merger = PyPDF2.PdfMerger()
    
    for pdf_file in pdf_files:
        merger.append(str(pdf_file))
    
    merger.write(str(output_path))
    merger.close()
    
    logger.info(f"Merged {len(pdf_files)} PDFs into {output_path}")


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text from PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    
    return text


def get_pdf_page_count(pdf_path: Path) -> int:
    """
    Get number of pages in PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Number of pages
    """
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        return len(pdf_reader.pages)


def create_cover_letter_pdf(text: str, output_path: Path) -> None:
    """
    Create a simple PDF from cover letter text.
    
    Args:
        text: Cover letter text
        output_path: Output PDF path
    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Set font
    c.setFont("Helvetica", 11)
    
    # Write text with wrapping
    y_position = height - 72  # Start 1 inch from top
    max_width = width - 144  # 1 inch margins on each side
    
    lines = text.split('\n')
    for line in lines:
        # Simple word wrap
        words = line.split(' ')
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if c.stringWidth(test_line, "Helvetica", 11) < max_width:
                current_line = test_line
            else:
                c.drawString(72, y_position, current_line.strip())
                y_position -= 14
                current_line = word + " "
                
                # Check if we need a new page
                if y_position < 72:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y_position = height - 72
        
        if current_line:
            c.drawString(72, y_position, current_line.strip())
            y_position -= 14
    
    c.save()
    logger.info(f"Created cover letter PDF: {output_path}")
