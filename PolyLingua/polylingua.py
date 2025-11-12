# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import os
import tempfile
from pathlib import Path

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from fastapi import File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from langdetect import LangDetectException, detect

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "swiss-ai/Apertus-8B-Instruct-2509")

# Language code to name mapping
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ar": "Arabic",
    "hi": "Hindi",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "sv": "Swedish",
}

# Text formats that can be read directly (no conversion needed)
TEXT_FORMATS = {".txt", ".md", ".markdown", ".rst", ".log", ".csv"}

# Document formats that require docling conversion
DOCUMENT_FORMATS = {".docx", ".html"}

# All supported extensions
SUPPORTED_EXTENSIONS = TEXT_FORMATS | DOCUMENT_FORMATS

# Maximum file size (20MB)
MAX_FILE_SIZE = 20 * 1024 * 1024


class DocumentProcessor:
    """Handles document processing using docling for various file formats."""

    def __init__(self):
        # Initialize document converter for office documents
        self.converter = DocumentConverter()

    async def process_file(self, file: UploadFile) -> list[str]:
        """Process an uploaded file and extract text content in chunks.

        Args:
            file: The uploaded file

        Returns:
            List of text chunks (each chunk as markdown string)

        Raises:
            ValueError: If file type is not supported or file is too large
        """
        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum limit of {MAX_FILE_SIZE / 1024 / 1024}MB")

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {file_ext}. " f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        page_texts = []
        CHUNK_SIZE = 8000  # ~2000 words per chunk

        # Handle plain text files (fast path - no conversion needed)
        if file_ext in TEXT_FORMATS:
            print(f"Reading text file {file.filename}...")
            try:
                # Try UTF-8 first
                text_content = contents.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1 for other encodings
                print("UTF-8 decode failed, trying latin-1...")
                text_content = contents.decode("latin-1")

            print(f"Read {len(text_content)} characters from text file")

            # Split into chunks if needed
            if len(text_content) > CHUNK_SIZE:
                print(f"Splitting into chunks of {CHUNK_SIZE} chars")
                for i in range(0, len(text_content), CHUNK_SIZE):
                    chunk = text_content[i : i + CHUNK_SIZE]
                    page_texts.append(chunk)
                    print(f"Chunk {len(page_texts)}: {len(chunk)} chars")
            else:
                page_texts.append(text_content)
                print(f"Single chunk: {len(text_content)} chars")

            print(f"Total chunks: {len(page_texts)}")
            return page_texts

        # Handle document files (DOCX, HTML - requires docling conversion)
        if file_ext in DOCUMENT_FORMATS:
            # Save file temporarily for docling
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(contents)
                tmp_path = tmp_file.name

            try:
                # Convert document using docling
                print(f"Converting document {file.filename}...")
                result = self.converter.convert(tmp_path)
                print("Conversion completed")

                # Export entire document to markdown
                full_markdown = result.document.export_to_markdown()
                print(f"Extracted {len(full_markdown)} characters from document")

                # Split into chunks for translation
                if len(full_markdown) > CHUNK_SIZE:
                    print(f"Splitting into chunks of {CHUNK_SIZE} chars")
                    # Split into manageable chunks
                    for i in range(0, len(full_markdown), CHUNK_SIZE):
                        chunk = full_markdown[i : i + CHUNK_SIZE]
                        page_texts.append(chunk)
                        print(f"Chunk {len(page_texts)}: {len(chunk)} chars")
                else:
                    # Small enough to translate as single chunk
                    page_texts.append(full_markdown)
                    print(f"Single chunk: {len(full_markdown)} chars")

                print(f"Total chunks: {len(page_texts)}")
                return page_texts

            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)

        # Should never reach here due to extension check above
        raise ValueError(f"Unsupported file type: {file_ext}")


class PolyLinguaService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.TRANSLATION)
        self.doc_processor = DocumentProcessor()

    def add_remote_service(self):
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(llm)

    async def translate_page(self, page_text: str, language_from: str, language_to: str) -> str:
        """Translate a single page of text by consuming streaming response."""
        prompt_template = """
            You are a translation assistant who is specialized in translating {language_from} to {language_to}.

            1. Answer should only contain the translation of the source language to the target language.
            2. Do not include any other text or information.
            3. Do not include any other language than the target language.
            4. Do not include any other information than the translation.

            Translate this from {language_from} to {language_to}:

            {source_language}

        """
        prompt = prompt_template.format(language_from=language_from, language_to=language_to, source_language=page_text)

        # Create chat completion request with streaming
        chat_request_dict = {
            "model": LLM_MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
            "stream": True,
        }

        result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs=chat_request_dict)

        # Find the LLM service response
        for node, response in result_dict.items():
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LLM
            ):
                # Consume the streaming response
                accumulated_text = ""

                # Get the response body iterator
                async for chunk in response.body_iterator:
                    chunk_str = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk

                    # Parse SSE format
                    lines = chunk_str.split("\n")
                    for line in lines:
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix

                            if data == "[DONE]":
                                continue

                            try:
                                parsed = json.loads(data)
                                # Extract content from chat completion format
                                text = parsed.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if text:
                                    accumulated_text += text
                            except:
                                continue

                return accumulated_text

        # Fallback if no streaming response found
        raise Exception("No LLM streaming response found")

    async def handle_request(self, request: Request):
        """Handle both JSON text input and multipart file uploads."""
        content_type = request.headers.get("content-type", "")
        is_file_upload = False

        # Check if this is a file upload request
        if "multipart/form-data" in content_type:
            # Handle file upload
            is_file_upload = True
            form_data = await request.form()
            language_from = form_data.get("language_from", "auto")
            language_to = form_data.get("language_to")
            file = form_data.get("file")

            if not file or not hasattr(file, "filename"):
                raise HTTPException(status_code=400, detail="No file uploaded")

            if not language_to:
                raise HTTPException(status_code=400, detail="Target language (language_to) is required")

            try:
                # Process the uploaded file to extract text page by page
                page_texts = await self.doc_processor.process_file(file)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

        else:
            # Handle JSON text input (existing behavior)
            data = await request.json()
            language_from = data.get("language_from", "auto")
            language_to = data.get("language_to")
            source_language = data.get("source_language")

            if not language_to:
                raise HTTPException(status_code=400, detail="Target language (language_to) is required")

            if not source_language:
                raise HTTPException(status_code=400, detail="Source text (source_language) is required")

        # Handle file upload (page-by-page translation)
        if is_file_upload:
            # Auto-detect source language from first page
            if language_from.lower() == "auto" and page_texts:
                try:
                    detected_code = detect(page_texts[0])
                    language_from = LANGUAGE_MAP.get(detected_code, "English")
                except LangDetectException:
                    language_from = "English"

            # Translate each page separately
            translated_pages = []
            for page_num, page_text in enumerate(page_texts, start=1):
                print(f"Translating page {page_num}/{len(page_texts)}...")
                try:
                    translated_page = await self.translate_page(page_text, language_from, language_to)
                    translated_pages.append(translated_page)
                except Exception as e:
                    print(f"Error translating page {page_num}: {str(e)}")
                    translated_pages.append(f"[Error translating page {page_num}]")

            # Combine all translated pages
            combined_translation = "\n\n--- Page Break ---\n\n".join(translated_pages)

            # Return combined result
            choices = []
            usage = UsageInfo()
            choices.append(
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=combined_translation),
                    finish_reason="stop",
                )
            )
            return ChatCompletionResponse(model="polylingua", choices=choices, usage=usage)

        # Handle text input (existing streaming behavior)
        else:
            # Auto-detect source language if set to "auto"
            if language_from.lower() == "auto":
                try:
                    detected_code = detect(source_language)
                    language_from = LANGUAGE_MAP.get(detected_code, "English")
                except LangDetectException:
                    language_from = "English"

            prompt_template = """
                You are a translation assistant who is specialized in translating {language_from} to {language_to}.

                1. Answer should only contain the translation of the source language to the target language.
                2. Do not include any other text or information.
                3. Do not include any other language than the target language.
                4. Do not include any other information than the translation.

                Translate this from {language_from} to {language_to}:

                {source_language}

            """
            prompt = prompt_template.format(
                language_from=language_from, language_to=language_to, source_language=source_language
            )

            # Create chat completion request as dict for the LLM service
            chat_request_dict = {
                "model": LLM_MODEL_ID,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }

            result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs=chat_request_dict)
            for node, response in result_dict.items():
                # Here it suppose the last microservice in the megaservice is LLM.
                if (
                    isinstance(response, StreamingResponse)
                    and node == list(self.megaservice.services.keys())[-1]
                    and self.megaservice.services[node].service_type == ServiceType.LLM
                ):
                    return response
            last_node = runtime_graph.all_leaves()[-1]
            response = result_dict[last_node]["text"]
            choices = []
            usage = UsageInfo()
            choices.append(
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response),
                    finish_reason="stop",
                )
            )
            return ChatCompletionResponse(model="polylingua", choices=choices, usage=usage)

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()


if __name__ == "__main__":
    polylingua = PolyLinguaService(port=MEGA_SERVICE_PORT)
    polylingua.add_remote_service()
    polylingua.start()
