# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import motor.motor_asyncio as motor
from config import DB_NAME, MONGO_HOST, MONGO_PORT


class MongoClient:
    conn_url = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

    @staticmethod
    def get_db_client() -> Any:
        try:
            client = motor.AsyncIOMotorClient(MongoClient.conn_url)
            db = client[DB_NAME]
            return db

        except Exception as e:
            print(e)
            raise Exception()
