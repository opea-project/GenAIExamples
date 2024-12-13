# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import multiprocessing
import unittest

from fastapi.testclient import TestClient

from comps import MicroService, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8080, endpoint="/v1/add")
async def add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "OPEA Project!"
    return {"text": text}


def sum_test():
    return 1 + 1


class TestMicroService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(opea_microservices["s1"].app)

        opea_microservices["s1"].add_route("/v1/sum", sum_test, methods=["GET"])
        self.process1 = multiprocessing.Process(target=opea_microservices["s1"].start, daemon=False, name="s1")

        self.process1.start()

        self.assertRaises(RuntimeError, MicroService, name="s2", host="0.0.0.0", port=8080, endpoint="/v1/add")

    def tearDown(self):
        opea_microservices["s1"].stop()
        self.process1.terminate()

    def test_add_route(self):
        response = self.client.post("/v1/add", json={"text": "Hello, "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Hello, OPEA Project!")
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/v1/health_check")
        self.assertEqual(
            response.json(), {"Service Title": "s1", "Service Description": "OPEA Microservice Infrastructure"}
        )

        response = self.client.get("/v1/sum")
        self.assertEqual(response.json(), 2)


if __name__ == "__main__":
    unittest.main()
