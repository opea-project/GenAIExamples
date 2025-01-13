# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from concurrent import futures
from typing import Union

import requests

from comps import (
    CustomLogger,
    LVMDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("lvm-llama-vision-tp-native")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@lvm_llama_vision_tp_native",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9599,
)
@register_statistics(names=["opea_service@lvm_llama_vision_tp_native"])
async def lvm(request: Union[LVMDoc]) -> Union[TextDoc]:
    if logflag:
        logger.info(request)

    start = time.time()
    # Initialize responses list
    responses = []

    # Function to send requests to individual TP workers
    def send_request_to_tp_worker(port):
        try:
            # Build the worker URL dynamically
            url = f"http://127.0.0.1:{port}/v1/lvm_serve"
            # Send POST request to the TP worker
            response = requests.post(url, json=request.dict())
            response.raise_for_status()  # Ensure the request was successful

            # Parse and process the response
            json_response = response.json()
            responses.append(TextDoc(text=json_response.get("text", "")))

        except requests.exceptions.RequestException as e:
            # Log any errors that occur
            logger.error(f"Error sending request to TP worker on port {port}: {e}")
            return None

    # Distribute work across TP workers using ThreadPoolExecutor
    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        # TP worker ports (e.g., worker processes listen on sequential ports)
        worker_ports = [9393 + i + 1 for i in range(4)]
        # Map the `send_request_to_tp_worker` function to each worker port
        executor.map(send_request_to_tp_worker, worker_ports)

    statistics_dict["opea_service@lvm_llama_vision_tp_native"].append_latency(time.time() - start, None)
    if responses:
        return responses[0]


if __name__ == "__main__":
    opea_microservices["opea_service@lvm_llama_vision_tp_native"].start()
