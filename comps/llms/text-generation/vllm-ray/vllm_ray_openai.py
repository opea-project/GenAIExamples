# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import os
import sys

# __serve_example_begin__
from typing import Dict, List, Optional

import torch
from fastapi import FastAPI
from huggingface_hub import login
from ray import serve
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.entrypoints.openai.cli_args import make_arg_parser
from vllm.entrypoints.openai.protocol import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.entrypoints.openai.serving_engine import LoRAModulePath

hg_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
if hg_token != "":
    login(token=hg_token)

logger = logging.getLogger("ray.serve")

app = FastAPI()


@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 10,
        "target_ongoing_requests": 5,
    },
    max_ongoing_requests=10,
)
@serve.ingress(app)
class VLLMDeployment:
    def __init__(
        self,
        engine_args: AsyncEngineArgs,
        response_role: str,
        lora_modules: Optional[List[LoRAModulePath]] = None,
        chat_template: Optional[str] = None,
    ):
        logger.info(f"Starting with engine args: {engine_args}")
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

        # Determine the name of the served model for the OpenAI client.
        if engine_args.served_model_name is not None:
            served_model_names = engine_args.served_model_name
        else:
            served_model_names = [engine_args.model]
        self.openai_serving_chat = OpenAIServingChat(
            self.engine, served_model_names, response_role, lora_modules, chat_template
        )

    @app.post("/v1/chat/completions")
    async def create_chat_completion(self, request: ChatCompletionRequest, raw_request: Request):
        """OpenAI-compatible HTTP endpoint.

        API reference:
            - https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
        """
        logger.info(f"Request: {request}")
        generator = await self.openai_serving_chat.create_chat_completion(request, raw_request)
        if isinstance(generator, ErrorResponse):
            return JSONResponse(content=generator.model_dump(), status_code=generator.code)
        if request.stream:
            return StreamingResponse(content=generator, media_type="text/event-stream")
        else:
            assert isinstance(generator, ChatCompletionResponse)
            return JSONResponse(content=generator.model_dump())


def parse_vllm_args(cli_args: Dict[str, str]):
    """Parses vLLM args based on CLI inputs.

    Currently uses argparse because vLLM doesn't expose Python models for all of the
    config options we want to support.
    """
    parser = make_arg_parser()
    arg_strings = []
    for key, value in cli_args.items():
        arg_strings.extend([f"--{key}", str(value)])
    logger.info(arg_strings)
    parsed_args = parser.parse_args(args=arg_strings)
    return parsed_args


def build_app(cli_args: Dict[str, str]) -> serve.Application:
    """Builds the Serve app based on CLI arguments.

    See https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#command-line-arguments-for-the-server
    for the complete set of arguments.

    Supported engine arguments: https://docs.vllm.ai/en/latest/models/engine_args.html.
    """  # noqa: E501
    device = cli_args.pop("device")
    enforce_eager = cli_args.pop("enforce_eager")
    parsed_args = parse_vllm_args(cli_args)
    engine_args = AsyncEngineArgs.from_cli_args(parsed_args)
    engine_args.worker_use_ray = True
    engine_args.enforce_eager = enforce_eager
    engine_args.block_size = 128
    engine_args.max_num_seqs = 256
    engine_args.max_seq_len_to_capture = 2048

    tp = engine_args.tensor_parallel_size
    logger.info(f"Tensor parallelism = {tp}")
    pg_resources = []
    pg_resources.append({"CPU": 1})  # for the deployment replica
    for i in range(tp):
        pg_resources.append({"CPU": 1, device: 1})  # for the vLLM actors

    # We use the "STRICT_PACK" strategy below to ensure all vLLM actors are placed on
    # the same Ray node.
    return VLLMDeployment.options(placement_group_bundles=pg_resources, placement_group_strategy="STRICT_PACK").bind(
        engine_args,
        parsed_args.response_role,
        parsed_args.lora_modules,
        parsed_args.chat_template,
    )


# __serve_example_end__


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve vLLM models with Ray.", add_help=True)
    parser.add_argument("--port_number", default="8000", type=str, help="Port number to serve on.", required=False)
    parser.add_argument(
        "--model_id_or_path",
        default="meta-llama/Llama-2-7b-chat-hf",
        type=str,
        help="Model id or path.",
        required=False,
    )
    parser.add_argument(
        "--tensor_parallel_size", default=2, type=int, help="parallel nodes number for 'hpu' mode.", required=False
    )
    parser.add_argument(
        "--enforce_eager", default=False, type=str2bool, help="Whether to enforce eager execution", required=False
    )
    args = parser.parse_args(argv)

    serve.start(http_options={"host": "0.0.0.0", "port": args.port_number})
    serve.run(
        build_app(
            {
                "model": args.model_id_or_path,
                "tensor-parallel-size": args.tensor_parallel_size,
                "device": "HPU",
                "enforce_eager": args.enforce_eager,
            }
        )
    )
    # input("Service is deployed successfully.")
    while 1:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
