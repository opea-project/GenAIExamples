# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import uuid

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.messages.tool import ToolCall

from .prompt import ANSWER_PARSER_PROMPT, SQL_QUERY_FIXER_PROMPT, SQL_QUERY_FIXER_PROMPT_with_result


def parse_answer_with_llm(text, history, chat_model):
    if "FINAL ANSWER:" in text.upper():
        if history == "":
            history = "The agent execution history is empty."

        prompt = ANSWER_PARSER_PROMPT.format(output=text, history=history)
        response = chat_model.invoke(prompt).content
        print("@@@ Answer parser response: ", response)

        temp = response[:5]
        if "yes" in temp.lower():
            return text.split("FINAL ANSWER:")[-1]
        else:
            temp = response.split("\n")[0]
            if "yes" in temp.lower():
                return text.split("FINAL ANSWER:")[-1]
            return None
    else:
        return None


def get_tool_calls_other_than_sql(text):
    """Get the tool calls other than sql_db_query."""
    tool_calls = []
    text = text.replace("assistant", "")
    json_lines = text.split("\n")
    # only get the unique lines
    json_lines = list(set(json_lines))
    for line in json_lines:
        if "TOOL CALL:" in line:
            if "sql_db_query" not in line:
                line = line.replace("TOOL CALL:", "")
                if "assistant" in line:
                    line = line.replace("assistant", "")
                if "\\" in line:
                    line = line.replace("\\", "")
                try:
                    parsed_line = json.loads(line)
                    if isinstance(parsed_line, dict):
                        if "tool" in parsed_line:
                            tool_calls.append(parsed_line)

                except:
                    pass
    return tool_calls


def get_all_sql_queries(text):
    queries = []
    if "```sql" in text:
        temp = text.split("```sql")
        for t in temp:
            if "```" in t:
                query = t.split("```")[0]
                if "SELECT" in query.upper() and "TOOL CALL" not in query.upper():
                    queries.append(query)

    return queries


def get_the_last_sql_query(text):
    queries = get_all_sql_queries(text)
    if queries:
        return queries[-1]
    else:
        return None


def check_query_if_executed_and_result(query, messages):
    # get previous sql_db_query tool calls
    previous_tool_calls = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                if tc["name"] == "sql_db_query":
                    previous_tool_calls.append(tc)
    for tc in previous_tool_calls:
        if query == tc["args"]["query"]:
            return get_tool_output(messages, tc["id"])

    return None


def parse_and_fix_sql_query_v2(text, chat_model, db_schema, hint, question, messages):
    chosen_query = get_the_last_sql_query(text)
    if chosen_query:
        # check if the query has been executed before
        # if yes, pass execution result to the fixer
        # if not, pass only the query to the fixer
        result = check_query_if_executed_and_result(chosen_query, messages)
        if result:
            prompt = SQL_QUERY_FIXER_PROMPT_with_result.format(
                DATABASE_SCHEMA=db_schema, HINT=hint, QUERY=chosen_query, QUESTION=question, RESULT=result
            )
        else:
            prompt = SQL_QUERY_FIXER_PROMPT.format(
                DATABASE_SCHEMA=db_schema, HINT=hint, QUERY=chosen_query, QUESTION=question
            )

        response = chat_model.invoke(prompt).content
        print("@@@ SQL query fixer response: ", response)
        if "query is correct" in response.lower():
            return chosen_query
        else:
            # parse the fixed query
            fixed_query = get_the_last_sql_query(response)
            return fixed_query
    else:
        return None


class LlamaOutputParserAndQueryFixer:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    def parse(self, text: str, history: str, db_schema: str, hint: str, question: str, messages: list):
        print("@@@ Raw output from llm:\n", text)
        answer = parse_answer_with_llm(text, history, self.chat_model)
        if answer:
            print("Final answer exists.")
            return answer
        else:
            tool_calls = get_tool_calls_other_than_sql(text)
            sql_query = parse_and_fix_sql_query_v2(text, self.chat_model, db_schema, hint, question, messages)
            if sql_query:
                sql_tool_call = [{"tool": "sql_db_query", "args": {"query": sql_query}}]
                tool_calls.extend(sql_tool_call)
            if tool_calls:
                return tool_calls
            else:
                return text


def convert_json_to_tool_call(json_str):
    tool_name = json_str["tool"]
    tool_args = json_str["args"]
    tcid = str(uuid.uuid4())
    tool_call = ToolCall(name=tool_name, args=tool_args, id=tcid)
    return tool_call


def get_tool_output(messages, id):
    tool_output = ""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            if msg.tool_call_id == id:
                tool_output = msg.content
                tool_output = tool_output[:1000]  # limit to 1000 characters
                break
    return tool_output


def assemble_history(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    breaker = "-" * 10
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0 and m.content != "Repeated previous steps.":
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    if tool == "sql_db_query":
                        sql_query = tc_args["query"]
                        query_history += (
                            f"Step {n}. Executed SQL query: {sql_query}\nQuery Result: {tool_output}\n{breaker}\n"
                        )
                    else:
                        query_history += (
                            f"Step {n}. Called tool: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
                        )
                    n += 1
            elif m.content == "Repeated previous steps.":  # repeated steps
                query_history += f"Step {n}. Repeated tool calls from previous steps.\n{breaker}\n"
                n += 1
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"

    return query_history


def remove_repeated_tool_calls(tool_calls, messages):
    """Remove repeated tool calls in the messages.

    tool_calls: list of tool calls: ToolCall(name=tool_name, args=tool_args, id=tcid)
    messages: list of messages: AIMessage, ToolMessage, HumanMessage
    """
    # first get all the previous tool calls in messages
    previous_tool_calls = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls and m.content != "Repeated previous steps.":
            for tc in m.tool_calls:
                previous_tool_calls.append({"tool": tc["name"], "args": tc["args"]})

    unique_tool_calls = []
    for tc in tool_calls:
        if {"tool": tc["name"], "args": tc["args"]} not in previous_tool_calls:
            unique_tool_calls.append(tc)

    return unique_tool_calls
