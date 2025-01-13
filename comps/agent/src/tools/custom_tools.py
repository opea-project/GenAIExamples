# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# tool for unit test
def search_web(query: str) -> str:
    """Search the web knowledge for a given query."""
    ret_text = """
    The Linux Foundation AI & Data announced the Open Platform for Enterprise AI (OPEA) as its latest Sandbox Project.
    OPEA aims to accelerate secure, cost-effective generative AI (GenAI) deployments for businesses by driving interoperability across a diverse and heterogeneous ecosystem, starting with retrieval-augmented generation (RAG).
    """
    return ret_text


def search_weather(query: str) -> str:
    """Search the weather for a given query."""
    ret_text = """
    It's clear.
    """
    return ret_text
