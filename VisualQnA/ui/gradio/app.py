# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Some code adapted from https://github.com/haotian-liu/LLaVA/blob/main/llava/serve/gradio_web_server.py
# and https://github.com/haotian-liu/LLaVA/blob/main/llava/conversation.py

import argparse
import base64
import os
from io import BytesIO

import gradio as gr
import requests

title_markdown = """
# 🌋 LLaVA demo on Gaudi2
"""

tos_markdown = """
### Terms of use
By using this service, users are required to agree to the following terms:
The service is a research preview intended for non-commercial use only. It only provides limited safety measures and may generate offensive content. It must not be used for any illegal, harmful, violent, racist, or sexual purposes. The service may collect user dialogue data for future research.
Please click the "Flag" button if you get any inappropriate answer! We will collect those to keep improving our moderator.
For an optimal experience, please use desktop computers for this demo, as mobile devices may compromise its quality.
"""

block_css = """

#buttons button {
    min-width: min(120px,100%);
}

"""

no_change_btn = gr.Button()
enable_btn = gr.Button(interactive=True)
disable_btn = gr.Button(interactive=False)


def process_image(image, return_pil=False, image_format="PNG", max_len=1344, min_len=672):
    if max(image.size) > max_len:
        max_hw, min_hw = max(image.size), min(image.size)
        aspect_ratio = max_hw / min_hw
        shortest_edge = int(min(max_len / aspect_ratio, min_len, min_hw))
        longest_edge = int(shortest_edge * aspect_ratio)
        W, H = image.size
        if H > W:
            H, W = longest_edge, shortest_edge
        else:
            H, W = shortest_edge, longest_edge
        image = image.resize((W, H))
    if return_pil:
        return image
    else:
        buffered = BytesIO()
        image.save(buffered, format=image_format)
        img_b64_str = base64.b64encode(buffered.getvalue()).decode()
        return img_b64_str


def handle_llava_request(text, image, max_new_tokens, chat_history):
    print(f"text: {text}, image: {image}, max_new_tokens: {max_new_tokens}\n")
    img_b64_str = process_image(image, return_pil=False, image_format="JPEG")
    img_str = f'<img src="data:image/jpeg;base64,{img_b64_str}" alt="user upload image" />'

    # skip embedding the image in latter messages
    if len(chat_history) < 1:
        msg = img_str + text.replace("<image>", "").strip()
    else:
        msg = text.replace("<image>", "").strip()

    req_dict = {"prompt": f"<image>\nUSER: {text}\nASSISTANT:", "image": img_b64_str, "max_new_tokens": max_new_tokens}
    result = requests.post(f"{args.worker_addr}/generate", json=req_dict, proxies={"http": None})
    answer = result.json()["text"]

    chat_history.append([msg, answer])
    return [chat_history] + [enable_btn]


def clear_history(chat_history, image, text):
    chat_history = []
    image = None
    text = None
    return [chat_history, image, text] + [disable_btn]


def build_demo(embed_mode, cur_dir=None, concurrency_count=10):
    textbox = gr.Textbox(show_label=False, placeholder="Enter text and press ENTER", container=False)
    with gr.Blocks(title="LLaVA", theme=gr.themes.Default(), css=block_css) as demo:
        state = gr.State()

        if not embed_mode:
            gr.Markdown(title_markdown)

        with gr.Row():
            with gr.Column(scale=3):
                imagebox = gr.Image(type="pil")

                if cur_dir is None:
                    cur_dir = os.path.dirname(os.path.abspath(__file__))
                gr.Examples(
                    examples=[
                        [f"{cur_dir}/resources/extreme_ironing.jpg", "What is unusual about this image?"],
                        [
                            f"{cur_dir}/resources/waterview.jpg",
                            "What are the things I should be cautious about when I visit here?",
                        ],
                    ],
                    inputs=[imagebox, textbox],
                )

                with gr.Accordion("Parameters", open=False) as parameter_row:
                    max_output_tokens = gr.Slider(
                        minimum=0,
                        maximum=1024,
                        value=512,
                        step=64,
                        interactive=True,
                        label="Max output tokens",
                    )

            with gr.Column(scale=8):
                chatbot = gr.Chatbot(
                    elem_id="chatbot",
                    label="LLaVA Chatbot",
                    height=650,
                    layout="panel",
                )
                with gr.Row():
                    with gr.Column(scale=8):
                        textbox.render()
                    with gr.Column(scale=1, min_width=50):
                        submit_btn = gr.Button(value="Send", variant="primary")
                with gr.Row(elem_id="buttons") as button_row:
                    clear_btn = gr.Button(value="🗑️  Clear", interactive=False)

        if not embed_mode:
            gr.Markdown(tos_markdown)

        btn_list = [clear_btn]

        clear_btn.click(
            clear_history,
            [chatbot, imagebox, textbox],
            [chatbot, imagebox, textbox] + btn_list,
        )

        textbox.submit(
            handle_llava_request,
            [textbox, imagebox, max_output_tokens, chatbot],
            [chatbot] + btn_list,
        )

        submit_btn.click(
            handle_llava_request,
            [textbox, imagebox, max_output_tokens, chatbot],
            [chatbot] + btn_list,
        )

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # frontend host and port
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int)
    # backend worker address
    parser.add_argument(
        "--worker-addr", type=str, default="http://localhost:8085", help="The worker address of the LLaVA server."
    )
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--embed", action="store_true")
    parser.add_argument("--concurrency-count", type=int, default=16)

    args = parser.parse_args()
    print(args)
    demo = build_demo(args.embed, concurrency_count=args.concurrency_count)

    demo.queue(api_open=False).launch(server_name=args.host, server_port=args.port, share=args.share)
