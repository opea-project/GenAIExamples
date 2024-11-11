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
from utils import build_logger, make_temp_image, moderation_msg, server_error_msg, split_video

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
    if state.image and os.path.exists(state.image):
        os.remove(state.image)
    state = multimodalqna_conv.copy()
    return (state, state.to_gradio_chatbot(), None, None, None) + (disable_btn,) * 1


def add_text(state, text, request: gr.Request):
    logger.info(f"add_text. ip: {request.client.host}. len: {len(text)}")
    if len(text) <= 0:
        state.skip_next = True
        return (state, state.to_gradio_chatbot(), None) + (no_change_btn,) * 1

    text = text[:2000]  # Hard cut-off

    state.append_message(state.roles[0], text)
    state.append_message(state.roles[1], None)
    state.skip_next = False
    return (state, state.to_gradio_chatbot(), None) + (disable_btn,) * 1


def http_bot(state, request: gr.Request):
    global gateway_addr
    logger.info(f"http_bot. ip: {request.client.host}")
    url = gateway_addr
    is_very_first_query = False
    if state.skip_next:
        # This generate call is skipped due to invalid inputs
        path_to_sub_videos = state.get_path_to_subvideos()
        yield (state, state.to_gradio_chatbot(), path_to_sub_videos, None) + (no_change_btn,) * 1
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
    yield (state, state.to_gradio_chatbot(), state.split_video, state.image) + (disable_btn,) * 1

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
                file_ext = os.path.splitext(state.video_file)[-1]
                if file_ext == ".mp4":
                    try:
                        splited_video_path = split_video(
                            state.video_file, state.time_of_frame_ms, tmp_dir, f"{state.time_of_frame_ms}__{video_file}"
                        )
                    except:
                        print(f"video {state.video_file} does not exist in UI host!")
                        splited_video_path = None
                    state.split_video = splited_video_path
                elif file_ext in [".jpg", ".jpeg", ".png", ".gif"]:
                    try:
                        output_image_path = make_temp_image(state.video_file, file_ext)
                    except:
                        print(f"image {state.video_file} does not exist in UI host!")
                        output_image_path = None
                    state.image = output_image_path

        else:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        state.messages[-1][-1] = server_error_msg
        yield (state, state.to_gradio_chatbot(), None, None) + (enable_btn,)
        return

    state.messages[-1][-1] = message
    yield (
        state,
        state.to_gradio_chatbot(),
        gr.Video(state.split_video, visible=state.split_video is not None),
        gr.Image(state.image, visible=state.image is not None),
    ) + (enable_btn,) * 1

    logger.info(f"{state.messages[-1][-1]}")
    return


def ingest_gen_transcript(filepath, filetype, request: gr.Request):
    yield (
        gr.Textbox(visible=True, value=f"Please wait while your uploaded {filetype} is ingested into the database...")
    )
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print(f"Found malicious {filetype} file name!")
        yield (
            gr.Textbox(
                visible=True,
                value=f"Your uploaded {filetype}'s file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copying uploaded file to static folder.")
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
        yield (gr.Textbox(visible=True, value=f"The {filetype} ingestion is done. Saving your uploaded {filetype}..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value=f"Congratulations, your upload is done!\nClick the X button on the top right of the {filetype} upload box to upload another {filetype}.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the {filetype} upload box to reupload your video.",
            )
        )
        time.sleep(2)
    return


def ingest_gen_caption(filepath, filetype, request: gr.Request):
    yield (
        gr.Textbox(visible=True, value=f"Please wait while your uploaded {filetype} is ingested into the database...")
    )
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print(f"Found malicious {filetype} file name!")
        yield (
            gr.Textbox(
                visible=True,
                value=f"Your uploaded {filetype}'s file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copying uploaded file to static folder.")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {
        "files": open(dest, "rb"),
    }
    response = requests.post(dataprep_gen_caption_addr, headers=headers, files=files)
    print(response.status_code)
    if response.status_code == 200:
        response = response.json()
        print(response)
        yield (gr.Textbox(visible=True, value=f"The {filetype} ingestion is done. Saving your uploaded {filetype}..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value=f"Congratulations, your upload is done!\nClick the X button on the top right of the {filetype} upload box to upload another {filetype}.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the {filetype} upload box to reupload your video.",
            )
        )
        time.sleep(2)
    return


def ingest_with_text(filepath, text, request: gr.Request):
    yield (gr.Textbox(visible=True, value="Please wait for your uploaded image to be ingested into the database..."))
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print("Found malicious image file name!")
        yield (
            gr.Textbox(
                visible=True,
                value="Your uploaded image's file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    text_basename = "{}.txt".format(os.path.splitext(basename)[0])
    text_dest = os.path.join(static_dir, text_basename)
    with open(text_dest, "w") as file:
        file.write(text)
    print("Done copying uploaded files to static folder!")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = [("files", (basename, open(dest, "rb"))), ("files", (text_basename, open(text_dest, "rb")))]
    try:
        response = requests.post(dataprep_ingest_addr, headers=headers, files=files)
    finally:
        os.remove(text_dest)
    print(response.status_code)
    if response.status_code == 200:
        response = response.json()
        print(response)
        yield (gr.Textbox(visible=True, value="Image ingestion is done. Saving your uploaded image..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value="Congratulation! Your upload is done!\nClick the X button on the top right of the image upload box to upload another image.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the image upload box to reupload your image!",
            )
        )
        time.sleep(2)
    return


def hide_text(request: gr.Request):
    return gr.Textbox(visible=False)


def clear_text(request: gr.Request):
    return None


with gr.Blocks() as upload_video:
    gr.Markdown("# Ingest Your Own Video Using Generated Transcripts or Captions")
    gr.Markdown("Use this interface to ingest your own video and generate transcripts or captions for it")

    def select_upload_type(choice, request: gr.Request):
        if choice == "transcript":
            return gr.Video(sources="upload", visible=True), gr.Video(sources="upload", visible=False)
        else:
            return gr.Video(sources="upload", visible=False), gr.Video(sources="upload", visible=True)

    with gr.Row():
        with gr.Column(scale=6):
            video_upload_trans = gr.Video(sources="upload", elem_id="video_upload_trans", visible=True)
            video_upload_cap = gr.Video(sources="upload", elem_id="video_upload_cap", visible=False)
        with gr.Column(scale=3):
            text_options_radio = gr.Radio(
                [
                    ("Generate transcript (video contains voice)", "transcript"),
                    ("Generate captions (video does not contain voice)", "caption"),
                ],
                label="Text Options",
                info="How should text be ingested?",
                value="transcript",
            )
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        video_upload_trans.upload(
            ingest_gen_transcript, [video_upload_trans, gr.Textbox(value="video", visible=False)], [text_upload_result]
        )
        video_upload_trans.clear(hide_text, [], [text_upload_result])
        video_upload_cap.upload(
            ingest_gen_caption, [video_upload_cap, gr.Textbox(value="video", visible=False)], [text_upload_result]
        )
        video_upload_cap.clear(hide_text, [], [text_upload_result])
        text_options_radio.change(select_upload_type, [text_options_radio], [video_upload_trans, video_upload_cap])

with gr.Blocks() as upload_image:
    gr.Markdown("# Ingest Your Own Image Using Generated or Custom Captions/Labels")
    gr.Markdown("Use this interface to ingest your own image and generate a caption for it")

    def select_upload_type(choice, request: gr.Request):
        if choice == "gen_caption":
            return gr.Image(sources="upload", visible=True), gr.Image(sources="upload", visible=False)
        else:
            return gr.Image(sources="upload", visible=False), gr.Image(sources="upload", visible=True)

    with gr.Row():
        with gr.Column(scale=6):
            image_upload_cap = gr.Image(type="filepath", sources="upload", elem_id="image_upload_cap", visible=True)
            image_upload_text = gr.Image(type="filepath", sources="upload", elem_id="image_upload_cap", visible=False)
        with gr.Column(scale=3):
            text_options_radio = gr.Radio(
                [("Generate caption", "gen_caption"), ("Custom caption or label", "custom_caption")],
                label="Text Options",
                info="How should text be ingested?",
                value="gen_caption",
            )
            custom_caption = gr.Textbox(visible=True, interactive=True, label="Custom Caption or Label")
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        image_upload_cap.upload(
            ingest_gen_caption, [image_upload_cap, gr.Textbox(value="image", visible=False)], [text_upload_result]
        )
        image_upload_cap.clear(hide_text, [], [text_upload_result])
        image_upload_text.upload(ingest_with_text, [image_upload_text, custom_caption], [text_upload_result]).then(
            clear_text, [], [custom_caption]
        )
        image_upload_text.clear(hide_text, [], [text_upload_result])
        text_options_radio.change(select_upload_type, [text_options_radio], [image_upload_cap, image_upload_text])

with gr.Blocks() as upload_audio:
    gr.Markdown("# Ingest Your Own Audio Using Generated Transcripts")
    gr.Markdown("Use this interface to ingest your own audio file and generate a transcript for it")
    with gr.Row():
        with gr.Column(scale=6):
            audio_upload = gr.Audio(type="filepath")
        with gr.Column(scale=3):
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        audio_upload.upload(
            ingest_gen_transcript, [audio_upload, gr.Textbox(value="audio", visible=False)], [text_upload_result]
        )
        audio_upload.stop_recording(
            ingest_gen_transcript, [audio_upload, gr.Textbox(value="audio", visible=False)], [text_upload_result]
        )
        audio_upload.clear(hide_text, [], [text_upload_result])

with gr.Blocks() as upload_pdf:
    gr.Markdown("# Ingest Your Own PDF")
    gr.Markdown("Use this interface to ingest your own PDF file with text, tables, images, and graphs")
    with gr.Row():
        with gr.Column(scale=6):
            image_upload_cap = gr.File()
        with gr.Column(scale=3):
            text_upload_result_cap = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        image_upload_cap.upload(
            ingest_gen_caption, [image_upload_cap, gr.Textbox(value="PDF", visible=False)], [text_upload_result_cap]
        )
        image_upload_cap.clear(hide_text, [], [text_upload_result_cap])

with gr.Blocks() as qna:
    state = gr.State(multimodalqna_conv.copy())
    with gr.Row():
        with gr.Column(scale=4):
            video = gr.Video(height=512, width=512, elem_id="video", visible=True, label="Media")
            image = gr.Image(height=512, width=512, elem_id="image", visible=False, label="Media")
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(elem_id="chatbot", label="MultimodalQnA Chatbot", height=390)
            with gr.Row():
                with gr.Column(scale=6):
                    # textbox.render()
                    textbox = gr.Textbox(
                        # show_label=False,
                        # container=False,
                        label="Query",
                        info="Enter a text query below",
                        # submit_btn=False,
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
        [state, chatbot, textbox, video, image, clear_btn],
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
        [state, chatbot, video, image, clear_btn],
    )
with gr.Blocks(css=css) as demo:
    gr.Markdown("# MultimodalQnA")
    with gr.Tabs():
        with gr.TabItem("MultimodalQnA"):
            qna.render()
        with gr.TabItem("Upload Video"):
            upload_video.render()
        with gr.TabItem("Upload Image"):
            upload_image.render()
        with gr.TabItem("Upload Audio"):
            upload_audio.render()

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
    dataprep_ingest_endpoint = os.getenv(
        "DATAPREP_INGEST_SERVICE_ENDPOINT", "http://localhost:6007/v1/ingest_with_text"
    )
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
    global dataprep_ingest_addr
    dataprep_ingest_addr = dataprep_ingest_endpoint
    global dataprep_gen_transcript_addr
    dataprep_gen_transcript_addr = dataprep_gen_transcript_endpoint
    global dataprep_gen_caption_addr
    dataprep_gen_caption_addr = dataprep_gen_caption_endpoint

    uvicorn.run(app, host=args.host, port=args.port)
