# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from comps import BaseService, ServiceBuilder


class TestServiceBuilder(unittest.TestCase):
    def setUp(self):
        self.service_builder = ServiceBuilder(port=1234, hostfile=None)
        self.s1 = BaseService(id="s1", endpoint="http://localhost:8081/v1/add")
        self.s2 = BaseService(id="s2", endpoint="http://localhost:8082/v1/add")
        self.s3 = BaseService(id="s3", endpoint="http://localhost:8083/v1/add")
        self.s4 = BaseService(id="s4", endpoint="http://localhost:8084/v1/add")
        self.s5 = BaseService(id="s5", endpoint="http://localhost:8085/v1/add")
        self.service_builder.add(self.s1).add(self.s2).add(self.s3).add(self.s4).add(self.s5)
        self.service_builder.flow_to(self.s1, self.s2)
        self.service_builder.flow_to(self.s5, self.s2)
        self.service_builder.flow_to(self.s2, self.s3)
        self.service_builder.flow_to(self.s2, self.s4)
        self.service_builder.flow_to(self.s3, self.s4)

    def test_schedule(self):
        self.service_builder.schedule(initial_inputs={"number": 0})
        self.service_builder.get_all_final_outputs()
        result_dict = self.service_builder.result_dict
        self.assertEqual(result_dict, "")


if __name__ == "__main__":
    unittest.main()
