# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import platform
import re
from datetime import datetime
from pathlib import Path

import cpuinfo
import distro  # if running Python 3.8 or above
import ecrag_client as cli
import gradio as gr
import httpx

# Creation of the ModelLoader instance and loading models remain the same
import platform_config as pconf
import psutil
import requests
from loguru import logger
from omegaconf import OmegaConf
from platform_config import get_available_devices, get_available_weights, get_local_available_models

pipeline_df = []

import os

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "127.0.0.1")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 16011))
UI_SERVICE_HOST_IP = os.getenv("UI_SERVICE_HOST_IP", "0.0.0.0")
UI_SERVICE_PORT = int(os.getenv("UI_SERVICE_PORT", 8084))


def get_llm_model_dir(llm_model_id, weights_compression):
    model_dirs = {
        "fp16_model_dir": Path(llm_model_id) / "FP16",
        "int8_model_dir": Path(llm_model_id) / "INT8_compressed_weights",
        "int4_model_dir": Path(llm_model_id) / "INT4_compressed_weights",
    }

    if weights_compression == "INT4":
        model_dir = model_dirs["int4_model_dir"]
    elif weights_compression == "INT8":
        model_dir = model_dirs["int8_model_dir"]
    else:
        model_dir = model_dirs["fp16_model_dir"]

    if not model_dir.exists():
        raise FileNotFoundError(f"The model directory {model_dir} does not exist.")
    elif not model_dir.is_dir():
        raise NotADirectoryError(f"The path {model_dir} is not a directory.")

    return model_dir


def get_system_status():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    memory_total_gb = memory_info.total / (1024**3)
    memory_used_gb = memory_info.used / (1024**3)
    # uptime_seconds = time.time() - psutil.boot_time()
    # uptime_hours, uptime_minutes = divmod(uptime_seconds // 60, 60)
    disk_usage = psutil.disk_usage("/").percent
    # net_io = psutil.net_io_counters()
    os_info = platform.uname()
    kernel_version = os_info.release
    processor = cpuinfo.get_cpu_info()["brand_raw"]
    dist_name = distro.name(pretty=True)

    now = datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M")

    status = (
        f"{current_time_str} \t"
        f"CPU Usage: {cpu_usage}% \t"
        f"Memory Usage: {memory_usage}% {memory_used_gb:.2f}GB / {memory_total_gb:.2f}GB \t"
        # f"System Uptime: {int(uptime_hours)} hours, {int(uptime_minutes)} minutes \t"
        f"Disk Usage: {disk_usage}% \t"
        # f"Bytes Sent: {net_io.bytes_sent}\n"
        # f"Bytes Received: {net_io.bytes_recv}\n"
        f"Kernel: {kernel_version} \t"
        f"Processor: {processor} \t"
        f"OS: {dist_name} \n"
    )
    return status


def build_demo(cfg, args):

    def load_chatbot_models(
        llm_id,
        llm_device,
        llm_weights,
        embedding_id,
        embedding_device,
        rerank_id,
        rerank_device,
    ):
        req_dict = {
            "llm_id": llm_id,
            "llm_device": llm_device,
            "llm_weights": llm_weights,
            "embedding_id": embedding_id,
            "embedding_device": embedding_device,
            "rerank_id": rerank_id,
            "rerank_device": rerank_device,
        }
        # hard code only for test
        worker_addr = "http://127.0.0.1:8084"
        print(req_dict)
        result = requests.post(f"{worker_addr}/load", json=req_dict, proxies={"http": None})
        return result.text

    def user(message, history):
        """Callback function for updating user messages in interface on submit button click.

        Params:
        message: current message
        history: conversation history
        Returns:
        None
        """
        # Append the user's message to the conversation history
        return "", history + [[message, ""]]

    async def bot(
        history,
        temperature,
        top_p,
        top_k,
        repetition_penalty,
        hide_full_prompt,
        do_rag,
        docs,
        spliter_name,
        vector_db,
        chunk_size,
        chunk_overlap,
        vector_search_top_k,
        vector_search_top_n,
        run_rerank,
        search_method,
        score_threshold,
    ):
        """Callback function for running chatbot on submit button click.

        Params:
        history: conversation history
        temperature:  parameter for control the level of creativity in AI-generated text.
                        By adjusting the `temperature`, you can influence the AI model's probability distribution, making the text more focused or diverse.
        top_p: parameter for control the range of tokens considered by the AI model based on their cumulative probability.
        top_k: parameter for control the range of tokens considered by the AI model based on their cumulative probability, selecting number of tokens with highest probability.
        repetition_penalty: parameter for penalizing tokens based on how frequently they occur in the text.
        conversation_id: unique conversation identifier.
        """
        # req_dict = {
        #     "history": history,
        #     "temperature": temperature,
        #     "top_p": top_p,
        #     "top_k": top_k,
        #     "repetition_penalty": repetition_penalty,
        #     "hide_full_prompt": hide_full_prompt,
        #     "do_rag": do_rag,
        #     "docs": docs,
        #     "spliter_name": spliter_name,
        #     "vector_db": vector_db,
        #     "chunk_size": chunk_size,
        #     "chunk_overlap": chunk_overlap,
        #     "vector_search_top_k": vector_search_top_k,
        #     "vector_search_top_n": vector_search_top_n,
        #     "run_rerank": run_rerank,
        #     "search_method": search_method,
        #     "score_threshold": score_threshold,
        #     "streaming": True
        # }
        print(history)
        new_req = {"messages": history[-1][0]}
        server_addr = f"http://{MEGA_SERVICE_HOST_IP}:{MEGA_SERVICE_PORT}"

        # Async for streaming response
        partial_text = ""
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{server_addr}/v1/chatqna", json=new_req, timeout=None) as response:
                partial_text = ""
                async for chunk in response.aiter_lines():
                    new_text = chunk
                    if new_text.startswith("data"):
                        new_text = re.sub(r"\r\n", "", chunk.split("data: ")[-1])
                    new_text = json.loads(chunk)["choices"][0]["message"]["content"]
                    partial_text = partial_text + new_text
                    history[-1][1] = partial_text
                    yield history

    avail_llms = get_local_available_models("llm")
    avail_embed_models = get_local_available_models("embed")
    avail_rerank_models = get_local_available_models("rerank")
    avail_devices = get_available_devices()
    avail_weights_compression = get_available_weights()
    avail_node_parsers = pconf.get_available_node_parsers()
    avail_indexers = pconf.get_available_indexers()
    avail_retrievers = pconf.get_available_retrievers()
    avail_postprocessors = pconf.get_available_postprocessors()
    avail_generators = pconf.get_available_generators()

    css = """
    .feedback textarea {font-size: 18px; !important }
    #blude_border {border: 1px solid #0000FF}
    #white_border {border: 2px solid #FFFFFF}
    .test textarea {color: E0E0FF; border: 1px solid #0000FF}
    .disclaimer {font-variant-caps: all-small-caps}
    """

    with gr.Blocks(theme=gr.themes.Soft(), css=css) as demo:
        gr.HTML(
            """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            .container {
                display: flex; /* Establish a flex container */
                align-items: center; /* Vertically align everything in the middle */
                width: 100%; /* Take the full width of the container */
            }

            .title-container {
                flex-grow: 1; /* Allow the title to grow and occupy the available space */
                text-align: center; /* Center the text block inside the title container */
            }

            .title-line {
                display: block; /* Makes the span behave like a div in terms of layout */
                line-height: 1.2; /* Adjust this value as needed for better appearance */
            }

            img {
                /* Consider setting a specific width or height if necessary */
            }
            </style>
            </head>
            <body>

            <div class="container">
            <!-- Image aligned to the left -->
            <a href="https://www.intel.cn/content/www/cn/zh/artificial-intelligence/overview.html"><img src="/file/assets/ai-logo-inline-onlight-3000.png" alt="Sample Image" width="200"></a>

            <!-- Title centered in the remaining space -->
                <!-- Title container centered in the remaining space -->
                <div class="title-container">
                    <span class="title-line"><h1 >Edge Craft RAG based Q&A Chatbot</h1></span>
                    <span class="title-line"><h5 style="margin: 0;">Powered by Intel NEXC Edge AI solutions</h5></span>
                </div>
            </div>

            </body>
            </html>
            """
        )
        _ = gr.Textbox(
            label="System Status",
            value=get_system_status,
            max_lines=1,
            every=1,
            info="",
            elem_id="white_border",
        )

        def get_pipeline_df():
            global pipeline_df
            pipeline_df = cli.get_current_pipelines()
            return pipeline_df

        # -------------------
        # RAG Settings Layout
        # -------------------
        with gr.Tab("RAG Settings"):
            with gr.Row():
                with gr.Column(scale=2):
                    u_pipelines = gr.Dataframe(
                        headers=["ID", "Name"],
                        column_widths=[70, 30],
                        value=get_pipeline_df,
                        label="Pipelines",
                        show_label=True,
                        interactive=False,
                        every=5,
                    )

                    u_rag_pipeline_status = gr.Textbox(label="Status", value="", interactive=False)

                with gr.Column(scale=3):
                    with gr.Accordion("Pipeline Configuration"):
                        with gr.Row():
                            rag_create_pipeline = gr.Button("Create Pipeline")
                            rag_activate_pipeline = gr.Button("Activate Pipeline")
                            rag_remove_pipeline = gr.Button("Remove Pipeline")

                        with gr.Column(variant="panel"):
                            u_pipeline_name = gr.Textbox(
                                label="Name",
                                value=cfg.name,
                                interactive=True,
                            )
                            u_active = gr.Checkbox(
                                value=True,
                                label="Activated",
                                interactive=True,
                            )

                        with gr.Column(variant="panel"):
                            with gr.Accordion("Node Parser"):
                                u_node_parser = gr.Dropdown(
                                    choices=avail_node_parsers,
                                    label="Node Parser",
                                    value=cfg.node_parser,
                                    info="Select a parser to split documents.",
                                    multiselect=False,
                                    interactive=True,
                                )
                                u_chunk_size = gr.Slider(
                                    label="Chunk size",
                                    value=cfg.chunk_size,
                                    minimum=100,
                                    maximum=2000,
                                    step=50,
                                    interactive=True,
                                    info="Size of sentence chunk",
                                )

                                u_chunk_overlap = gr.Slider(
                                    label="Chunk overlap",
                                    value=cfg.chunk_overlap,
                                    minimum=0,
                                    maximum=400,
                                    step=1,
                                    interactive=True,
                                    info=("Overlap between 2 chunks"),
                                )

                        with gr.Column(variant="panel"):
                            with gr.Accordion("Indexer"):
                                u_indexer = gr.Dropdown(
                                    choices=avail_indexers,
                                    label="Indexer",
                                    value=cfg.indexer,
                                    info="Select an indexer for indexing content of the documents.",
                                    multiselect=False,
                                    interactive=True,
                                )

                                with gr.Accordion("Embedding Model Configuration"):
                                    u_embed_model_id = gr.Dropdown(
                                        choices=avail_embed_models,
                                        value=cfg.embedding_model_id,
                                        label="Embedding Model",
                                        # info="Select a Embedding Model",
                                        multiselect=False,
                                        allow_custom_value=True,
                                    )

                                    u_embed_device = gr.Dropdown(
                                        choices=avail_devices,
                                        value=cfg.embedding_device,
                                        label="Embedding run device",
                                        # info="Run embedding model on which device?",
                                        multiselect=False,
                                    )

                        with gr.Column(variant="panel"):
                            with gr.Accordion("Retriever"):
                                u_retriever = gr.Dropdown(
                                    choices=avail_retrievers,
                                    value=cfg.retriever,
                                    label="Retriever",
                                    info="Select a retriever for retrieving context.",
                                    multiselect=False,
                                    interactive=True,
                                )
                                u_vector_search_top_k = gr.Slider(
                                    1,
                                    50,
                                    value=cfg.k_retrieval,
                                    step=1,
                                    label="Search top k",
                                    info="Number of searching results, must >= Rerank top n",
                                    interactive=True,
                                )

                        with gr.Column(variant="panel"):
                            with gr.Accordion("Postprocessor"):
                                u_postprocessor = gr.Dropdown(
                                    choices=avail_postprocessors,
                                    value=cfg.postprocessor,
                                    label="Postprocessor",
                                    info="Select postprocessors for post-processing of the context.",
                                    multiselect=True,
                                    interactive=True,
                                )

                                with gr.Accordion("Rerank Model Configuration", open=True):
                                    u_rerank_model_id = gr.Dropdown(
                                        choices=avail_rerank_models,
                                        value=cfg.rerank_model_id,
                                        label="Rerank Model",
                                        # info="Select a Rerank Model",
                                        multiselect=False,
                                        allow_custom_value=True,
                                    )

                                    u_rerank_device = gr.Dropdown(
                                        choices=avail_devices,
                                        value=cfg.rerank_device,
                                        label="Rerank run device",
                                        # info="Run rerank model on which device?",
                                        multiselect=False,
                                    )

                        with gr.Column(variant="panel"):
                            with gr.Accordion("Generator"):
                                u_generator = gr.Dropdown(
                                    choices=avail_generators,
                                    value=cfg.generator,
                                    label="Generator",
                                    info="Select a generator for AI inference.",
                                    multiselect=False,
                                    interactive=True,
                                )

                                with gr.Accordion("LLM Configuration", open=True):
                                    u_llm_model_id = gr.Dropdown(
                                        choices=avail_llms,
                                        value=cfg.llm_model_id,
                                        label="Large Language Model",
                                        # info="Select a Large Language Model",
                                        multiselect=False,
                                        allow_custom_value=True,
                                    )

                                    u_llm_device = gr.Dropdown(
                                        choices=avail_devices,
                                        value=cfg.llm_device,
                                        label="LLM run device",
                                        # info="Run LLM on which device?",
                                        multiselect=False,
                                    )

                                    u_llm_weights = gr.Radio(
                                        avail_weights_compression,
                                        label="Weights",
                                        info="weights compression",
                                    )

        # -------------------
        # RAG Settings Events
        # -------------------
        # Event handlers
        def show_pipeline_detail(evt: gr.SelectData):
            # get selected pipeline id
            # Dataframe: {'headers': '', 'data': [[x00, x01], [x10, x11]}
            # SelectData.index: [i, j]
            print(u_pipelines.value["data"])
            print(evt.index)
            # always use pipeline id for indexing
            selected_id = pipeline_df[evt.index[0]][0]
            pl = cli.get_pipeline(selected_id)
            # TODO: change to json fomart
            # pl["postprocessor"][0]["processor_type"]
            # pl["postprocessor"]["model"]["model_id"], pl["postprocessor"]["model"]["device"]
            return (
                pl["name"],
                pl["status"]["active"],
                pl["node_parser"]["parser_type"],
                pl["node_parser"]["chunk_size"],
                pl["node_parser"]["chunk_overlap"],
                pl["indexer"]["indexer_type"],
                pl["retriever"]["retriever_type"],
                pl["retriever"]["retrieve_topk"],
                pl["generator"]["generator_type"],
                pl["generator"]["model"]["model_id"],
                pl["generator"]["model"]["device"],
                "",
                pl["indexer"]["model"]["model_id"],
                pl["indexer"]["model"]["device"],
            )

        def modify_create_pipeline_button():
            return "Create Pipeline"

        def modify_update_pipeline_button():
            return "Update Pipeline"

        def create_update_pipeline(
            name,
            active,
            node_parser,
            chunk_size,
            chunk_overlap,
            indexer,
            retriever,
            vector_search_top_k,
            postprocessor,
            generator,
            llm_id,
            llm_device,
            llm_weights,
            embedding_id,
            embedding_device,
            rerank_id,
            rerank_device,
        ):
            res = cli.create_update_pipeline(
                name,
                active,
                node_parser,
                chunk_size,
                chunk_overlap,
                indexer,
                retriever,
                vector_search_top_k,
                postprocessor,
                generator,
                llm_id,
                llm_device,
                llm_weights,
                embedding_id,
                embedding_device,
                rerank_id,
                rerank_device,
            )
            return res, get_pipeline_df()

        # Events
        u_pipelines.select(
            show_pipeline_detail,
            inputs=None,
            outputs=[
                u_pipeline_name,
                u_active,
                # node parser
                u_node_parser,
                u_chunk_size,
                u_chunk_overlap,
                # indexer
                u_indexer,
                # retriever
                u_retriever,
                u_vector_search_top_k,
                # postprocessor
                # u_postprocessor,
                # generator
                u_generator,
                # models
                u_llm_model_id,
                u_llm_device,
                u_llm_weights,
                u_embed_model_id,
                u_embed_device,
                # u_rerank_model_id,
                # u_rerank_device
            ],
        )

        u_pipeline_name.input(modify_create_pipeline_button, inputs=None, outputs=rag_create_pipeline)

        # Create pipeline button will change to update pipeline button if any
        # of the listed fields changed
        gr.on(
            triggers=[
                u_active.input,
                # node parser
                u_node_parser.input,
                u_chunk_size.input,
                u_chunk_overlap.input,
                # indexer
                u_indexer.input,
                # retriever
                u_retriever.input,
                u_vector_search_top_k.input,
                # postprocessor
                u_postprocessor.input,
                # generator
                u_generator.input,
                # models
                u_llm_model_id.input,
                u_llm_device.input,
                u_llm_weights.input,
                u_embed_model_id.input,
                u_embed_device.input,
                u_rerank_model_id.input,
                u_rerank_device.input,
            ],
            fn=modify_update_pipeline_button,
            inputs=None,
            outputs=rag_create_pipeline,
        )

        rag_create_pipeline.click(
            create_update_pipeline,
            inputs=[
                u_pipeline_name,
                u_active,
                u_node_parser,
                u_chunk_size,
                u_chunk_overlap,
                u_indexer,
                u_retriever,
                u_vector_search_top_k,
                u_postprocessor,
                u_generator,
                u_llm_model_id,
                u_llm_device,
                u_llm_weights,
                u_embed_model_id,
                u_embed_device,
                u_rerank_model_id,
                u_rerank_device,
            ],
            outputs=[u_rag_pipeline_status, u_pipelines],
            queue=False,
        )

        rag_activate_pipeline.click(
            cli.activate_pipeline,
            inputs=[u_pipeline_name],
            outputs=[u_rag_pipeline_status, u_active],
            queue=False,
        )

        # --------------
        # Chatbot Layout
        # --------------
        def get_files():
            return cli.get_files()

        def create_vectordb(docs, spliter, vector_db):
            res = cli.create_vectordb(docs, spliter, vector_db)
            return gr.update(value=get_files()), res

        global u_files_selected_row
        u_files_selected_row = None

        def select_file(data, evt: gr.SelectData):
            if not evt.selected or len(evt.index) == 0:
                return "No file selected"
            global u_files_selected_row
            row_index = evt.index[0]
            u_files_selected_row = data.iloc[row_index]
            file_name, file_id = u_files_selected_row
            return f"File Name: {file_name}\nFile ID: {file_id}"

        def deselect_file():
            global u_files_selected_row
            u_files_selected_row = None
            return gr.update(value=get_files()), "Selection cleared"

        def delete_file():
            global u_files_selected_row
            if u_files_selected_row is None:
                res = "Please select a file first."
            else:
                file_name, file_id = u_files_selected_row
                u_files_selected_row = None
                res = cli.delete_file(file_id)
            return gr.update(value=get_files()), res

        with gr.Tab("Chatbot"):
            with gr.Row():
                with gr.Column(scale=1):
                    docs = gr.File(
                        label="Step 1: Load text files",
                        file_count="multiple",
                        file_types=[
                            ".csv",
                            ".doc",
                            ".docx",
                            ".enex",
                            ".epub",
                            ".html",
                            ".md",
                            ".odt",
                            ".pdf",
                            ".ppt",
                            ".pptx",
                            ".txt",
                        ],
                    )
                    retriever_argument = gr.Accordion("Vector Store Configuration", open=False)
                    with retriever_argument:
                        spliter = gr.Dropdown(
                            ["Character", "RecursiveCharacter", "Markdown", "Chinese"],
                            value=cfg.splitter_name,
                            label="Text Spliter",
                            info="Method used to split the documents",
                            multiselect=False,
                        )

                        vector_db = gr.Dropdown(
                            ["FAISS", "Chroma"],
                            value=cfg.vector_db,
                            label="Vector Stores",
                            info="Stores embedded data and performs vector search.",
                            multiselect=False,
                        )
                    load_docs = gr.Button("Upload files")

                    u_files_status = gr.Textbox(label="File Processing Status", value="", interactive=False)
                    u_files = gr.Dataframe(
                        headers=["Loaded File Name", "File ID"],
                        value=get_files,
                        label="Loaded Files",
                        show_label=False,
                        interactive=False,
                        every=5,
                    )

                    with gr.Accordion("Delete File", open=False):
                        selected_files = gr.Textbox(label="Click file to select", value="", interactive=False)
                        with gr.Row():
                            with gr.Column():
                                delete_button = gr.Button("Delete Selected File")
                            with gr.Column():
                                deselect_button = gr.Button("Clear Selection")

                    do_rag = gr.Checkbox(
                        value=True,
                        label="RAG is ON",
                        interactive=True,
                        info="Whether to do RAG for generation",
                    )
                    with gr.Accordion("Generation Configuration", open=False):
                        with gr.Row():
                            with gr.Column():
                                with gr.Row():
                                    temperature = gr.Slider(
                                        label="Temperature",
                                        value=0.1,
                                        minimum=0.0,
                                        maximum=1.0,
                                        step=0.1,
                                        interactive=True,
                                        info="Higher values produce more diverse outputs",
                                    )
                            with gr.Column():
                                with gr.Row():
                                    top_p = gr.Slider(
                                        label="Top-p (nucleus sampling)",
                                        value=1.0,
                                        minimum=0.0,
                                        maximum=1,
                                        step=0.01,
                                        interactive=True,
                                        info=(
                                            "Sample from the smallest possible set of tokens whose cumulative probability "
                                            "exceeds top_p. Set to 1 to disable and sample from all tokens."
                                        ),
                                    )
                            with gr.Column():
                                with gr.Row():
                                    top_k = gr.Slider(
                                        label="Top-k",
                                        value=50,
                                        minimum=0.0,
                                        maximum=200,
                                        step=1,
                                        interactive=True,
                                        info="Sample from a shortlist of top-k tokens — 0 to disable and sample from all tokens.",
                                    )
                            with gr.Column():
                                with gr.Row():
                                    repetition_penalty = gr.Slider(
                                        label="Repetition Penalty",
                                        value=1.1,
                                        minimum=1.0,
                                        maximum=2.0,
                                        step=0.1,
                                        interactive=True,
                                        info="Penalize repetition — 1.0 to disable.",
                                    )
                with gr.Column(scale=4):
                    chatbot = gr.Chatbot(
                        height=600,
                        label="Step 2: Input Query",
                        show_copy_button=True,
                    )
                    with gr.Row():
                        with gr.Column():
                            msg = gr.Textbox(
                                label="QA Message Box",
                                placeholder="Chat Message Box",
                                show_label=False,
                                container=False,
                            )
                        with gr.Column():
                            with gr.Row():
                                submit = gr.Button("Submit")
                                stop = gr.Button("Stop")
                                clear = gr.Button("Clear")
                    retriever_argument = gr.Accordion("Retriever Configuration", open=True)
                    with retriever_argument:
                        with gr.Row():
                            with gr.Row():
                                do_rerank = gr.Checkbox(
                                    value=True,
                                    label="Rerank searching result",
                                    interactive=True,
                                )
                                hide_context = gr.Checkbox(
                                    value=True,
                                    label="Hide searching result in prompt",
                                    interactive=True,
                                )
                            with gr.Row():
                                search_method = gr.Dropdown(
                                    ["similarity_score_threshold", "similarity", "mmr"],
                                    value=cfg.search_method,
                                    label="Searching Method",
                                    info="Method used to search vector store",
                                    multiselect=False,
                                    interactive=True,
                                )
                            with gr.Row():
                                score_threshold = gr.Slider(
                                    0.01,
                                    0.99,
                                    value=cfg.score_threshold,
                                    step=0.01,
                                    label="Similarity Threshold",
                                    info="Only working for 'similarity score threshold' method",
                                    interactive=True,
                                )
                            with gr.Row():
                                vector_rerank_top_n = gr.Slider(
                                    1,
                                    10,
                                    value=cfg.k_rerank,
                                    step=1,
                                    label="Rerank top n",
                                    info="Number of rerank results",
                                    interactive=True,
                                )
        load_docs.click(
            create_vectordb,
            inputs=[
                docs,
                spliter,
                vector_db,
            ],
            outputs=[u_files, u_files_status],
            queue=True,
        )
        # TODO: Need to de-select the dataframe,
        # otherwise every time the dataframe is updated, a select event is triggered
        u_files.select(select_file, inputs=[u_files], outputs=selected_files, queue=True)

        delete_button.click(
            delete_file,
            outputs=[u_files, u_files_status],
            queue=True,
        )
        deselect_button.click(
            deselect_file,
            outputs=[u_files, selected_files],
            queue=True,
        )

        submit_event = msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot,
            [
                chatbot,
                temperature,
                top_p,
                top_k,
                repetition_penalty,
                hide_context,
                do_rag,
                docs,
                spliter,
                vector_db,
                u_chunk_size,
                u_chunk_overlap,
                u_vector_search_top_k,
                vector_rerank_top_n,
                do_rerank,
                search_method,
                score_threshold,
            ],
            chatbot,
            queue=True,
        )
        submit_click_event = submit.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot,
            [
                chatbot,
                temperature,
                top_p,
                top_k,
                repetition_penalty,
                hide_context,
                do_rag,
                docs,
                spliter,
                vector_db,
                u_chunk_size,
                u_chunk_overlap,
                u_vector_search_top_k,
                vector_rerank_top_n,
                do_rerank,
                search_method,
                score_threshold,
            ],
            chatbot,
            queue=True,
        )
        # stop.click(
        #     fn=request_cancel,
        #     inputs=None,
        #     outputs=None,
        #     cancels=[submit_event, submit_click_event],
        #     queue=False,
        # )
        clear.click(lambda: None, None, chatbot, queue=False)
    return demo


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Load Embedding and LLM Models with OpenVino.")
    # Add the arguments
    parser.add_argument("--prompt_template", type=str, required=False, help="User specific template")
    # parser.add_argument("--server_name", type=str, default="0.0.0.0")
    # parser.add_argument("--server_port", type=int, default=8082)
    parser.add_argument("--config", type=str, default="./default.yaml", help="configuration file path")
    parser.add_argument("--share", action="store_true", help="share model")
    parser.add_argument("--debug", action="store_true", help="enable debugging")

    # Execute the parse_args() method to collect command line arguments
    args = parser.parse_args()
    logger.info(args)
    cfg = OmegaConf.load(args.config)
    init_cfg_(cfg)
    logger.info(cfg)

    demo = build_demo(cfg, args)
    # if you are launching remotely, specify server_name and server_port
    # demo.launch(server_name='your server name', server_port='server port in int')
    # if you have any issue to launch on your platform, you can pass share=True to launch method:
    # demo.launch(share=True)
    # it creates a publicly shareable link for the interface. Read more in the docs: https://gradio.app/docs/
    # demo.launch(share=True)
    demo.queue().launch(
        server_name=UI_SERVICE_HOST_IP, server_port=UI_SERVICE_PORT, share=args.share, allowed_paths=["."]
    )

    # %%
    # please run this cell for stopping gradio interface
    demo.close()


def init_cfg_(cfg):
    if "name" not in cfg:
        cfg.name = "default"
    if "embedding_device" not in cfg:
        cfg.embedding_device = "CPU"
    if "rerank_device" not in cfg:
        cfg.rerank_device = "CPU"
    if "llm_device" not in cfg:
        cfg.llm_device = "CPU"
    if "model_language" not in cfg:
        cfg.model_language = "Chinese"
    if "vector_db" not in cfg:
        cfg.vector_db = "FAISS"
    if "splitter_name" not in cfg:
        cfg.splitter_name = "RecursiveCharacter"  # or "Chinese"
    if "search_method" not in cfg:
        cfg.search_method = "similarity"
    if "score_threshold" not in cfg:
        cfg.score_threshold = 0.5


if __name__ == "__main__":
    main()
