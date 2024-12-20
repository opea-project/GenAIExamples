# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from typing import List

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import DocSumLLMParams
from fastapi import File, Request, UploadFile
from fastapi.responses import StreamingResponse

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))

DATA_SERVICE_HOST_IP = os.getenv("DATA_SERVICE_HOST_IP", "0.0.0.0")
DATA_SERVICE_PORT = int(os.getenv("DATA_SERVICE_PORT", 7079))

LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.LLM:
        docsum_parameters = kwargs.get("docsum_parameters", None)
        if docsum_parameters:
            docsum_parameters = docsum_parameters.model_dump()
            del docsum_parameters["query"]
            inputs.update(docsum_parameters)
    return inputs


def read_pdf(file):
    from langchain.document_loaders import PyPDFLoader

    loader = PyPDFLoader(file)
    docs = loader.load_and_split()
    return docs


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


class DocSumService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.DOC_SUMMARY)

    def add_remote_service(self):

        data = MicroService(
            name="multimedia2text",
            host=DATA_SERVICE_HOST_IP,
            port=DATA_SERVICE_PORT,
            endpoint="/v1/multimedia2text",
            use_remote_service=True,
            service_type=ServiceType.DATAPREP,
        )

        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/docsum",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )

        self.megaservice.add(data).add(llm)
        self.megaservice.flow_to(data, llm)

    async def handle_request(self, request: Request, files: List[UploadFile] = File(default=None)):

        if "application/json" in request.headers.get("content-type"):
            data = await request.json()
            stream_opt = data.get("stream", True)
            summary_type = data.get("summary_type", "auto")
            chunk_size = data.get("chunk_size", -1)
            chunk_overlap = data.get("chunk_overlap", -1)
            chat_request = ChatCompletionRequest.model_validate(data)
            prompt = handle_message(chat_request.messages)

            initial_inputs_data = {data["type"]: prompt}

        elif "multipart/form-data" in request.headers.get("content-type"):
            data = await request.form()
            stream_opt = data.get("stream", True)
            summary_type = data.get("summary_type", "auto")
            chunk_size = data.get("chunk_size", -1)
            chunk_overlap = data.get("chunk_overlap", -1)
            chat_request = ChatCompletionRequest.model_validate(data)

            data_type = data.get("type")

            file_summaries = []
            if files:
                for file in files:
                    file_path = f"/tmp/{file.filename}"

                    if data_type is not None and data_type in ["audio", "video"]:
                        raise ValueError(
                            "Audio and Video file uploads are not supported in docsum with curl request, please use the UI."
                        )

                    else:
                        import aiofiles

                        async with aiofiles.open(file_path, "wb") as f:
                            await f.write(await file.read())

                        docs = read_text_from_file(file, file_path)
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
                initial_inputs_data = {"query": prompt}

        else:
            raise ValueError(f"Unknown request type: {request.headers.get('content-type')}")

        docsum_parameters = DocSumLLMParams(
            query="",
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
            model=chat_request.model if chat_request.model else None,
            language=chat_request.language if chat_request.language else "auto",
            summary_type=summary_type,
            chunk_overlap=chunk_overlap,
            chunk_size=chunk_size,
        )

        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs=initial_inputs_data, docsum_parameters=docsum_parameters
        )

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
        return ChatCompletionResponse(model="docsum", choices=choices, usage=usage)

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
    docsum = DocSumService(port=MEGA_SERVICE_PORT)
    docsum.add_remote_service()
    docsum.start()
