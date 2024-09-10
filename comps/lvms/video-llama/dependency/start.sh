# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# /bin/bash
# Download models
MODEL_REPO=https://huggingface.co/DAMO-NLP-SG/Video-LLaMA-2-7B-Finetuned
llm_download=${llm_download}
echo "llm_download: ${llm_download}"
if [ "$llm_download" = "True" ]; then
  # clean if exists
  rm -rf /home/user/model/Video-LLaMA-2-7B-Finetuned

  echo "Please wait for model download..."
  git lfs install &&  git clone ${MODEL_REPO} /home/user/model/Video-LLaMA-2-7B-Finetuned
  # rm Video-LLaMA-2-7B-Finetuned/AL*.pth Video-LLaMA-2-7B-Finetuned/imagebind_huge.pth
elif [ "$llm_download" = "False" ]; then
  echo "No model download"
else
  echo "llm_download should be True or False"
  exit 1
fi

python server.py
