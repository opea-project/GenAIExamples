# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep
from langgraph.prebuilt import ToolNode

from ...utils import setup_chat_model, tool_renderer
from ..base_agent import BaseAgent
from .hint import pick_hints, read_hints
from .prompt import AGENT_NODE_TEMPLATE, AGENT_SYSM, QUERYFIXER_PROMPT
from .sql_tools import get_sql_query_tool, get_table_schema
from .utils import (
    LlamaOutputParserAndQueryFixer,
    assemble_history,
    convert_json_to_tool_call,
    remove_repeated_tool_calls,
)


class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    hint: str


class AgentNodeLlama:
    def __init__(self, args, tools):
        self.llm = setup_chat_model(args)
        self.args = args
        # two types of tools:
        # sql_db_query - always available, no need to specify
        # other tools - user defined
        # here, self.tools is a list of user defined tools
        self.tools = tool_renderer(tools)
        print("@@@@ Tools: ", self.tools)

        self.chain = self.llm

        self.output_parser = LlamaOutputParserAndQueryFixer(chat_model=self.llm)

        if args.use_hints:
            from sentence_transformers import SentenceTransformer

            self.cols_descriptions, self.values_descriptions = read_hints(args.hints_file)
            self.embed_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            self.column_embeddings = self.embed_model.encode(self.values_descriptions)
            print("Done embedding column descriptions")

    def __call__(self, state):
        print("----------Call Agent Node----------")
        question = state["messages"][0].content
        table_schema, num_tables = get_table_schema(self.args.db_path)
        print("@@@@ Table Schema: ", table_schema)
        if self.args.use_hints:
            if not state["hint"]:
                hints = pick_hints(question, self.embed_model, self.column_embeddings, self.cols_descriptions)
            else:
                hints = state["hint"]
            print("@@@ Hints: ", hints)
        else:
            hints = ""

        history = assemble_history(state["messages"])
        print("@@@ History: ", history)

        prompt = AGENT_NODE_TEMPLATE.format(
            domain=self.args.db_name,
            tools=self.tools,
            num_tables=num_tables,
            tables_schema=table_schema,
            question=question,
            hints=hints,
            history=history,
        )

        output = self.chain.invoke(prompt)
        output = self.output_parser.parse(
            output.content, history, table_schema, hints, question, state["messages"]
        )  # text: str, history: str, db_schema: str, hint: str
        print("@@@@@ Agent output:\n", output)

        # convert output to tool calls
        tool_calls = []
        for res in output:
            if "tool" in res:
                tool_call = convert_json_to_tool_call(res)
                tool_calls.append(tool_call)

        # check if same tool calls have been made before
        # if yes, then remove the repeated tool calls
        if tool_calls:
            new_tool_calls = remove_repeated_tool_calls(tool_calls, state["messages"])
            print("@@@@ New Tool Calls:\n", new_tool_calls)
        else:
            new_tool_calls = []

        if new_tool_calls:
            ai_message = AIMessage(content="", tool_calls=new_tool_calls)
        elif tool_calls:
            ai_message = AIMessage(content="Repeated previous steps.", tool_calls=tool_calls)
        elif "answer" in output[0]:
            ai_message = AIMessage(content=str(output[0]["answer"]))
        else:
            ai_message = AIMessage(content=str(output))

        return {"messages": [ai_message], "hint": hints}


class SQLAgentLlama(BaseAgent):
    # need new args:
    # # db_name and db_path
    # # use_hints, hints_file
    def __init__(self, args, with_memory=False, **kwargs):
        super().__init__(args, local_vars=globals(), **kwargs)
        # note: here tools only include user defined tools
        # we need to add the sql query tool as well
        print("@@@@ user defined tools: ", self.tools_descriptions)
        agent = AgentNodeLlama(args, self.tools_descriptions)
        sql_tool = get_sql_query_tool(args.db_path)
        print("@@@@ SQL Tool: ", sql_tool)
        tools = self.tools_descriptions + [sql_tool]
        print("@@@@ ALL Tools: ", tools)
        tool_node = ToolNode(tools)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            self.decide_next_step,
            {
                # If `tools`, then we call the tool node.
                "tools": "tools",
                "agent": "agent",
                "end": END,
            },
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")

        self.app = workflow.compile()

    def decide_next_step(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls and last_message.content == "Repeated previous steps.":
            print("@@@@ Repeated tool calls from previous steps, go back to agent")
            return "agent"
        elif last_message.tool_calls and last_message.content != "Repeated previous steps.":
            print("@@@@ New Tool calls, go to tools")
            return "tools"
        else:
            return "end"

    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "is_last_step": IsLastStep(False), "hint": ""}


################################################
# Below is SQL agent using OpenAI models
################################################
class AgentNode:
    def __init__(self, args, llm, tools):
        self.llm = llm.bind_tools(tools)
        self.args = args
        if args.use_hints:
            from sentence_transformers import SentenceTransformer

            self.cols_descriptions, self.values_descriptions = read_hints(args.hints_file)
            self.embed_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            self.column_embeddings = self.embed_model.encode(self.values_descriptions)

    def __call__(self, state):
        print("----------Call Agent Node----------")
        question = state["messages"][0].content
        table_schema, num_tables = get_table_schema(self.args.db_path)
        if self.args.use_hints:
            if not state["hint"]:
                hints = pick_hints(question, self.embed_model, self.column_embeddings, self.cols_descriptions)
            else:
                hints = state["hint"]
        else:
            hints = ""

        sysm = AGENT_SYSM.format(num_tables=num_tables, tables_schema=table_schema, question=question, hints=hints)
        _system_message = SystemMessage(content=sysm)
        state_modifier_runnable = RunnableLambda(
            lambda state: [_system_message] + state["messages"],
            name="StateModifier",
        )

        chain = state_modifier_runnable | self.llm
        response = chain.invoke(state)

        return {"messages": [response], "hint": hints}


class QueryFixerNode:
    def __init__(self, args, llm):
        prompt = PromptTemplate(
            template=QUERYFIXER_PROMPT,
            input_variables=["DATABASE_SCHEMA", "QUESTION", "HINT", "QUERY", "RESULT"],
        )
        self.chain = prompt | llm
        self.args = args

    def get_sql_query_and_result(self, state):
        messages = state["messages"]
        assert isinstance(messages[-1], ToolMessage), "The last message should be a tool message"
        result = messages[-1].content
        id = messages[-1].tool_call_id
        query = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                if msg.tool_calls[0]["id"] == id:
                    query = msg.tool_calls[0]["args"]["query"]
                    break
        print("@@@@ Executed SQL Query: ", query)
        print("@@@@ Execution Result: ", result)
        return query, result

    def __call__(self, state):
        print("----------Call Query Fixer Node----------")
        table_schema, _ = get_table_schema(self.args.db_path)
        question = state["messages"][0].content
        hint = state["hint"]
        query, result = self.get_sql_query_and_result(state)
        response = self.chain.invoke(
            {
                "DATABASE_SCHEMA": table_schema,
                "QUESTION": question,
                "HINT": hint,
                "QUERY": query,
                "RESULT": result,
            }
        )
        # print("@@@@@ Query fixer output:\n", response.content)
        return {"messages": [response]}


class SQLAgent(BaseAgent):
    def __init__(self, args, with_memory=False, **kwargs):
        super().__init__(args, local_vars=globals(), **kwargs)

        sql_tool = get_sql_query_tool(args.db_path)
        tools = self.tools_descriptions + [sql_tool]
        print("@@@@ ALL Tools: ", tools)

        tool_node = ToolNode(tools)
        agent = AgentNode(args, self.llm, tools)
        query_fixer = QueryFixerNode(args, self.llm)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
        workflow.add_node("query_fixer", query_fixer)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                # If `tools`, then we call the tool node.
                "continue": "tools",
                "end": END,
            },
        )

        workflow.add_conditional_edges(
            "tools",
            self.should_go_to_query_fixer,
            {"true": "query_fixer", "false": "agent"},
        )
        workflow.add_edge("query_fixer", "agent")

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

    def should_go_to_query_fixer(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        assert isinstance(last_message, ToolMessage), "The last message should be a tool message"
        print("@@@@ Called Tool: ", last_message.name)
        if last_message.name == "sql_db_query":
            print("@@@@ Going to Query Fixer")
            return "true"
        else:
            print("@@@@ Going back to Agent")
            return "false"

    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "is_last_step": IsLastStep(False), "hint": ""}
