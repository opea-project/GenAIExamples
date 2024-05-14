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

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, TypeVar, Union

import yaml
from pydantic import BaseModel, Field, root_validator

TModel = TypeVar("TModel", bound="ModelList")
TCompletion = TypeVar("TCompletion", bound="CompletionResponse")
TChatCompletion = TypeVar("TChatCompletion", bound="ChatCompletionResponse")
ModelT = TypeVar("ModelT", bound=BaseModel)


class ErrorResponse(BaseModel):
    object: str = "error"
    message: str
    internal_message: str
    type: str
    param: Dict[str, Any] = {}
    code: int


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "llmonray"
    root: Optional[str] = None
    parent: Optional[str] = None


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard] = []


class UsageInfo(BaseModel):
    prompt_tokens: int
    total_tokens: int
    completion_tokens: Optional[int] = 0

    @classmethod
    def from_response(cls, response: Union["ModelResponse", Dict[str, Any]]) -> "UsageInfo":
        if isinstance(response, BaseModel):
            response_dict = response.dict()
        else:
            response_dict = response
        return cls(
            prompt_tokens=response_dict["num_input_tokens"] or 0,
            completion_tokens=response_dict["num_generated_tokens"] or 0,
            total_tokens=(response_dict["num_input_tokens"] or 0) + (response_dict["num_generated_tokens"] or 0),
        )


class CompletionResponseChoice(BaseModel):
    index: int
    text: str
    logprobs: Optional[int] = None
    finish_reason: Optional[str]


class CompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{str(uuid.uuid4().hex)}")
    object: str = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[CompletionResponseChoice]
    usage: Optional[UsageInfo]


class FunctionCall(BaseModel):
    name: str
    arguments: Optional[str] = None


class ToolCall(BaseModel):
    function: FunctionCall
    type: Literal["function"]
    id: str

    def __str__(self):
        return str(self.dict())


class ChatMessage(BaseModel):
    role: Literal["system", "assistant", "user", "tool"]
    content: Optional[Union[str, list]] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

    def __str__(self):
        # if tool_calls is not None, then we are passing a tool message
        # using get attr instead of  just in case the attribute is deleted off of
        # the object
        if getattr(self, "tool_calls", None):
            return str(self.content)
        return str(self.dict())


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str]


class Function(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ToolChoice(BaseModel):
    type: Literal["function"]
    function: Function


class Tool(BaseModel):
    type: Literal["function"]
    function: Function


class DeltaRole(BaseModel):
    role: Literal["system", "assistant", "user"]

    def __str__(self):
        return self.role


class DeltaEOS(BaseModel):
    class Config:
        extra = "forbid"


class DeltaContent(BaseModel):
    content: str
    tool_calls: Optional[List[ToolCall]] = None

    def __str__(self):
        if self.tool_calls:
            return str(self.tool_calls)
        else:
            return str(self.dict())


class DeltaChoices(BaseModel):
    delta: Union[DeltaRole, DeltaContent, DeltaEOS]
    index: int
    finish_reason: Optional[str]


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{str(uuid.uuid4().hex)}")
    object: str
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Union[ChatCompletionResponseChoice, DeltaChoices]]
    usage: Optional[UsageInfo]


class Prompt(BaseModel):
    prompt: Union[str, List[ChatMessage]]
    use_prompt_format: bool = True
    parameters: Optional[Union[Dict[str, Any], BaseModel]] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Union[Literal["auto", "none"], ToolChoice] = "auto"


class BaseModelExtended(BaseModel):
    @classmethod
    def parse_yaml(cls: Type[ModelT], file, **kwargs) -> ModelT:
        kwargs.setdefault("Loader", yaml.SafeLoader)
        dict_args = yaml.load(file, **kwargs)
        return cls.parse_obj(dict_args)

    def yaml(
        self,
        *,
        stream=None,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: Union[bool, None] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        **kwargs,
    ):
        """Generate a YAML representation of the model, `include` and `exclude`
        arguments as per `dict()`."""
        return yaml.dump(
            self.dict(
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                skip_defaults=skip_defaults,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            ),
            stream=stream,
            **kwargs,
        )


class ComputedPropertyMixin:
    """Include properties in the dict and json representations of the model."""

    # Replace with pydantic.computed_field once it's available
    @classmethod
    def get_properties(cls):
        return [prop for prop in dir(cls) if isinstance(getattr(cls, prop), property)]

    def dict(self, *args, **kwargs):
        self.__dict__.update({prop: getattr(self, prop) for prop in self.get_properties()})
        return super().dict(*args, **kwargs)  # type: ignore

    def json(
        self,
        *args,
        **kwargs,
    ) -> str:
        self.__dict__.update({prop: getattr(self, prop) for prop in self.get_properties()})

        return super().json(*args, **kwargs)  # type: ignore


class ModelResponse(ComputedPropertyMixin, BaseModelExtended):
    generated_text: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    num_input_tokens: Optional[int] = None
    num_input_tokens_batch: Optional[int] = None
    num_generated_tokens: Optional[int] = None
    num_generated_tokens_batch: Optional[int] = None
    preprocessing_time: Optional[float] = None
    generation_time: Optional[float] = None
    timestamp: Optional[float] = Field(default_factory=time.time)
    finish_reason: Optional[str] = None
    error: Optional[ErrorResponse] = None

    @root_validator(skip_on_failure=True)
    def text_or_error_or_finish_reason(cls, values):
        if values.get("generated_text") is None and values.get("error") is None and values.get("finish_reason") is None:
            raise ValueError("Either 'generated_text' or 'error' or 'finish_reason' must be set")
        return values

    @classmethod
    def merge_stream(cls, *responses: "ModelResponse") -> "ModelResponse":
        """Merge a stream of responses into a single response.

        The generated text is concatenated. Fields are maxed, except for
        num_generated_tokens and generation_time, which are summed.
        """
        if len(responses) == 1:
            return responses[0]

        generated_text = "".join([response.generated_text or "" for response in responses])
        num_input_tokens = [
            response.num_input_tokens for response in responses if response.num_input_tokens is not None
        ]
        max_num_input_tokens = max(num_input_tokens) if num_input_tokens else None
        num_input_tokens_batch = [
            response.num_input_tokens_batch for response in responses if response.num_input_tokens_batch is not None
        ]
        max_num_input_tokens_batch = max(num_input_tokens_batch) if num_input_tokens_batch else None
        num_generated_tokens = [
            response.num_generated_tokens for response in responses if response.num_generated_tokens is not None
        ]
        total_generated_tokens = sum(num_generated_tokens) if num_generated_tokens else None
        num_generated_tokens_batch = [
            response.num_generated_tokens_batch
            for response in responses
            if response.num_generated_tokens_batch is not None
        ]
        total_generated_tokens_batch = sum(num_generated_tokens_batch) if num_generated_tokens_batch else None
        preprocessing_time = [
            response.preprocessing_time for response in responses if response.preprocessing_time is not None
        ]
        max_preprocessing_time = max(preprocessing_time) if preprocessing_time else None
        generation_time = [response.generation_time for response in responses if response.generation_time is not None]
        total_generation_time = sum(generation_time) if generation_time else None
        error = next((response.error for response in reversed(responses) if response.error), None)

        return cls(
            generated_text=generated_text,
            num_input_tokens=max_num_input_tokens,
            num_input_tokens_batch=max_num_input_tokens_batch,
            num_generated_tokens=total_generated_tokens,
            num_generated_tokens_batch=total_generated_tokens_batch,
            preprocessing_time=max_preprocessing_time,
            generation_time=total_generation_time,
            timestamp=responses[-1].timestamp,
            finish_reason=responses[-1].finish_reason,
            error=error,
        )

    @property
    def total_time(self) -> Optional[float]:
        if self.generation_time is None and self.preprocessing_time is None:
            return None
        return (self.preprocessing_time or 0) + (self.generation_time or 0)

    @property
    def num_total_tokens(self) -> Optional[float]:
        try:
            return (self.num_input_tokens or 0) + (self.num_generated_tokens or 0)
        except Exception:
            return None

    @property
    def num_total_tokens_batch(self) -> Optional[float]:
        try:
            return (self.num_input_tokens_batch or 0) + (self.num_generated_tokens_batch or 0)
        except Exception:
            return None

    def unpack(self) -> Tuple["ModelResponse", ...]:
        return (self,)


class CompletionRequest(BaseModel):
    model: str
    prompt: str
    suffix: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: int = 1
    max_tokens: Optional[int] = 16
    stop: Optional[List[str]] = None
    stream: bool = False
    echo: Optional[bool] = False
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logprobs: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: int = 1
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logprobs: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Union[Literal["auto", "none"], ToolChoice] = "auto"
    ignore_eos: bool = False  # used in vllm engine benchmark


class FinishReason(str, Enum):
    LENGTH = "length"
    STOP = "stop"
    ERROR = "error"
    CANCELLED = "cancelled"
    TOOL_CALLS = "tool_calls"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_vllm_finish_reason(cls, finish_reason: Optional[str]) -> Optional["FinishReason"]:
        if finish_reason is None:
            return None
        if finish_reason == "stop":
            return cls.STOP
        if finish_reason == "length":
            return cls.LENGTH
        if finish_reason == "abort":
            return cls.CANCELLED
        return cls.STOP
