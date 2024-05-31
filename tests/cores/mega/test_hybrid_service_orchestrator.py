# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from comps import MicroService, ServiceOrchestrator, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8086, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


class TestServiceOrchestrator(unittest.TestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s1.start()

        self.service_builder = ServiceOrchestrator()

    def tearDown(self):
        self.s1.stop()

    def test_add_remote_service(self):
        s2 = MicroService(name="s2", host="fakehost", port=8008, endpoint="/v1/add", use_remote_service=True)
        self.service_builder.add(opea_microservices["s1"]).add(s2)
        self.service_builder.flow_to(self.s1, s2)
        self.assertEqual(s2.endpoint_path, "http://fakehost:8008/v1/add")
        # Check whether the right exception is raise when init/stop remote service
        try:
            s2.start()
        except Exception as e:
            self.assertTrue("Method not allowed" in str(e))


if __name__ == "__main__":
    unittest.main()
