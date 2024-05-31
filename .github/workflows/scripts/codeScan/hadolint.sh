#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

source /GenAIExamples/.github/workflows/scripts/change_color
log_dir=/GenAIExamples/.github/workflows/scripts/codeScan

find . -type f \( -name "Dockerfile*" \) -print -exec hadolint --ignore DL3006 --ignore DL3007 --ignore DL3008 {} \; 2>&1 | tee ${log_dir}/hadolint.log

if [[ $(grep -c "error" ${log_dir}/hadolint.log) != 0 ]]; then
    $BOLD_RED && echo "Error!! Please Click on the artifact button to download and check error details." && $RESET
    exit 1
fi

$BOLD_PURPLE && echo "Congratulations, Hadolint check passed!" && $LIGHT_PURPLE && echo " You can click on the artifact button to see the log details." && $RESET
exit 0
