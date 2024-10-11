# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import uuid

from huggingface_hub import ChatCompletionOutputFunctionDefinition, ChatCompletionOutputToolCall
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.output_parsers import BaseOutputParser


class ReActLlamaOutputParser(BaseOutputParser):
    def parse(self, text: str):
        print("raw output from llm: ", text)
        json_lines = text.split("\n")
        print("json_lines: ", json_lines)
        output = []
        for line in json_lines:
            try:
                if "assistant" in line:
                    line = line.replace("assistant", "")
                output.append(json.loads(line))
            except Exception as e:
                print("Exception happened in output parsing: ", str(e))
        if output:
            return output
        else:
            return text  # None


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


def assemble_history(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    query_history += f"Tool Call: {tool} - {tc_args}\n"
            else:
                # did not make tool calls
                query_history += f"Assistant Output {n}: {m.content}\n"
        elif isinstance(m, ToolMessage):
            query_history += f"Tool Output: {m.content}\n"
    return query_history
