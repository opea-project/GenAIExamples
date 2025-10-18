# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from browser_use import Agent, BrowserProfile
from comps import opea_microservices, register_microservice
from comps.cores.telemetry.opea_telemetry import opea_telemetry
from fastapi import Request
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

LLM = None
BROWSER_PROFILE = None
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://0.0.0.0:8008")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-VL-32B-Instruct")


def initiate_llm_and_browser(llm_endpoint: str, model: str, secret_key: str = "sk-xxxxxx"):
    # Initialize global LLM and BrowserProfile if not already initialized
    global LLM, BROWSER_PROFILE
    if not LLM:
        LLM = ChatOpenAI(base_url=f"{llm_endpoint}/v1", model=model, api_key=SecretStr(secret_key), temperature=0.1)
    if not BROWSER_PROFILE:
        BROWSER_PROFILE = BrowserProfile(
            headless=True,
            chromium_sandbox=False,
        )
    return LLM, BROWSER_PROFILE


class BrowserUseRequest(BaseModel):
    task_prompt: str
    use_vision: bool = True
    secret_key: str = "sk-xxxxxx"
    llm_endpoint: str = LLM_ENDPOINT
    llm_model: str = LLM_MODEL
    agent_max_steps: int = 10


class BrowserUseResponse(BaseModel):
    is_success: bool = False
    model: str
    task_prompt: str
    use_vision: bool
    agent_researched_urls: list[str] = []
    agent_actions: list[str] = []
    agent_durations: float
    agent_steps: int
    final_result: str


@register_microservice(
    name="opea_service@browser_use_agent",
    endpoint="/v1/browser_use_agent",
    host="0.0.0.0",
    port=8022,
)
@opea_telemetry
async def run(request: Request):
    data = await request.json()
    chat_request = BrowserUseRequest.model_validate(data)
    llm, browser_profile = initiate_llm_and_browser(
        llm_endpoint=chat_request.llm_endpoint, model=chat_request.llm_model, secret_key=chat_request.secret_key
    )
    agent = Agent(
        task=chat_request.task_prompt,
        llm=llm,
        use_vision=chat_request.use_vision,
        enable_memory=False,
        browser_profile=browser_profile,
    )
    history = await agent.run(max_steps=chat_request.agent_max_steps)

    return BrowserUseResponse(
        is_success=history.is_successful() if history.is_successful() is not None else False,
        model=chat_request.llm_model,
        task_prompt=chat_request.task_prompt,
        use_vision=chat_request.use_vision,
        agent_researched_urls=history.urls(),
        agent_actions=history.action_names(),
        agent_durations=round(history.total_duration_seconds(), 3),
        agent_steps=history.number_of_steps(),
        final_result=history.final_result() if history.is_successful() else f"Task failed: {history.errors()}",
    )


if __name__ == "__main__":
    opea_microservices["opea_service@browser_use_agent"].start()
