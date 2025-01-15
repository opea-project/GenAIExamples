# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Folder name you're looking for
target_folder="GenAIComps"
proj_folder=$(pwd)

# Start from the current directory
current_dir=$(pwd)

# Loop until the folder is found or we reach the root
while [[ "$current_dir" != "/" ]]; do
  # Check if the folder exists in the current directory
  if [ -d "$current_dir/$target_folder" ]; then
    # If found, change to that directory and exit
    cd "$current_dir/$target_folder" || exit
    echo "Found and changed to $current_dir/$target_folder"
  fi
  # Move up one level
  current_dir=$(dirname "$current_dir")
done

docker build --no-cache \
    -t opea/guardrails-hallucination-detection:latest \
    --build-arg https_proxy=$https_proxy \
    --build-arg http_proxy=$http_proxy \
    -f $proj_folder/Dockerfile .
