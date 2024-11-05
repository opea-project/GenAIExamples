# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import opea_microservices
from edgecraftrag.api.v1 import chatqna, data, model, pipeline
from llama_index.core.settings import Settings

if __name__ == "__main__":
    Settings.llm = None

    opea_microservices["opea_service@ec_rag"].start()
