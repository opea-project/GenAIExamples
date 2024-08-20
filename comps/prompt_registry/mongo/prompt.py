# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os
from typing import Optional

from mongo_store import PromptStore
from pydantic import BaseModel

from comps import CustomLogger
from comps.cores.mega.micro_service import opea_microservices, register_microservice

logger = CustomLogger("prompt_mongo")
logflag = os.getenv("LOGFLAG", False)


class PromptCreate(BaseModel):
    """This class represents the data model for creating and storing a new prompt in the database.

    Attributes:
        prompt_text (str): The text content of the prompt.
        user (str): The user or creator of the prompt.
    """

    prompt_text: str
    user: str


class PromptId(BaseModel):
    """This class represent the data model for retrieve prompt stored in database.

    Attributes:
        user (str): The user of the requested prompt.
        prompt_id (str): The prompt_id of prompt to be retrieved from database.
    """

    user: str
    prompt_id: Optional[str] = None
    prompt_text: Optional[str] = None


@register_microservice(
    name="opea_service@prompt_mongo",
    endpoint="/v1/prompt/create",
    host="0.0.0.0",
    input_datatype=PromptCreate,
    port=6012,
)
async def create_prompt(prompt: PromptCreate):
    """Creates and stores a prompt in prompt store.

    Args:
        prompt (PromptCreate): The PromptCreate class object containing the data to be stored.

    Returns:
        JSON (PromptResponse): PromptResponse class object, None otherwise.
    """
    if logflag:
        logger.info(prompt)
    try:
        prompt_store = PromptStore(prompt.user)
        prompt_store.initialize_storage()
        response = await prompt_store.save_prompt(prompt)
        if logflag:
            logger.info(response)
        return response

    except Exception as e:
        logger.info(f"An error occurred: {str(e)}")
        return None


@register_microservice(
    name="opea_service@prompt_mongo",
    endpoint="/v1/prompt/get",
    host="0.0.0.0",
    input_datatype=PromptId,
    port=6012,
)
async def get_prompt(prompt: PromptId):
    """Retrieves prompt from prompt store based on provided PromptId or user.

    Args:
        prompt (PromptId): The PromptId object containing user and prompt_id.

    Returns:
        JSON: Retrieved prompt data if successful, None otherwise.
    """
    if logflag:
        logger.info(prompt)
    try:
        prompt_store = PromptStore(prompt.user)
        prompt_store.initialize_storage()
        if prompt.prompt_id is not None:
            response = await prompt_store.get_user_prompt_by_id(prompt.prompt_id)
        elif prompt.prompt_text:
            response = await prompt_store.prompt_search(prompt.prompt_text)
        else:
            response = await prompt_store.get_all_prompt_of_user()
        if logflag:
            logger.info(response)
        return response

    except Exception as e:
        logger.info(f"An error occurred: {str(e)}")
        return None


@register_microservice(
    name="opea_service@prompt_mongo",
    endpoint="/v1/prompt/delete",
    host="0.0.0.0",
    input_datatype=PromptId,
    port=6012,
)
async def delete_prompt(prompt: PromptId):
    """Delete a prompt from prompt store by given PromptId.

    Args:
        prompt (PromptId): The PromptId object containing user and prompt_id.

    Returns:
        Result of deletion if successful, None otherwise.
    """
    if logflag:
        logger.info(prompt)
    try:
        prompt_store = PromptStore(prompt.user)
        prompt_store.initialize_storage()
        if prompt.prompt_id is None:
            raise Exception("Prompt id is required.")
        else:
            response = await prompt_store.delete_prompt(prompt.prompt_id)
        if logflag:
            logger.info(response)
        return response

    except Exception as e:
        logger.info(f"An error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    opea_microservices["opea_service@prompt_mongo"].start()
