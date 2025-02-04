# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys


# jsonfile = "perfspect_2025-02-03_16-28-37" + os.sep + "louie-P14s-Gen-5.json"
def parse_used_disk_from_report(jsonfile):
    used_diskspace = 0
    with open(jsonfile, "r") as file:
        data = json.load(file)
        for item in data["Filesystem"]:
            if item["Mounted on"] == "/":
                used_diskspace = float(item["Used"].replace("G", ""))
                # print(item['Used'])
    return used_diskspace


jsonfile = "perfspect_2025-02-03_16-29-32" + os.sep + "louie-P14s-Gen-5_telem.json"


def parse_used_memory_from_report(jsonfile):
    max_memory_usage = 0
    with open(jsonfile, "r") as file:
        data = json.load(file)
        # print(data)
        for item in data["Memory Stats"]:
            # if item['Mounted on'] == '/':
            memory_usage = int(item["used"])
            if memory_usage > max_memory_usage:
                max_memory_usage = memory_usage
    max_memory_usage_mb = float(memory_usage / 1000)
    # print(max_memory_usage_mb)
    return max_memory_usage_mb


if __name__ == "__main__":

    jsonfile = sys.argv[1]
    if "telem" in jsonfile:
        max_memory_usage = parse_used_memory_from_report(jsonfile)
        print(max_memory_usage)
    else:
        disk_usage = parse_used_disk_from_report(jsonfile)
        print(disk_usage)
