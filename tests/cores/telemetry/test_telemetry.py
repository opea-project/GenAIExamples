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

import asyncio
import time
import unittest

from comps import opea_telemetry
from comps.cores.telemetry.opea_telemetry import in_memory_exporter


@opea_telemetry
def dummy_func_child():
    return


@opea_telemetry
def dummy_func():
    time.sleep(1)
    dummy_func_child()


@opea_telemetry
async def dummy_async_func_child():
    return


@opea_telemetry
async def dummy_async_func():
    await asyncio.sleep(2)
    await dummy_async_func_child()


class TestTelemetry(unittest.TestCase):

    def test_time_tracing(self):
        dummy_func()
        asyncio.run(dummy_async_func())
        time.sleep(2)  # wait until all telemetries are finished
        self.assertEqual(len(in_memory_exporter.get_finished_spans()), 4)

        for i in in_memory_exporter.get_finished_spans():
            if i.name == "dummy_func":
                self.assertTrue(int((i.end_time - i.start_time) / 1e9) == 1)
            elif i.name == "dummy_async_func":
                self.assertTrue(int((i.end_time - i.start_time) / 1e9) == 2)
        in_memory_exporter.clear()

    def test_call_tracing(self):
        dummy_func()
        asyncio.run(dummy_async_func())
        time.sleep(2)  # wait until all telemetries are finished
        self.assertEqual(len(in_memory_exporter.get_finished_spans()), 4)
        for i in in_memory_exporter.get_finished_spans():
            if i.name == "dummy_func":
                dummy_func_trace_id = i.get_span_context().trace_id
            elif i.name == "dummy_func_child":
                dummy_func_child_parent_id = i.parent.trace_id
            elif i.name == "dummy_async_func":
                dummy_async_func_id = i.get_span_context().trace_id
            elif i.name == "dummy_async_func_child":
                dummy_async_func_child_parent_id = i.parent.trace_id
            else:
                self.assertTrue(False)
        self.assertEqual(dummy_func_trace_id, dummy_func_child_parent_id)
        self.assertEqual(dummy_async_func_id, dummy_async_func_child_parent_id)
        in_memory_exporter.clear()


if __name__ == "__main__":
    unittest.main()
