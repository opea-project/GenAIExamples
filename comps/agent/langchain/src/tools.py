# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import glob
import importlib
import os

import yaml
from langchain.tools import BaseTool, StructuredTool
from langchain_community.agent_toolkits.load_tools import load_tools
from pydantic import BaseModel, Field, create_model


def generate_request_function(url):
    def process_request(query):
        import json

        import requests

        content = json.dumps({"query": query})
        print(content)
        try:
            resp = requests.post(url=url, data=content)
            ret = resp.text
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        except requests.exceptions.RequestException as e:
            ret = f"An error occurred:{e}"
        print(ret)
        return ret

    return process_request


def load_func_str(tools_dir, func_str, env=None, pip_dependencies=None):
    if env is not None:
        env_list = [i.split("=") for i in env.split(",")]
        for k, v in env_list:
            print(f"set env for {func_str}: {k} = {v}")
            os.environ[k] = v

    if pip_dependencies is not None:
        import pip

        pip_list = pip_dependencies.split(",")
        for package in pip_list:
            pip.main(["install", "-q", package])
    # case 1: func is an endpoint api
    if func_str.startswith("http://") or func_str.startswith("https://"):
        return generate_request_function(func_str)

    # case 2: func is a python file + function
    elif ".py:" in func_str:
        file_path, func_name = func_str.rsplit(":", 1)
        file_path = os.path.join(tools_dir, file_path)
        file_name = os.path.basename(file_path).split(".")[0]
        spec = importlib.util.spec_from_file_location(file_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        func_str = getattr(module, func_name)

    # case 3: func is a langchain tool
    elif "." not in func_str:
        return load_tools([func_str])[0]

    # case 4: func is a python loadable module
    else:
        module_path, func_name = func_str.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func_str = getattr(module, func_name)
        tool_inst = func_str()
        if isinstance(tool_inst, BaseTool):
            return tool_inst
    return func_str


def load_func_args(tool_name, args_dict):
    fields = {}
    for arg_name, arg_item in args_dict.items():
        fields[arg_name] = (arg_item["type"], Field(description=arg_item["description"]))
    return create_model(f"{tool_name}Input", **fields, __base__=BaseModel)


def load_langchain_tool(tools_dir, tool_setting_tuple):
    tool_name = tool_setting_tuple[0]
    tool_setting = tool_setting_tuple[1]
    env = tool_setting["env"] if "env" in tool_setting else None
    pip_dependencies = tool_setting["pip_dependencies"] if "pip_dependencies" in tool_setting else None
    func_definition = load_func_str(tools_dir, tool_setting["callable_api"], env, pip_dependencies)
    if "args_schema" not in tool_setting or "description" not in tool_setting:
        if isinstance(func_definition, BaseTool):
            return func_definition
        else:
            raise ValueError(
                f"Tool {tool_name} is missing 'args_schema' or 'description' in the tool setting. Tool is {func_definition}"
            )
    else:
        func_inputs = load_func_args(tool_name, tool_setting["args_schema"])
        return StructuredTool(
            name=tool_name,
            description=tool_setting["description"],
            func=func_definition,
            args_schema=func_inputs,
        )


def load_yaml_tools(file_dir_path: str):
    tools_setting = yaml.safe_load(open(file_dir_path))
    tools_dir = os.path.dirname(file_dir_path)
    tools = []
    if tools_setting is None or len(tools_setting) == 0:
        return tools
    for t in tools_setting.items():
        tools.append(load_langchain_tool(tools_dir, t))
    return tools


def load_python_tools(file_dir_path: str):
    print(file_dir_path)
    spec = importlib.util.spec_from_file_location("custom_tools", file_dir_path)
    module = importlib.util.module_from_spec(spec)
    # sys.modules["custom_tools"] = module
    spec.loader.exec_module(module)
    return module.tools_descriptions()


def get_tools_descriptions(file_dir_path: str):
    tools = []
    file_path_list = []
    if os.path.isdir(file_dir_path):
        file_path_list += glob.glob(file_dir_path + "/*")
    else:
        file_path_list.append(file_dir_path)
    for file in file_path_list:
        if os.path.basename(file).endswith(".yaml"):
            tools += load_yaml_tools(file)
        elif os.path.basename(file).endswith(".yml"):
            tools += load_yaml_tools(file)
        elif os.path.basename(file).endswith(".py"):
            tools += load_python_tools(file)
        else:
            pass
    return tools
