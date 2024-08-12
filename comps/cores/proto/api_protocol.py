# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from enum import IntEnum
from typing import Any, Dict, List, Literal, Optional, Union

import shortuuid
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ServiceCard(BaseModel):
    object: str = "service"
    service_name: str
    description: str
    created: int = Field(default_factory=lambda: int(time.time()))
    owner: str = "opea"


class ServiceList(BaseModel):
    object: str = "list"
    data: List[ServiceCard] = []


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0
    completion_tokens: Optional[int] = 0


class ResponseFormat(BaseModel):
    # type must be "json_object" or "text"
    type: Literal["text", "json_object"]


class StreamOptions(BaseModel):
    # refer https://github.com/vllm-project/vllm/blob/main/vllm/entrypoints/openai/protocol.py#L105
    include_usage: Optional[bool]


class FunctionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ChatCompletionToolsParam(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionDefinition


class ChatCompletionNamedFunction(BaseModel):
    name: str


class ChatCompletionNamedToolChoiceParam(BaseModel):
    function: ChatCompletionNamedFunction
    type: Literal["function"] = "function"


class TokenCheckRequestItem(BaseModel):
    model: str
    prompt: str
    max_tokens: int


class TokenCheckRequest(BaseModel):
    prompts: List[TokenCheckRequestItem]


class TokenCheckResponseItem(BaseModel):
    fits: bool
    tokenCount: int
    contextLength: int


class TokenCheckResponse(BaseModel):
    prompts: List[TokenCheckResponseItem]


class EmbeddingRequest(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/embeddings
    model: Optional[str] = None
    input: Union[List[int], List[List[int]], str, List[str]]
    encoding_format: Optional[str] = Field("float", pattern="^(float|base64)$")
    dimensions: Optional[int] = None
    user: Optional[str] = None

    # define
    request_type: Literal["embedding"] = "embedding"


class EmbeddingResponseData(BaseModel):
    index: int
    object: str = "embedding"
    embedding: Union[List[float], str]


class EmbeddingResponse(BaseModel):
    object: str = "list"
    model: Optional[str] = None
    data: List[EmbeddingResponseData]
    usage: Optional[UsageInfo] = None


class RetrievalRequest(BaseModel):
    embedding: Union[EmbeddingResponse, List[float]] = None
    input: Optional[str] = None  # search_type maybe need, like "mmr"
    search_type: str = "similarity"
    k: int = 4
    distance_threshold: Optional[float] = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    score_threshold: float = 0.2

    # define
    request_type: Literal["retrieval"] = "retrieval"


class RetrievalResponseData(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


class RetrievalResponse(BaseModel):
    retrieved_docs: List[RetrievalResponseData]


class RerankingRequest(BaseModel):
    input: str
    retrieved_docs: Union[List[RetrievalResponseData], List[Dict[str, Any]], List[str]]
    top_n: int = 1

    # define
    request_type: Literal["reranking"] = "reranking"


class RerankingResponseData(BaseModel):
    text: str
    score: Optional[float] = 0.0


class RerankingResponse(BaseModel):
    reranked_docs: List[RerankingResponseData]


class ChatCompletionRequest(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/chat/create
    messages: Union[
        str,
        List[Dict[str, str]],
        List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]],
    ]
    model: Optional[str] = "Intel/neural-chat-7b-v3-3"
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = 0
    max_tokens: Optional[int] = 16  # use https://platform.openai.com/docs/api-reference/completions/create
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    response_format: Optional[ResponseFormat] = None
    seed: Optional[int] = None
    service_tier: Optional[str] = None
    stop: Union[str, List[str], None] = Field(default_factory=list)
    stream: Optional[bool] = False
    stream_options: Optional[StreamOptions] = None
    temperature: Optional[float] = 1.0  # vllm default 0.7
    top_p: Optional[float] = None  # openai default 1.0, but tgi needs `top_p` must be > 0.0 and < 1.0, set None
    tools: Optional[List[ChatCompletionToolsParam]] = None
    tool_choice: Optional[Union[Literal["none"], ChatCompletionNamedToolChoiceParam]] = "none"
    parallel_tool_calls: Optional[bool] = True
    user: Optional[str] = None

    # Ordered by official OpenAI API documentation
    # default values are same with
    # https://platform.openai.com/docs/api-reference/completions/create
    best_of: Optional[int] = 1
    suffix: Optional[str] = None

    # vllm reference: https://github.com/vllm-project/vllm/blob/main/vllm/entrypoints/openai/protocol.py#L130
    repetition_penalty: Optional[float] = 1.0

    # tgi reference: https://huggingface.github.io/text-generation-inference/#/Text%20Generation%20Inference/generate
    # some tgi parameters in use
    # default values are same with
    # https://github.com/huggingface/text-generation-inference/blob/main/router/src/lib.rs#L190
    # max_new_tokens: Optional[int] = 100 # Priority use openai
    top_k: Optional[int] = None
    # top_p: Optional[float] = None # Priority use openai
    typical_p: Optional[float] = None
    # repetition_penalty: Optional[float] = None

    # doc: begin-chat-completion-extra-params
    echo: Optional[bool] = Field(
        default=False,
        description=(
            "If true, the new message will be prepended with the last message " "if they belong to the same role."
        ),
    )
    add_generation_prompt: Optional[bool] = Field(
        default=True,
        description=(
            "If true, the generation prompt will be added to the chat template. "
            "This is a parameter used by chat template in tokenizer config of the "
            "model."
        ),
    )
    add_special_tokens: Optional[bool] = Field(
        default=False,
        description=(
            "If true, special tokens (e.g. BOS) will be added to the prompt "
            "on top of what is added by the chat template. "
            "For most models, the chat template takes care of adding the "
            "special tokens so this should be set to False (as is the "
            "default)."
        ),
    )
    documents: Optional[Union[List[Dict[str, str]], List[str]]] = Field(
        default=None,
        description=(
            "A list of dicts representing documents that will be accessible to "
            "the model if it is performing RAG (retrieval-augmented generation)."
            " If the template does not support RAG, this argument will have no "
            "effect. We recommend that each document should be a dict containing "
            '"title" and "text" keys.'
        ),
    )
    chat_template: Optional[str] = Field(
        default=None,
        description=(
            "A template to use for this conversion. "
            "If this is not passed, the model's default chat template will be "
            "used instead. We recommend that the template contains {context} and {question} for rag,"
            "or only contains {question} for chat completion without rag."
        ),
    )
    chat_template_kwargs: Optional[Dict[str, Any]] = Field(
        default=None,
        description=("Additional kwargs to pass to the template renderer. " "Will be accessible by the chat template."),
    )
    # doc: end-chat-completion-extra-params

    # embedding
    input: Union[List[int], List[List[int]], str, List[str]] = None  # user query/question from messages[-]
    encoding_format: Optional[str] = Field("float", pattern="^(float|base64)$")
    dimensions: Optional[int] = None
    embedding: Union[EmbeddingResponse, List[float]] = Field(default_factory=list)

    # retrieval
    search_type: str = "similarity"
    k: int = 4
    distance_threshold: Optional[float] = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    score_threshold: float = 0.2
    retrieved_docs: Union[List[RetrievalResponseData], List[Dict[str, Any]]] = Field(default_factory=list)

    # reranking
    top_n: int = 1
    reranked_docs: Union[List[RerankingResponseData], List[Dict[str, Any]]] = Field(default_factory=list)

    # define
    request_type: Literal["chat"] = "chat"


class AudioChatCompletionRequest(BaseModel):
    audio: str
    messages: Optional[
        Union[
            str,
            List[Dict[str, str]],
            List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]],
        ]
    ] = None
    model: Optional[str] = "Intel/neural-chat-7b-v3-3"
    temperature: Optional[float] = 0.01
    top_p: Optional[float] = 0.95
    top_k: Optional[int] = 10
    n: Optional[int] = 1
    max_tokens: Optional[int] = 1024
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    presence_penalty: Optional[float] = 1.03
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[Literal["stop", "length"]] = None


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{shortuuid.random()}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: UsageInfo


class DeltaMessage(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length"]] = None


class ChatCompletionStreamResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{shortuuid.random()}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseStreamChoice]


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[Any]]
    suffix: Optional[str] = None
    temperature: Optional[float] = 0.7
    n: Optional[int] = 1
    max_tokens: Optional[int] = 16
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    top_k: Optional[int] = -1
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    use_beam_search: Optional[bool] = False
    best_of: Optional[int] = None


class CompletionResponseChoice(BaseModel):
    index: int
    text: str
    finish_reason: Optional[Literal["stop", "length"]] = None


class CompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{shortuuid.random()}")
    object: str = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[CompletionResponseChoice]
    usage: UsageInfo


class CompletionResponseStreamChoice(BaseModel):
    index: int
    text: str
    finish_reason: Optional[Literal["stop", "length"]] = None


class CompletionStreamResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{shortuuid.random()}")
    object: str = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[CompletionResponseStreamChoice]


class AudioQnaRequest(BaseModel):
    file: UploadFile = File(...)
    language: str = "auto"


class ErrorResponse(BaseModel):
    object: str = "error"
    message: str
    code: int


class ApiErrorCode(IntEnum):
    """
    https://platform.openai.com/docs/guides/error-codes/api-errors
    """

    VALIDATION_TYPE_ERROR = 40001

    INVALID_AUTH_KEY = 40101
    INCORRECT_AUTH_KEY = 40102
    NO_PERMISSION = 40103

    INVALID_MODEL = 40301
    PARAM_OUT_OF_RANGE = 40302
    CONTEXT_OVERFLOW = 40303

    RATE_LIMIT = 42901
    QUOTA_EXCEEDED = 42902
    ENGINE_OVERLOADED = 42903

    INTERNAL_ERROR = 50001
    CUDA_OUT_OF_MEMORY = 50002
    GRADIO_REQUEST_ERROR = 50003
    GRADIO_STREAM_UNKNOWN_ERROR = 50004


def create_error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(content=ErrorResponse(message=message, code=status_code), status_code=status_code.value)


def check_requests(request) -> Optional[JSONResponse]:
    # Check all params
    if request.max_tokens is not None and request.max_tokens <= 0:
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.max_tokens} is less than the minimum of 1 - 'max_tokens'",
        )
    if request.n is not None and request.n <= 0:
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.n} is less than the minimum of 1 - 'n'",
        )
    if request.temperature is not None and request.temperature < 0:
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.temperature} is less than the minimum of 0 - 'temperature'",
        )

    if request.temperature is not None and request.temperature > 2:
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.temperature} is greater than the maximum of 2 - 'temperature'",
        )
    if request.top_p is not None and request.top_p < 0:
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.top_p} is less than the minimum of 0 - 'top_p'",
        )
    if request.top_p is not None and request.top_p > 1:
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.top_p} is greater than the maximum of 1 - 'temperature'",
        )
    if request.top_k is not None and (request.top_k > -1 and request.top_k < 1):
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.top_k} is out of Range. Either set top_k to -1 or >=1.",
        )
    if request.stop is not None and (not isinstance(request.stop, str) and not isinstance(request.stop, list)):
        return create_error_response(
            ApiErrorCode.PARAM_OUT_OF_RANGE,
            f"{request.stop} is not valid under any of the given schemas - 'stop'",
        )

    return None
