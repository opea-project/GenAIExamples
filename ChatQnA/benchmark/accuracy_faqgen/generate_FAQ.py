# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time

import requests

llm_endpoint = os.getenv("FAQ_ENDPOINT", "http://0.0.0.0:9000/v1/faqgen")

f = open("data/sqv2_context.json", "r")
sqv2_context = json.load(f)

start_time = time.time()
headers = {"Content-Type": "application/json"}
for i in range(1204):
    start_time_tmp = time.time()
    print(i)
    inputs = sqv2_context[str(i)]
    data = {"query": inputs, "max_new_tokens": 128}
    response = requests.post(llm_endpoint, json=data, headers=headers)
    f = open(f"data/result/sqv2_faq_{i}", "w")
    f.write(inputs)
    f.write(str(response.content, encoding="utf-8"))
    f.close()
    print(f"Cost {time.time()-start_time_tmp} seconds")
print(f"\n Finished! \n Totally Cost {time.time()-start_time} seconds\n")
