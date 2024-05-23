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

import os
import re
import sys
from typing import Any, Dict

import ray
from easydict import EasyDict as edict
from ray import serve
from rayllm.api_openai_backend.query_client import RouterQueryClient
from rayllm.api_openai_backend.router_app import Router, router_app
from rayllm.ray_serve import LLMServe


def router_application(deployments, max_concurrent_queries):
    """Create a Router Deployment.

    Router Deployment will point to a Serve Deployment for each specified base model,
    and have a client to query each one.
    """
    merged_client = RouterQueryClient(deployments)

    RouterDeployment = serve.deployment(
        route_prefix="/",
        max_concurrent_queries=max_concurrent_queries,  # Maximum backlog for a single replica
    )(serve.ingress(router_app)(Router))

    return RouterDeployment.bind(merged_client)


def openai_serve_run(deployments, host, route_prefix, port, max_concurrent_queries):
    router_app = router_application(deployments, max_concurrent_queries)

    serve.start(http_options={"host": host, "port": port})
    serve.run(
        router_app,
        name="router",
        route_prefix=route_prefix,
    ).options(
        stream=True,
        use_new_handle_api=True,
    )
    deployment_address = f"http://{host}:{port}{route_prefix}"
    print(f"Deployment is ready at `{deployment_address}`.")
    return deployment_address


def get_deployment_actor_options(hpus_per_worker, ipex_enabled=False):
    _ray_env_key = "env_vars"
    # OMP_NUM_THREADS will be set by num_cpus, so not set in env
    _predictor_runtime_env_ipex = {
        "KMP_BLOCKTIME": "1",
        "KMP_SETTINGS": "1",
        "KMP_AFFINITY": "granularity=fine,compact,1,0",
        "MALLOC_CONF": "oversize_threshold:1,background_thread:true,\
            metadata_thp:auto,dirty_decay_ms:9000000000,muzzy_decay_ms:9000000000",
    }
    runtime_env: Dict[str, Any] = {_ray_env_key: {}}
    if ipex_enabled:
        runtime_env[_ray_env_key].update(_predictor_runtime_env_ipex)
    ray_actor_options: Dict[str, Any] = {"runtime_env": runtime_env}
    ray_actor_options["resources"] = {"HPU": hpus_per_worker}

    return ray_actor_options


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Serve LLM models with Ray Serve.", add_help=True)
    parser.add_argument("--port_number", default=8080, type=int, help="Port number to serve on.")
    parser.add_argument(
        "--model_id_or_path", default="meta-llama/Llama-2-7b-chat-hf", type=str, help="Model id or path."
    )
    parser.add_argument(
        "--chat_processor", default="ChatModelNoFormat", type=str, help="Chat processor for aligning the prompts."
    )
    parser.add_argument("--max_num_seqs", default=256, type=int, help="Maximum number of sequences to generate.")
    parser.add_argument("--max_batch_size", default=8, type=int, help="Maximum batch size.")
    parser.add_argument("--num_replicas", default=1, type=int, help="Number of replicas to start.")
    parser.add_argument("--num_cpus_per_worker", default=8, type=int, help="Number of CPUs per worker.")
    parser.add_argument("--num_hpus_per_worker", default=1, type=int, help="Number of HPUs per worker.")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args(argv)

    ray.init(address="auto")

    host_port = os.environ.get("RAY_Serve_ENDPOINT", "http://127.0.0.1:8080")
    host = re.search(r"([\d\.]+)", host_port).group(1)
    port = args.port_number
    model_name = args.model_id_or_path.split("/")[-1] if args.model_id_or_path else ""
    route_prefix = "/"

    infer_conf = {}
    infer_conf["use_auth_token"] = os.environ.get("HUGGINGFACEHUB_API_TOKEN", None)
    infer_conf["trust_remote_code"] = os.environ.get("TRUST_REMOTE_CODE", None)
    infer_conf["model_id_or_path"] = args.model_id_or_path
    infer_conf["chat_processor"] = args.chat_processor
    infer_conf["max_batch_size"] = args.max_batch_size
    infer_conf["max_num_seqs"] = args.max_num_seqs
    infer_conf["num_replicas"] = args.num_replicas
    infer_conf["num_cpus_per_worker"] = args.num_cpus_per_worker
    infer_conf["num_hpus_per_worker"] = args.num_hpus_per_worker
    infer_conf["max_concurrent_queries"] = int(os.environ.get("MAX_CONCURRENT_QUERIES", 100))
    infer_conf = edict(infer_conf)

    print(f"infer_conf: {infer_conf}")

    deployment = {}
    ray_actor_options = get_deployment_actor_options(infer_conf["num_hpus_per_worker"])
    deployment[model_name] = LLMServe.options(
        num_replicas=infer_conf["num_replicas"],
        ray_actor_options=ray_actor_options,
        max_concurrent_queries=infer_conf["max_concurrent_queries"],
    ).bind(infer_conf, infer_conf["max_num_seqs"], infer_conf["max_batch_size"])
    deployment = edict(deployment)
    openai_serve_run(deployment, host, route_prefix, port, infer_conf["max_concurrent_queries"])
    input("Service is deployed successfully.")


if __name__ == "__main__":
    main(sys.argv[1:])
