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
import os
from langdetect import detect, LangDetectException

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from fastapi import Request
from fastapi.responses import StreamingResponse

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


class TranslationService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.TRANSLATION)

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

    async def handle_request(self, request: Request):
        data = await request.json()
        language_from = data["language_from"]
        language_to = data["language_to"]
        source_language = data["source_language"]

        # Auto-detect source language if set to "auto"
        if language_from.lower() == "auto":
            try:
                detected_code = detect(source_language)
                language_from = LANGUAGE_MAP.get(detected_code, "English")
            except LangDetectException:
                # Fallback to English if detection fails
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
            "stream": True
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
        return ChatCompletionResponse(model="translation", choices=choices, usage=usage)

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
    translation = TranslationService(port=MEGA_SERVICE_PORT)
    translation.add_remote_service()
    translation.start()
