# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import re
from typing import List, Union

from comps import opea_microservices, register_microservice
from comps.cores.telemetry.opea_telemetry import opea_telemetry
from pydantic import BaseModel
from utils import create_agent

config_path = os.path.join(os.path.dirname(__file__), "deep_researcher.yaml")
agent = create_agent(config_path)


class SimpleRequest(BaseModel):
    question: Union[str, List[str]]


@register_microservice(
    name="opea_service@deep_research_agent",
    endpoint="/v1/deep_research_agent",
    host="0.0.0.0",
    port=8022,
)
@opea_telemetry
async def run(request: SimpleRequest):

    question = f"Question: {request.question}"

    result = await agent(question)

    return {"answer": result}


if __name__ == "__main__":
    opea_microservices["opea_service@deep_research_agent"].start()
