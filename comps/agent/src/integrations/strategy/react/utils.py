# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import uuid

from huggingface_hub import ChatCompletionOutputFunctionDefinition, ChatCompletionOutputToolCall
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.output_parsers import BaseOutputParser


class ReActLlamaOutputParser(BaseOutputParser):
    def parse(self, text: str):
        print("raw output from llm: ", text)
        json_lines = text.split("\n")
        output = []
        for line in json_lines:
            try:
                if "TOOL CALL:" in line:
                    line = line.replace("TOOL CALL:", "")
                if "FINAL ANSWER:" in line:
                    line = line.replace("FINAL ANSWER:", "")
                if "assistant" in line:
                    line = line.replace("assistant", "")
                parsed_line = json.loads(line)
                if isinstance(parsed_line, dict):
                    print("parsed line: ", parsed_line)
                    output.append(parsed_line)
            except Exception as e:
                print("Exception happened in output parsing: ", str(e))
        if output:
            return output
        else:
            return text


def convert_json_to_tool_call(json_str):
    tool_name = json_str["tool"]
    tool_args = json_str["args"]
    tcid = str(uuid.uuid4())
    add_kw_tc = {
        "tool_calls": [
            ChatCompletionOutputToolCall(
                function=ChatCompletionOutputFunctionDefinition(arguments=tool_args, name=tool_name, description=None),
                id=tcid,
                type="function",
            )
        ]
    }
    tool_call = ToolCall(name=tool_name, args=tool_args, id=tcid)
    return add_kw_tc, tool_call


def get_tool_output(messages, id):
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            if msg.tool_call_id == id:
                tool_output = msg.content
                break
    return tool_output


def assemble_history(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    breaker = "-" * 10
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    query_history += f"Tool Call: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"

    return query_history


def assemble_memory(messages):
    """
    messages: Human, AI, TOOL, AI, TOOL, etc.
    """
    query = ""
    query_id = None
    query_history = ""
    breaker = "-" * 10

    # get query
    for m in messages[::-1]:
        if isinstance(m, HumanMessage):
            query = m.content
            query_id = m.id
            break

    for m in messages:
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    query_history += f"Tool Call: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"

        elif isinstance(m, HumanMessage):
            if m.id == query_id:
                continue
            query_history += f"Human Input: {m.content}\n"

    return query, query_history
