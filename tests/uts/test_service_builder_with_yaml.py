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
from unittest.mock import patch

from comps.mega.yaml_service_builder import YAMLServiceBuilder


class TestYAMLServiceBuilder(unittest.TestCase):
    def test_schedule(self):
        service_builder = YAMLServiceBuilder(yaml_file_path="mega_service.yaml")
        service_builder.schedule(initial_inputs={"number": 0})
        service_builder.get_all_final_outputs()
        result_dict = service_builder.result_dict
        self.assertEqual(result_dict, "")


if __name__ == "__main__":
    unittest.main()
