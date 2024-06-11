# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np

# name => statistic dict
statistics_dict = {}


class BaseStatistics:
    """Base class to store in-memory statistics of an entity for measurement in one service."""

    def __init__(
        self,
    ):
        self.response_times = []  # store responses time for all requests
        self.first_token_latencies = []  # store first token latencies for all requests

    def append_latency(self, latency, first_token_latency=None):
        self.response_times.append(latency)
        if first_token_latency:
            self.first_token_latencies.append(first_token_latency)

    def calcuate_statistics(self):
        if not self.response_times:
            return {
                "p50_latency": None,
                "p99_latency": None,
                "average_latency": None,
            }
        # Calculate the P50 (median)
        p50 = np.percentile(self.response_times, 50)

        # Calculate the P99
        p99 = np.percentile(self.response_times, 99)

        avg = np.average(self.response_times)

        return {
            "p50_latency": p50,
            "p99_latency": p99,
            "average_latency": avg,
        }

    def calcuate_first_token_statistics(self):
        if not self.first_token_latencies:
            return {
                "p50_latency_first_token": None,
                "p99_latency_first_token": None,
                "average_latency_first_token": None,
            }
        # Calculate the P50 (median)
        p50 = np.percentile(self.first_token_latencies, 50)

        # Calculate the P99
        p99 = np.percentile(self.first_token_latencies, 99)

        avg = np.average(self.first_token_latencies)

        return {
            "p50_latency_first_token": p50,
            "p99_latency_first_token": p99,
            "average_latency_first_token": avg,
        }


def register_statistics(
    names,
):
    def decorator(func):
        for name in names:
            statistics_dict[name] = BaseStatistics()
        return func

    return decorator


def collect_all_statistics():
    results = {}
    if statistics_dict:
        for name, statistic in statistics_dict.items():
            tmp_dict = statistic.calcuate_statistics()
            tmp_dict.update(statistic.calcuate_first_token_statistics())
            results.update({name: tmp_dict})
    return results
