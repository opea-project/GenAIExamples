# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain.agents import AgentExecutor, create_react_agent

from ...utils import has_multi_tool_inputs, tool_renderer
from ..base_agent import BaseAgent
from .prompt import hwchase17_react_prompt


class ReActAgentwithLangchain(BaseAgent):
    def __init__(self, args):
        super().__init__(args)
        prompt = hwchase17_react_prompt
        if has_multi_tool_inputs(self.tools_descriptions):
            raise ValueError("Only supports single input tools when using strategy == react")
        else:
            agent_chain = create_react_agent(
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
