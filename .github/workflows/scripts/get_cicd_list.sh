#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

WORKPATH=$PWD
# echo "mode is: "$1 "compose file is: "$2
if [ ! -d GenAIExamples ]; then
    git clone https://github.com/opea-project/GenAIExamples.git
fi
all_ci_yaml=$(find GenAIExamples -name "build.yaml")
all_ci_lists=$(grep '^[[:space:]]\{2\}[a-zA-Z0-9_-]\+:' $all_ci_yaml | awk -F: '{print$2}' | sed 's/^[[:space:]]\+//' | tr '\n' ',' | sed 's/,$//')

all_lists=$(grep '^[[:space:]]\{2\}[a-zA-Z0-9_-]\+:' $2 | sed 's/^[[:space:]]\{2\}\([a-zA-Z0-9_-]\+\):.*/\1/' | tr '\n' ',' | sed 's/,$//')
cd_lists=$(echo "$all_lists" | tr ',' '\n' | grep -v -F -x -f <(echo "$all_ci_lists" | tr ',' '\n') | tr '\n' ',' | sed 's/,$//')
ci_lists=$(echo "$all_lists" | tr ',' '\n' | grep -F -x -f <(echo "$all_ci_lists" | tr ',' '\n') | tr '\n' ',' | sed 's/,$//')
if [[ "$1" == "CI" ]]; then
    echo "$ci_lists"
elif [[ "$1" == "CD" ]]; then
    echo "$cd_lists"
elif [[ "$1" == "CICD" ]]; then
    echo "$all_lists"
fi
