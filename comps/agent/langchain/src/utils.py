# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse

from .config import env_config


def format_date(date):
    # input m/dd/yyyy hr:min
    # output yyyy-mm-dd
    date = date.split(" ")[0]  # remove hr:min
    # print(date)
    try:
        date = date.split("/")  # list
        # print(date)
        year = date[2]
        month = date[0]
        if len(month) == 1:
            month = "0" + month
        day = date[1]
        return f"{year}-{month}-{day}"
    except:
        return date


def setup_hf_tgi_client(args):
    from langchain_huggingface import HuggingFaceEndpoint

    generation_params = {
        "max_new_tokens": args.max_new_tokens,
        "top_k": args.top_k,
        "top_p": args.top_p,
        "temperature": args.temperature,
        "repetition_penalty": args.repetition_penalty,
        "return_full_text": args.return_full_text,
        "streaming": args.streaming,
    }

    llm = HuggingFaceEndpoint(
        endpoint_url=args.llm_endpoint_url,  ## endpoint_url = "localhost:8080",
        task="text-generation",
        **generation_params,
    )
    return llm


def setup_vllm_client(args):
    from langchain_community.llms.vllm import VLLMOpenAI

    openai_endpoint = f"{args.llm_endpoint_url}/v1"
    llm = VLLMOpenAI(
        openai_api_key="EMPTY",
        openai_api_base=openai_endpoint,
        model_name=args.model,
        streaming=args.streaming,
    )
    return llm


def setup_openai_client(args):
    """Lower values for temperature result in more consistent outputs (e.g. 0.2),
    while higher values generate more diverse and creative results (e.g. 1.0).

    Select a temperature value based on the desired trade-off between coherence
    and creativity for your specific application. The temperature can range is from 0 to 2.
    """
    from langchain_openai import ChatOpenAI

    params = {
        "temperature": args.temperature,
        "max_tokens": args.max_new_tokens,
        "streaming": args.streaming,
    }
    llm = ChatOpenAI(model_name=args.model, **params)
    return llm


def setup_llm(args):
    if args.llm_engine == "vllm":
        model = setup_vllm_client(args)
    elif args.llm_engine == "tgi":
        model = setup_hf_tgi_client(args)
    elif args.llm_engine == "openai":
        model = setup_openai_client(args)
    else:
        raise ValueError("Only supports vllm or hf_tgi mode for now")
    return model


def tool_renderer(tools):
    tool_strings = []
    for tool in tools:
        description = f"{tool.name} - {tool.description}"

        arg_schema = []
        for k, tool_dict in tool.args.items():
            k_type = tool_dict["type"] if "type" in tool_dict else ""
            k_desc = tool_dict["description"] if "description" in tool_dict else ""
            arg_schema.append(f"{k} ({k_type}): {k_desc}")

        tool_strings.append(f"{description}, args: {arg_schema}")
    return "\n".join(tool_strings)


def has_multi_tool_inputs(tools):
    ret = False
    for tool in tools:
        if len(tool.args) > 1:
            ret = True
            break
    return ret


def get_args():
    parser = argparse.ArgumentParser()
    # llm args
    parser.add_argument("--streaming", type=str, default="true")
    parser.add_argument("--port", type=int, default=9090)
    parser.add_argument("--agent_name", type=str, default="OPEA_Default_Agent")
    parser.add_argument("--strategy", type=str, default="react")
    parser.add_argument("--role_description", type=str, default="LLM enhanced agent")
    parser.add_argument("--tools", type=str, default="tools/custom_tools.yaml")
    parser.add_argument("--recursion_limit", type=int, default=5)
    parser.add_argument("--require_human_feedback", action="store_true", help="If this agent requires human feedback")
    parser.add_argument("--debug", action="store_true", help="Test with endpoint mode")

    parser.add_argument("--model", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--llm_engine", type=str, default="tgi")
    parser.add_argument("--llm_endpoint_url", type=str, default="http://localhost:8080")
    parser.add_argument("--max_new_tokens", type=int, default=1024)
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--temperature", type=float, default=0.01)
    parser.add_argument("--repetition_penalty", type=float, default=1.03)
    parser.add_argument("--return_full_text", type=bool, default=False)

    sys_args, unknown_args = parser.parse_known_args()
    # print("env_config: ", env_config)
    if env_config != []:
        env_args, env_unknown_args = parser.parse_known_args(env_config)
        unknown_args += env_unknown_args
        for key, value in vars(env_args).items():
            setattr(sys_args, key, value)

    if sys_args.streaming == "true":
        sys_args.streaming = True
    else:
        sys_args.streaming = False
    return sys_args, unknown_args
