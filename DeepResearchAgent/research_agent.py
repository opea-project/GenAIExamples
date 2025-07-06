# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import re

from comps import register_microservice, opea_microservices
from comps.cores.telemetry.opea_telemetry import opea_telemetry
from typing import List, Union
from pydantic import BaseModel
from utils import *


agent = create_agent("./deep_researcher.yaml")


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

    question = (
        f"Question: {request.question}"
    )
    
    return agent(goal=question)

if __name__ == "__main__":
    opea_microservices["opea_service@deep_research_agent"].start()
