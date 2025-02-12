# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
import base64
import json
import logging
import os
from urllib.parse import urlparse

import gradio as gr
import requests
import uvicorn
from fastapi import FastAPI
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, UnstructuredURLLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocSumUI:
    def __init__(self):
        """Initialize the DocSumUI class with accepted file types, headers, and backend service endpoint."""
        self.ACCEPTED_FILE_TYPES = ["pdf", "doc", "docx"]
        self.HEADERS = {"Content-Type": "application/json"}
        self.BACKEND_SERVICE_ENDPOINT = os.getenv("BACKEND_SERVICE_ENDPOINT", "http://localhost:8888/v1/docsum")

    def encode_file_to_base64(self, file_path):
        """Encode the content of a file to a base64 string.

        Args:
            file_path (str): The path to the file to be encoded.

        Returns:
            str: The base64 encoded string of the file content.
        """
        logger.info(">>> Encoding file to base64: %s", file_path)
        with open(file_path, "rb") as f:
            base64_str = base64.b64encode(f.read()).decode("utf-8")
        return base64_str

    def read_file(self, file):
        """Read and process the content of a file.

        Args:
            file (file-like object): The file to be read.

        Returns:
            str: The content of the file or an error message if the file type is unsupported.
        """
        self.page_content = ""
        self.pages = []

        if file.name.endswith(".pdf"):
            loader = PyPDFLoader(file)
        elif file.name.endswith((".doc", ".docx")):
            loader = Docx2txtLoader(file)
        else:
            msg = f"Unsupported file type '{file.name}'. Choose from {self.ACCEPTED_FILE_TYPES}"
            logger.error(msg)
            return msg

        for page in loader.lazy_load():
            self.page_content += page.page_content

        return self.page_content

    def read_audio_file(self, file):
        """Read and process the content of an audio file.

        Args:
            file (file-like object): The audio file to be read.

        Returns:
            str: The base64 encoded content of the audio file.
        """
        logger.info(">>> Reading audio file: %s", file.name)
        base64_str = self.encode_file_to_base64(file)
        return base64_str

    def read_video_file(self, file):
        """Read and process the content of a video file.

        Args:
            file (file-like object): The video file to be read.

        Returns:
            str: The base64 encoded content of the video file.
        """
        logger.info(">>> Reading video file: %s", file.name)
        base64_str = self.encode_file_to_base64(file)
        return base64_str

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def read_url(self, url):
        """Read and process the content of a url.

        Args:
            url: The url to be read as a document.

        Returns:
            str: The content of the website or an error message if the url is unsupported.
        """

        self.page_content = ""

        logger.info(">>> Reading url: %s", url)
        if self.is_valid_url(url=url):
            os.environ["no_proxy"] = f"{os.environ.get('no_proxy', '')},{url}".strip(",")
            try:
                loader = UnstructuredURLLoader([url])
                page = loader.load()
                self.page_content = [content.page_content for content in page][0]
            except Exception as e:
                msg = f"There was an error trying to read '{url}' --> '{e}'\nTry adding the domain name to your `no_proxy` variable and try again. Example: example.com*"
                logger.error(msg)
        else:
            msg = f"Invalid URL '{url}'. Make sure the link provided is a valid URL"
            logger.error(msg)
            return msg

        return self.page_content

    def generate_summary(self, doc_content, document_type="text"):
        """Generate a summary for the given document content.

        Args:
            doc_content (str): The content of the document.
            document_type (str): The type of the document (default is "text").

        Returns:
            str: The generated summary or an error message.
        """

        logger.info(">>> BACKEND_SERVICE_ENDPOINT - %s", self.BACKEND_SERVICE_ENDPOINT)

        data = {"max_tokens": 256, "type": document_type, "messages": doc_content}

        try:
            response = requests.post(
                url=self.BACKEND_SERVICE_ENDPOINT,
                headers=self.HEADERS,
                data=json.dumps(data),
                proxies={"http_proxy": os.environ["http_proxy"], "https_proxy": os.environ["https_proxy"]},
            )

            if response.status_code == 200:
                try:
                    # Check if the specific log path is in the response text
                    if "/logs/LLMChain/final_output" in response.text:
                        # Extract the relevant part of the response
                        temp = ast.literal_eval(
                            [
                                i.split("data: ")[1]
                                for i in response.text.split("\n\n")
                                if "/logs/LLMChain/final_output" in i
                            ][0]
                        )["ops"]

                        # Find the final output value
                        final_output = [i["value"] for i in temp if i["path"] == "/logs/LLMChain/final_output"][0]
                        return final_output["text"]
                    else:
                        # Perform string replacements to clean the response text
                        cleaned_text = response.text
                        replacements = [
                            ("'\n\ndata: b'", ""),
                            ("data: b' ", ""),
                            ("</s>'\n\ndata: [DONE]\n\n", ""),
                            ("\n\ndata: b", ""),
                            ("'\n\n", ""),
                            ("'\n", ""),
                            ('''\'"''', ""),
                        ]
                        for old, new in replacements:
                            cleaned_text = cleaned_text.replace(old, new)
                        return cleaned_text
                except (IndexError, KeyError, ValueError) as e:
                    # Handle potential errors during parsing
                    logger.error("Error parsing response: %s", e)
                    return response.text

        except requests.exceptions.RequestException as e:
            logger.error("Request exception: %s", e)
            return str(e)

        return str(response.status_code)

    def create_upload_ui(self, label, file_types, process_function, document_type="text"):
        """Create a Gradio UI for file uploads.

        Args:
            label (str): The label for the upload button.
            file_types (list): The list of accepted file types.
            process_function (function): The function to process the uploaded file.

        Returns:
            gr.Blocks: The Gradio Blocks object representing the upload UI.
        """
        logger.info(">>> Creating upload UI for label: %s", label)
        with gr.Blocks() as upload_ui:
            with gr.Row():
                with gr.Column():
                    upload_btn = gr.UploadButton(label=label, file_count="single", file_types=file_types)
                with gr.Column():
                    generated_text = gr.TextArea(
                        label="Text Summary", placeholder="Summarized text will be displayed here"
                    )
            upload_btn.upload(
                lambda file: self.generate_summary(process_function(file), document_type=document_type),
                upload_btn,
                generated_text,
            )
        return upload_ui

    def render(self):
        """Render the Gradio UI for the DocSum application.

        Returns:
            gr.Blocks: The Gradio Blocks object representing the UI.
        """
        logger.info(">>> Rendering Gradio UI")
        # Plain text UI
        with gr.Blocks() as text_ui:
            with gr.Row():
                with gr.Column():
                    input_text = gr.TextArea(
                        label="Please paste content for summarization",
                        placeholder="Paste the text information you need to summarize",
                    )
                    submit_btn = gr.Button("Generate Summary")
                with gr.Column():
                    generated_text = gr.TextArea(
                        label="Text Summary", placeholder="Summarized text will be displayed here"
                    )
            submit_btn.click(fn=self.generate_summary, inputs=[input_text], outputs=[generated_text])

        with gr.Blocks() as url_ui:
            # URL text UI
            with gr.Row():
                with gr.Column():
                    input_text = gr.TextArea(
                        label="Please paste a URL for summarization",
                        placeholder="Paste a URL for the information you need to summarize",
                    )
                    submit_btn = gr.Button("Generate Summary")
                with gr.Column():
                    generated_text = gr.TextArea(
                        label="Text Summary", placeholder="Summarized text will be displayed here"
                    )
            submit_btn.click(
                lambda input_text: self.generate_summary(self.read_url(input_text)),
                inputs=input_text,
                outputs=generated_text,
            )

        # File Upload UI
        file_ui = self.create_upload_ui(
            label="Please upload a document (.pdf, .doc, .docx)",
            file_types=[".pdf", ".doc", ".docx"],
            process_function=self.read_file,
        )

        # Audio Upload UI
        audio_ui = self.create_upload_ui(
            label="Please upload audio file (.wav, .mp3)",
            file_types=[".wav", ".mp3"],
            process_function=self.read_audio_file,
            document_type="audio",
        )

        # Video Upload UI
        video_ui = self.create_upload_ui(
            label="Please upload Video file (.mp4)",
            file_types=[".mp4"],
            process_function=self.read_video_file,
            document_type="video",
        )

        # Render all the UI in separate tabs
        with gr.Blocks() as self.demo:
            gr.Markdown("# Doc Summary")
            with gr.Tabs():
                with gr.TabItem("Paste Text"):
                    text_ui.render()
                with gr.TabItem("Upload file"):
                    file_ui.render()
                with gr.TabItem("Upload Audio"):
                    audio_ui.render()
                with gr.TabItem("Upload Video"):
                    video_ui.render()
                # with gr.TabItem("Enter URL"):
                #     url_ui.render()

        return self.demo


app = FastAPI()

demo = DocSumUI().render()

demo.queue()

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import argparse

    import nltk

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5173)

    args = parser.parse_args()
    logger.info(">>> Starting server at %s:%d", args.host, args.port)

    # Needed for UnstructuredURLLoader when reading content from a URL
    nltk.download("punkt_tab")
    nltk.download("averaged_perceptron_tagger_eng")

    uvicorn.run(app, host=args.host, port=args.port)
