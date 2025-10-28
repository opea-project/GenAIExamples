#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

WORKING_DIR="$(pwd)"
PUBLIC_HOSTNAME="$(hostname -I | awk '{print $1}')"
SHOPPING_ADMIN_USER="admin"
SHOPPING_ADMIN_PASSWORD="admin1234"
SHOPPING_ADMIN_PORT=8084
SHOPPING_ADMIN_URL="http://${PUBLIC_HOSTNAME}:${SHOPPING_ADMIN_PORT}/admin"
ARCHIVES_LOCATION="/data2/hf_model"
