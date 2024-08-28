# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import unittest

import requests


class ChatQnA(unittest.TestCase):

    def test_embed(self):
        # ip_address = 0.0.0.0#os.environ.get("ip_address")
        endpoint = "http://0.0.0.0:6006/embed"

        data = {"inputs": "What is Deep Learning?"}
        response = requests.post(
            url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
        )
        # print(f"Status code: {response.status_code}")
        # print(response.json())
        self.assertEqual(response.status_code, 200)

    def test_embeddings(self):
        # ip_address = 0.0.0.0#os.environ.get("ip_address")
        endpoint = "http://0.0.0.0:6000/v1/embeddings"

        data = {"text": "hello"}
        response = requests.post(
            url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
        )
        self.assertEqual(response.status_code, 200)

    def test_retrival(self):
        # ip_address = 0.0.0.0#os.environ.get("ip_address")
        import random

        embedding = [random.uniform(-1, 1) for _ in range(768)]
        endpoint = "http://0.0.0.0:7000/v1/retrieval"

        data = {"text": '"text":"test","embedding":${embedding}'}
        response = requests.post(
            url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
        )
        self.assertEqual(response.status_code, 200)

    def test_rerank(self):
        # ip_address = 0.0.0.0#os.environ.get("ip_address")
        endpoint = "http://0.0.0.0:8808/rerank"

        data = {"query": "What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}
        response = requests.post(
            url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
        )
        self.assertEqual(response.status_code, 200)

    def test_reranking(self):
        # ip_address = 0.0.0.0#os.environ.get("ip_address")
        endpoint = "http://0.0.0.0:8000/v1/reranking"

        data = {
            "initial_query": "What is Deep Learning?",
            "retrieved_docs": [{"text": "Deep Learning is not..."}, {"text": "Deep learning is..."}],
        }
        response = requests.post(
            url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
        )
        self.assertEqual(response.status_code, 200)

    def test_llm(self):
        # ip_address = 0.0.0.0#os.environ.get("ip_address")
        endpoint = "http://0.0.0.0:9000/v1/completions"

        data = {
            "query": "What is Deep Learning?",
            "max_new_tokens": 17,
            "top_k": 10,
            "top_p": 0.95,
            "typical_p": 0.95,
            "temperature": 0.01,
            "repetition_penalty": 1.03,
            "streaming": True,
        }
        response = requests.post(
            url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
