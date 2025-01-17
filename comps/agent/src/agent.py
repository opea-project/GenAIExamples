# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import sys
from datetime import datetime
from typing import List, Optional, Union

from fastapi.responses import StreamingResponse
from pydantic import BaseModel

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../")
sys.path.append(comps_path)

from comps import CustomLogger, GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice
from comps.agent.src.integrations.agent import instantiate_agent
from comps.agent.src.integrations.global_var import assistants_global_kv, threads_global_kv
from comps.agent.src.integrations.thread import instantiate_thread_memory, thread_completion_callback
from comps.agent.src.integrations.utils import get_args, assemble_store_messages
from comps.cores.proto.api_protocol import (
    AssistantsObject,
    ChatCompletionRequest,
    CreateAssistantsRequest,
    CreateMessagesRequest,
    CreateRunResponse,
    CreateThreadsRequest,
    MessageContent,
    MessageObject,
    ThreadObject,
)

logger = CustomLogger("comps-react-agent")
logflag = os.getenv("LOGFLAG", False)

args, _ = get_args()

db_client = None

logger.info("========initiating agent============")
logger.info(f"args: {args}")
agent_inst = instantiate_agent(args, args.strategy, with_memory=args.with_memory)


class AgentCompletionRequest(ChatCompletionRequest):
    # rewrite, specify tools in this turn of conversation
    tool_choice: Optional[List[str]] = None
    # for short/long term in-memory
    thread_id: str = "0"
    user_id: str = "0"


@register_microservice(
    name="opea_service@comps-chat-agent",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=args.port,
)
async def llm_generate(input: AgentCompletionRequest):
    if logflag:
        logger.info(input)

    # don't use global stream setting
    # input.stream = args.stream
    config = {"recursion_limit": args.recursion_limit, "tool_choice": input.tool_choice}

    if args.with_memory:
        config["configurable"] = {"thread_id": input.thread_id}

    if logflag:
        logger.info(type(agent_inst))

    # openai compatible input
    if isinstance(input.messages, str):
        messages = input.messages
    else:
        # TODO: need handle multi-turn messages
        messages = input.messages[-1]["content"]

    # 2. prepare the input for the agent
    if input.stream:
        logger.info("-----------STREAMING-------------")
        return StreamingResponse(
            agent_inst.stream_generator(messages, config),
            media_type="text/event-stream",
        )

    else:
        logger.info("-----------NOT STREAMING-------------")
        response = await agent_inst.non_streaming_run(messages, config)
        logger.info("-----------Response-------------")
        return GeneratedDoc(text=response, prompt=messages)


class RedisConfig(BaseModel):
    redis_uri: Optional[str] = "redis://127.0.0.1:6379"


class AgentConfig(BaseModel):
    stream: Optional[bool] = False
    agent_name: Optional[str] = "OPEA_Default_Agent"
    strategy: Optional[str] = "react_llama"
    role_description: Optional[str] = "LLM enhanced agent"
    tools: Optional[str] = None
    recursion_limit: Optional[int] = 5

    model: Optional[str] = "meta-llama/Meta-Llama-3-8B-Instruct"
    llm_engine: Optional[str] = None
    llm_endpoint_url: Optional[str] = None
    max_new_tokens: Optional[int] = 1024
    top_k: Optional[int] = 10
    top_p: Optional[float] = 0.95
    temperature: Optional[float] = 0.01
    repetition_penalty: Optional[float] = 1.03
    return_full_text: Optional[bool] = False
    custom_prompt: Optional[str] = None

    # short/long term memory
    with_memory: Optional[bool] = False
    # persistence
    with_store: Optional[bool] = False
    store_config: Optional[RedisConfig] = None

    timeout: Optional[int] = 60

    # sql agent config
    db_path: Optional[str] = None
    db_name: Optional[str] = None
    use_hints: Optional[bool] = False
    hints_file: Optional[str] = None

    # specify tools in this turn of conversation
    tool_choice: Optional[List[str]] = None


class CreateAssistant(CreateAssistantsRequest):
    agent_config: AgentConfig


@register_microservice(
    name="opea_service@comps-chat-agent",
    endpoint="/v1/assistants",
    host="0.0.0.0",
    port=args.port,
)
def create_assistants(input: CreateAssistant):
    # 1. initialize the agent
    agent_inst = instantiate_agent(
        input.agent_config, input.agent_config.strategy, with_memory=input.agent_config.with_memory
    )
    assistant_id = agent_inst.id
    created_at = int(datetime.now().timestamp())
    with assistants_global_kv as g_assistants:
        g_assistants[assistant_id] = (agent_inst, created_at)
    logger.info(f"Record assistant inst {assistant_id} in global KV")

    if input.agent_config.with_store:
        logger.info(f"Save Agent Config to database")
        agent_inst.with_store = input.agent_config.with_store
        print(input)
        global db_client
        if db_client is None:
            from comps.agent.src.integrations.storage.persistence_redis import RedisPersistence
            db_client = RedisPersistence(input.agent_config.store_config.redis_uri)
        # save
        db_client.put(assistant_id,
            {"config": input.model_dump_json(), "created_at": created_at},
            "agent_config"
        )

    # get current time in string format
    return AssistantsObject(
        id=assistant_id,
        created_at=created_at,
    )


@register_microservice(
    name="opea_service@comps-chat-agent",
    endpoint="/v1/threads",
    host="0.0.0.0",
    port=args.port,
)
def create_threads(input: CreateThreadsRequest):
    # create a memory KV for the thread
    thread_inst, thread_id = instantiate_thread_memory()
    created_at = int(datetime.now().timestamp())
    status = "ready"
    with threads_global_kv as g_threads:
        g_threads[thread_id] = (thread_inst, created_at, status)
    logger.info(f"Record thread inst {thread_id} in global KV")

    return ThreadObject(
        id=thread_id,
        created_at=created_at,
    )


@register_microservice(
    name="opea_service@comps-chat-agent",
    endpoint="/v1/threads/{thread_id}/messages",
    host="0.0.0.0",
    port=args.port,
)
def create_messages(thread_id, input: CreateMessagesRequest):
    with threads_global_kv as g_threads:
        thread_inst, _, _ = g_threads[thread_id]

    # create a memory KV for the message
    role = input.role
    if isinstance(input.content, str):
        query = input.content
    else:
        query = input.content[-1]["text"]
    msg_id, created_at = thread_inst.add_query(query)

    structured_content = MessageContent(text=query)
    message = MessageObject(
        id=msg_id,
        created_at=created_at,
        thread_id=thread_id,
        role=role,
        content=[structured_content],
        assistant_id=input.assistant_id
    )

    # save messages using assistant_id as key
    if input.assistant_id is not None:
        with assistants_global_kv as g_assistants:
            agent_inst, _ = g_assistants[input.assistant_id]
        if agent_inst.with_store:
            logger.info(f"Save Agent Messages, assistant_id: {input.assistant_id}, thread_id: {thread_id}")
            # if with store, db_client initialized already
            global db_client
            db_client.put(
                msg_id,
                message.model_dump_json(),
                input.assistant_id
            )

    return message


@register_microservice(
    name="opea_service@comps-chat-agent",
    endpoint="/v1/threads/{thread_id}/runs",
    host="0.0.0.0",
    port=args.port,
)
def create_run(thread_id, input: CreateRunResponse):
    with threads_global_kv as g_threads:
        thread_inst, _, status = g_threads[thread_id]

    if status == "running":
        return "[error] Thread is already running, need to cancel the current run or wait for it to finish"

    assistant_id = input.assistant_id
    with assistants_global_kv as g_assistants:
        agent_inst, _ = g_assistants[assistant_id]

    config = {"recursion_limit": args.recursion_limit}

    if agent_inst.with_store:
        # assemble multi-turn messages
        global db_client
        input_query = assemble_store_messages(db_client.get_all(assistant_id))
    else:
        input_query = thread_inst.get_query()

    try:
        return StreamingResponse(
            thread_completion_callback(agent_inst.stream_generator(input_query, config, thread_id), thread_id),
            media_type="text/event-stream",
        )
    except Exception as e:
        with threads_global_kv as g_threads:
            thread_inst, created_at, status = g_threads[thread_id]
            g_threads[thread_id] = (thread_inst, created_at, "ready")
        return f"An error occurred: {e}. This thread is now set as ready"


@register_microservice(
    name="opea_service@comps-chat-agent",
    endpoint="/v1/threads/{thread_id}/runs/cancel",
    host="0.0.0.0",
    port=args.port,
)
def cancel_run(thread_id):
    with threads_global_kv as g_threads:
        thread_inst, created_at, status = g_threads[thread_id]
        if status == "ready":
            return "Thread is not running, no need to cancel"
        elif status == "try_cancel":
            return "cancel request is submitted"
        else:
            g_threads[thread_id] = (thread_inst, created_at, "try_cancel")
            return "submit cancel request"


if __name__ == "__main__":
    opea_microservices["opea_service@comps-chat-agent"].start()
