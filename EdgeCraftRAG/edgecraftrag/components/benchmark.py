# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any, List, Optional

import requests
from edgecraftrag.base import BaseComponent, CompType, InferenceType, ModelType
from prometheus_client.parser import text_string_to_metric_families
from pydantic import BaseModel, Field, model_serializer


class Benchmark(BaseComponent):

    def __init__(self, enable_benchmark, inference_type):
        super().__init__()
        self.enabled = enable_benchmark
        self.is_vllm = True if inference_type == InferenceType.VLLM else False

        self.benchmark_data_list = {}
        self.llm_data_list = {}

        self.last_idx = 0

    def is_enabled(self):
        return self.enabled

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def init_benchmark_data(self):
        pipeline_comp = [CompType.RETRIEVER, CompType.POSTPROCESSOR, CompType.GENERATOR]
        if self.is_enabled():
            self.last_idx += 1
            idx = self.last_idx
            data = {}
            data["idx"] = idx
            for comp in pipeline_comp:
                data[comp] = ""
            self.benchmark_data_list[idx] = data
            return idx

    def update_benchmark_data(self, idx, comp_type, start, end):
        if self.is_enabled() and idx in self.benchmark_data_list and comp_type in self.benchmark_data_list[idx]:
            self.benchmark_data_list[idx][comp_type] = end - start

    def insert_llm_data(self, idx):
        if self.is_enabled():
            if self.is_vllm:
                metrics = get_vllm_metrics()
            else:
                metrics = None
            self.llm_data_list[idx] = metrics

    @model_serializer
    def ser_model(self):
        if self.enabled:
            if self.is_vllm:
                set = {
                    "Benchmark enabled": self.enabled,
                    "last_benchmark_data": (
                        self.benchmark_data_list[self.last_idx] if self.last_idx in self.benchmark_data_list else None
                    ),
                    "vllm_metrics": self.llm_data_list[self.last_idx] if self.last_idx in self.llm_data_list else None,
                }
            else:
                set = {
                    "Benchmark enabled": self.enabled,
                    "last_benchmark_data": (
                        self.benchmark_data_list[self.last_idx] if self.last_idx in self.benchmark_data_list else None
                    ),
                }
        else:
            set = {
                "Benchmark enabled": self.enabled,
            }
        return set

    def run(self, **kwargs) -> Any:
        pass


def get_vllm_metrics():

    llm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8008")
    response = requests.get(f"{llm_endpoint}/metrics", headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        metrics_data = text_string_to_metric_families(response.text)
    else:
        return None

    parsed_metrics = {}
    for family in metrics_data:
        for sample in family.samples:
            parsed_metrics[sample.name] = sample

    vllm_metrics = [
        "vllm:prompt_tokens_total",
        "vllm:generation_tokens_total",
        "vllm:time_to_first_token_seconds_sum",
        "vllm:time_to_first_token_seconds_count",
        "vllm:time_per_output_token_seconds_sum",
        "vllm:time_per_output_token_seconds_count",
        "vllm:e2e_request_latency_seconds_sum",
        "vllm:e2e_request_latency_seconds_count",
    ]
    metrics = {}
    for metric in vllm_metrics:
        if metric in parsed_metrics:
            metrics[metric] = parsed_metrics[metric].value

    if "vllm:time_to_first_token_seconds_sum" in metrics and "vllm:time_to_first_token_seconds_count" in metrics:
        metrics["average_time_to_first_token_seconds"] = (
            metrics["vllm:time_to_first_token_seconds_sum"] / metrics["vllm:time_to_first_token_seconds_count"]
            if metrics["vllm:time_to_first_token_seconds_count"] > 0
            else None
        )
    if "vllm:time_per_output_token_seconds_sum" in metrics and "vllm:time_per_output_token_seconds_count" in metrics:
        metrics["average_time_per_output_token_seconds"] = (
            metrics["vllm:time_per_output_token_seconds_sum"] / metrics["vllm:time_per_output_token_seconds_count"]
            if metrics["vllm:time_per_output_token_seconds_count"] > 0
            else None
        )
    if "vllm:e2e_request_latency_seconds_sum" in metrics and "vllm:e2e_request_latency_seconds_count" in metrics:
        metrics["average_e2e_request_latency_seconds"] = (
            metrics["vllm:e2e_request_latency_seconds_sum"] / metrics["vllm:e2e_request_latency_seconds_count"]
            if metrics["vllm:e2e_request_latency_seconds_count"] > 0
            else None
        )

    return metrics
