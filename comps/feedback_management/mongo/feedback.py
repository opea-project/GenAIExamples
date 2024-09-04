# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os
from typing import Annotated, Optional

from fastapi import HTTPException
from mongo_store import FeedbackStore
from pydantic import BaseModel, Field

from comps import CustomLogger
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.proto.api_protocol import ChatCompletionRequest

logger = CustomLogger("feedback_mongo")
logflag = os.getenv("LOGFLAG", False)


class FeedbackData(BaseModel):
    """This class represents the data model of FeedbackData collected to store in database.".

    Attributes:
        is_thumbs_up (bool): True if the response is satisfy, False otherwise.
        rating: (int)[Optional]: Score rating. Range from 0 (bad rating) to 5(good rating).
        comment (str)[Optional]: Comment given for response.
    """

    is_thumbs_up: bool
    rating: Annotated[Optional[int], Field(ge=0, le=5)] = None
    comment: Optional[str] = None


class ChatFeedback(BaseModel):
    """This class represents the model for chat to collect FeedbackData together with ChatCompletionRequest data to store in database.

    Attributes:
        chat_data (ChatCompletionRequest): ChatCompletionRequest object containing chat data to be stored.
        feedback_data (FeedbackData): FeedbackData object containing feedback data for chat to be stored.
        chat_id (str)[Optional]: The chat_id associated to the chat to be store together with feedback data.
        feedback_id (str)[Optional]: The feedback_id of feedback data to be retrieved from database.
    """

    chat_data: ChatCompletionRequest
    feedback_data: FeedbackData
    chat_id: Optional[str] = None
    feedback_id: Optional[str] = None


class FeedbackId(BaseModel):
    """This class represent the data model for retrieve feedback data stored in database.

    Attributes:
        user (str): The user of the requested feedback data.
        feedback_id (str): The feedback_id of feedback data to be retrieved from database.
    """

    user: str
    feedback_id: Optional[str] = None


@register_microservice(
    name="opea_service@feedback_mongo",
    endpoint="/v1/feedback/create",
    host="0.0.0.0",
    input_datatype=FeedbackData,
    port=6016,
)
async def create_feedback_data(feedback: ChatFeedback):
    """Creates and stores a feedback data in database.

    Args:
        feedback (ChatFeedback): The ChatFeedback class object containing feedback data to be stored.

    Returns:
        response (str/bool): FeedbackId of the object created in database. True if data update successfully.
    """
    if logflag:
        logger.info(feedback)

    try:
        feedback_store = FeedbackStore(feedback.chat_data.user)
        feedback_store.initialize_storage()
        if feedback.feedback_id is None:
            response = await feedback_store.save_feedback(feedback)
        else:
            response = await feedback_store.update_feedback(feedback)

        if logflag:
            logger.info(response)
        return response

    except Exception as e:
        logger.info(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@register_microservice(
    name="opea_service@feedback_mongo",
    endpoint="/v1/feedback/get",
    host="0.0.0.0",
    input_datatype=FeedbackId,
    port=6016,
)
async def get_feedback(feedback: FeedbackId):
    """Retrieves feedback_data from feedback store based on provided FeedbackId or user.

    Args:
        feedback (FeedbackId): The FeedbackId object containing user and feedback_id or chat_id.

    Returns:
        JSON: Retrieved feedback data if successful, error otherwise.
    """
    if logflag:
        logger.info(feedback)

    try:
        feedback_store = FeedbackStore(feedback.user)
        feedback_store.initialize_storage()
        if feedback.feedback_id:
            response = await feedback_store.get_feedback_by_id(feedback.feedback_id)
        else:
            response = await feedback_store.get_all_feedback_of_user()

        if logflag:
            logger.info(response)

        return response

    except Exception as e:
        logger.info(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@register_microservice(
    name="opea_service@feedback_mongo",
    endpoint="/v1/feedback/delete",
    host="0.0.0.0",
    input_datatype=FeedbackId,
    port=6016,
)
async def delete_feedback(feedback: FeedbackId):
    """Delete a feedback data from feedback store by given feedback Id.

    Args:
        feedback (FeedbackId): The FeedbackId object containing user and feedback_id or chat_id

    Returns:
        Result of deletion if successful, None otherwise.
    """
    if logflag:
        logger.info(feedback)

    try:
        feedback_store = FeedbackStore(feedback.user)
        feedback_store.initialize_storage()
        if feedback.feedback_id is None:
            raise Exception("feedback_id is required.")
        else:
            response = await feedback_store.delete_feedback(feedback.feedback_id)

        if logflag:
            logger.info(response)

        return response

    except Exception as e:
        logger.info(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    opea_microservices["opea_service@feedback_mongo"].start()
