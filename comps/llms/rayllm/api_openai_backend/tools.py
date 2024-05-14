# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import re
from enum import Enum
from typing import List, Union

import jinja2
from rayllm.api_openai_backend.openai_protocol import ChatMessage, FunctionCall, ToolCall


class ToolsCallsTemplateContext(Enum):
    """This is used within the template to generate depending on the context."""

    CALL_TOKEN = 1
    FUNCTIONS_LIST = 2
    FORCE_CALL = 3
    CALLS_NOTIF = 4
    TOOL_RESPONSE = 5


class ToolsCallsTemplate:
    def __init__(self, template_path=None):
        self.trim_blocks = True
        self.lstrip_blocks = True
        if template_path is None:
            template_path = os.path.dirname(__file__) + "/templates/tools_functions.jinja"
        self.environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(template_path)))
        self.template = self.environment.get_template(os.path.basename(template_path))
        self.template.globals["FUNCTIONS_LIST"] = ToolsCallsTemplateContext.FUNCTIONS_LIST
        self.template.globals["FORCE_CALL"] = ToolsCallsTemplateContext.FORCE_CALL
        self.template.globals["CALL_TOKEN"] = ToolsCallsTemplateContext.CALL_TOKEN
        self.template.globals["CALLS_NOTIF"] = ToolsCallsTemplateContext.CALLS_NOTIF
        self.template.globals["TOOL_RESPONSE"] = ToolsCallsTemplateContext.TOOL_RESPONSE

    def get_func_call_token(self) -> str:
        """Return the special token used to find functions calls."""
        return self.template.render(CONTEXT=ToolsCallsTemplateContext.CALL_TOKEN)

    def render_toolcalls(self, tool_calls: List[ToolCall]):
        return self.template.render(CONTEXT=ToolsCallsTemplateContext.CALLS_NOTIF, tool_calls=tool_calls)

    def render_toolmessage(self, message: ChatMessage):
        return self.template.render(CONTEXT=ToolsCallsTemplateContext.TOOL_RESPONSE, message=message)

    def render_toolslist(self, tool_choice: Union[str, None], tools_list) -> str:
        if isinstance(tool_choice, str) and tool_choice == "auto":
            tool_choice = None
        if tool_choice is not None:
            for tool in tools_list:
                # Search if the tool_choice is in the tools_list
                if tool.type == "function" and tool.function.name == tool_choice:
                    return self.template.render(CONTEXT=ToolsCallsTemplateContext.FORCE_CALL, tool=tool)
            return ""
        else:
            return self.template.render(CONTEXT=ToolsCallsTemplateContext.FUNCTIONS_LIST, tools_list=tools_list)


class OpenAIToolsPrompter:
    """
    https://platform.openai.com/docs/assistants/tools
    """

    def __init__(self, template_path=None):
        self.template = ToolsCallsTemplate(template_path)
        self.call_token_str = self.template.get_func_call_token()
        if self.call_token_str is None:
            raise ValueError("There is something wrong with the tools template.")
        else:
            self.call_token_pre = self.call_token_str[0]

    def func_call_token_pre(self) -> str:
        return self.call_token_pre

    def func_call_token_size(self) -> int:
        return len(self.call_token_str)

    def func_call_token(self) -> str:
        return self.call_token_str

    def content_from_assistant(self, message: ChatMessage) -> str:
        text = self.template.render_toolcalls(message.tool_calls)
        if message.content is None:
            return text
        else:
            return message.content + "\n" + text

    def content_from_tool(self, message: ChatMessage) -> str:
        return self.template.render_toolmessage(message)

    def inject_prompt(self, request, tools, tool_choice):
        """Generate and inject the prompt for tools calls."""
        if tools is not None and self.call_token_str is not None and len(tools):
            select_tool_choice = tool_choice if (tool_choice is not None and tool_choice != "auto") else None
            text_inject = self.template.render_toolslist(tool_choice=select_tool_choice, tools_list=tools)
            if request[-1].role == "user":
                request[-1].content = text_inject + "\n The following is User Question: \n" + request[-1].content
        return request


class ChatPromptCapture:
    def __init__(self):
        self.content: str = ""
        self.func_call_content: str = ""
        self.func_start_pos: int = -1
        self.print_end_pos: int = 0
        self.calls_list = []
        self.call_indx = 0

    def reset(self):
        self.content: str = ""
        self.func_call_content: str = ""
        self.func_start_pos: int = -1
        self.print_end_pos: int = 0
        self.calls_list = []

    def make_calls_list(self, call_id: int, func_call_content):
        if func_call_content is None:
            return
        try:
            call_dict = json.loads(func_call_content)
            call_dict["arguments"] = json.dumps(call_dict["arguments"])
            self.calls_list.append(ToolCall(id=f"call_{call_id}", type="function", function=FunctionCall(**call_dict)))
        except Exception:
            pass

    def process_full_output(self, output: str, openai_tools_prompter: OpenAIToolsPrompter, original_prompts):
        ret_output = ""
        # FIXME: for some model, prompt will be append along with answer, need to remove
        start_pos = sum([len(prompt) for prompt in original_prompts]) - 6

        if openai_tools_prompter.func_call_token() in output[start_pos:]:  # we found func_call
            if is_func := re.findall("(\{(.*)\})", output[start_pos:]):
                for idx, found in enumerate(is_func):
                    func_call_content = found[0]
                    c1 = func_call_content.count("{")
                    c2 = func_call_content.count("}")
                    if c1 == c2:  # We have the complete call block
                        func_call_content = found[0]
                        self.make_calls_list(idx, func_call_content)
        else:
            ret_output = output[start_pos:]

        return ret_output, self.calls_list

    def process_stream_output(self, output: str, openai_tools_prompter: OpenAIToolsPrompter):
        ret_output = ""
        self.content += output

        # scenario 1: not reach the length for identifying a func call.
        if len(self.content) < openai_tools_prompter.func_call_token_size():
            # wait for possible function call
            return ret_output, self.calls_list

        # scenario 2: reach the length for identifying if a func call.
        if self.func_start_pos == -1:
            if openai_tools_prompter.func_call_token() in self.content:  # we found func_call
                self.func_start_pos = self.content.index(openai_tools_prompter.func_call_token())
                return ret_output, self.calls_list
            else:  # unhold self.content
                print_start_pos = self.print_end_pos
                self.print_end_pos = len(self.content)
                ret_output = self.content[print_start_pos : self.print_end_pos]
                return ret_output, self.calls_list

        # scenario 3: wait until we can extract the function call
        calls_list = []
        if is_func := re.findall("(\{(.*)\})", self.content):
            for idx, found in enumerate(is_func):
                func_call_content = found[0]
                c1 = func_call_content.count("{")
                c2 = func_call_content.count("}")
                if c1 == c2:  # We have the complete call block
                    self.make_calls_list(self.call_indx, func_call_content)
                    calls_list = self.calls_list
                    self.call_indx += 1
                    self.reset()
        return ret_output, calls_list
