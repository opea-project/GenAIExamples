# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import bson.errors as BsonError
from bson.objectid import ObjectId
from config import COLLECTION_NAME
from mongo_conn import MongoClient


class FeedbackStore:

    def __init__(
        self,
        user: str,
    ):
        self.user = user

    def initialize_storage(self) -> None:
        self.db_client = MongoClient.get_db_client()
        self.collection = self.db_client[COLLECTION_NAME]

    async def save_feedback(self, feedback_data) -> str:
        """Stores a new feedback data into the storage.

        Args:
            feedback_data (object): The document to be stored.

        Returns:
            str: The ID of the inserted feedback data.

        Raises:
            Exception: If an error occurs while storing the feedback_data.
        """
        try:
            inserted_feedback_data = await self.collection.insert_one(
                feedback_data.model_dump(by_alias=True, mode="json", exclude={"feedback_id"})
            )
            feedback_id = str(inserted_feedback_data.inserted_id)
            return feedback_id

        except Exception as e:
            print(e)
            raise Exception(e)

    async def update_feedback(self, feedback_data) -> bool:
        """Update a feedback data in the collection with given id.

        Args:
            feedback_id (str): The ID of the data to be updated.
            updated_data (object):  The data to be updated in the entry.

        Returns:
            bool: True if the data updated successfully, False otherwise.
        """
        try:
            _id = ObjectId(feedback_data.feedback_id)
            updated_result = await self.collection.update_one(
                {"_id": _id, "chat_data.user": self.user},
                {"$set": {"feedback_data": feedback_data.feedback_data.model_dump(by_alias=True, mode="json")}},
            )

            if updated_result.modified_count == 1:
                print(f"Updated document: {feedback_data.feedback_id} !")
                return True
            else:
                raise Exception("Not able to update the data.")

        except BsonError.InvalidId as e:
            print(e)
            raise KeyError(e)

        except Exception as e:
            print(e)
            raise Exception(e)

    async def get_all_feedback_of_user(self) -> list[dict]:
        """Retrieves all feedback data of a user from the collection.

        Returns:
            list[dict] | None: List of dict of feedback data of the user, None otherwise.

        Raises:
            Exception: If there is an error while retrieving data.
        """
        try:
            feedback_data_list: list = []
            cursor = self.collection.find({"chat_data.user": self.user}, {"feedback_data": 0})

            async for document in cursor:
                document["feedback_id"] = str(document["_id"])
                del document["_id"]
                feedback_data_list.append(document)
            return feedback_data_list

        except Exception as e:
            print(e)
            raise Exception(e)

    async def get_feedback_by_id(self, feedback_id) -> dict | None:
        """Retrieves a user feedback data from the collection based on the given feedback ID.

        Args:
            feedback_id (str): The ID of the feedback data to retrieve.

        Returns:
            dict | None: The user's feedback data if found, None otherwise.

        Raises:
            Exception: If there is an error while retrieving data.
        """
        try:
            _id = ObjectId(feedback_id)
            response: dict | None = await self.collection.find_one({"_id": _id, "chat_data.user": self.user})
            if response:
                del response["_id"]
                return response
            return None

        except BsonError.InvalidId as e:
            print(e)
            raise KeyError(e)

        except Exception as e:
            print(e)
            raise Exception(e)

    async def delete_feedback(self, feedback_id) -> bool:
        """Delete a feedback data from collection by given feedback_id.

        Args:
            feedback_id(str): The ID of the feedback data to be deleted.

        Returns:
            bool: True if feedback is successfully deleted, False otherwise.

        Raises:
            KeyError: If the provided feedback_id is invalid:
            Exception: If any errors occurs during delete process.
        """
        try:
            _id = ObjectId(feedback_id)
            result = await self.collection.delete_one({"_id": _id, "chat_data.user": self.user})

            delete_count = result.deleted_count
            print(f"Deleted {delete_count} documents!")

            return True if delete_count == 1 else False

        except BsonError.InvalidId as e:
            print(e)
            raise KeyError(e)

        except Exception as e:
            print(e)
            raise Exception(e)
