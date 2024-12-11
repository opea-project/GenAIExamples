# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os

import pandas as pd
import requests


def generate_answer_agent_api(url, prompt):
    proxies = {"http": ""}
    payload = {
        "query": prompt,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    answer = response.json()["text"]
    return answer


def save_json_lines(json_lines, args):
    outfile = "sql_agent_results.json"
    output = os.path.join(args.output_dir, outfile)
    with open(output, "w") as f:
        for line in json_lines:
            f.write(str(line) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_file", type=str)
    parser.add_argument("--output_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    df = pd.read_csv(args.query_file)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    ip_address = os.getenv("ip_address", "localhost")
    url = f"http://{ip_address}:9095/v1/chat/completions"

    json_lines = []
    for _, row in df.iterrows():
        query = row["Query"]
        ref_answer = row["Answer"]
        print("******Query:\n", query)
        res = generate_answer_agent_api(url, query)
        print("******Answer:\n", res)
        # json_lines.append({"query": query,"answer":ref_answer, "agent_answer": res})
        # save_json_lines(json_lines, args)
        print("=" * 20)

    df.to_csv(os.path.join(args.output_dir, args.output_file), index=False)
