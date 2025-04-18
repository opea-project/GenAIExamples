# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
import asyncio
import os

from comps import CustomLogger, MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import LLMParams
from fastapi import Request
from fastapi.responses import StreamingResponse
from langchain.prompts import PromptTemplate

logger = CustomLogger("opea_dataprep_microservice")
logflag = os.getenv("LOGFLAG", False)

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 7778))
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))
RETRIEVAL_SERVICE_HOST_IP = os.getenv("RETRIEVAL_SERVICE_HOST_IP", "0.0.0.0")
REDIS_RETRIEVER_PORT = int(os.getenv("REDIS_RETRIEVER_PORT", 7000))
TEI_EMBEDDING_HOST_IP = os.getenv("TEI_EMBEDDING_HOST_IP", "0.0.0.0")
EMBEDDER_PORT = int(os.getenv("EMBEDDER_PORT", 6000))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

grader_prompt = """You are a grader assessing relevance of a retrieved document to a user question. \n
Here is the user question: {question} \n
Here is the retrieved document: \n\n {document} \n\n

If the document contains keywords related to the user question, grade it as relevant.
It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
Rules:
- Do not return the question, the provided document or explanation.
- if this document is relevant to the question, return 'yes' otherwise return 'no'.
- Do not include any other details in your response.
"""


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    """Aligns the inputs based on the service type of the current node.

    Parameters:
    - self: Reference to the current instance of the class.
    - inputs: Dictionary containing the inputs for the current node.
    - cur_node: The current node in the service orchestrator.
    - runtime_graph: The runtime graph of the service orchestrator.
    - llm_parameters_dict: Dictionary containing the LLM parameters.
    - kwargs: Additional keyword arguments.

    Returns:
    - inputs: The aligned inputs for the current node.
    """

    # Check if the current service type is EMBEDDING
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        # Store the input query for later use
        self.input_query = inputs["query"]
        # Set the input for the embedding service
        inputs["input"] = inputs["query"]

    # Check if the current service type is RETRIEVER
    if self.services[cur_node].service_type == ServiceType.RETRIEVER:
        # Extract the embedding from the inputs
        embedding = inputs["data"][0]["embedding"]
        # Align the inputs for the retriever service
        inputs = {"index_name": llm_parameters_dict["index_name"], "text": self.input_query, "embedding": embedding}

    return inputs


class CodeGenService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        self.megaservice_llm = ServiceOrchestrator()
        self.megaservice_retriever = ServiceOrchestrator()
        self.megaservice_retriever_llm = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.CODE_GEN)

    def add_remote_service(self):
        """Adds remote microservices to the service orchestrators and defines the flow between them."""

        # Define the embedding microservice
        embedding = MicroService(
            name="embedding",
            host=TEI_EMBEDDING_HOST_IP,
            port=EMBEDDER_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )

        # Define the retriever microservice
        retriever = MicroService(
            name="retriever",
            host=RETRIEVAL_SERVICE_HOST_IP,
            port=REDIS_RETRIEVER_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )

        # Define the LLM microservice
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            api_key=OPENAI_API_KEY,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )

        # Add the microservices to the megaservice_retriever_llm orchestrator and define the flow
        self.megaservice_retriever_llm.add(embedding).add(retriever).add(llm)
        self.megaservice_retriever_llm.flow_to(embedding, retriever)
        self.megaservice_retriever_llm.flow_to(retriever, llm)

        # Add the microservices to the megaservice_retriever orchestrator and define the flow
        self.megaservice_retriever.add(embedding).add(retriever)
        self.megaservice_retriever.flow_to(embedding, retriever)

        # Add the LLM microservice to the megaservice_llm orchestrator
        self.megaservice_llm.add(llm)

    async def read_streaming_response(self, response: StreamingResponse):
        """Reads the streaming response from a StreamingResponse object.

        Parameters:
        - self: Reference to the current instance of the class.
        - response: The StreamingResponse object to read from.

        Returns:
        - str: The complete response body as a decoded string.
        """
        body = b""  # Initialize an empty byte string to accumulate the response chunks
        async for chunk in response.body_iterator:
            body += chunk  # Append each chunk to the body
        return body.decode("utf-8")  # Decode the accumulated byte string to a regular string

    async def handle_request(self, request: Request):
        """Handles the incoming request, processes it through the appropriate microservices,
        and returns the response.

        Parameters:
        - self: Reference to the current instance of the class.
        - request: The incoming request object.

        Returns:
        - ChatCompletionResponse: The response from the LLM microservice.
        """
        # Parse the incoming request data
        data = await request.json()

        # Get the stream option from the request data, default to True if not provided
        stream_opt = data.get("stream", True)

        # Validate and parse the chat request data
        chat_request = ChatCompletionRequest.model_validate(data)

        # Handle the chat messages to generate the prompt
        prompt = handle_message(chat_request.messages)

        # Get the agents flag from the request data, default to False if not provided
        agents_flag = data.get("agents_flag", False)

        # Define the LLM parameters
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=stream_opt,
            index_name=chat_request.index_name,
        )

        # Initialize the initial inputs with the generated prompt
        initial_inputs = {"query": prompt}

        # Check if the key index name is provided in the parameters
        if parameters.index_name:
            if agents_flag:
                # Schedule the retriever microservice
                result_ret, runtime_graph = await self.megaservice_retriever.schedule(
                    initial_inputs=initial_inputs, llm_parameters=parameters
                )

                # Switch to the LLM microservice
                megaservice = self.megaservice_llm

                relevant_docs = []
                for doc in result_ret["retriever/MicroService"]["retrieved_docs"]:
                    # Create the PromptTemplate
                    prompt_agent = PromptTemplate(template=grader_prompt, input_variables=["question", "document"])

                    # Format the template with the input variables
                    formatted_prompt = prompt_agent.format(question=prompt, document=doc["text"])
                    initial_inputs_grader = {"query": formatted_prompt}

                    # Schedule the LLM microservice for grading
                    grade, runtime_graph = await self.megaservice_llm.schedule(
                        initial_inputs=initial_inputs_grader, llm_parameters=parameters
                    )

                    for node, response in grade.items():
                        if isinstance(response, StreamingResponse):
                            # Read the streaming response
                            grader_response = await self.read_streaming_response(response)

                            # Replace null with None
                            grader_response = grader_response.replace("null", "None")

                            # Split the response by "data:" and process each part
                            for i in grader_response.split("data:"):
                                if '"text":' in i:
                                    # Convert the string to a dictionary
                                    r = ast.literal_eval(i)
                                    # Check if the response text is "yes"
                                    if r["choices"][0]["text"] == "yes":
                                        # Append the document to the relevant_docs list
                                        relevant_docs.append(doc)

                # Update the initial inputs with the relevant documents
                if len(relevant_docs) > 0:
                    logger.info(f"[ CodeGenService - handle_request ] {len(relevant_docs)} relevant document\s found.")
                    query = initial_inputs["query"]
                    initial_inputs = {}
                    initial_inputs["retrieved_docs"] = relevant_docs
                    initial_inputs["initial_query"] = query

                else:
                    logger.info(
                        "[ CodeGenService - handle_request ] Could not find any relevant documents. The query will be used as input to the LLM."
                    )

            else:
                # Use the combined retriever and LLM microservice
                megaservice = self.megaservice_retriever_llm
        else:
            # Use the LLM microservice only
            megaservice = self.megaservice_llm

        # Schedule the final megaservice
        result_dict, runtime_graph = await megaservice.schedule(
            initial_inputs=initial_inputs, llm_parameters=parameters
        )

        for node, response in result_dict.items():
            # Check if the last microservice in the megaservice is LLM
            if (
                isinstance(response, StreamingResponse)
                and node == list(megaservice.services.keys())[-1]
                and megaservice.services[node].service_type == ServiceType.LLM
            ):
                return response

        # Get the response from the last node in the runtime graph
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
        return ChatCompletionResponse(model="codegen", choices=choices, usage=usage)

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
    chatqna = CodeGenService(port=MEGA_SERVICE_PORT)
    chatqna.add_remote_service()
    chatqna.start()
