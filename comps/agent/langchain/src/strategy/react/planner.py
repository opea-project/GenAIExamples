# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent as create_react_langchain_agent
from langchain_core.messages import HumanMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ...utils import has_multi_tool_inputs, tool_renderer
from ..base_agent import BaseAgent
from .prompt import REACT_SYS_MESSAGE, hwchase17_react_prompt


class ReActAgentwithLangchain(BaseAgent):
    def __init__(self, args):
        super().__init__(args)
        prompt = hwchase17_react_prompt
        if has_multi_tool_inputs(self.tools_descriptions):
            raise ValueError("Only supports single input tools when using strategy == react_langchain")
        else:
            agent_chain = create_react_langchain_agent(
                self.llm_endpoint, self.tools_descriptions, prompt, tools_renderer=tool_renderer
            )
        self.app = AgentExecutor(
            agent=agent_chain, tools=self.tools_descriptions, verbose=True, handle_parsing_errors=True
        )

    def prepare_initial_state(self, query):
        return {"input": query}

    async def stream_generator(self, query, config):
        initial_state = self.prepare_initial_state(query)
        async for chunk in self.app.astream(initial_state, config=config):
            if "actions" in chunk:
                for action in chunk["actions"]:
                    yield f"Calling Tool: `{action.tool}` with input `{action.tool_input}`\n\n"
            # Observation
            elif "steps" in chunk:
                for step in chunk["steps"]:
                    yield f"Tool Result: `{step.observation}`\n\n"
            # Final result
            elif "output" in chunk:
                yield f"data: {repr(chunk['output'])}\n\n"
            else:
                raise ValueError()
            print("---")
        yield "data: [DONE]\n\n"


class ReActAgentwithLanggraph(BaseAgent):
    def __init__(self, args):
        super().__init__(args)

        if isinstance(self.llm_endpoint, HuggingFaceEndpoint):
            self.llm = ChatHuggingFace(llm=self.llm_endpoint, model_id=args.model)
        elif isinstance(self.llm_endpoint, ChatOpenAI):
            self.llm = self.llm_endpoint

        tools = self.tools_descriptions

        self.app = create_react_agent(self.llm, tools=tools, state_modifier=REACT_SYS_MESSAGE)

    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)]}

    async def stream_generator(self, query, config):
        initial_state = self.prepare_initial_state(query)
        try:
            async for event in self.app.astream(initial_state, config=config):
                for node_name, node_state in event.items():
                    yield f"--- CALL {node_name} ---\n"
                    for k, v in node_state.items():
                        if v is not None:
                            yield f"{k}: {v}\n"

                yield f"data: {repr(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield str(e)

    async def non_streaming_run(self, query, config):
        initial_state = self.prepare_initial_state(query)
        try:
            async for s in self.app.astream(initial_state, config=config, stream_mode="values"):
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()

            last_message = s["messages"][-1]
            print("******Response: ", last_message.content)
            return last_message.content
        except Exception as e:
            return str(e)
