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


import inspect
from functools import wraps

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

in_memory_exporter = InMemorySpanExporter()
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(HTTPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(in_memory_exporter))
tracer = trace.get_tracer(__name__)


def opea_telemetry(func):
    print(f"[*** telemetry ***] {func.__name__} under telemetry.")
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(func.__name__):
                res = await func(*args, **kwargs)
            return res

    else:

        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(func.__name__):
                res = func(*args, **kwargs)
            return res

    return wrapper
