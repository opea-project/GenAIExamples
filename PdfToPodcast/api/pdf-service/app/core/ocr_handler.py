import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OCRHandler:
    """
    Handle OCR processing for scanned/image-based PDFs
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR handler

        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        self.supported_languages = ['eng']  # Can be extended

    def extract_text_from_pdf(
        self,
        pdf_bytes: bytes,
        language: str = 'eng',
        dpi: int = 300
    ) -> Dict:
        """
        Extract text from scanned PDF using OCR

        Args:
            pdf_bytes: PDF file content as bytes
            language: OCR language (default: English)
            dpi: DPI for PDF to image conversion

        Returns:
            Dict with extracted text and metadata
        """
        try:
            logger.info(f"Starting OCR extraction with DPI={dpi}")

            # Convert PDF pages to images
            images = self._pdf_to_images(pdf_bytes, dpi=dpi)

            if not images:
                logger.error("No images extracted from PDF")
                return {
                    "text": "",
                    "method": "ocr_failed",
                    "metadata": {"error": "No images extracted"}
                }

            # Extract text from each page
            page_texts = []
            confidence_scores = []

            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing page {page_num}/{len(images)}")

                # Preprocess image
                processed_image = self._preprocess_image(image)

                # Extract text with confidence
                result = self._extract_with_confidence(
                    processed_image,
                    language=language
                )

                page_texts.append(result["text"])
                confidence_scores.append(result["confidence"])

            # Combine all pages
            full_text = "\n\n".join(page_texts)

            # Calculate average confidence
            avg_confidence = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores else 0
            )

            return {
                "text": full_text,
                "method": "ocr",
                "metadata": {
                    "pages": len(images),
                    "word_count": len(full_text.split()),
                    "character_count": len(full_text),
                    "avg_confidence": round(avg_confidence, 2),
                    "language": language,
                    "dpi": dpi,
                }
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {
                "text": "",
                "method": "ocr_failed",
                "metadata": {"error": str(e)}
            }

    def _pdf_to_images(self, pdf_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
        """
        Convert PDF pages to images

        Args:
            pdf_bytes: PDF content
            dpi: Resolution for conversion

        Returns:
            List of PIL Images
        """
        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='png',
                thread_count=4
            )
            logger.info(f"Converted PDF to {len(images)} images")
            return images

        except Exception as e:
            logger.error(f"PDF to image conversion failed: {str(e)}")
            return []

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results

        Args:
            image: PIL Image

        Returns:
            Processed PIL Image
        """
        try:
            # Convert to grayscale
            image = image.convert('L')

            # Increase contrast (simple thresholding)
            # This helps with poor quality scans
            from PIL import ImageEnhance

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            return image

        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            return image

    def _extract_with_confidence(
        self,
        image: Image.Image,
        language: str = 'eng'
    ) -> Dict:
        """
        Extract text with confidence score

        Args:
            image: PIL Image
            language: OCR language

        Returns:
            Dict with text and confidence
        """
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(image, lang=language)

            # Calculate average confidence
            confidences = [
                int(conf)
                for conf in data['conf']
                if conf != '-1'
            ]

            avg_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0
            )

            return {
                "text": text,
                "confidence": avg_confidence
            }

        except Exception as e:
            logger.error(f"OCR with confidence failed: {str(e)}")
            # Fallback to simple extraction
            try:
                text = pytesseract.image_to_string(image, lang=language)
                return {"text": text, "confidence": 0}
            except:
                return {"text": "", "confidence": 0}

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        language: str = 'eng'
    ) -> Dict:
        """
        Extract text from a single image

        Args:
            image_bytes: Image content as bytes
            language: OCR language

        Returns:
            Dict with extracted text and metadata
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            processed_image = self._preprocess_image(image)
            result = self._extract_with_confidence(processed_image, language)

            return {
                "text": result["text"],
                "method": "ocr",
                "metadata": {
                    "confidence": result["confidence"],
                    "language": language,
                    "word_count": len(result["text"].split()),
                }
            }

        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            return {
                "text": "",
                "method": "ocr_failed",
                "metadata": {"error": str(e)}
            }

    def is_tesseract_available(self) -> bool:
        """
        Check if Tesseract is installed and available

        Returns:
            True if Tesseract is available
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.error(f"Tesseract not available: {str(e)}")
            return False

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported OCR languages

        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.error(f"Could not get languages: {str(e)}")
            return self.supported_languages

    def detect_language(self, image: Image.Image) -> str:
        """
        Attempt to detect language in image

        Args:
            image: PIL Image

        Returns:
            Detected language code
        """
        try:
            # Tesseract can detect language
            osd = pytesseract.image_to_osd(image)

            # Parse OSD output for language
            for line in osd.split('\n'):
                if 'Script:' in line:
                    script = line.split(':')[1].strip()
                    logger.info(f"Detected script: {script}")

            return 'eng'  # Default to English

        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return 'eng'
