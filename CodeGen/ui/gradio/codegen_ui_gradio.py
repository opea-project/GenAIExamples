# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# This is a Gradio app that includes two tabs: one for code generation and another for resource management.
# The resource management tab has been updated to allow file uploads, deletion, and a table listing all the files.
# Additionally, three small text boxes have been added for managing file dataframe parameters.

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import gradio as gr
import pandas as pd
import requests
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logflag = os.getenv("LOGFLAG", False)

# create a FastAPI app
app = FastAPI()
cur_dir = os.getcwd()
static_dir = Path(os.path.join(cur_dir, "static/"))
tmp_dir = Path(os.path.join(cur_dir, "split_tmp_videos/"))

Path(static_dir).mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

tmp_upload_folder = "/tmp/gradio/"


host_ip = os.getenv("host_ip")
DATAPREP_REDIS_PORT = os.getenv("DATAPREP_REDIS_PORT", 6007)
DATAPREP_ENDPOINT = os.getenv("DATAPREP_ENDPOINT", f"http://{host_ip}:{DATAPREP_REDIS_PORT}/v1/dataprep")
MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 7778)

backend_service_endpoint = os.getenv("BACKEND_SERVICE_ENDPOINT", f"http://{host_ip}:{MEGA_SERVICE_PORT}/v1/codegen")

dataprep_ingest_endpoint = f"{DATAPREP_ENDPOINT}/ingest"
dataprep_get_files_endpoint = f"{DATAPREP_ENDPOINT}/get"
dataprep_delete_files_endpoint = f"{DATAPREP_ENDPOINT}/delete"
dataprep_get_indices_endpoint = f"{DATAPREP_ENDPOINT}/indices"


# Define the functions that will be used in the app
def conversation_history(prompt, index, use_agent, history):
    print(f"Generating code for prompt: {prompt} using index: {index} and use_agent is {use_agent}")
    history.append([prompt, ""])
    response_generator = generate_code(prompt, index, use_agent)
    for token in response_generator:
        history[-1][-1] += token
        yield history


def upload_media(media, index=None, chunk_size=1500, chunk_overlap=100):
    media = media.strip().split("\n")
    if not chunk_size:
        chunk_size = 1500
    if not chunk_overlap:
        chunk_overlap = 100

    requests = []
    if type(media) is list:
        for file in media:
            file_ext = os.path.splitext(file)[-1]
            if is_valid_url(file):
                yield (
                    gr.Textbox(
                        visible=True,
                        value="Ingesting URL...",
                    )
                )
                value = ingest_url(file, index, chunk_size, chunk_overlap)
                requests.append(value)
                yield value
            elif file_ext in [".pdf", ".txt"]:
                yield (
                    gr.Textbox(
                        visible=True,
                        value="Ingesting file...",
                    )
                )
                value = ingest_file(file, index, chunk_size, chunk_overlap)
                requests.append(value)
                yield value
            else:
                yield (
                    gr.Textbox(
                        visible=True,
                        value="Your media is either an invalid URL or the file extension type is not supported. (Supports .pdf, .txt, url)",
                    )
                )
                return
        yield requests

    else:
        file_ext = os.path.splitext(media)[-1]
        if is_valid_url(media):
            value = ingest_url(media, index, chunk_size, chunk_overlap)
            yield value
        elif file_ext in [".pdf", ".txt"]:
            value = ingest_file(media, index, chunk_size, chunk_overlap)
            yield value
        else:
            yield (
                gr.Textbox(
                    visible=True,
                    value="Your file extension type is not supported.",
                )
            )
            return


def generate_code(query, index=None, use_agent=False):
    if index is None or index == "None":
        input_dict = {"messages": query, "agents_flag": use_agent}
    else:
        input_dict = {"messages": query, "index_name": index, "agents_flag": use_agent}

    print("Query is ", input_dict)
    headers = {"Content-Type": "application/json"}

    response = requests.post(url=backend_service_endpoint, headers=headers, data=json.dumps(input_dict), stream=True)

    line_count = 0
    for line in response.iter_lines():
        line_count += 1
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):  # Only process lines starting with "data: "
                json_part = line[len("data: ") :]  # Remove the "data: " prefix
            else:
                json_part = line
            if json_part.strip() == "[DONE]":  # Ignore the DONE marker
                continue
            try:
                json_obj = json.loads(json_part)  # Convert to dictionary
                if "choices" in json_obj:
                    for choice in json_obj["choices"]:
                        if "text" in choice:
                            # Yield each token individually
                            yield choice["text"]
            except json.JSONDecodeError:
                print("Error parsing JSON:", json_part)

    if line_count == 0:
        yield "Something went wrong, No Response Generated! \nIf you are using an Index, try uploading your media again with a smaller chunk size to avoid exceeding the token max. \
        \nOr, check the Use Agent box and try again."


def ingest_file(file, index=None, chunk_size=100, chunk_overlap=150):
    headers = {}
    file_input = {"files": open(file, "rb")}

    if index:
        data = {"index_name": index, "chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
    else:
        data = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}

    response = requests.post(url=dataprep_ingest_endpoint, headers=headers, files=file_input, data=data)

    return response.text


def ingest_url(url, index=None, chunk_size=100, chunk_overlap=150):
    url = str(url)
    if not is_valid_url(url):
        return "Invalid URL entered. Please enter a valid URL"

    headers = {}
    if index:
        url_input = {
            "link_list": json.dumps([url]),
            "index_name": index,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
    else:
        url_input = {"link_list": json.dumps([url]), "chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
    response = requests.post(url=dataprep_ingest_endpoint, headers=headers, data=url_input)

    return response.text


def is_valid_url(url):
    url = str(url)
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_files(index=None):
    headers = {}
    if index:
        if index == "All":
            response = requests.post(url=dataprep_get_files_endpoint, headers=headers, data='{"index_name": "all"}')
            table = response.json()
            return table
        else:
            response = requests.post(
                url=dataprep_get_files_endpoint, headers=headers, data=f'{{"index_name": "{index}"}}'
            )
            table = response.json()
            return table
    else:
        response = requests.post(url=dataprep_get_files_endpoint, headers=headers)
        table = response.json()
        return table


def update_table(index=None):
    if index == "All Files":
        index = None
    files = get_files(index)
    if len(files) == 0:
        df = pd.DataFrame(files, columns=["Files"])
        return df
    else:
        df = pd.DataFrame(files)
        return df


def delete_file(file, index=None):
    # Remove the selected file from the file list
    headers = {}
    if index:
        file_input = f'{{"file_path": "{file}", "index_name": "{index}"}}'
    else:
        f'{{"file_path": "{file}"}}'
    response = requests.post(url=dataprep_delete_files_endpoint, headers=headers, data=file_input)
    table = update_table(index)
    return table


def delete_all_files(index=None):
    # Remove all files from the file list
    headers = {}
    if index:
        response = requests.post(
            url=dataprep_delete_files_endpoint, headers=headers, data=f'{{"file_path": "all", "index_name": "{index}"}}'
        )
    else:
        response = requests.post(url=dataprep_delete_files_endpoint, headers=headers, data='{"file_path": "all"}')
    table = update_table()

    return table


def get_indices():
    headers = {}
    response = requests.post(url=dataprep_get_indices_endpoint, headers=headers)
    indices = ["None", "All"]
    indices += response.json()
    return indices


def update_indices_dropdown():
    new_dd = gr.update(choices=get_indices(), value="All")
    return new_dd


def update_files_dropdown(index):
    choice = []
    files = get_files(index)
    for file in files:
        choice.append(file["name"])
    new_dd = gr.update(choices=choice, value="None")
    return new_dd


def get_file_names(files):
    file_str = ""
    if not files:
        return file_str

    for file in files:
        file_str += file + "\n"
    file_str.strip()
    return file_str


# Define UI components
with gr.Blocks() as ui:
    with gr.Tab("Code Generation"):
        gr.Markdown("### Generate Code from Natural Language")
        chatbot = gr.Chatbot(label="Chat History")
        prompt_input = gr.Textbox(label="Enter your query")
        with gr.Column():
            with gr.Row(equal_height=True):
                database_dropdown = gr.Dropdown(choices=get_indices(), label="Select Index", value="None", scale=10)
                db_refresh_button = gr.Button("Refresh Dropdown", scale=0.1)
                db_refresh_button.click(update_indices_dropdown, outputs=database_dropdown)
                use_agent = gr.Checkbox(label="Use Agent", container=False)

        generate_button = gr.Button("Generate Code")
        generate_button.click(
            conversation_history, inputs=[prompt_input, database_dropdown, use_agent, chatbot], outputs=chatbot
        )

    with gr.Tab("Resource Management"):
        # File management components
        with gr.Row():
            with gr.Column(scale=1):
                index_name_input = gr.Textbox(label="Index Name")
                chunk_size_input = gr.Textbox(
                    label="Chunk Size", value="1500", placeholder="Enter an integer (default: 1500)"
                )
                chunk_overlap_input = gr.Textbox(
                    label="Chunk Overlap", value="100", placeholder="Enter an integer (default: 100)"
                )
            with gr.Column(scale=3):
                file_upload = gr.File(label="Upload Files", file_count="multiple")
                url_input = gr.Textbox(label="Media to be ingested (Append URL's in a new line)")
                upload_button = gr.Button("Upload", variant="primary")
                upload_status = gr.Textbox(label="Upload Status")
                file_upload.change(get_file_names, inputs=file_upload, outputs=url_input)
            with gr.Column(scale=2):
                file_dropdown = gr.Dropdown(choices=get_indices(), label="Select an Index")
                files_dataframe = gr.Dataframe()
                file_dropdown.change(fn=update_table, inputs=file_dropdown, outputs=files_dataframe)
                refresh_button = gr.Button("Refresh", variant="primary", size="sm")
                refresh_button.click(update_indices_dropdown, outputs=file_dropdown)
                upload_button.click(
                    upload_media,
                    inputs=[url_input, index_name_input, chunk_size_input, chunk_overlap_input],
                    outputs=upload_status,
                )

                delete_all_button = gr.Button("Delete All", variant="primary", size="sm")
                delete_all_button.click(delete_all_files, inputs=file_dropdown, outputs=files_dataframe)

                files = get_files(file_dropdown)
                delete_dropdown = gr.Dropdown(choices=files, label="Select a file to delete")
                file_dropdown.change(fn=update_files_dropdown, inputs=file_dropdown, outputs=delete_dropdown)

                delete_file_button = gr.Button("Delete Selected File", variant="primary", size="sm")
                delete_file_button.click(delete_file, inputs=[delete_dropdown, file_dropdown], outputs=files_dataframe)


@app.get("/health")
def health_check():
    return {"status": "ok"}


ui.queue()
app = gr.mount_gradio_app(app, ui, path="/")
share = False
enable_queue = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=os.getenv("UI_PORT", 5173))
    parser.add_argument("--concurrency-count", type=int, default=20)
    parser.add_argument("--share", action="store_true")

    host_ip = os.getenv("host_ip")
    DATAPREP_REDIS_PORT = os.getenv("DATAPREP_REDIS_PORT", 6007)
    DATAPREP_ENDPOINT = os.getenv("DATAPREP_ENDPOINT", f"http://{host_ip}:{DATAPREP_REDIS_PORT}/v1/dataprep")
    MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 7778)

    backend_service_endpoint = os.getenv("BACKEND_SERVICE_ENDPOINT", f"http://{host_ip}:{MEGA_SERVICE_PORT}/v1/codegen")

    args = parser.parse_args()
    global gateway_addr
    gateway_addr = backend_service_endpoint
    global dataprep_ingest_addr
    dataprep_ingest_addr = dataprep_ingest_endpoint
    global dataprep_get_files_addr
    dataprep_get_files_addr = dataprep_get_files_endpoint

    uvicorn.run(app, host=args.host, port=args.port)
