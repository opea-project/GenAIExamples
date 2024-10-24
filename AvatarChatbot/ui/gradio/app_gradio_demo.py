# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import io
import os
import shutil
import subprocess
import time

import aiohttp
import gradio as gr
import numpy as np
import requests
import soundfile as sf
from PIL import Image


# %% AudioQnA functions
def preprocess_audio(audio):
    """The audio data is a 16-bit integer array with values ranging from -32768 to 32767 and the shape of the audio data array is (samples,)"""
    sr, y = audio
    # Convert to normalized float32 audio
    y = y.astype(np.float32)
    y /= np.max(np.abs(y))
    # Convert the normalized float32 audio to a WAV file in memory
    buf = io.BytesIO()
    sf.write(buf, y, sr, format="WAV")
    buf.seek(0)  # Reset the buffer position to the beginning
    # Encode the WAV file to base64 string
    base64_bytes = base64.b64encode(buf.read())
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def base64_to_int16(base64_string):
    wav_bytes = base64.b64decode(base64_string)
    buf = io.BytesIO(wav_bytes)
    y, sr = sf.read(buf, dtype="int16")
    return sr, y


async def transcribe(audio_input):
    """Input: mic audio; Output: ai audio, text, text"""
    global ai_chatbot_url, chat_history
    chat_history = ""
    # Preprocess the audio
    base64bytestr = preprocess_audio(audio_input)

    # if not audio_choice:
    #     base64bytestr = preprocess_audio(audio_input)
    # else:
    #     # convert wav file to base64
    #     audio_index = int(audio_choice.split(".")[0]) - 1
    #     audio_filepath = audio_filepaths[audio_index]
    #     audio_input.value = audio_filepath
    #     with open(audio_filepath, "rb") as file:
    #         base64bytestr = base64.b64encode(file.read()).decode('utf-8')

    # Send the audio to the backend server
    initial_inputs = {"audio": base64bytestr, "max_tokens": 64}

    async with aiohttp.ClientSession() as session:
        async with session.post(ai_chatbot_url, json=initial_inputs) as response:
            # response = requests.post(ai_chatbot_url, json=initial_inputs)

            # Check the response status code
            if response.status == 200:
                response_json = await response.json()
                # with open("response.txt", "w") as file:
                #     file.write(response)

                # Decode the base64 string
                sampling_rate, audio_int16 = base64_to_int16(response_json["byte_str"])
                chat_history += f"User: {response_json['query']}\n\n"

                chat_ai = response_json["text"]
                hitted_ends = [",", ".", "?", "!", "。", ";"]
                last_punc_idx = max([chat_ai.rfind(punc) for punc in hitted_ends])
                if last_punc_idx != -1:
                    chat_ai = chat_ai[: last_punc_idx + 1]
                chat_history += f"AI: {chat_ai}"
                chat_history = chat_history.replace("OPEX", "OPEA")
                return (sampling_rate, audio_int16)  # handle the response
            else:
                return {"error": "Failed to transcribe audio", "status_code": response.status_code}


def resize_image(image_pil, size=(720, 720)):
    """Resize the image to the specified size."""
    return image_pil.resize(size, Image.LANCZOS)


def resize_video(video_path, save_path, size=(720, 1280)):
    """Resize the video to the specified size."""
    # command_resize_video = f"ffmpeg -y -i {video_path} -vf scale={size[0]}:{size[1]} {save_path}"
    # subprocess.run(command_resize_video, shell=True)


# %% Wav2Lip functions
async def gen_video(image, audio, model_choice):
    """Input: image (saved .png path), ai audio (saved .wav path); Output: video"""
    # 0. Preprocess audio
    # buf = io.BytesIO()
    sr, y = audio
    output_audio_save_path = "inputs/intermediate.wav"
    sf.write(output_audio_save_path, y, sr, format="WAV")

    # 1. Set environment variables
    match model_choice:
        case "wav2lip":
            os.environ["INFERENCE_MODE"] = "wav2lip_only"
            os.environ["CHECKPOINT_PATH"] = "Wav2Lip/checkpoints/wav2lip.pth"
        case "wav2lip+GAN":
            os.environ["INFERENCE_MODE"] = "wav2lip_only"
            os.environ["CHECKPOINT_PATH"] = "Wav2Lip/checkpoints/wav2lip_gan.pth"
        case "wav2lip+GFPGAN":
            os.environ["INFERENCE_MODE"] = "wav2lip+gfpgan"
            os.environ["CHECKPOINT_PATH"] = "Wav2Lip/checkpoints/wav2lip.pth"

    # os.environ['INFERENCE_MODE'] = 'wav2lip_only'
    # os.environ['CHECKPOINT_PATH'] = 'Wav2Lip/checkpoints/wav2lip_gan.pth'
    os.environ["FACE"] = image  # path to either an image or a video
    os.environ["AUDIO"] = output_audio_save_path  # path to .wav audio
    # os.environ['AUDIO'] = audio
    os.environ["FACESIZE"] = "96"
    os.environ["OUTFILE"] = "outputs/result6.mp4"
    os.environ["GFPGAN_MODEL_VERSION"] = "1.3"
    os.environ["UPSCALE_FACTOR"] = "1"  # int
    # os.environ['FPS'] = '25.' # can be lower (e.g., 10)
    os.environ["FPS"] = "10."  # can be lower when using an image (e.g., 10)

    # 2. Run inference.sh bash script to perform Wav2Lip+GFPGAN inference
    # Output video is saved at the path 'OUTFILE'
    # command_wav2lip_gfpgan = "bash inference_vars.sh"
    # subprocess.run(command_wav2lip_gfpgan, shell=True)

    outfile = os.environ.get("OUTFILE")
    if os.path.exists(outfile):
        res_video = outfile
    else:
        res_video = "inputs/loading.mp4"
    return res_video


# %% AI Avatar demo function
# ctao 7/19 - make it asynchronous
async def aiavatar_demo(audio_input):
    """Input: mic audio, image; Output: ai audio, text, text, ai video"""
    # Include AudioQnA
    output_audio = await transcribe(audio_input)  # AudioQnA

    if isinstance(output_audio, dict):  # in case of an error
        return None, None
    else:
        sr, audio_int16 = output_audio
        audio_file = "outputs/output_audio.wav"
        sf.write(audio_file, audio_int16, sr)
        # return audio_file, audio_file, image
        return audio_file


async def final_update(audio, image, model_choice):
    res_video = await gen_video(image, audio, model_choice)
    return res_video


# %% Main
if __name__ == "__main__":
    # HOST_IP = os.getenv("host_ip")
    HOST_IP = subprocess.check_output("hostname -I | awk '{print $1}'", shell=True).decode("utf-8").strip()

    # Fetch the AudioQnA backend server
    ai_chatbot_url = f"http://{HOST_IP}:3008/v1/audioqna"

    # Collect chat history to print in the interface
    chat_history = ""

    # Prepare 3 image paths
    # HOME = os.getenv("HOME")
    # HOME="/mnt/localdisk4"
    HOME = "/home/demo/"
    image_pils = [
        Image.open(os.path.join("../assets/img/woman1.png")),
        Image.open(os.path.join("../assets/img/man1.png")),
        Image.open(os.path.join("../assets/img/woman2.png")),
    ]

    video_paths = [
        os.path.join("../assets/video/man1.mp4"),
        os.path.join("../assets/video/woman2.mp4"),
        os.path.join("../assets/video/man4.mp4"),
    ]

    def image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Convert your images to Base64
    # opea_qr_base64 = image_to_base64('../rfcs/opea_qr.png')
    # opea_gh_qr_base64 = image_to_base64('../rfcs/opea_gh_qr.png')
    xeon_base64 = image_to_base64("../rfcs/xeon.jpg")
    gaudi_base64 = image_to_base64("../rfcs/gaudi.png")

    # List of prerecorded WAV files containing audio questions
    audio_filepaths = [
        "../assets/audio/intel1.wav",
        "../assets/audio/intel2.wav",
        "../assets/audio/intel3.wav",
        "../assets/audio/intel4.wav",
        "../assets/audio/pnp1.wav",
        "../assets/audio/pnp2.wav",
        "../assets/audio/pnp3.wav",
        "../assets/audio/pnp4.wav",
        "../assets/audio/entertainment1.wav",
        "../assets/audio/entertainment2.wav",
    ]
    audio_questions = [
        "1. What are the latest data center processor and AI accelerator products at Intel? Name them.",
        "2. What's the objective of the Open Platform for Enterprise AI? How is it helpful to enterprises building AI solutions?",
        "3. What is Intel's Gaudi 3 AI Accelerator performance compared to Nvidia H100?",
        "4. What kinds of Intel AI tools are available to accelerate AI workloads?",
        "5. What is Plug and Play Technology Center? Where is it located?",
        "6. Tell us about inflation in the US in the past few years?",
        "7. What is the difference between an index fund and a mutual fund?",
        "8. What is the difference between pretax and roth retirement accounts?",
        "9. Which team won the Superbowl in 2022?",
        "10. In the Lord of the Rings, who threw the Ring into Mount Doom?",
    ]

    # Demo frontend
    demo = gr.Blocks()
    with demo:
        # Define processing functions
        count = 0

        def initial_process(audio_input):
            global count, chat_history
            start_time = time.time()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_file = loop.run_until_complete(aiavatar_demo(audio_input))
            count += 1
            end_time = time.time()
            return audio_file, gr.State(value=str(count)), f"{(end_time - start_time):.1f} seconds", chat_history

        def final_process(audio, image, model_choice):
            start_time = time.time()
            # loop = asyncio.get_event_loop()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res_video = loop.run_until_complete(final_update(audio, image, model_choice))
            end_time = time.time()
            return res_video, f"{(end_time - start_time):.1f} seconds"

        def update_selected_image_state(image_index):
            selected_image_state.value = image_index
            # change image_input here
            if image_index < len(image_pils):
                return f"inputs/face_{image_index}.png"
            else:
                return f"inputs/video_{image_index - len(image_pils)}.mp4"

        def update_audio_input(audio_choice):
            if audio_choice:
                audio_index = int(audio_choice.split(".")[0]) - 1
                audio_filepath_gradio = f"inputs/audio_{audio_index:d}.wav"
                shutil.copyfile(audio_filepaths[audio_index], audio_filepath_gradio)
                # audio_input.value = audio_filepath_gradio
                return audio_filepath_gradio

        # UI Components
        # Title & Introduction
        gr.Markdown("<h1 style='font-size: 36px;'>A PyTorch and OPEA based AI Avatar Audio Chatbot</h1>")
        # gr.Markdown("# **Using OPEA to implement a RAG-Powered Human-Like AI Avatar Audio Chatbot**")
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown(
                    """
                <p style='font-size: 24px;'>Welcome to our AI Avatar Audio Chatbot! This application leverages PyTorch and <strong>OPEA (Open Platform for Enterprise AI) v0.8</strong> to provide you with a human-like conversational experience. It's run on Intel® Gaudi® AI Accelerator and Intel® Xeon® Processor, with hardware and software optimizations.<br>
                Please feel free to interact with the AI avatar by choosing your own avatar and talking into the mic.</p>
                            """
                )
            with gr.Column(scale=1):
                # with gr.Row():
                #     gr.Markdown(f"""
                #     <img src='data:image/png;base64,{opea_qr_base64}' alt='OPEA QR Code' style='width: 150px; height: auto;'>
                #     """, label="OPEA QR Code")
                #     gr.Markdown(f"""
                #     <img src='data:image/png;base64,{opea_gh_qr_base64}' alt='OPEA GitHub QR Code' style='width: 150px; height: auto;'>
                #     """, label="OPEA GitHub QR Code")
                with gr.Row():
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{gaudi_base64}' alt='Intel®Gaudi' style='width: 120px; height: auto;'>""",
                        label="Intel®Gaudi",
                    )
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{xeon_base64}' alt='Intel®Xeon' style='width: 120px; height: auto;'>""",
                        label="Intel®Xeon",
                    )
        gr.Markdown("<hr>")  # Divider

        # Inputs
        # Image gallery
        selected_image_state = gr.State(value=-1)
        image_clicks = []
        image_click_buttons = []
        video_clicks = []
        video_click_buttons = []
        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(sources=None, format="wav", label="🎤 or 📤 for your Input audio!")
                audio_choice = gr.Dropdown(
                    choices=audio_questions,
                    label="Choose an audio question",
                    value=None,  # default value
                )
                # Update audio_input when a selection is made from the dropdown
                audio_choice.change(fn=update_audio_input, inputs=audio_choice, outputs=audio_input)

                face_input = gr.File(
                    file_count="single",
                    file_types=["image", "video"],
                    label="Choose an avatar or 📤 an image or video!",
                )
                model_choice = gr.Dropdown(
                    choices=["wav2lip", "wav2lip+GAN", "wav2lip+GFPGAN"],
                    label="Choose a DL model",
                )
            with gr.Column(scale=2):
                # Display 3 images and buttons
                with gr.Row():
                    for i, image_pil in enumerate(image_pils):
                        image_pil = resize_image(image_pil)
                        save_path = f"inputs/face_{i}.png"
                        image_pil.save(save_path, "PNG")
                        image_clicks.append(gr.Image(type="filepath", value=save_path, label=f"Avatar {i+1}"))
                with gr.Row():
                    for i in range(len(image_pils)):
                        image_click_buttons.append(gr.Button(f"Use Image {i+1}"))
                # Display 3 videos and buttons
                with gr.Row():
                    for i, video_path in enumerate(video_paths):
                        save_path = f"inputs/video_{i}.mp4"
                        # shutil.copyfile(video_path, save_path)
                        resize_video(video_path, save_path)
                        video_clicks.append(gr.Video(value=save_path, label=f"Video {i+1}"))
                with gr.Row():
                    for i in range(len(video_paths)):
                        video_click_buttons.append(gr.Button(f"Use Video {i+1}"))

        submit_button = gr.Button("Submit")

        # Outputs
        gr.Markdown("<hr>")  # Divider
        with gr.Row():
            with gr.Column(scale=1):
                audio_output_interm = gr.Audio(label="🔊 Output audio", autoplay=True)
                chat_history_box = gr.Textbox(label="Chat History", value=chat_history)
                audio_time_text = gr.Textbox(label="Audio processing time", value="0.0 seconds")
            with gr.Column(scale=2):
                video_output = gr.Video(label="Your AI Avatar video: ", format="mp4", width=1280, height=720)
                video_time_text = gr.Textbox(label="Video processing time", value="0.0 seconds")

        # Technical details
        gr.Markdown("<hr>")  # Divider
        with gr.Row():
            gr.Markdown(
                """
                <p style='font-size: 24px;'>OPEA megaservice deployed: <br>
                <ul style='font-size: 24px;'>
                    <li><strong>AvatarChatbot</strong></li>
                </ul></p>
                <p style='font-size: 24px;'>OPEA microservices deployed:
                <ul style='font-size: 24px;'>
                    <li><strong>ASR</strong> (service: opea/whisper-gaudi, model: openai/whisper-small)</li>
                    <li><strong>LLM 'text-generation'</strong> (service: opea/llm-tgi, model: Intel/neural-chat-7b-v3-3)</li>
                    <li><strong>TTS</strong> (service: opea/speecht5-gaudi, model: microsoft/speecht5_tts)</li>
                    <li><strong>Animation</strong> (service: opea/animation, model: wav2lip+gfpgan)</li>
                </ul></p>
                        """
            )
            # <p style='font-size: 20px;'>OPEA's "AvatarChatbot" megaservice is composed of "ASR->LLM->TTS->Animation" microservices. It first generates an expert answer based on your query, and then animates the avatar figure with output audio. Feel free to interact with the AI avatar by choosing your own avatar and talking into the mic. </p>
        with gr.Row():
            gr.Image("./flowchart_1.png", label="Megaservice Flowchart")
        with gr.Row():
            gr.Markdown(
                """
            <p style='font-size: 24px;'>The AI Avatar Audio Chatbot is powered by the following Intel® AI software:<br>
                        <ul style='font-size: 24px;'>
                        <li><strong>Intel Gaudi Software v1.17.0</strong></li>
                        <li><strong>PyTorch v2.3.1 (Eager mode + torch.compile) </strong></li>
                        <li><strong>HPU Graph</strong></li>
                        <li><strong>Intel Neural Compressor (INC)</strong></li>
                        </ul></p>
                        """
            )

        # Disclaimer
        gr.Markdown("<hr>")  # Divider
        gr.Markdown("<h2 style='font-size: 24px;'>Notices & Disclaimers</h1>")
        gr.Markdown(
            """
                    <p style='font-size: 20px;'>Intel is committed to respecting human rights and avoiding complicity in human rights abuses. See Intel's Global Human Rights Principles. Intel's products and software are intended only to be used in applications that do not cause or contribute to a violation of an internationally recognized human right.<br></p>
                    <p style='font-size: 20px;'>© Intel Corporation.  Intel, the Intel logo, and other Intel marks are trademarks of Intel Corporation or its subsidiaries.  Other names and brands may be claimed as the property of others.<br></p>
                    <p style='font-size: 20px;'>You may not use or facilitate the use of this document in connection with any infringement or other legal analysis concerning Intel products described herein. You agree to grant Intel a non-exclusive, royalty-free license to any patent claim thereafter drafted which includes subject matter disclosed herein.<br></p>
                    """
        )

        # States
        interm_state = gr.State(value="initial")

        # State transitions
        for i in range(len(image_pils)):
            image_click_buttons[i].click(
                update_selected_image_state, inputs=[gr.Number(value=i, visible=False)], outputs=[face_input]
            )
        for i in range(len(video_paths)):
            video_click_buttons[i].click(
                update_selected_image_state,
                inputs=[gr.Number(value=i + len(image_pils), visible=False)],
                outputs=[face_input],
            )
        # submit_button = gr.Button("Submit")
        submit_button.click(
            initial_process,
            inputs=[audio_input],
            outputs=[
                audio_output_interm,
                interm_state,
                audio_time_text,
                chat_history_box,
            ],  # need to change interm_state
        )
        interm_state.change(
            final_process,
            inputs=[audio_output_interm, face_input, model_choice],
            outputs=[video_output, video_time_text],
        )

        demo.queue().launch(server_name="0.0.0.0", server_port=7861)
