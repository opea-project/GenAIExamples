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
import traceback
from typing import AsyncIterator, List

from fastapi import HTTPException, Request, status
from pydantic import ValidationError as PydanticValidationError
from rayllm.api_openai_backend.openai_protocol import ErrorResponse, FinishReason, ModelResponse, Prompt
from starlette.responses import JSONResponse


class OpenAIHTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        type: str = "Unknown",
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.type = type


def openai_exception_handler(r: Request, exc: OpenAIHTTPException):
    assert isinstance(exc, OpenAIHTTPException), f"Unable to handle invalid exception {type(exc)}"
    if exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        message = "Internal Server Error"
        internal_message = message
        exc_type = "InternalServerError"
    else:
        internal_message = extract_message_from_exception(exc)
        message = exc.message
        exc_type = exc.type
    err_response = ModelResponse(
        error=ErrorResponse(
            message=message,
            code=exc.status_code,
            internal_message=internal_message,
            type=exc_type,
        )
    )
    return JSONResponse(content=err_response.dict(), status_code=exc.status_code)


def extract_message_from_exception(e: Exception) -> str:
    # If the exception is a Ray exception, we need to dig through the text to get just
    # the exception message without the stack trace
    # This also works for normal exceptions (we will just return everything from
    # format_exception_only in that case)
    message_lines = traceback.format_exception_only(type(e), e)[-1].strip().split("\n")
    message = ""
    # The stack trace lines will be prefixed with spaces, so we need to start
    # from the bottom and stop at the last line before a line with a space
    found_last_line_before_stack_trace = False
    for line in reversed(message_lines):
        if not line.startswith(" "):
            found_last_line_before_stack_trace = True
        if found_last_line_before_stack_trace and line.startswith(" "):
            break
        message = line + "\n" + message
    message = message.strip()
    return message


async def handle_request(
    model: str,
    request_id: str,
    prompt: Prompt,
    async_iterator: AsyncIterator[ModelResponse],
):
    # Handle errors for an ModelResopnse stream.
    model_tags = {"model_id": model}
    print("handle_request: ", model_tags)

    responses: List[ModelResponse] = []
    try:
        async for response in async_iterator:
            responses.append(response)
            yield response
    except asyncio.CancelledError as e:
        # The request is cancelled. Try to return a last Model response, then raise
        # We raise here because we don't want to interrupt the cancellation
        yield _get_response_for_error(e, request_id=request_id)
        raise
    except Exception as e:
        # Something went wrong.
        yield _get_response_for_error(e, request_id=request_id)
        # DO NOT RAISE.
        # We do not raise here because that would cause a disconnection for streaming.


def _get_response_for_error(e, request_id: str):
    """Convert an exception to an ModelResponse object."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(e, HTTPException):
        status_code = e.status_code
    elif isinstance(e, OpenAIHTTPException):
        status_code = e.status_code
    elif isinstance(e, PydanticValidationError):
        status_code = 400
    else:
        # Try to get the status code attribute
        status_code = getattr(e, "status_code", status_code)

    if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        message = "Internal Server Error"
        exc_type = "InternalServerError"
    else:
        message = extract_message_from_exception(e)
        exc_type = e.__class__.__name__

    message += f" (Request ID: {request_id})"

    return ModelResponse(
        error=ErrorResponse(
            message=message,
            code=status_code,
            internal_message=message,
            type=exc_type,
        ),
        finish_reason=FinishReason.ERROR,
    )
