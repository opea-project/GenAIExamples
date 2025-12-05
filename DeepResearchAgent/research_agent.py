# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import List, Union

from agent_factory import create_agent
from comps import CustomLogger, opea_microservices, register_microservice
from comps.cores.telemetry.opea_telemetry import opea_telemetry
from pydantic import BaseModel
from research_agents.deepagents.utils import format_message

logger = CustomLogger(__name__)
log_level = logging.DEBUG if os.getenv("LOGFLAG", "").lower() == "true" else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


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

    logger.debug(f"Received question: {request.question}")

    logger.debug("Creating DeepAgents research agent...")
    agent = create_agent(impl="DeepAgents")

    logger.debug("Invoking agent with the provided question...")
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Question: {request.question}",
                }
            ],
        },
    )
    logger.debug("Agent invocation completed.")
    if os.getenv("LOGFLAG", "").lower() == "true":
        format_message(result["messages"])

    return {"answer": result["messages"][-1].content}


if __name__ == "__main__":
    opea_microservices["opea_service@deep_research_agent"].start()
