#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

function get_latest_version() {
    repo_image=$1
    versions=$(curl -s "https://registry.hub.docker.com/v2/repositories/$repo_image/tags/" | jq '."results"[]["name"]' | tr -d '"')
    echo "version list: $versions"
    latest_version=$(printf "%s\n" "${versions[@]}" | grep -v "latest" | sort -V | tail -n 1)
    echo "latest version: $latest_version"
    replace_image_version $repo_image $latest_version
}

function replace_image_version() {
    repo_image=$1
    version=$2
    find . -name "Dockerfile" | xargs sed -i "s|$repo_image:latest|$repo_image:$version|g"
}

function check_branch_name() {
    if [[ "$GITHUB_REF_NAME" == "main" ]]; then
        echo "$GITHUB_REF_NAME is protected branch"
        exit 0
    else
        echo "branch name is $GITHUB_REF_NAME"
    fi
}

function main() {
    check_branch_name
    repo_image_list="langchain/langchain"
    for repo_image in $repo_image_list; do
        echo "::group::check $repo_image"
        get_latest_version $repo_image
        echo "::endgroup::"
    done
    freeze_tag_in_markdown
}

main
