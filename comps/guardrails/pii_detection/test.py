# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os

import requests
from utils import Timer


def test_html(ip_addr="localhost", batch_size=20):
    import pandas as pd

    proxies = {"http": ""}
    url = f"http://{ip_addr}:6357/v1/piidetect"
    urls = pd.read_csv("data/ai_rss.csv")["Permalink"]
    urls = urls[:batch_size].to_list()
    payload = {"link_list": json.dumps(urls)}

    with Timer(f"send {len(urls)} link to pii detection endpoint"):
        try:
            resp = requests.post(url=url, data=payload, proxies=proxies)
            print(resp.text)
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
            print("Request successful!")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)


def test_text(ip_addr="localhost", batch_size=20):
    proxies = {"http": ""}
    url = f"http://{ip_addr}:6357/v1/piidetect"
    if os.path.exists("data/ai_rss.csv"):
        import pandas as pd

        content = pd.read_csv("data/ai_rss.csv")["Description"]
        content = content[:batch_size].to_list()
    else:
        content = (
            [
                """With new architectures, there comes a bit of a dilemma. After having spent billions of dollars training models with older architectures, companies rightfully wonder if it is worth spending billions more on a newer architecture that may itself be outmoded&nbsp;soon.
One possible solution to this dilemma is transfer learning. The idea here is to put noise into the trained model and then use the output given to then backpropagate on the new model. The idea here is that you don’t need to worry about generating huge amounts of novel data and potentially the number of epochs you have to train for is also significantly reduced. This idea has not been perfected yet, so it remains to be seen the role it will play in the&nbsp;future.
Nevertheless, as businesses become more invested in these architectures the potential for newer architectures that improve cost will only increase. Time will tell how quickly the industry moves to adopt&nbsp;them.
For those who are building apps that allow for a seamless transition between models, you can look at the major strives made in throughput and latency by YOCO and have hope that the major bottlenecks your app is having may soon be resolved.
It’s an exciting time to be building.
With special thanks to Christopher Taylor for his feedback on this blog&nbsp;post.
[1] Sun, Y., et al. “You Only Cache Once: Decoder-Decoder Architectures for Language Models” (2024),&nbsp;arXiv
[2] Sun, Y., et al. “Retentive Network: A Successor to Transformer for Large Language Models” (2023),&nbsp;arXiv
[3] Wikimedia Foundation, et al. “Hadamard product (matrices)” (2024), Wikipedia
[4] Sanderson, G. et al., “Attention in transformers, visually explained | Chapter 6, Deep Learning” (2024),&nbsp;YouTube
[5] A. Vaswani, et al., “Attention Is All You Need” (2017),&nbsp;arXiv
Understanding You Only Cache Once was originally published in Towards Data Science on Medium, where people are continuing the conversation by highlighting and responding to this story."""
            ]
            * batch_size
        )
    payload = {"text_list": json.dumps(content)}

    with Timer(f"send {len(content)} text to pii detection endpoint"):
        try:
            resp = requests.post(url=url, data=payload, proxies=proxies)
            print(resp.text)
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
            print("Request successful!")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)


def test_pdf(ip_addr="localhost", batch_size=20):
    proxies = {"http": ""}
    url = f"http://{ip_addr}:6357/v1/piidetect"
    dir_path = "data/pdf"
    file_list = os.listdir(dir_path)
    file_list = file_list[:batch_size]
    files = [("files", (f, open(os.path.join(dir_path, f), "rb"), "application/pdf")) for f in file_list]
    with Timer(f"send {len(files)} documents to pii detection endpoint"):
        try:
            resp = requests.request("POST", url=url, headers={}, files=files, proxies=proxies)
            print(resp.text)
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
            print("Request successful!")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_html", action="store_true", help="Test HTML pii detection")
    parser.add_argument("--test_pdf", action="store_true", help="Test PDF pii detection")
    parser.add_argument("--test_text", action="store_true", help="Test Text pii detection")
    parser.add_argument("--batch_size", type=int, default=20, help="Batch size for testing")
    parser.add_argument("--ip_addr", type=str, default="localhost", help="IP address of the server")

    args = parser.parse_args()
    if args.test_html:
        test_html(ip_addr=args.ip_addr, batch_size=args.batch_size)
    elif args.test_pdf:
        test_pdf(ip_addr=args.ip_addr, batch_size=args.batch_size)
    elif args.test_text:
        test_text(ip_addr=args.ip_addr, batch_size=args.batch_size)
    else:
        print("Please specify the test type")
