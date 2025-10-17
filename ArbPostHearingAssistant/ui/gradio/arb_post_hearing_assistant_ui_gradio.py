# Copyright (C) 2025 Zensar Technologies Private Ltd.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import re

import gradio as gr
import requests
import uvicorn
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArbPostHearingAssistantUI:
    def __init__(self):
        """Initialize class with headers and backend endpoint."""
        self.HEADERS = {"Content-Type": "application/json"}
        self.BACKEND_SERVICE_ENDPOINT = os.getenv(
            "BACKEND_SERVICE_ENDPOINT", "http://localhost:8888/v1/arb-post-hearing"
        )

    def extract_json(self, text: str):
        """Extract and clean embedded JSON from text."""
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logger.error("Error extracting JSON: %s", e)
        return None

    def summarize_arbitration_transcript(self, transcript):
        """Generate a summary for the given document content."""
        logger.info(">>> BACKEND_SERVICE_ENDPOINT - %s", self.BACKEND_SERVICE_ENDPOINT)

        data = {"messages": transcript, "type": "text", "language": "en"}

        try:
            response = requests.post(
                url=self.BACKEND_SERVICE_ENDPOINT,
                headers=self.HEADERS,
                data=json.dumps(data),
                proxies={
                    "http": os.environ.get("http_proxy", ""),
                    "https": os.environ.get("https_proxy", ""),
                },
            )

            if response.status_code == 200:
                result = response.json()
                raw_text = result["choices"][0]["message"]["content"]
                extracted_json = self.extract_json(raw_text)

                # Return pretty JSON if available
                if extracted_json:
                    return json.dumps(extracted_json, indent=4)

                # Fallback if no JSON found
                return json.dumps({"message": "something went wrong, please try again"}, indent=4)

        except requests.exceptions.RequestException as e:
            logger.error("Request exception: %s", e)
            return json.dumps({"message": "something went wrong, please try again"}, indent=4)

        return json.dumps({"message": "something went wrong, please try again"}, indent=4)

    def render(self):
        """Render the Gradio UI."""
        logger.info(">>> Rendering Gradio UI")

        with gr.Blocks() as text_ui:
            with gr.Row():
                with gr.Column():
                    input_text = gr.TextArea(
                        label="Enter your arbitration transcript to process:",
                        placeholder="Please enter arbitration transcript before submitting",
                        lines=20,
                    )
                    submit_btn = gr.Button("Generate")
                with gr.Column():
                    # ✅ Use Textbox to show formatted JSON properly
                    generated_text = gr.JSON(label="Generated arbitration Summary", height=462, max_height=500)
            submit_btn.click(fn=self.summarize_arbitration_transcript, inputs=[input_text], outputs=[generated_text])

        with gr.Blocks() as self.demo:
            gr.Markdown(
                "<h1 style='text-align:center;'>⚖️ Arbitration Post Hearing Assistant</h1>",
                elem_classes=["centered-title"],
            )
            with gr.Tabs():
                with gr.TabItem("Paste Arbitration Transcript"):
                    text_ui.render()

        return self.demo


# FastAPI + Gradio Integration
app = FastAPI()

demo = ArbPostHearingAssistantUI().render()
demo.queue()
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5173)

    args = parser.parse_args()
    logger.info(">>> Starting server at %s:%d", args.host, args.port)

    uvicorn.run("arb_post_hearing_assistant_ui_gradio:app", host=args.host, port=args.port)
