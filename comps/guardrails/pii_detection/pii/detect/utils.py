# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import Enum, auto


class PIIEntityType(Enum):
    IP_ADDRESS = auto()
    NAME = auto()
    EMAIL = auto()
    PHONE_NUMBER = auto()
    PASSWORD = auto()
    KEY = auto()

    @classmethod
    def default(cls):
        return [PIIEntityType.IP_ADDRESS, PIIEntityType.EMAIL, PIIEntityType.PHONE_NUMBER, PIIEntityType.KEY]

    @classmethod
    def parse(cls, entity):
        if "name" == entity:
            return PIIEntityType.NAME
        elif "password" == entity:
            return PIIEntityType.PASSWORD
        elif "email" == entity:
            return PIIEntityType.EMAIL
        elif "phone_number" == entity:
            return PIIEntityType.PHONE_NUMBER
        elif "ip" == entity:
            return PIIEntityType.PHONE_NUMBER
        elif "key" == entity:
            return PIIEntityType.KEY
        else:
            raise NotImplementedError(f" entity type {entity} is not supported!")
