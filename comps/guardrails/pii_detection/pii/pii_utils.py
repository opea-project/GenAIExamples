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
            print("NER detector instantiated successfully!")
        except Exception as e:
            print("Failed to load model, skip NER classification", e)
            self.pipeline = None

    def detect_pii(self, text):
        print("Scanning text with NER detector...")
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
        import joblib
        from huggingface_hub import hf_hub_download
        from sentence_transformers import SentenceTransformer

        super().__init__()
        print("Loading embedding model...")
        embed_model_id = "nomic-ai/nomic-embed-text-v1"
        self.model = SentenceTransformer(model_name_or_path=embed_model_id, trust_remote_code=True)

        print("Loading classifier model...")
        REPO_ID = "Intel/business_safety_logistic_regression_classifier"
        FILENAME = "lr_clf.joblib"

        self.clf = joblib.load(hf_hub_download(repo_id=REPO_ID, filename=FILENAME))

        print("ML detector instantiated successfully!")

    def detect_pii(self, text):
        # text is a string
        print("Scanning text with ML detector...")
        embeddings = self.model.encode(text, convert_to_tensor=True).reshape(1, -1).cpu()
        predictions = self.clf.predict(embeddings)
        return True if predictions[0] == 1 else False
