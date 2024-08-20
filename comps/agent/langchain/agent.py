# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import pathlib
import sys

from fastapi.responses import StreamingResponse

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../")
sys.path.append(comps_path)

from comps import CustomLogger, GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice
from comps.agent.langchain.src.agent import instantiate_agent
from comps.agent.langchain.src.utils import get_args

logger = CustomLogger("comps-react-agent")
logflag = os.getenv("LOGFLAG", False)

args, _ = get_args()


@register_microservice(
    name="opea_service@comps-react-agent",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=args.port,
    input_datatype=LLMParamsDoc,
)
async def llm_generate(input: LLMParamsDoc):
    if logflag:
        logger.info(input)
    # 1. initialize the agent
    if logflag:
        logger.info("args: ", args)
    input.streaming = args.streaming
    config = {"recursion_limit": args.recursion_limit}
    agent_inst = instantiate_agent(args, args.strategy)
    if logflag:
        logger.info(type(agent_inst))

    # 2. prepare the input for the agent
    if input.streaming:
        print("-----------STREAMING-------------")
        return StreamingResponse(agent_inst.stream_generator(input.query, config), media_type="text/event-stream")

    else:
        # TODO: add support for non-streaming mode
        print("-----------NOT STREAMING-------------")
        response = await agent_inst.non_streaming_run(input.query, config)
        print("-----------Response-------------")
        print(response)
        return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@comps-react-agent"].start()
