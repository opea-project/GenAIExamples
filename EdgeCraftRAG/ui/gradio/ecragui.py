# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import platform
from datetime import datetime

import cpuinfo
import distro  # if running Python 3.8 or above
import ecrag_client as cli
import gradio as gr
import httpx

# Creation of the ModelLoader instance and loading models remain the same
import platform_config as pconf
import psutil
from loguru import logger
from omegaconf import OmegaConf
from platform_config import (
    get_avail_llm_inference_type,
    get_available_devices,
    get_available_weights,
    get_local_available_models,
)

pipeline_df = []


MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "127.0.0.1")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 16011))
UI_SERVICE_HOST_IP = os.getenv("UI_SERVICE_HOST_IP", "0.0.0.0")
UI_SERVICE_PORT = int(os.getenv("UI_SERVICE_PORT", 8082))


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


def build_app(cfg, args):

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
        max_tokens,
        docs,
        chunk_size,
        chunk_overlap,
        vector_search_top_k,
        vector_rerank_top_n,
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
        if history[-1][0] == "" or len(history[-1][0]) == 0:
            yield history[:-1]
            return

        stream_opt = True
        new_req = {
            "messages": history[-1][0],
            "stream": stream_opt,
            "max_tokens": max_tokens,
            "top_n": vector_rerank_top_n,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty,
        }
        server_addr = f"http://{MEGA_SERVICE_HOST_IP}:{MEGA_SERVICE_PORT}"

        # Async for streaming response
        partial_text = ""
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{server_addr}/v1/chatqna", json=new_req, timeout=None) as response:
                async for chunk in response.aiter_text():
                    partial_text = partial_text + chunk
                    history[-1][1] = partial_text
                    yield history

    avail_llms = get_local_available_models("llm")
    avail_embed_models = get_local_available_models("embed")
    avail_rerank_models = get_local_available_models("rerank")
    avail_devices = get_available_devices()
    avail_weights_compression = get_available_weights()
    avail_llm_inference_type = get_avail_llm_inference_type()
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

    with gr.Blocks(theme=gr.themes.Soft(), css=css) as app:
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
                    <span class="title-line"><h5 style="margin: 0;">Powered by Intel</h5></span>
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
                                        interactive=True,
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
                                        interactive=True,
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

                                u_llm_infertype = gr.Radio(
                                    choices=avail_llm_inference_type, label="LLM Inference Type", value="local"
                                )

                                with gr.Accordion("LLM Configuration", open=True) as accordion:
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
                                        interactive=True,
                                    )

                                    u_llm_weights = gr.Radio(
                                        avail_weights_compression,
                                        label="Weights",
                                        info="weights compression",
                                        value=cfg.llm_weights,
                                        interactive=True,
                                    )

        # -------------------
        # RAG Settings Events
        # -------------------
        # Event handlers
        def update_visibility(selected_value):  # Accept the event argument, even if not used
            if selected_value == "vllm":
                return gr.Accordion(visible=False)
            else:
                return gr.Accordion(visible=True)

        def show_pipeline_detail(evt: gr.SelectData):
            # get selected pipeline id
            # Dataframe: {'headers': '', 'data': [[x00, x01], [x10, x11]}
            # SelectData.index: [i, j]
            # always use pipeline id for indexing
            selected_id = pipeline_df[evt.index[0]][0]
            pl = cli.get_pipeline(selected_id)
            return (
                pl["name"],
                pl["status"]["active"],
                pl["node_parser"]["parser_type"],
                pl["node_parser"]["chunk_size"],
                pl["node_parser"]["chunk_overlap"],
                pl["indexer"]["indexer_type"],
                pl["retriever"]["retriever_type"],
                pl["retriever"]["retrieve_topk"],
                pl["postprocessor"][0]["postprocessor_type"],
                pl["generator"]["generator_type"],
                pl["generator"]["inference_type"],
                pl["generator"]["model"]["model_id"],
                pl["generator"]["model"]["device"],
                pl["generator"]["model"]["weight"],
                pl["indexer"]["model"]["model_id"],
                pl["indexer"]["model"]["device"],
                pl["postprocessor"][0]["model"]["model_id"] if pl["postprocessor"][0]["model"] is not None else "",
                pl["postprocessor"][0]["model"]["device"] if pl["postprocessor"][0]["model"] is not None else "",
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
            llm_infertype,
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
                llm_infertype,
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
        u_llm_infertype.change(update_visibility, inputs=u_llm_infertype, outputs=accordion)

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
                u_postprocessor,
                # generator
                u_generator,
                u_llm_infertype,
                # models
                u_llm_model_id,
                u_llm_device,
                u_llm_weights,
                u_embed_model_id,
                u_embed_device,
                u_rerank_model_id,
                u_rerank_device,
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
                u_llm_infertype.input,
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
                u_llm_infertype,
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

        def create_vectordb(docs, spliter):
            res = cli.create_vectordb(docs, spliter)
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
                            with gr.Column():
                                with gr.Row():
                                    u_max_tokens = gr.Slider(
                                        label="Max Token Number",
                                        value=512,
                                        minimum=1,
                                        maximum=8192,
                                        step=10,
                                        interactive=True,
                                        info="Set Max Output Token",
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
                                clear = gr.Button("Clear")
                    retriever_argument = gr.Accordion("Retriever Configuration", open=False)
                    with retriever_argument:
                        with gr.Row():
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
                u_max_tokens,
                docs,
                u_chunk_size,
                u_chunk_overlap,
                u_vector_search_top_k,
                vector_rerank_top_n,
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
                u_max_tokens,
                docs,
                u_chunk_size,
                u_chunk_overlap,
                u_vector_search_top_k,
                vector_rerank_top_n,
            ],
            chatbot,
            queue=True,
        )
        clear.click(lambda: None, None, chatbot, queue=False)
    return app


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Load Embedding and LLM Models with OpenVino.")
    # Add the arguments
    parser.add_argument("--prompt_template", type=str, required=False, help="User specific template")
    parser.add_argument("--config", type=str, default="./default.yaml", help="configuration file path")
    parser.add_argument("--share", action="store_true", help="share model")
    parser.add_argument("--debug", action="store_true", help="enable debugging")

    # Execute the parse_args() method to collect command line arguments
    args = parser.parse_args()
    logger.info(args)
    cfg = OmegaConf.load(args.config)
    init_cfg_(cfg)
    logger.info(cfg)

    app = build_app(cfg, args)
    # if you are launching remotely, specify server_name and server_port
    # app.launch(server_name='your server name', server_port='server port in int')
    # if you have any issue to launch on your platform, you can pass share=True to launch method:
    # app.launch(share=True)
    # it creates a publicly shareable link for the interface. Read more in the docs: https://gradio.app/docs/
    # app.launch(share=True)
    app.queue().launch(
        server_name=UI_SERVICE_HOST_IP, server_port=UI_SERVICE_PORT, share=args.share, allowed_paths=["."]
    )

    # %%
    # please run this cell for stopping gradio interface
    app.close()


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
    if "splitter_name" not in cfg:
        cfg.splitter_name = "RecursiveCharacter"  # or "Chinese"
    if "search_method" not in cfg:
        cfg.search_method = "similarity"
    if "score_threshold" not in cfg:
        cfg.score_threshold = 0.5
    if "llm_weights" not in cfg:
        cfg.llm_weights = "FP16"


if __name__ == "__main__":
    main()
