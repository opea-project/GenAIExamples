# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

UI_DIRECTORY = os.getenv("TMPFILE_PATH", "/home/user/ui_cache")
# Define the root directory for knowledge base files
CONFIG_DIRECTORY = os.path.join(UI_DIRECTORY, "configs")
if not os.path.exists(CONFIG_DIRECTORY):
    os.makedirs(CONFIG_DIRECTORY, exist_ok=True)

IMG_OUTPUT_DIR = os.path.join(UI_DIRECTORY, "pic")
os.makedirs(IMG_OUTPUT_DIR, exist_ok=True)

KNOWLEDGEBASE_FILE = os.path.join(CONFIG_DIRECTORY, "knowledgebase.json")
PIPELINE_FILE = os.path.join(CONFIG_DIRECTORY, "pipeline.json")
AGENT_FILE = os.path.join(CONFIG_DIRECTORY, "agent.json")

EXPERIENCE_FILE = os.path.join(UI_DIRECTORY, "experience_dir/experience.json")
DOCUMENT_DATA_FILE = os.path.join(UI_DIRECTORY, "document_data.json")
SESSION_FILE = os.path.join(UI_DIRECTORY, "session.json")

SEARCH_CONFIG_PATH = os.path.join(UI_DIRECTORY, "configs/search_config.yaml")
SEARCH_DIR = os.path.join(UI_DIRECTORY, "configs/experience_dir/experience.json")
