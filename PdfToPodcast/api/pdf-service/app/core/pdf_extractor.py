import pypdf
import pdfplumber
import io
import logging
from typing import Dict, List, Tuple
from PIL import Image

logger = logging.getLogger(__name__)

class PDFExtractor:
    """
    Extract text and metadata from PDF files using multiple methods
    """

    def __init__(self):
        self.extraction_methods = [
            self._extract_with_pdfplumber,
            self._extract_with_pypdf2,
        ]

    def extract(self, pdf_bytes: bytes) -> Dict:
        """
        Extract text from PDF using the best available method

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Dict with extracted text, metadata, and extraction info
        """
        try:
            # Try pdfplumber first (best for complex layouts)
            result = self._extract_with_pdfplumber(pdf_bytes)

            # If no text found, try PyPDF2
            if not result["text"].strip():
                logger.warning("pdfplumber found no text, trying PyPDF2")
                result = self._extract_with_pypdf2(pdf_bytes)

            # Extract metadata
            metadata = self._extract_metadata(pdf_bytes)
            result["metadata"].update(metadata)

            return result

        except Exception as e:
            logger.error(f"Error extracting PDF: {str(e)}")
            raise

    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> Dict:
        """Extract text using pdfplumber (best for complex layouts)"""
        try:
            text_parts = []
            page_count = 0
            has_images = False
            tables_found = 0

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    # Check for images
                    if page.images:
                        has_images = True

                    # Extract tables if any
                    tables = page.extract_tables()
                    if tables:
                        tables_found += len(tables)
                        for table in tables:
                            # Convert table to text
                            table_text = self._table_to_text(table)
                            text_parts.append(table_text)

            full_text = "\n\n".join(text_parts)

            return {
                "text": full_text,
                "method": "pdfplumber",
                "metadata": {
                    "pages": page_count,
                    "has_images": has_images,
                    "tables_found": tables_found,
                    "word_count": len(full_text.split()),
                    "character_count": len(full_text),
                }
            }

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            return {"text": "", "method": "pdfplumber_failed", "metadata": {}}

    def _extract_with_pypdf2(self, pdf_bytes: bytes) -> Dict:
        """Extract text using PyPDF2 (fallback method)"""
        try:
            text_parts = []
            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(pdf_reader.pages)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)

            return {
                "text": full_text,
                "method": "pypdf2",
                "metadata": {
                    "pages": page_count,
                    "word_count": len(full_text.split()),
                    "character_count": len(full_text),
                }
            }

        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return {"text": "", "method": "pypdf2_failed", "metadata": {}}

    def _extract_metadata(self, pdf_bytes: bytes) -> Dict:
        """Extract PDF metadata"""
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            metadata = pdf_reader.metadata

            if metadata:
                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                }
            return {}

        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return {}

    def _table_to_text(self, table: List[List]) -> str:
        """Convert table data to formatted text"""
        if not table:
            return ""

        lines = []
        for row in table:
            # Filter out None values and join cells
            cells = [str(cell) if cell else "" for cell in row]
            line = " | ".join(cells)
            lines.append(line)

        return "\n".join(lines)

    def check_if_scanned(self, pdf_bytes: bytes) -> bool:
        """
        Check if PDF is likely a scanned document (image-based)

        Returns:
            True if PDF appears to be scanned (needs OCR)
        """
        try:
            # Extract text using both methods
            text_length = 0

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_length += len(text.strip())

            # If very little text extracted, likely scanned
            # Threshold: less than 50 characters per page on average
            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(pdf_reader.pages)

            avg_chars_per_page = text_length / page_count if page_count > 0 else 0

            return avg_chars_per_page < 50

        except Exception as e:
            logger.error(f"Error checking if scanned: {str(e)}")
            return False

    def extract_page_structure(self, pdf_bytes: bytes) -> List[Dict]:
        """
        Analyze document structure (headings, paragraphs)

        Returns:
            List of structured content blocks
        """
        try:
            structure = []

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text with layout info
                    words = page.extract_words()

                    if not words:
                        continue

                    # Group words into lines
                    lines = self._group_words_into_lines(words)

                    # Classify lines (heading, paragraph, etc.)
                    for line in lines:
                        block = {
                            "page": page_num,
                            "text": line["text"],
                            "type": self._classify_text_block(line),
                            "font_size": line.get("font_size", 0),
                        }
                        structure.append(block)

            return structure

        except Exception as e:
            logger.error(f"Structure extraction failed: {str(e)}")
            return []

    def _group_words_into_lines(self, words: List[Dict]) -> List[Dict]:
        """Group words into lines based on vertical position"""
        if not words:
            return []

        lines = []
        current_line = []
        current_y = words[0]["top"]
        tolerance = 5  # pixels

        for word in words:
            if abs(word["top"] - current_y) <= tolerance:
                current_line.append(word)
            else:
                if current_line:
                    lines.append({
                        "text": " ".join([w["text"] for w in current_line]),
                        "font_size": max([w.get("height", 0) for w in current_line]),
                        "y_position": current_y,
                    })
                current_line = [word]
                current_y = word["top"]

        # Add last line
        if current_line:
            lines.append({
                "text": " ".join([w["text"] for w in current_line]),
                "font_size": max([w.get("height", 0) for w in current_line]),
                "y_position": current_y,
            })

        return lines

    def _classify_text_block(self, line: Dict) -> str:
        """Classify text block as heading, paragraph, etc."""
        text = line["text"].strip()
        font_size = line.get("font_size", 0)

        # Simple heuristics
        if not text:
            return "empty"

        # Large font = likely heading
        if font_size > 14:
            return "heading"

        # All caps short text = likely heading
        if text.isupper() and len(text.split()) <= 10:
            return "heading"

        # Numbered or bulleted
        if text[0].isdigit() or text.startswith("•") or text.startswith("-"):
            return "list_item"

        return "paragraph"
