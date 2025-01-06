# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import uuid

from huggingface_hub import ChatCompletionOutputFunctionDefinition, ChatCompletionOutputToolCall
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.output_parsers import BaseOutputParser


class QueryWriterLlamaOutputParser(BaseOutputParser):
    def parse(self, text: str):
        print("raw output from llm: ", text)
        json_lines = text.split("\n")
        output = []
        for line in json_lines:
            try:
                if "assistant" in line:
                    line = line.replace("assistant", "")
                print("line: ", line)
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    output.append(parsed)
            except Exception as e:
                print("Exception happened in output parsing: ", str(e))
        if output:
            return output
        else:
            return "Error occurred when parsing LLM output."


def convert_json_to_tool_call(json_str, tool):
    tool_name = tool.name
    tcid = str(uuid.uuid4())
    add_kw_tc = {
        "tool_calls": [
            ChatCompletionOutputToolCall(
                function=ChatCompletionOutputFunctionDefinition(
                    arguments={"query": json_str["query"]}, name=tool_name, description=None
                ),
                id=tcid,
                type="function",
            )
        ]
    }
    tool_call = ToolCall(name=tool_name, args={"query": json_str["query"]}, id=tcid)
    return add_kw_tc, tool_call


def assemble_history(messages):
    """
    messages: AI (query writer), TOOL (retriever), HUMAN (Doc Grader), AI, TOOL, HUMAN, etc.
    """
    query_history = ""
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    query = tool_call["args"]["query"]
                    query_history += f"{n}. {query}\n"
                    n += 1
    return query_history


def aggregate_docs(messages):
    """
    messages: AI (query writer), TOOL (retriever), HUMAN (Doc Grader
    """
    docs = []
    context = ""
    for m in messages[::-1]:
        if isinstance(m, ToolMessage):
            docs.append(m.content)
        elif isinstance(m, AIMessage):
            break
    for doc in docs[::-1]:
        context = context + doc + "\n"
    return context
