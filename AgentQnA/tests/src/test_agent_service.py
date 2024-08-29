# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os

import pandas as pd
import requests
from commons import QUERY_SEPERATOR


def get_test_data(args):
    if args.query_file.endswith(".jsonl"):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith(".csv"):
        df = pd.read_csv(args.query_file)
    return df


def generate_answer(url, prompt):
    proxies = {"http": ""}
    payload = {
        "query": prompt,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    answer = response.json()["text"]
    return answer


def save_results(output_file, output_list):
    with open(output_file, "w") as f:
        for output in output_list:
            f.write(json.dumps(output))
            f.write("\n")


def save_as_csv(output):
    df = pd.read_json(output, lines=True, convert_dates=False)
    df.to_csv(output.replace(".jsonl", ".csv"), index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host_ip", type=str, default="localhost", help="host ip of the retrieval tool")
    parser.add_argument("--port", type=str, default="9095", help="port of the retrieval tool")
    parser.add_argument("--query_file", type=str, default=None, help="query jsonl file")
    parser.add_argument("--output_file", type=str, default="output.jsonl", help="output jsonl file")
    parser.add_argument("--quick_test", action="store_true", help="run quick test")
    args = parser.parse_args()

    host_ip = args.host_ip
    port = args.port
    endpoint = "{port}/v1/chat/completions".format(port=port)
    url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=endpoint)

    if args.quick_test:
        query = [
            "Taylor Swift hometown",
            # "how many songs has the band the beatles released that have been recorded at abbey road studios?",
            # "what's the most recent album from the founder of ysl records?",
            # "when did dolly parton's song, blown away, come out?"
            # "what song topped the billboard chart on 2004-02-04?",
            # "what grammy award did edgar barrera win this year?",
            # "who has had more number one hits on the us billboard hot 100 chart, michael jackson or elvis presley?",
        ]
        query_time = [
            "08/11/2024, 23:37:29 PT",
            # "03/21/2024, 23:37:29 PT",
            # "03/21/2024, 23:37:29 PT",
            # "03/21/2024, 23:37:29 PT",
        ]
        df = pd.DataFrame({"query": query, "query_time": query_time})
    else:
        df = get_test_data(args)
        df = df.head()  # for validation purpose

    output_list = []
    n = 0
    for _, row in df.iterrows():
        q = row["query"]
        t = row["query_time"]
        prompt = "Question: {}\nThe question was asked at: {}".format(q, t)
        print(QUERY_SEPERATOR)
        print("******Query:\n", prompt)
        print("******Agent is working on the query")
        answer = generate_answer(url, prompt)
        print("******Answer from agent:\n", answer)
        print("=" * 50)
        output_list.append(
            {
                "query": q,
                "query_time": t,
                # "ref_answer": row["answer"],
                "answer": answer,
                # "question_type": row["question_type"],
                # "static_or_dynamic": row["static_or_dynamic"],
            }
        )
        save_results(args.output_file, output_list)
        # n += 1
        # if n > 1:
        #     break
    save_results(args.output_file, output_list)
    save_as_csv(args.output_file)
