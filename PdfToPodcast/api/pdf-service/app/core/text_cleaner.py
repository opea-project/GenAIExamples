import re
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Clean and preprocess extracted PDF text
    """

    def __init__(self):
        # Common header/footer patterns
        self.header_footer_patterns = [
            r'^\d+$',  # Page numbers
            r'^Page \d+',  # "Page N"
            r'^\d+ of \d+$',  # "1 of 10"
            r'^Copyright ©',  # Copyright notices
            r'^©\s*\d{4}',  # © 2024
            r'^All rights reserved',
            r'^\d{4}-\d{2}-\d{2}$',  # Dates in headers
        ]

        # Common noise patterns
        self.noise_patterns = [
            r'\[image:.*?\]',  # Image placeholders
            r'\[table:.*?\]',  # Table placeholders
            r'\x0c',  # Form feed characters
        ]

    def clean(self, text: str, aggressive: bool = False) -> str:
        """
        Clean extracted text

        Args:
            text: Raw extracted text
            aggressive: If True, apply more aggressive cleaning

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        try:
            # Step 1: Normalize whitespace
            text = self._normalize_whitespace(text)

            # Step 2: Remove headers and footers
            text = self._remove_headers_footers(text)

            # Step 3: Remove common noise patterns
            text = self._remove_noise(text)

            # Step 4: Fix hyphenation (words split across lines)
            text = self._fix_hyphenation(text)

            # Step 5: Remove extra line breaks
            text = self._normalize_paragraphs(text)

            # Step 6: Fix common OCR errors (if aggressive)
            if aggressive:
                text = self._fix_ocr_errors(text)

            # Step 7: Final cleanup
            text = text.strip()

            return text

        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text

    def _remove_headers_footers(self, text: str) -> str:
        """Remove common header and footer patterns"""
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Check if line matches header/footer patterns
            is_header_footer = False
            for pattern in self.header_footer_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    is_header_footer = True
                    break

            if not is_header_footer:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _remove_noise(self, text: str) -> str:
        """Remove noise patterns"""
        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text

    def _fix_hyphenation(self, text: str) -> str:
        """
        Fix words split across lines with hyphens

        Example: "under-\nstand" -> "understand"
        """
        # Match word-hyphen-newline-word pattern
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        return text

    def _normalize_paragraphs(self, text: str) -> str:
        """
        Normalize paragraph breaks

        - Single line breaks within paragraphs become spaces
        - Multiple line breaks become paragraph breaks
        """
        # Replace 3+ line breaks with placeholder
        text = re.sub(r'\n{3,}', '<<<PARAGRAPH>>>', text)

        # Replace single/double line breaks with space
        text = re.sub(r'\n{1,2}', ' ', text)

        # Restore paragraph breaks
        text = text.replace('<<<PARAGRAPH>>>', '\n\n')

        # Remove extra spaces
        text = re.sub(r' +', ' ', text)

        return text

    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors"""
        # Common OCR substitutions
        ocr_fixes = {
            r'\b0\b': 'O',  # Zero mistaken for O
            r'\bl\b': 'I',  # lowercase L mistaken for I
            r'\brn\b': 'm',  # rn mistaken for m
            r'\|': 'I',  # Pipe mistaken for I
        }

        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)

        return text

    def extract_sections(self, text: str) -> List[dict]:
        """
        Split text into logical sections based on headings

        Returns:
            List of sections with headings and content
        """
        sections = []
        lines = text.split('\n')

        current_section = {"heading": "Introduction", "content": []}

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # Check if line is a heading (simple heuristic)
            if self._is_heading(line_stripped):
                # Save previous section
                if current_section["content"]:
                    sections.append({
                        "heading": current_section["heading"],
                        "content": "\n".join(current_section["content"])
                    })

                # Start new section
                current_section = {"heading": line_stripped, "content": []}
            else:
                current_section["content"].append(line_stripped)

        # Add last section
        if current_section["content"]:
            sections.append({
                "heading": current_section["heading"],
                "content": "\n".join(current_section["content"])
            })

        return sections

    def _is_heading(self, line: str) -> bool:
        """Detect if a line is likely a heading"""
        # Heuristics for heading detection
        if not line:
            return False

        # All caps and short
        if line.isupper() and len(line.split()) <= 10:
            return True

        # Starts with number (e.g., "1. Introduction")
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True

        # Common heading words
        heading_keywords = [
            'Introduction', 'Conclusion', 'Abstract', 'Summary',
            'Chapter', 'Section', 'Background', 'Methods',
            'Results', 'Discussion', 'References'
        ]

        for keyword in heading_keywords:
            if line.startswith(keyword):
                return True

        return False

    def remove_references(self, text: str) -> str:
        """Remove references/bibliography section"""
        # Common reference section markers
        ref_markers = [
            'References', 'Bibliography', 'Works Cited',
            'REFERENCES', 'BIBLIOGRAPHY'
        ]

        lines = text.split('\n')
        ref_start_idx = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            for marker in ref_markers:
                if line_stripped == marker or line_stripped.startswith(marker):
                    ref_start_idx = i
                    break
            if ref_start_idx is not None:
                break

        # Remove everything after reference section
        if ref_start_idx is not None:
            lines = lines[:ref_start_idx]

        return '\n'.join(lines)

    def get_statistics(self, text: str) -> dict:
        """Get text statistics"""
        if not text:
            return {
                "word_count": 0,
                "character_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "avg_words_per_sentence": 0,
            }

        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')

        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraph_count = len([p for p in paragraphs if p.strip()])

        return {
            "word_count": word_count,
            "character_count": len(text),
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "avg_words_per_sentence": round(word_count / sentence_count, 2) if sentence_count > 0 else 0,
        }
