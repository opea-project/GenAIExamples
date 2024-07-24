# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json

import bson.errors as BsonError
from bson.objectid import ObjectId
from config import COLLECTION_NAME
from mongo_conn import MongoClient


class PromptStore:

    def __init__(
        self,
        user: str,
    ):
        self.user = user

    def initialize_storage(self) -> None:
        self.db_client = MongoClient.get_db_client()
        self.collection = self.db_client[COLLECTION_NAME]

    async def save_prompt(self, prompt) -> str:
        """Stores a new prompt into the storage.

        Args:
            prompt: The document to be stored.

        Returns:
            str: The ID of the inserted prompt.

        Raises:
            Exception: If an error occurs while storing the prompt.
        """
        try:
            inserted_prompt = await self.collection.insert_one(
                prompt.model_dump(by_alias=True, mode="json", exclude={"id"})
            )
            prompt_id = str(inserted_prompt.inserted_id)
            return prompt_id

        except Exception as e:
            print(e)
            raise Exception(e)

    async def get_all_prompt_of_user(self) -> list[dict]:
        """Retrieves all prompts of a user from the collection.

        Returns:
            list[dict] | None: List of dict of prompts of the user, None otherwise.

        Raises:
            Exception: If there is an error while retrieving data.
        """
        try:
            prompt_list: list = []
            cursor = self.collection.find({"user": self.user}, {"data": 0})

            async for document in cursor:
                document["id"] = str(document["_id"])
                del document["_id"]
                prompt_list.append(document)
            return prompt_list

        except Exception as e:
            print(e)
            raise Exception(e)

    async def get_user_prompt_by_id(self, prompt_id) -> dict | None:
        """Retrieves a user prompt from the collection based on the given prompt ID.

        Args:
            prompt_id (str): The ID of the prompt to retrieve.

        Returns:
            dict | None: The user prompt if found, None otherwise.

        Raises:
            Exception: If there is an error while retrieving data.
        """
        try:
            _id = ObjectId(prompt_id)
            response: dict | None = await self.collection.find_one({"_id": _id, "user": self.user})
            if response:
                del response["_id"]
                return response["prompt_text"]
            return None

        except BsonError.InvalidId as e:
            print(e)
            raise KeyError(e)

        except Exception as e:
            print(e)
            raise Exception(e)

    async def prompt_search(self, keyword) -> list | None:
        """Retrieves prompt from the collection based on keyword provided.

        Args:
            keyword (str): The keyword of prompt to search for.

        Returns:
            list | None: The list of relevant prompt if found, None otherwise.

        Raises:
            Exception: If there is an error while searching data.
        """
        try:
            # Create a text index if not already created
            self.collection.create_index([("$**", "text")])
            # Perform text search
            results = self.collection.find({"$text": {"$search": keyword}}, {"score": {"$meta": "textScore"}})
            sorted_results = results.sort([("score", {"$meta": "textScore"})])

            # Return a list of top 5 most relevant data
            relevant_data = await sorted_results.to_list(length=5)

            # Serialize data and return
            serialized_data = [
                {"id": str(doc["_id"]), "prompt_text": doc["prompt_text"], "user": doc["user"], "score": doc["score"]}
                for doc in relevant_data
            ]

            return serialized_data

        except Exception as e:
            print(e)
            raise Exception(e)

    async def delete_prompt(self, prompt_id) -> bool:
        """Delete a prompt from collection by given prompt_id.

        Args:
            prompt_id(str): The ID of the prompt to be deleted.

        Returns:
            bool: True if prompt is successfully deleted, False otherwise.

        Raises:
            KeyError: If the provided prompt_id is invalid:
            Exception: If any errors occurs during delete process.
        """
        try:
            _id = ObjectId(prompt_id)
            result = await self.collection.delete_one({"_id": _id, "user": self.user})

            delete_count = result.deleted_count
            print(f"Deleted {delete_count} documents!")

            return True if delete_count == 1 else False

        except BsonError.InvalidId as e:
            print(e)
            raise KeyError(e)

        except Exception as e:
            print(e)
            raise Exception(e)
