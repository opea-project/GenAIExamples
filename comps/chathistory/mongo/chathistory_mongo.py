# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os
from typing import Optional

from fastapi import HTTPException
from mongo_store import DocumentStore
from pydantic import BaseModel

from comps import CustomLogger
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.proto.api_protocol import ChatCompletionRequest

logger = CustomLogger("chathistory_mongo")
logflag = os.getenv("LOGFLAG", False)


class ChatMessage(BaseModel):
    data: ChatCompletionRequest
    first_query: Optional[str] = None
    id: Optional[str] = None


class ChatId(BaseModel):
    user: str
    id: Optional[str] = None


def get_first_string(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, list):
        # Assuming we want the first string from the first dictionary
        if value and isinstance(value[0], dict):
            first_dict = value[0]
            if first_dict:
                # Get the first value from the dictionary
                first_key = next(iter(first_dict))
                return first_dict[first_key]


@register_microservice(
    name="opea_service@chathistory_mongo",
    endpoint="/v1/chathistory/create",
    host="0.0.0.0",
    input_datatype=ChatMessage,
    port=6012,
)
async def create_documents(document: ChatMessage):
    """Creates or updates a document in the document store.

    Args:
        document (ChatMessage): The ChatMessage object containing the data to be stored.

    Returns:
        The result of the operation if successful, None otherwise.
    """
    if logflag:
        logger.info(document)
    try:
        if document.data.user is None:
            raise HTTPException(status_code=500, detail="Please provide the user information")
        store = DocumentStore(document.data.user)
        store.initialize_storage()
        if document.first_query is None:
            document.first_query = get_first_string(document.data.messages)
        if document.id:
            res = await store.update_document(document.id, document.data, document.first_query)
        else:
            res = await store.save_document(document)
        if logflag:
            logger.info(res)
        return res
    except Exception as e:
        # Handle the exception here
        logger.info(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@register_microservice(
    name="opea_service@chathistory_mongo",
    endpoint="/v1/chathistory/get",
    host="0.0.0.0",
    input_datatype=ChatId,
    port=6012,
)
async def get_documents(document: ChatId):
    """Retrieves documents from the document store based on the provided ChatId.

    Args:
        document (ChatId): The ChatId object containing the user and optional document id.

    Returns:
        The retrieved documents if successful, None otherwise.
    """
    if logflag:
        logger.info(document)
    try:
        store = DocumentStore(document.user)
        store.initialize_storage()
        if document.id is None:
            res = await store.get_all_documents_of_user()
        else:
            res = await store.get_user_documents_by_id(document.id)
        if logflag:
            logger.info(res)
        return res
    except Exception as e:
        # Handle the exception here
        logger.info(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@register_microservice(
    name="opea_service@chathistory_mongo",
    endpoint="/v1/chathistory/delete",
    host="0.0.0.0",
    input_datatype=ChatId,
    port=6012,
)
async def delete_documents(document: ChatId):
    """Deletes a document from the document store based on the provided ChatId.

    Args:
        document (ChatId): The ChatId object containing the user and document id.

    Returns:
        The result of the deletion if successful, None otherwise.
    """
    if logflag:
        logger.info(document)
    try:
        store = DocumentStore(document.user)
        store.initialize_storage()
        if document.id is None:
            raise Exception("Document id is required.")
        else:
            res = await store.delete_document(document.id)
        if logflag:
            logger.info(res)
        return res
    except Exception as e:
        # Handle the exception here
        logger.info(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    opea_microservices["opea_service@chathistory_mongo"].start()
