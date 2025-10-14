# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import json
import os
import subprocess
import uuid
from typing import List

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    ArbPostHearingAssistantChatCompletionRequest,
    UsageInfo,
)
from fastapi import File, Request, UploadFile
from fastapi.responses import StreamingResponse

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))

LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.LLM:
        for key_to_replace in ["text", "asr_result"]:
            if key_to_replace in inputs:
                inputs["messages"] = inputs[key_to_replace]
                del inputs[key_to_replace]

        arbPostHearingAssistant_parameters = kwargs.get("arbPostHearingAssistant_parameters", None)
        if arbPostHearingAssistant_parameters:
            arbPostHearingAssistant_parameters = arbPostHearingAssistant_parameters.model_dump()
            del arbPostHearingAssistant_parameters["messages"]
            inputs.update(arbPostHearingAssistant_parameters)
        if "id" in inputs:
            del inputs["id"]
        if "max_new_tokens" in inputs:
            del inputs["max_new_tokens"]
        if "input" in inputs:
            del inputs["input"]
    return inputs


def read_pdf(file):
    from langchain.document_loaders import PyPDFLoader

    loader = PyPDFLoader(file)
    docs = loader.load_and_split()
    return docs


def encode_file_to_base64(file_path):
    """Encode the content of a file to a base64 string.

    Args:
        file_path (str): The path to the file to be encoded.

    Returns:
        str: The base64 encoded string of the file content.
    """
    with open(file_path, "rb") as f:
        base64_str = base64.b64encode(f.read()).decode("utf-8")
    return base64_str


def read_text_from_file(file, save_file_name):
    import docx2txt
    from langchain.text_splitter import CharacterTextSplitter

    # read text file
    if file.headers["content-type"] == "text/plain":
        file.file.seek(0)
        content = file.file.read().decode("utf-8")
        # Split text
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(content)
        # Create multiple documents
        file_content = texts
    # read pdf file
    elif file.headers["content-type"] == "application/pdf":
        documents = read_pdf(save_file_name)
        file_content = [doc.page_content for doc in documents]
    # read docx file
    elif (
        file.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or file.headers["content-type"] == "application/octet-stream"
    ):
        file_content = docx2txt.process(save_file_name)

    return file_content


def align_generator(self, gen, **kwargs):
    # OpenAI response format
    # b'data:{"id":"","object":"text_completion","created":1725530204,"model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"2.0.1-native","choices":[{"index":0,"delta":{"role":"assistant","content":"?"},"logprobs":null,"finish_reason":null}]}\n\n'
    for line in gen:
        line = line.decode("utf-8")
        start = -1
        end = -1
        try:
            start = line.find("{")
            end = line.rfind("}") + 1
            if start == -1 or end <= start:
                # Handle cases where '{' or '}' are not found or are in the wrong order
                json_str = ""
            else:
                json_str = line[start:end]
        except Exception as e:
            print(f"Error finding JSON boundaries: {e}")
            json_str = ""

        try:
            # sometimes yield empty chunk, do a fallback here
            json_data = json.loads(json_str)
            if "ops" in json_data and "op" in json_data["ops"][0]:
                if "value" in json_data["ops"][0] and isinstance(json_data["ops"][0]["value"], str):
                    yield f"data: {repr(json_data['ops'][0]['value'].encode('utf-8'))}\n\n"
                else:
                    pass
            elif (
                json_data["choices"][0]["finish_reason"] != "eos_token"
                and "content" in json_data["choices"][0]["delta"]
            ):
                yield f"data: {repr(json_data['choices'][0]['delta']['content'].encode('utf-8'))}\n\n"
        except Exception as e:
            yield f"data: {repr(json_str.encode('utf-8'))}\n\n"
    yield "data: [DONE]\n\n"


class OpeaArbPostHearingAssistantService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_generator = align_generator
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(getattr(MegaServiceEndpoint, "ARB_POST_HEARING_ASSISTANT", "/v1/arb-post-hearing"))

    def add_remote_service(self):

        llm = MicroService(
            name="opea_service@arb_post_hearing_assistant",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/arb-post-hearing",
            use_remote_service=True,
            service_type=ServiceType.ARB_POST_HEARING_ASSISTANT,
        )
        self.megaservice.add(llm)

    async def handle_request(self, request: Request, files: List[UploadFile] = File(default=None)):
        """Accept pure text, or files .txt/.pdf.docx"""
        if "application/json" in request.headers.get("content-type"):
            data = await request.json()
            chunk_size = data.get("chunk_size", -1)
            chunk_overlap = data.get("chunk_overlap", -1)
            chat_request = ChatCompletionRequest.model_validate(data)
            prompt = handle_message(chat_request.messages)

            initial_inputs_data = {data["type"]: prompt}

        elif "multipart/form-data" in request.headers.get("content-type"):
            data = await request.form()
            chunk_size = data.get("chunk_size", -1)
            chunk_overlap = data.get("chunk_overlap", -1)
            chat_request = ChatCompletionRequest.model_validate(data)

            data_type = data.get("type")

            file_summaries = []
            if files:
                for file in files:
                    # Fix concurrency issue with the same file name
                    # https://github.com/opea-project/GenAIExamples/issues/1279
                    uid = str(uuid.uuid4())
                    file_path = f"/tmp/{uid}"

                    import aiofiles

                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(await file.read())

                    if data_type == "text":
                        docs = read_text_from_file(file, file_path)
                    else:
                        raise ValueError(f"Data type not recognized: {data_type}")

                    os.remove(file_path)

                    if isinstance(docs, list):
                        file_summaries.extend(docs)
                    else:
                        file_summaries.append(docs)

            if file_summaries:
                prompt = handle_message(chat_request.messages) + "\n".join(file_summaries)
            else:
                prompt = handle_message(chat_request.messages)

            data_type = data.get("type")
            if data_type is not None:
                initial_inputs_data = {}
                initial_inputs_data[data_type] = prompt
            else:
                initial_inputs_data = {"messages": prompt}

        else:
            raise ValueError(f"Unknown request type: {request.headers.get('content-type')}")

        arbPostHearingAssistant_parameters = ArbPostHearingAssistantChatCompletionRequest(
            messages="",
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=stream_opt,
            model=chat_request.model if chat_request.model else None,
            language=chat_request.language if chat_request.language else "en",
            chunk_overlap=chunk_overlap,
            chunk_size=chunk_size,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs=initial_inputs_data, arbPostHearingAssistant_parameters=arbPostHearingAssistant_parameters
        )

        for node, response in result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.ARB_POST_HEARING_ASSISTANT
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
        return ChatCompletionResponse(model="arbPostHearingAssistant", choices=choices, usage=usage)

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
    arbPostHearingAssistant = OpeaArbPostHearingAssistantService(port=MEGA_SERVICE_PORT)
    arbPostHearingAssistant.add_remote_service()
    arbPostHearingAssistant.start()
