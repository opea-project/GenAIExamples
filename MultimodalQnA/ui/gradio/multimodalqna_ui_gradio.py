# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import shutil
import time
from pathlib import Path

import gradio as gr
import requests
import uvicorn
from conversation import multimodalqna_conv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from utils import build_logger, moderation_msg, server_error_msg, split_video

logger = build_logger("gradio_web_server", "gradio_web_server.log")

headers = {"Content-Type": "application/json"}

css = """
h1 {
    text-align: center;
    display:block;
}
"""
tmp_upload_folder = "/tmp/gradio/"

# create a FastAPI app
app = FastAPI()
cur_dir = os.getcwd()
static_dir = Path(os.path.join(cur_dir, "static/"))
tmp_dir = Path(os.path.join(cur_dir, "split_tmp_videos/"))

Path(static_dir).mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

description = "This Space lets you engage with MultimodalQnA on a video through a chat box."

no_change_btn = gr.Button()
enable_btn = gr.Button(interactive=True)
disable_btn = gr.Button(interactive=False)


def clear_history(state, request: gr.Request):
    logger.info(f"clear_history. ip: {request.client.host}")
    if state.split_video and os.path.exists(state.split_video):
        os.remove(state.split_video)
    state = multimodalqna_conv.copy()
    return (state, state.to_gradio_chatbot(), "", None) + (disable_btn,) * 1


def add_text(state, text, request: gr.Request):
    logger.info(f"add_text. ip: {request.client.host}. len: {len(text)}")
    if len(text) <= 0:
        state.skip_next = True
        return (state, state.to_gradio_chatbot(), "", None) + (no_change_btn,) * 1

    text = text[:2000]  # Hard cut-off

    state.append_message(state.roles[0], text)
    state.append_message(state.roles[1], None)
    state.skip_next = False
    return (state, state.to_gradio_chatbot(), "") + (disable_btn,) * 1


def http_bot(state, request: gr.Request):
    global gateway_addr
    logger.info(f"http_bot. ip: {request.client.host}")
    url = gateway_addr
    is_very_first_query = False
    if state.skip_next:
        # This generate call is skipped due to invalid inputs
        path_to_sub_videos = state.get_path_to_subvideos()
        yield (state, state.to_gradio_chatbot(), path_to_sub_videos) + (no_change_btn,) * 1
        return

    if len(state.messages) == state.offset + 2:
        # First round of conversation
        is_very_first_query = True
        new_state = multimodalqna_conv.copy()
        new_state.append_message(new_state.roles[0], state.messages[-2][1])
        new_state.append_message(new_state.roles[1], None)
        state = new_state

    # Construct prompt
    prompt = state.get_prompt()

    # Make requests

    pload = {
        "messages": prompt,
    }

    logger.info(f"==== request ====\n{pload}")
    logger.info(f"==== url request ====\n{gateway_addr}")

    state.messages[-1][-1] = "▌"
    yield (state, state.to_gradio_chatbot(), state.split_video) + (disable_btn,) * 1

    try:
        response = requests.post(
            url,
            headers=headers,
            json=pload,
            timeout=100,
        )
        print(response.status_code)
        print(response.json())
        if response.status_code == 200:
            response = response.json()
            choice = response["choices"][-1]
            metadata = choice["metadata"]
            message = choice["message"]["content"]
            if (
                is_very_first_query
                and not state.video_file
                and "source_video" in metadata
                and not state.time_of_frame_ms
                and "time_of_frame_ms" in metadata
            ):
                video_file = metadata["source_video"]
                state.video_file = os.path.join(static_dir, metadata["source_video"])
                state.time_of_frame_ms = metadata["time_of_frame_ms"]
                try:
                    splited_video_path = split_video(
                        state.video_file, state.time_of_frame_ms, tmp_dir, f"{state.time_of_frame_ms}__{video_file}"
                    )
                except:
                    print(f"video {state.video_file} does not exist in UI host!")
                    splited_video_path = None
                state.split_video = splited_video_path
        else:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        state.messages[-1][-1] = server_error_msg
        yield (state, state.to_gradio_chatbot(), None) + (enable_btn,)
        return

    state.messages[-1][-1] = message
    yield (state, state.to_gradio_chatbot(), state.split_video) + (enable_btn,) * 1

    logger.info(f"{state.messages[-1][-1]}")
    return


def ingest_video_gen_transcript(filepath, request: gr.Request):
    yield (gr.Textbox(visible=True, value="Please wait for ingesting your uploaded video into database..."))
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print("Found malicious video file name!")
        yield (
            gr.Textbox(
                visible=True,
                value="Your uploaded video's file name has special characters that are not allowed. Please consider update the video file name!",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copy uploaded file to static folder!")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {
        "files": open(dest, "rb"),
    }
    response = requests.post(dataprep_gen_transcript_addr, headers=headers, files=files)
    print(response.status_code)
    if response.status_code == 200:
        response = response.json()
        print(response)
        yield (gr.Textbox(visible=True, value="Video ingestion is done. Saving your uploaded video..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "video_id_maps" in response and fn_no_ext in response["video_id_maps"]:
            new_dst = os.path.join(static_dir, response["video_id_maps"][fn_no_ext])
            print(response["video_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value="Congratulation! Your upload is done!\nClick the X button on the top right of the video upload box to upload another video.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value="Something wrong!\nPlease click the X button on the top right of the video upload boxreupload your video!",
            )
        )
        time.sleep(2)
    return


def ingest_video_gen_caption(filepath, request: gr.Request):
    yield (gr.Textbox(visible=True, value="Please wait for ingesting your uploaded video into database..."))
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print("Found malicious video file name!")
        yield (
            gr.Textbox(
                visible=True,
                value="Your uploaded video's file name has special characters that are not allowed. Please consider update the video file name!",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copy uploaded file to static folder!")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {
        "files": open(dest, "rb"),
    }
    response = requests.post(dataprep_gen_captiono_addr, headers=headers, files=files)
    print(response.status_code)
    if response.status_code == 200:
        response = response.json()
        print(response)
        yield (gr.Textbox(visible=True, value="Video ingestion is done. Saving your uploaded video..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "video_id_maps" in response and fn_no_ext in response["video_id_maps"]:
            new_dst = os.path.join(static_dir, response["video_id_maps"][fn_no_ext])
            print(response["video_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value="Congratulation! Your upload is done!\nClick the X button on the top right of the video upload box to upload another video.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value="Something wrong!\nPlease click the X button on the top right of the video upload boxreupload your video!",
            )
        )
        time.sleep(2)
    return


def clear_uploaded_video(request: gr.Request):
    return gr.Textbox(visible=False)


with gr.Blocks() as upload_gen_trans:
    gr.Markdown("# Ingest Your Own Video - Utilizing Generated Transcripts")
    gr.Markdown(
        "Please use this interface to ingest your own video if the video has meaningful audio (e.g., announcements, discussions, etc...)"
    )
    with gr.Row():
        with gr.Column(scale=6):
            video_upload = gr.Video(sources="upload", height=512, width=512, elem_id="video_upload")
        with gr.Column(scale=3):
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        video_upload.upload(ingest_video_gen_transcript, [video_upload], [text_upload_result])
        video_upload.clear(clear_uploaded_video, [], [text_upload_result])

with gr.Blocks() as upload_gen_captions:
    gr.Markdown("# Ingest Your Own Video - Utilizing Generated Captions")
    gr.Markdown(
        "Please use this interface to ingest your own video if the video has meaningless audio (e.g., background musics, etc...)"
    )
    with gr.Row():
        with gr.Column(scale=6):
            video_upload_cap = gr.Video(sources="upload", height=512, width=512, elem_id="video_upload_cap")
        with gr.Column(scale=3):
            text_upload_result_cap = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        video_upload_cap.upload(ingest_video_gen_transcript, [video_upload_cap], [text_upload_result_cap])
        video_upload_cap.clear(clear_uploaded_video, [], [text_upload_result_cap])

with gr.Blocks() as qna:
    state = gr.State(multimodalqna_conv.copy())
    with gr.Row():
        with gr.Column(scale=4):
            video = gr.Video(height=512, width=512, elem_id="video")
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(elem_id="chatbot", label="MultimodalQnA Chatbot", height=390)
            with gr.Row():
                with gr.Column(scale=6):
                    # textbox.render()
                    textbox = gr.Textbox(
                        # show_label=False,
                        # container=False,
                        label="Query",
                        info="Enter your query here!",
                    )
                with gr.Column(scale=1, min_width=100):
                    with gr.Row():
                        submit_btn = gr.Button(value="Send", variant="primary", interactive=True)
                    with gr.Row(elem_id="buttons") as button_row:
                        clear_btn = gr.Button(value="🗑️  Clear", interactive=False)

    clear_btn.click(
        clear_history,
        [
            state,
        ],
        [state, chatbot, textbox, video, clear_btn],
    )

    submit_btn.click(
        add_text,
        [state, textbox],
        [state, chatbot, textbox, clear_btn],
    ).then(
        http_bot,
        [
            state,
        ],
        [state, chatbot, video, clear_btn],
    )
with gr.Blocks(css=css) as demo:
    gr.Markdown("# MultimodalQnA")
    with gr.Tabs():
        with gr.TabItem("MultimodalQnA With Your Videos"):
            qna.render()
        with gr.TabItem("Upload Your Own Videos"):
            upload_gen_trans.render()
        with gr.TabItem("Upload Your Own Videos"):
            upload_gen_captions.render()

demo.queue()
app = gr.mount_gradio_app(app, demo, path="/")
share = False
enable_queue = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--concurrency-count", type=int, default=20)
    parser.add_argument("--share", action="store_true")

    backend_service_endpoint = os.getenv("BACKEND_SERVICE_ENDPOINT", "http://localhost:8888/v1/multimodalqna")
    dataprep_gen_transcript_endpoint = os.getenv(
        "DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT", "http://localhost:6007/v1/generate_transcripts"
    )
    dataprep_gen_caption_endpoint = os.getenv(
        "DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT", "http://localhost:6007/v1/generate_captions"
    )
    args = parser.parse_args()
    logger.info(f"args: {args}")
    global gateway_addr
    gateway_addr = backend_service_endpoint
    global dataprep_gen_transcript_addr
    dataprep_gen_transcript_addr = dataprep_gen_transcript_endpoint
    global dataprep_gen_captiono_addr
    dataprep_gen_captiono_addr = dataprep_gen_caption_endpoint

    uvicorn.run(app, host=args.host, port=args.port)
