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
    model: Optional[str] = None
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = 0
    max_tokens: Optional[int] = 1024  # use https://platform.openai.com/docs/api-reference/completions/create
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    response_format: Optional[ResponseFormat] = None
    seed: Optional[int] = None
    service_tier: Optional[str] = None
    stop: Union[str, List[str], None] = Field(default_factory=list)
    stream: Optional[bool] = False
    stream_options: Optional[StreamOptions] = None
    temperature: Optional[float] = 0.01  # vllm default 0.7
    top_p: Optional[float] = None  # openai default 1.0, but tgi needs `top_p` must be > 0.0 and < 1.0, set None
    tools: Optional[List[ChatCompletionToolsParam]] = None
    tool_choice: Optional[Union[Literal["none"], ChatCompletionNamedToolChoiceParam]] = "none"
    parallel_tool_calls: Optional[bool] = True
    user: Optional[str] = None
    language: str = "auto"  # can be "en", "zh"

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


class DocSumChatCompletionRequest(BaseModel):
    llm_params: Optional[ChatCompletionRequest] = None
    text: Optional[str] = None
    audio: Optional[str] = None
    video: Optional[str] = None
    type: Optional[str] = None


class AudioChatCompletionRequest(BaseModel):
    audio: str
    voice: str = "default"
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
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    repetition_penalty: Optional[float] = 1.03
    user: Optional[str] = None


# Pydantic does not support UploadFile directly
# class AudioTranscriptionRequest(BaseModel):
#     # Ordered by official OpenAI API documentation
#     # default values are same with
#     # https://platform.openai.com/docs/api-reference/audio/createTranscription
#     file: UploadFile = File(...)
#     model: Optional[str] = "openai/whisper-small"
#     language: Optional[str] = "english"
#     prompt: Optional[str] = None
#     response_format: Optional[str] = "json"
#     temperature: Optional[str] = 0
#     timestamp_granularities: Optional[List] = None


class AudioTranscriptionResponse(BaseModel):
    # Ordered by official OpenAI API documentation
    # default values are same with
    # https://platform.openai.com/docs/api-reference/audio/json-object
    text: str


class AudioSpeechRequest(BaseModel):
    # Ordered by official OpenAI API documentation
    # default values are same with
    # https://platform.openai.com/docs/api-reference/audio/createSpeech
    input: str
    model: Optional[str] = "microsoft/speecht5_tts"
    voice: Optional[str] = "default"
    response_format: Optional[str] = "mp3"
    speed: Optional[float] = 1.0


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[Literal["stop", "length"]] = None
    metadata: Optional[Dict[str, Any]] = None


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
    repetition_penalty: Optional[float] = 1.03
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


class ThreadObject(BaseModel):
    id: str
    object: str = "thread"
    created_at: int


class AssistantsObject(BaseModel):
    id: str
    object: str = "assistant"
    created_at: int
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = "Intel/neural-chat-7b-v3-3"
    instructions: Optional[str] = None
    tools: Optional[List[ChatCompletionToolsParam]] = None


class Attachments(BaseModel):
    file_list: List[UploadFile] = []


class MessageContent(BaseModel):
    type: str = "text"
    text: Optional[str] = None


class MessageObject(BaseModel):
    id: str
    object: str = "thread.message"
    created_at: int
    thread_id: str
    role: str
    status: Optional[str] = None
    content: List[MessageContent]
    assistant_id: Optional[str] = None
    run_id: Optional[str] = None
    attachments: Attachments = None


class RunObject(BaseModel):
    id: str
    object: str = "run"
    created_at: int
    thread_id: str
    assistant_id: str
    status: Optional[str] = None
    last_error: Optional[str] = None


class CreateAssistantsRequest(BaseModel):
    model: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    tools: Optional[List[ChatCompletionToolsParam]] = None


class CreateMessagesRequest(BaseModel):
    role: str = "user"
    content: Union[str, List[MessageContent]]
    attachments: Attachments = None


class CreateThreadsRequest(BaseModel):
    messages: Optional[List[CreateMessagesRequest]] = None


class CreateRunResponse(BaseModel):
    assistant_id: str


class ListAssistantsRequest(BaseModel):
    limit: int = 10
    order: Optional[str] = "desc"


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


class Hyperparameters(BaseModel):
    batch_size: Optional[Union[Literal["auto"], int]] = "auto"
    """Number of examples in each batch.

    A larger batch size means that model parameters are updated less frequently, but with lower variance.
    """

    learning_rate_multiplier: Optional[Union[Literal["auto"], float]] = "auto"
    """Scaling factor for the learning rate.

    A smaller learning rate may be useful to avoid overfitting.
    """

    n_epochs: Optional[Union[Literal["auto"], int]] = "auto"
    """The number of epochs to train the model for.

    An epoch refers to one full cycle through the training dataset. "auto" decides
    the optimal number of epochs based on the size of the dataset. If setting the
    number manually, we support any number between 1 and 50 epochs.
    """


class FineTuningJobWandbIntegration(BaseModel):
    project: str
    """The name of the project that the new run will be created under."""

    entity: Optional[str] = None
    """The entity to use for the run.

    This allows you to set the team or username of the WandB user that you would
    like associated with the run. If not set, the default entity for the registered
    WandB API key is used.
    """

    name: Optional[str] = None
    """A display name to set for the run.

    If not set, we will use the Job ID as the name.
    """

    tags: Optional[List[str]] = None
    """A list of tags to be attached to the newly created run.

    These tags are passed through directly to WandB. Some default tags are generated
    by OpenAI: "openai/finetune", "openai/{base-model}", "openai/{ftjob-abcdef}".
    """


class FineTuningJobWandbIntegrationObject(BaseModel):
    type: Literal["wandb"]
    """The type of the integrations being enabled for the fine-tuning job."""

    wandb: FineTuningJobWandbIntegration
    """The settings for your integrations with Weights and Biases.

    This payload specifies the project that metrics will be sent to. Optionally, you
    can set an explicit display name for your run, add tags to your run, and set a
    default entity (team, username, etc) to be associated with your run.
    """


class FineTuningJobsRequest(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/fine-tuning/create
    model: str
    """The name of the model to fine-tune."""

    training_file: str
    """The ID of an uploaded file that contains training data."""

    hyperparameters: Optional[Hyperparameters] = None
    """The hyperparameters used for the fine-tuning job."""

    suffix: Optional[str] = None
    """A string of up to 64 characters that will be added to your fine-tuned model name."""

    validation_file: Optional[str] = None
    """The ID of an uploaded file that contains validation data."""

    integrations: Optional[List[FineTuningJobWandbIntegrationObject]] = None
    """A list of integrations to enable for your fine-tuning job."""

    seed: Optional[str] = None


class Error(BaseModel):
    code: str
    """A machine-readable error code."""

    message: str
    """A human-readable error message."""

    param: Optional[str] = None
    """The parameter that was invalid, usually `training_file` or `validation_file`.

    This field will be null if the failure was not parameter-specific.
    """


class FineTuningJob(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/fine-tuning/object
    id: str
    """The object identifier, which can be referenced in the API endpoints."""

    created_at: int
    """The Unix timestamp (in seconds) for when the fine-tuning job was created."""

    error: Optional[Error] = None
    """For fine-tuning jobs that have `failed`, this will contain more information on
    the cause of the failure."""

    fine_tuned_model: Optional[str] = None
    """The name of the fine-tuned model that is being created.

    The value will be null if the fine-tuning job is still running.
    """

    finished_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the fine-tuning job was finished.

    The value will be null if the fine-tuning job is still running.
    """

    hyperparameters: Hyperparameters
    """The hyperparameters used for the fine-tuning job.

    See the [fine-tuning guide](https://platform.openai.com/docs/guides/fine-tuning)
    for more details.
    """

    model: str
    """The base model that is being fine-tuned."""

    object: Literal["fine_tuning.job"] = "fine_tuning.job"
    """The object type, which is always "fine_tuning.job"."""

    organization_id: Optional[str] = None
    """The organization that owns the fine-tuning job."""

    result_files: List[str] = None
    """The compiled results file ID(s) for the fine-tuning job.

    You can retrieve the results with the
    [Files API](https://platform.openai.com/docs/api-reference/files/retrieve-contents).
    """

    status: Literal["validating_files", "queued", "running", "succeeded", "failed", "cancelled"]
    """The current status of the fine-tuning job, which can be either
    `validating_files`, `queued`, `running`, `succeeded`, `failed`, or `cancelled`."""

    trained_tokens: Optional[int] = None
    """The total number of billable tokens processed by this fine-tuning job.

    The value will be null if the fine-tuning job is still running.
    """

    training_file: str
    """The file ID used for training.

    You can retrieve the training data with the
    [Files API](https://platform.openai.com/docs/api-reference/files/retrieve-contents).
    """

    validation_file: Optional[str] = None
    """The file ID used for validation.

    You can retrieve the validation results with the
    [Files API](https://platform.openai.com/docs/api-reference/files/retrieve-contents).
    """

    integrations: Optional[List[FineTuningJobWandbIntegrationObject]] = None
    """A list of integrations to enable for this fine-tuning job."""

    seed: Optional[int] = None
    """The seed used for the fine-tuning job."""

    estimated_finish: Optional[int] = None
    """The Unix timestamp (in seconds) for when the fine-tuning job is estimated to
    finish.

    The value will be null if the fine-tuning job is not running.
    """


class FineTuningJobIDRequest(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/fine-tuning/retrieve
    # https://platform.openai.com/docs/api-reference/fine-tuning/cancel
    fine_tuning_job_id: str
    """The ID of the fine-tuning job."""


class FineTuningJobListRequest(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/fine-tuning/list
    after: Optional[str] = None
    """Identifier for the last job from the previous pagination request."""

    limit: Optional[int] = 20
    """Number of fine-tuning jobs to retrieve."""


class FineTuningJobList(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/fine-tuning/list
    object: str = "list"
    """The object type, which is always "list".

    This indicates that the returned data is a list of fine-tuning jobs.
    """

    data: List[FineTuningJob]
    """A list containing FineTuningJob objects."""

    has_more: bool
    """Indicates whether there are more fine-tuning jobs beyond the current list.

    If true, additional requests can be made to retrieve more jobs.
    """


class UploadFileRequest(BaseModel):
    purpose: str
    """The intended purpose of the uploaded file.

    Use "assistants" for Assistants and Message files, "vision" for Assistants image file inputs, "batch" for Batch API, and "fine-tune" for Fine-tuning.
    """

    file: UploadFile
    """The File object (not file name) to be uploaded."""


class FileObject(BaseModel):
    # Ordered by official OpenAI API documentation
    # https://platform.openai.com/docs/api-reference/files/object
    id: str
    """The file identifier, which can be referenced in the API endpoints."""

    bytes: int
    """The size of the file, in bytes."""

    created_at: int
    """The Unix timestamp (in seconds) for when the file was created."""

    filename: str
    """The name of the file."""

    object: str = "file"
    """The object type, which is always file."""

    purpose: str
    """The intended purpose of the file.

    Supported values are assistants, assistants_output, batch, batch_output, fine-tune, fine-tune-results and vision.
    """


class Metrics(BaseModel):
    full_valid_loss: Optional[float] = None

    full_valid_mean_token_accuracy: Optional[float] = None

    step: Optional[float] = None

    train_loss: Optional[float] = None

    train_mean_token_accuracy: Optional[float] = None

    valid_loss: Optional[float] = None

    valid_mean_token_accuracy: Optional[float] = None


class FineTuningJobCheckpoint(BaseModel):
    id: str
    """The checkpoint identifier, which can be referenced in the API endpoints."""

    created_at: int
    """The Unix timestamp (in seconds) for when the checkpoint was created."""

    fine_tuned_model_checkpoint: str
    """The name of the fine-tuned checkpoint model that is created."""

    fine_tuning_job_id: str
    """The name of the fine-tuning job that this checkpoint was created from."""

    fine_tuning_job_id: str
    """The name of the fine-tuning job that this checkpoint was created from."""

    metrics: Optional[Metrics] = None
    """Metrics at the step number during the fine-tuning job."""

    object: Literal["fine_tuning.job.checkpoint"]
    """The object type, which is always "fine_tuning.job.checkpoint"."""

    step_number: Optional[int] = None
    """The step number that the checkpoint was created at."""
