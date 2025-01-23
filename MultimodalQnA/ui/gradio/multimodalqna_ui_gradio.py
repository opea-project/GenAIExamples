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
from gradio_pdf import PDF
from utils import build_logger, make_temp_image, server_error_msg, split_video

logger = build_logger("gradio_web_server", "gradio_web_server.log")
logflag = os.getenv("LOGFLAG", False)

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
    if state.pdf and os.path.exists(state.pdf):
        os.remove(state.pdf)
    state = multimodalqna_conv.copy()
    video = gr.Video(height=512, width=512, elem_id="video", visible=True, label="Media")
    image = gr.Image(height=512, width=512, elem_id="image", visible=False, label="Media")
    pdf = PDF(height=512, elem_id="pdf", interactive=False, visible=False, label="Media")
    return (state, state.to_gradio_chatbot(), {"text": "", "files": []}, None, video, image, pdf) + (disable_btn,) * 1


def add_text(state, textbox, audio, request: gr.Request):
    text = textbox["text"]
    logger.info(f"add_text. ip: {request.client.host}. len: {len(text)}")
    if audio:
        state.audio_query_file = audio
        state.append_message(state.roles[0], "--input placeholder--")
        state.append_message(state.roles[1], None)
        state.skip_next = False
        return (state, state.to_gradio_chatbot(), None, None) + (disable_btn,) * 1
    # If it is a image query
    elif textbox["files"]:
        image_file = textbox["files"][0]
        state.image_query_files[len(state.messages)] = image_file
        state.append_message(state.roles[0], text)
        state.append_message(state.roles[1], None)
        state.skip_next = False
        return (state, state.to_gradio_chatbot(), None, None) + (disable_btn,) * 1
    elif len(text) <= 0:
        state.skip_next = True
        return (state, state.to_gradio_chatbot(), None, None) + (no_change_btn,) * 1

    text = text[:2000]  # Hard cut-off

    state.append_message(state.roles[0], text)
    state.append_message(state.roles[1], None)
    state.skip_next = False

    return (state, state.to_gradio_chatbot(), None, None) + (disable_btn,) * 1


def http_bot(state, request: gr.Request):
    global gateway_addr
    logger.info(f"http_bot. ip: {request.client.host}")
    url = gateway_addr
    is_very_first_query = False
    is_audio_query = state.audio_query_file is not None
    if state.skip_next:
        # This generate call is skipped due to invalid inputs
        yield (state, state.to_gradio_chatbot(), None, None, None) + (no_change_btn,) * 1
        return

    if len(state.messages) == state.offset + 2:
        # First round of conversation
        is_very_first_query = True
        new_state = multimodalqna_conv.copy()
        new_state.append_message(new_state.roles[0], state.messages[-2][1])
        new_state.append_message(new_state.roles[1], None)
        new_state.audio_query_file = state.audio_query_file
        new_state.image_query_files = state.image_query_files
        state = new_state

    # Construct prompt
    prompt = state.get_prompt()

    # Make requests
    pload = {
        "messages": prompt,
    }

    if logflag:
        logger.info(f"==== request ====\n{pload}")
    logger.info(f"==== url request ====\n{gateway_addr}")

    state.messages[-1][-1] = "▌"

    yield (state, state.to_gradio_chatbot(), state.split_video, state.image, state.pdf) + (disable_btn,) * 1

    try:
        response = requests.post(
            url,
            headers=headers,
            json=pload,
            timeout=100,
        )
        logger.info(response.status_code)
        if logflag:
            logger.info(response.json())

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
                state.caption = metadata["transcript_for_inference"]
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
                elif file_ext == ".pdf":
                    try:
                        output_pdf_path = make_temp_image(state.video_file, file_ext)
                    except:
                        print(f"pdf {state.video_file} does not exist in UI host!")
                        output_pdf_path = None
                    state.pdf = output_pdf_path

        else:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        state.messages[-1][-1] = server_error_msg
        yield (state, state.to_gradio_chatbot(), None, None, None) + (enable_btn,)
        return

    state.messages[-1][-1] = message

    if is_audio_query:
        state.messages[-2][-1] = metadata.get("audio", "--transcribed audio not available--")
        state.audio_query_file = None

    yield (
        state,
        state.to_gradio_chatbot(),
        gr.Video(state.split_video, visible=state.split_video is not None),
        gr.Image(state.image, visible=state.image is not None),
        PDF(state.pdf, visible=state.pdf is not None, interactive=False, starting_page=int(state.time_of_frame_ms)),
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
    logger.info(response.status_code)
    if response.status_code == 200:
        response = response.json()
        if logflag:
            logger.info(response)
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
    logger.info(response.status_code)
    if response.status_code == 200:
        response = response.json()
        if logflag:
            logger.info(response)
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
    logger.info(response.status_code)
    if response.status_code == 200:
        response = response.json()
        if logflag:
            logger.info(response)
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


def ingest_pdf(filepath, request: gr.Request):
    yield (gr.Textbox(visible=True, value="Please wait while your uploaded PDF is ingested into the database..."))
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print("Found malicious PDF file name!")
        yield (
            gr.Textbox(
                visible=True,
                value="Your uploaded PDF's file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
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
    response = requests.post(dataprep_ingest_addr, headers=headers, files=files)
    print(response.status_code)
    if response.status_code == 200:
        response = response.json()
        yield (gr.Textbox(visible=True, value="The PDF ingestion is done. Saving your uploaded PDF..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value="Congratulations, your upload is done!\nClick the X button on the top right of the PDF upload box to upload another file.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the PDF upload box to reupload your file.",
            )
        )
        time.sleep(2)
    return


def hide_text(request: gr.Request):
    return gr.Textbox(visible=False)


def clear_text(request: gr.Request):
    return None


with gr.Blocks() as upload_video:
    gr.Markdown("# Ingest Videos Using Generated Transcripts or Captions")
    gr.Markdown("Use this interface to ingest a video and generate transcripts or captions for it")

    def select_upload_type(choice, request: gr.Request):
        if choice == "transcript":
            return gr.Video(sources="upload", visible=True, format="mp4"), gr.Video(
                sources="upload", visible=False, format="mp4"
            )
        else:
            return gr.Video(sources="upload", visible=False, format="mp4"), gr.Video(
                sources="upload", visible=True, format="mp4"
            )

    with gr.Row():
        with gr.Column(scale=6):
            video_upload_trans = gr.Video(sources="upload", elem_id="video_upload_trans", visible=True, format="mp4")
            video_upload_cap = gr.Video(sources="upload", elem_id="video_upload_cap", visible=False, format="mp4")
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
    gr.Markdown("# Ingest Images Using Generated or Custom Captions")
    gr.Markdown("Use this interface to ingest an image and generate a caption for it")

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
    gr.Markdown("# Ingest Audio Using Generated Transcripts")
    gr.Markdown("Use this interface to ingest an audio file and generate a transcript for it")
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
    gr.Markdown("# Ingest PDF Files")
    gr.Markdown("Use this interface to ingest a PDF file with text and images")
    with gr.Row():
        with gr.Column(scale=6):
            pdf_upload = PDF(label="PDF File")
        with gr.Column(scale=3):
            pdf_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        pdf_upload.upload(ingest_pdf, [pdf_upload], [pdf_upload_result])

with gr.Blocks() as qna:
    state = gr.State(multimodalqna_conv.copy())
    with gr.Row():
        with gr.Column(scale=2):
            video = gr.Video(height=512, width=512, elem_id="video", visible=True, label="Media")
            image = gr.Image(height=512, width=512, elem_id="image", visible=False, label="Media")
            pdf = PDF(height=512, elem_id="pdf", interactive=False, visible=False, label="Media")
        with gr.Column(scale=9):
            chatbot = gr.Chatbot(elem_id="chatbot", label="MultimodalQnA Chatbot", height=390)
            with gr.Row():
                with gr.Column(scale=8):
                    with gr.Tabs():
                        with gr.TabItem("Text & Image Query"):
                            textbox = gr.MultimodalTextbox(
                                show_label=False, container=True, submit_btn=False, file_types=["image"]
                            )
                        with gr.TabItem("Audio Query"):
                            audio = gr.Audio(
                                type="filepath",
                                sources=["microphone", "upload"],
                                show_label=False,
                                container=False,
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
        [state, chatbot, textbox, audio, video, image, pdf, clear_btn],
    )

    submit_btn.click(
        add_text,
        [state, textbox, audio],
        [state, chatbot, textbox, audio, clear_btn],
    ).then(
        http_bot,
        [
            state,
        ],
        [state, chatbot, video, image, pdf, clear_btn],
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
        with gr.TabItem("Upload PDF"):
            upload_pdf.render()

demo.queue()
app = gr.mount_gradio_app(app, demo, path="/")
share = False
enable_queue = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=os.getenv("UI_PORT", 5173))
    parser.add_argument("--concurrency-count", type=int, default=20)
    parser.add_argument("--share", action="store_true")

    MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 8888)
    DATAPREP_MMR_PORT = os.getenv("DATAPREP_MMR_PORT", 6007)

    backend_service_endpoint = os.getenv(
        "BACKEND_SERVICE_ENDPOINT", f"http://localhost:{MEGA_SERVICE_PORT}/v1/multimodalqna"
    )
    dataprep_ingest_endpoint = os.getenv(
        "DATAPREP_INGEST_SERVICE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/ingest"
    )
    dataprep_gen_transcript_endpoint = os.getenv(
        "DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/generate_transcripts"
    )
    dataprep_gen_caption_endpoint = os.getenv(
        "DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/generate_captions"
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
