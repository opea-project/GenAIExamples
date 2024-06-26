# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import List

from .detect.emails_detection import detect_email
from .detect.ip_detection import detect_ip
from .detect.keys_detection import detect_keys
from .detect.name_password_detection import detect_name_password
from .detect.phones_detection import detect_phones
from .detect.utils import PIIEntityType


class PIIDetector:
    def __init__(strategy: str):
        pass

    def detect_pii(self, data):
        import random

        return random.choice([True, False])


class PIIDetectorWithLLM(PIIDetector):
    def __init__(self):
        super().__init__()

    def detect_pii(self, text):
        return True


class PIIDetectorWithNER(PIIDetector):
    def __init__(self, model_path=None):
        super().__init__()
        from transformers import AutoTokenizer, pipeline

        _model_key = "bigcode/starpii"
        _model_key = _model_key if model_path is None else os.path.join(model_path, _model_key)
        try:
            tokenizer = AutoTokenizer.from_pretrained(_model_key, model_max_length=512)
            self.pipeline = pipeline(
                model=_model_key, task="token-classification", tokenizer=tokenizer, grouped_entities=True
            )
        except Exception as e:
            print("Failed to load model, skip NER classification", e)
            self.pipeline = None

    def detect_pii(self, text):
        result = []
        # use a regex to detect ip addresses

        entity_types = PIIEntityType.default()

        if PIIEntityType.IP_ADDRESS in entity_types:
            result = result + detect_ip(text)
        # use a regex to detect emails
        if PIIEntityType.EMAIL in entity_types:
            result = result + detect_email(text)
        # for phone number use phonenumbers tool
        if PIIEntityType.PHONE_NUMBER in entity_types:
            result = result + detect_phones(text)
        if PIIEntityType.KEY in entity_types:
            result = result + detect_keys(text)

        if PIIEntityType.NAME in entity_types or PIIEntityType.PASSWORD in entity_types:
            result = result + detect_name_password(text, self.pipeline, entity_types)

        return True if len(result) > 0 else False  # Dummy function, replace with actual logic


class PIIDetectorWithML(PIIDetector):
    def __init__(self):
        super().__init__()

    def detect_pii(self, text):
        return True
