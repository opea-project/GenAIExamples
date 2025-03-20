# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json

faq_dict = {}
fails = []
for i in range(1204):
    data = open(f"data/result/sqv2_faq_{i}", "r").readlines()
    result = data[-6][6:]
    # print(result)
    if "LLMChain/final_output" not in result:
        print(f"error1: fail for {i}")
        fails.append(i)
        continue
    try:
        result2 = json.loads(result)
        result3 = result2["ops"][0]["value"]["text"]
        faq_dict[str(i)] = result3
    except:
        print(f"error2: fail for {i}")
        fails.append(i)
        continue
with open("data/sqv2_faq.json", "w") as outfile:
    json.dump(faq_dict, outfile)
print("Failure index:")
print(fails)
