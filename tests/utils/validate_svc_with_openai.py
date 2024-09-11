#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import sys

import openai


def validate_svc(ip_address, service_port, service_type):
    openai.api_key = os.getenv("OPENAI_API_KEY", "empty")

    endpoint = f"http://{ip_address}:{service_port}"
    client = openai.OpenAI(
        api_key=openai.api_key,
        base_url=endpoint + "/v1",
    )

    if service_type == "llm":
        response = client.chat.completions.create(model="tgi", messages="What is Deep Learning?", max_tokens=128)
    elif service_type == "embedding":
        response = client.embeddings.create(model="tei", input="What is Deep Learning?")
    else:
        print(f"Unknown service type: {service_type}")
        exit(1)
    result = response.choices[0].text.strip() if service_type == "llm" else response.data[0].embedding
    if "Deep Learning is" in result if service_type == "llm" else result:
        print("Result correct.")
    else:
        print(f"Result wrong. Received was {result}")
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 validate_svc_with_openai.py <ip_address> <service_port> <service_type>")
        exit(1)
    ip_address = sys.argv[1]
    service_port = sys.argv[2]
    service_type = sys.argv[3]
    validate_svc(ip_address, service_port, service_type)
