# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
from typing import Optional

import click
from cli.client import EcragApiClient
from cli.config import get_config


def pretty_print(data):
    """Pretty print JSON data."""
    click.echo(json.dumps(data, indent=2))


def run_rag_query(client: EcragApiClient, query: str, top_n: int, max_tokens: int):
    """Run the standard RAG query flow used by both query and chat rag."""
    result = client.ragqna(query, top_n, max_tokens)
    pretty_print(result)


def run_chatqna_query(client: EcragApiClient, query: str, top_n: int, max_tokens: int):
    """Run the default ChatQnA query flow used by the top-level query command."""
    result = client.chatqna(query, top_n, max_tokens)
    pretty_print(result)


@click.group()
@click.option("--host", default=None, help="Server host URL (env: ECRAG_HOST)")
@click.option("--port", default=None, type=int, help="Server port (env: ECRAG_PORT)")
@click.option("--mega-port", default=None, type=int, help="Mega service port (env: ECRAG_MEGA_PORT)")
@click.pass_context
def cli(ctx, host: Optional[str], port: Optional[int], mega_port: Optional[int]):
    """EdgeCraft RAG CLI Tool.

    Configure server connection via command-line options or environment variables:
    - ECRAG_HOST: Server host (default: http://localhost)
    - ECRAG_PORT: Server port (default: 16010)
    - ECRAG_MEGA_PORT: Mega service port (default: 16011)
    """
    ctx.ensure_object(dict)

    # Get defaults from config
    config = get_config()

    # Use provided options or environment/defaults
    final_host = host or config.host
    final_port = port or config.port
    final_mega_port = mega_port or config.mega_port

    # Normalize host URL
    if not final_host.startswith(("http://", "https://")):
        final_host = f"http://{final_host}"

    ctx.obj["client"] = EcragApiClient(host=final_host, server_port=final_port, mega_port=final_mega_port)


# ============== Pipeline Commands ==============


@cli.group()
def pipeline():
    """Manage pipelines."""
    pass


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.option("-f", "--file", type=click.Path(exists=True), help="Pipeline JSON file")
@click.option("-d", "--data", help="Pipeline data as JSON string")
@click.pass_context
def create(ctx, name: str, file: Optional[str], data: Optional[str]):
    """Create a new pipeline."""
    client = ctx.obj["client"]

    if file:
        with open(file, "r") as f:
            pipeline_data = json.load(f)
    elif data:
        pipeline_data = json.loads(data)
    else:
        click.echo("Error: either --file or --data must be provided")
        return

    pipeline_data["name"] = name
    result = client.create_pipeline(pipeline_data)
    pretty_print(result)


@pipeline.command()
@click.pass_context
def list(ctx):
    """List all pipelines."""
    client = ctx.obj["client"]
    result = client.get_pipelines()
    pretty_print(result)


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.pass_context
def get(ctx, name: str):
    """Get a specific pipeline."""
    client = ctx.obj["client"]
    result = client.get_pipeline(name)
    pretty_print(result)


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.pass_context
def get_json(ctx, name: str):
    """Get pipeline JSON data."""
    client = ctx.obj["client"]
    result = client.get_pipeline_json(name)
    pretty_print(result)


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.pass_context
def activate(ctx, name: str):
    """Activate a pipeline."""
    client = ctx.obj["client"]
    result = client.activate_pipeline(name)
    pretty_print(result)


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.pass_context
def deactivate(ctx, name: str):
    """Deactivate a pipeline."""
    client = ctx.obj["client"]
    result = client.deactivate_pipeline(name)
    pretty_print(result)


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.pass_context
def delete(ctx, name: str):
    """Delete a pipeline."""
    client = ctx.obj["client"]
    if click.confirm(f"Are you sure you want to delete pipeline '{name}'?"):
        result = client.delete_pipeline(name)
        pretty_print(result)


@pipeline.command()
@click.option("-n", "--name", required=True, help="Pipeline name")
@click.pass_context
def benchmark(ctx, name: Optional[str]):
    """Get pipeline benchmark data."""
    client = ctx.obj["client"]
    if name:
        result = client.get_pipeline_benchmarks(name)
    else:
        result = client.get_pipeline_benchmark()
    pretty_print(result)


@pipeline.command()
@click.option("-f", "--file", type=click.Path(exists=True), required=True, help="Pipeline JSON file to import")
@click.pass_context
def import_pipeline(ctx, file: str):
    """Import a pipeline from JSON file."""
    client = ctx.obj["client"]
    result = client.import_pipeline(file)
    pretty_print(result)


# ============== Model Commands ==============


@cli.group()
def model():
    """Manage models."""
    pass


@model.command()
@click.option("--type", "model_type", default="LLM", help="Model type (LLM, vLLM, reranker, embedding, etc.)")
@click.option("--id", "model_id", required=True, help="Model ID")
@click.option("--path", "model_path", default="./", help="Model path")
@click.option("--device", default="cpu", help="Device (cpu, gpu)")
@click.option("--weight", default="INT4", help="Weight type (INT4, INT8, FP16)")
@click.pass_context
def load(ctx, model_type: str, model_id: str, model_path: str, device: str, weight: str):
    """Load a model."""
    client = ctx.obj["client"]
    model_data = {
        "model_type": model_type,
        "model_id": model_id,
        "model_path": model_path,
        "device": device,
        "weight": weight,
    }
    result = client.load_model(model_data)
    pretty_print(result)


@model.command()
@click.pass_context
def list(ctx):  # noqa: F811
    """List all models."""
    client = ctx.obj["client"]
    result = client.get_models()
    pretty_print(result)


@model.command()
@click.option("--id", "model_id", required=True, help="Model ID")
@click.pass_context
def get(ctx, model_id: str):  # noqa: F811
    """Get a specific model."""
    client = ctx.obj["client"]
    result = client.get_model(model_id)
    pretty_print(result)


@model.command()
@click.option("--id", "model_id", required=True, help="Model ID")
@click.option("--device", help="New device")
@click.option("--weight", help="New weight")
@click.pass_context
def update(ctx, model_id: str, device: Optional[str], weight: Optional[str]):
    """Update a model."""
    client = ctx.obj["client"]
    model_data = {}
    if device:
        model_data["device"] = device
    if weight:
        model_data["weight"] = weight
    result = client.update_model(model_id, model_data)
    pretty_print(result)


@model.command()
@click.option("--id", "model_id", required=True, help="Model ID")
@click.pass_context
def delete(ctx, model_id: str):  # noqa: F811
    """Delete a model."""
    client = ctx.obj["client"]
    if click.confirm(f"Are you sure you want to delete model '{model_id}'?"):
        result = client.delete_model(model_id)
        pretty_print(result)


@model.command()
@click.option("--id", "model_id", required=True, help="Model ID")
@click.pass_context
def weights(ctx, model_id: str):
    """Get available weights for a model."""
    client = ctx.obj["client"]
    result = client.get_model_weights(model_id)
    pretty_print(result)


@model.command()
@click.option("--type", "model_type", required=True, help="Model type (LLM, vLLM, reranker, embedding, etc.)")
@click.option("--server", help="vLLM server address (optional)")
@click.pass_context
def available(ctx, model_type: str, server: Optional[str]):
    """List available models by type."""
    client = ctx.obj["client"]
    result = client.get_available_models(model_type, server)
    pretty_print(result)


# ============== Knowledge Base Commands ==============


@cli.group()
def kb():
    """Manage knowledge bases."""
    pass


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.option("--description", help="Knowledge base description")
@click.option("-f", "--file", type=click.Path(exists=True), help="KB config JSON file")
@click.pass_context
def create(ctx, name: str, description: Optional[str], file: Optional[str]):  # noqa: F811
    """Create a knowledge base."""
    client = ctx.obj["client"]

    if file:
        with open(file, "r") as f:
            kb_data = json.load(f)
    else:
        kb_data = {"name": name}
        if description:
            kb_data["description"] = description

    result = client.create_knowledge_base(kb_data)
    pretty_print(result)


@kb.command()
@click.pass_context
def list(ctx):  # noqa: F811
    """List all knowledge bases."""
    client = ctx.obj["client"]
    result = client.get_knowledge_bases()
    pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.pass_context
def get(ctx, name: str):  # noqa: F811
    """Get a specific knowledge base."""
    client = ctx.obj["client"]
    result = client.get_knowledge_base(name)
    pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.pass_context
def get_json(ctx, name: str):  # noqa: F811
    """Get knowledge base JSON data."""
    client = ctx.obj["client"]
    result = client.get_knowledge_base_json(name)
    pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.option("--page", "page_num", default=1, type=int, help="Page number")
@click.option("--size", "page_size", default=20, type=int, help="Page size")
@click.pass_context
def filemap(ctx, name: str, page_num: int, page_size: int):
    """Get knowledge base file map."""
    client = ctx.obj["client"]
    result = client.get_knowledge_base_filemap(name, page_num, page_size)
    pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.option("--active", type=bool, help="Set active status")
@click.option("--description", help="Update description")
@click.pass_context
def update(ctx, name: str, active: Optional[bool], description: Optional[str]):  # noqa: F811
    """Update a knowledge base."""
    client = ctx.obj["client"]
    kb_data = {"name": name}
    if active is not None:
        kb_data["active"] = active
    if description:
        kb_data["description"] = description
    result = client.update_knowledge_base(kb_data)
    pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.pass_context
def delete(ctx, name: str):  # noqa: F811
    """Delete a knowledge base."""
    client = ctx.obj["client"]
    if click.confirm(f"Are you sure you want to delete knowledge base '{name}'?"):
        result = client.delete_knowledge_base(name)
        pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.option("--paths", multiple=True, required=True, help="File paths to add")
@click.pass_context
def add_files(ctx, name: str, paths: tuple):
    """Add files to a knowledge base."""
    client = ctx.obj["client"]
    result = client.add_files_to_kb(name, list(paths))
    pretty_print(result)


@kb.command()
@click.option("-n", "--name", required=True, help="Knowledge base name")
@click.option("--paths", multiple=True, required=True, help="File paths to delete")
@click.pass_context
def delete_files(ctx, name: str, paths: tuple):
    """Delete files from a knowledge base."""
    client = ctx.obj["client"]
    result = client.delete_files_from_kb(name, list(paths))
    pretty_print(result)


# ============== Experience Commands ==============


@cli.group()
def experience():
    """Manage experiences (Q&A pairs)."""
    pass


@experience.command()
@click.pass_context
def list(ctx):  # noqa: F811
    """List all experiences."""
    client = ctx.obj["client"]
    result = client.get_experiences()
    pretty_print(result)


@experience.command()
@click.option("--id", required=True, help="Experience ID")
@click.pass_context
def get(ctx, id: str):  # noqa: F811
    """Get a specific experience."""
    client = ctx.obj["client"]
    result = client.get_experience(id)
    pretty_print(result)


@experience.command()
@click.option("--id", required=True, help="Experience ID")
@click.option("--question", required=True, help="Question")
@click.option("--content", multiple=True, required=True, help="Answer content")
@click.pass_context
def create(ctx, id: str, question: str, content: tuple):  # noqa: F811
    """Create or update an experience."""
    client = ctx.obj["client"]
    exp_data = {"idx": id, "question": question, "content": list(content)}
    result = client.update_experience(exp_data)
    pretty_print(result)


@experience.command()
@click.option("--id", required=True, help="Experience ID")
@click.pass_context
def delete(ctx, id: str):  # noqa: F811
    """Delete an experience."""
    client = ctx.obj["client"]
    if click.confirm(f"Are you sure you want to delete experience '{id}'?"):
        result = client.delete_experience(id)
        pretty_print(result)


@experience.command()
@click.option("-f", "--file", type=click.Path(exists=True), required=True, help="Experiences JSON file")
@click.pass_context
def load_file(ctx, file: str):
    """Load experiences from a file."""
    client = ctx.obj["client"]
    result = client.add_experiences_from_file(file)
    pretty_print(result)


# ============== Agent Commands ==============


@cli.group()
def agent():
    """Manage agents."""
    pass


@agent.command()
@click.pass_context
def list(ctx):  # noqa: F811
    """List all agents."""
    client = ctx.obj["client"]
    result = client.get_agents()
    pretty_print(result)


@agent.command()
@click.option("-n", "--name", required=True, help="Agent name")
@click.pass_context
def get(ctx, name: str):  # noqa: F811
    """Get a specific agent."""
    client = ctx.obj["client"]
    result = client.get_agent(name)
    pretty_print(result)


@agent.command()
@click.option("--type", required=True, help="Agent type (react_llm, etc.)")
@click.pass_context
def configs(ctx, type: str):
    """Get default configs for an agent type."""
    client = ctx.obj["client"]
    result = client.get_agent_configs(type)
    pretty_print(result)


@agent.command()
@click.option("-n", "--name", required=True, help="Agent name")
@click.option("--type", required=True, help="Agent type")
@click.option("--pipeline", required=True, help="Pipeline index or name")
@click.pass_context
def create(ctx, name: str, type: str, pipeline: str):  # noqa: F811
    """Create an agent."""
    client = ctx.obj["client"]
    agent_data = {"name": name, "type": type, "pipeline_idx": pipeline}
    result = client.create_agent(agent_data)
    pretty_print(result)


@agent.command()
@click.option("-n", "--name", required=True, help="Agent name")
@click.option("--active", type=bool, help="Active status")
@click.pass_context
def update(ctx, name: str, active: Optional[bool]):  # noqa: F811
    """Update an agent."""
    client = ctx.obj["client"]
    agent_data = {}
    if active is not None:
        agent_data["active"] = active
    result = client.update_agent(name, agent_data)
    pretty_print(result)


@agent.command()
@click.option("-n", "--name", required=True, help="Agent name")
@click.pass_context
def delete(ctx, name: str):  # noqa: F811
    """Delete an agent."""
    client = ctx.obj["client"]
    if click.confirm(f"Are you sure you want to delete agent '{name}'?"):
        result = client.delete_agent(name)
        pretty_print(result)


# ============== Prompt Commands ==============


@cli.group()
def prompt():
    """Manage system prompts."""
    pass


@prompt.command()
@click.pass_context
def get(ctx):  # noqa: F811
    """Get the current system prompt."""
    client = ctx.obj["client"]
    result = client.get_prompt()
    pretty_print(result)


@prompt.command()
@click.pass_context
def get_tagged(ctx):
    """Get the tagged system prompt."""
    client = ctx.obj["client"]
    result = client.get_tagged_prompt()
    pretty_print(result)


@prompt.command()
@click.pass_context
def get_default(ctx):
    """Get the default system prompt."""
    client = ctx.obj["client"]
    result = client.get_default_prompt()
    pretty_print(result)


@prompt.command()
@click.option("--text", help="Prompt text")
@click.option("-f", "--file", type=click.Path(exists=True), help="Prompt file")
@click.pass_context
def set(ctx, text: Optional[str], file: Optional[str]):
    """Update the system prompt."""
    client = ctx.obj["client"]

    if file:
        with open(file, "r") as f:
            prompt_text = f.read()
    elif text:
        prompt_text = text
    else:
        click.echo("Error: either --text or --file must be provided")
        return

    result = client.update_prompt(prompt_text)
    pretty_print(result)


@prompt.command()
@click.pass_context
def reset(ctx):
    """Reset the system prompt to default."""
    client = ctx.obj["client"]
    if click.confirm("Are you sure you want to reset prompt to default?"):
        result = client.reset_prompt()
        pretty_print(result)


# ============== Data Commands ==============


@cli.group()
def data():
    """Manage data (nodes, documents, files)."""
    pass


@data.command()
@click.pass_context
def nodes(ctx):
    """Get all nodes in active knowledge base."""
    client = ctx.obj["client"]
    result = client.get_nodes()
    pretty_print(result)


@data.command()
@click.option("-n", "--name", required=True, help="Document name")
@click.pass_context
def nodes_by_doc(ctx, name: str):
    """Get nodes by document name."""
    client = ctx.obj["client"]
    result = client.get_nodes_by_document(name)
    pretty_print(result)


@data.command()
@click.pass_context
def documents(ctx):
    """Get all document names in active knowledge base."""
    client = ctx.obj["client"]
    result = client.get_documents()
    pretty_print(result)


@data.command()
@click.pass_context
def files(ctx):
    """Get all files."""
    client = ctx.obj["client"]
    result = client.get_files()
    pretty_print(result)


@data.command()
@click.option("-n", "--name", required=True, help="File name")
@click.pass_context
def get_file(ctx, name: str):
    """Get a specific file."""
    client = ctx.obj["client"]
    result = client.get_file(name)
    pretty_print(result)


@data.command()
@click.option("-n", "--name", required=True, help="File name")
@click.option("--path", required=True, type=click.Path(exists=True), help="File path")
@click.pass_context
def upload(ctx, name: str, path: str):
    """Upload a file."""
    client = ctx.obj["client"]
    result = client.upload_file(name, path)
    pretty_print(result)


# ============== Session Commands ==============


@cli.group()
def session():
    """Manage sessions."""
    pass


@session.command()
@click.pass_context
def list(ctx):  # noqa: F811
    """List all sessions."""
    client = ctx.obj["client"]
    result = client.get_sessions()
    pretty_print(result)


@session.command()
@click.option("--id", required=True, help="Session ID")
@click.pass_context
def get(ctx, id: str):  # noqa: F811
    """Get a specific session."""
    client = ctx.obj["client"]
    result = client.get_session(id)
    pretty_print(result)


# ============== System Commands ==============


@cli.group()
def system():
    """Get system information."""
    pass


@system.command()
@click.pass_context
def info(ctx):
    """Get system information."""
    client = ctx.obj["client"]
    result = client.get_system_info()
    pretty_print(result)


@system.command()
@click.pass_context
def devices(ctx):
    """Get available inference devices."""
    client = ctx.obj["client"]
    result = client.get_available_devices()
    pretty_print(result)


# ============== Chat/Query Commands ==============


@cli.group()
def chat():
    """Chat and query operations."""
    pass


@chat.command()
@click.option("--query", required=True, help="Query string")
@click.option("--top-n", default=5, type=int, help="Number of results to retrieve")
@click.option("--max-tokens", default=512, type=int, help="Max tokens in response")
@click.pass_context
def retrieve(ctx, query: str, top_n: int, max_tokens: int):
    """Retrieve relevant context chunks."""
    client = ctx.obj["client"]
    result = client.retrieval(query, top_n, max_tokens)
    pretty_print(result)


@chat.command()
@click.option("--query", required=True, help="Query string")
@click.option("--top-n", default=5, type=int, help="Number of results to retrieve")
@click.option("--max-tokens", default=512, type=int, help="Max tokens in response")
@click.pass_context
def rag(ctx, query: str, top_n: int, max_tokens: int):
    """Run RAG pipeline (retrieval + generation)."""
    client = ctx.obj["client"]
    run_rag_query(client, query, top_n, max_tokens)


@cli.command()
@click.argument("query")
@click.option("--top-n", default=5, type=int, help="Number of results to retrieve")
@click.option("--max-tokens", default=512, type=int, help="Max tokens in response")
@click.pass_context
def query(ctx, query: str, top_n: int, max_tokens: int):
    """Shortcut for chat mega using a positional query argument."""
    client = ctx.obj["client"]
    run_chatqna_query(client, query, top_n, max_tokens)


@chat.command()
@click.option("--query", required=True, help="Query string")
@click.option("--top-n", default=5, type=int, help="Number of results to retrieve")
@click.option("--max-tokens", default=512, type=int, help="Max tokens in response")
@click.pass_context
def mega(ctx, query: str, top_n: int, max_tokens: int):
    """Run full ChatQnA (mega service)."""
    client = ctx.obj["client"]
    result = client.chatqna(query, top_n, max_tokens)
    pretty_print(result)


@chat.command()
@click.option("--server", required=True, help="vLLM server address")
@click.option("--model", required=True, help="Model name")
@click.pass_context
def check_vllm(ctx, server: str, model: str):
    """Check vLLM server connection."""
    client = ctx.obj["client"]
    result = client.check_vllm_connection(server, model)
    pretty_print(result)


if __name__ == "__main__":
    cli(obj={})
