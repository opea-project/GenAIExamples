# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent as create_react_langchain_agent
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import ChatHuggingFace
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ...global_var import threads_global_kv
from ...utils import has_multi_tool_inputs, tool_renderer, wrap_chat
from ..base_agent import BaseAgent
from .prompt import REACT_SYS_MESSAGE, hwchase17_react_prompt


class ReActAgentwithLangchain(BaseAgent):
    def __init__(self, args, with_memory=False):
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
        self.memory = {}

        def get_session_history(session_id):
            if session_id in self.memory:
                return self.memory[session_id]
            else:
                mem = ChatMessageHistory()
                self.memory[session_id] = mem
                return mem

        if with_memory:
            self.app = RunnableWithMessageHistory(
                self.app,
                get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                history_factory_config=[],
            )

    def prepare_initial_state(self, query):
        return {"input": query}

    async def stream_generator(self, query, config, thread_id=None):
        initial_state = self.prepare_initial_state(query)
        if thread_id is not None:
            config["configurable"] = {"session_id": thread_id}
        async for chunk in self.app.astream(initial_state, config=config):
            if thread_id is not None:
                with threads_global_kv as g_threads:
                    thread_inst, created_at, status = g_threads[thread_id]
                    if status == "try_cancel":
                        yield "[thread_completion_callback] signal to cancel! Changed status to ready"
                        print("[thread_completion_callback] signal to cancel! Changed status to ready")
                        g_threads[thread_id] = (thread_inst, created_at, "ready")
                        break
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
    def __init__(self, args, with_memory=False):
        super().__init__(args)

        self.llm = wrap_chat(self.llm_endpoint, args.model)

        tools = self.tools_descriptions

        if with_memory:
            self.app = create_react_agent(
                self.llm, tools=tools, state_modifier=REACT_SYS_MESSAGE, checkpointer=MemorySaver()
            )
        else:
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


from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

###############################################################################
# ReAct Agent:
# Temporary workaround for open-source LLM served by TGI-gaudi
# Only validated with with Llama3.1-70B-Instruct model served with TGI-gaudi
from langgraph.managed import IsLastStep
from langgraph.prebuilt import ToolNode


class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep


class ReActAgentNodeLlama:
    """Do planning and reasoning and generate tool calls.

    A workaround for open-source llm served by TGI-gaudi.
    """

    def __init__(self, llm_endpoint, model_id, tools, args):
        from .prompt import REACT_AGENT_LLAMA_PROMPT
        from .utils import ReActLlamaOutputParser

        output_parser = ReActLlamaOutputParser()
        prompt = PromptTemplate(
            template=REACT_AGENT_LLAMA_PROMPT,
            input_variables=["input", "history", "tools"],
        )
        llm = ChatHuggingFace(llm=llm_endpoint, model_id=model_id)
        self.tools = tools
        self.chain = prompt | llm | output_parser

    def __call__(self, state):
        from .utils import assemble_history, convert_json_to_tool_call

        print("---CALL Agent node---")
        messages = state["messages"]

        # assemble a prompt from messages
        query = messages[0].content
        history = assemble_history(messages)
        print("@@@ History: ", history)

        tools_descriptions = tool_renderer(self.tools)
        print("@@@ Tools description: ", tools_descriptions)

        # invoke chain
        output = self.chain.invoke({"input": query, "history": history, "tools": tools_descriptions})
        print("@@@ Output from chain: ", output)

        # convert output to tool calls
        tool_calls = []
        for res in output:
            if "tool" in res:
                add_kw_tc, tool_call = convert_json_to_tool_call(res)
                # print("Tool call:\n", tool_call)
                tool_calls.append(tool_call)

        if tool_calls:
            ai_message = AIMessage(content="", additional_kwargs=add_kw_tc, tool_calls=tool_calls)
        elif "answer" in output[0]:
            ai_message = AIMessage(content=output[0]["answer"])
        else:
            ai_message = AIMessage(content=output)
        return {"messages": [ai_message]}


class ReActAgentLlama(BaseAgent):
    def __init__(self, args, with_memory=False):
        super().__init__(args)
        agent = ReActAgentNodeLlama(
            llm_endpoint=self.llm_endpoint, model_id=args.model, tools=self.tools_descriptions, args=args
        )
        tool_node = ToolNode(self.tools_descriptions)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.should_continue,
            # Finally we pass in a mapping.
            # The keys are strings, and the values are other nodes.
            # END is a special node marking that the graph should finish.
            # What will happen is we will call `should_continue`, and then the output of that
            # will be matched against the keys in this mapping.
            # Based on which one it matches, that node will then be called.
            {
                # If `tools`, then we call the tool node.
                "continue": "tools",
                # Otherwise we finish.
                "end": END,
            },
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")

        if with_memory:
            self.app = workflow.compile(checkpointer=MemorySaver())
        else:
            self.app = workflow.compile()

    # Define the function that determines whether to continue or not
    def should_continue(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"

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
