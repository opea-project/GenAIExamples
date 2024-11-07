#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

declare -A dict
dict["langchain/langchain"]="docker://docker.io/langchain/langchain"
dict["vault.habana.ai/gaudi-docker/1.18.0/ubuntu22.04/habanalabs/pytorch-installer-2.4.0"]="docker://vault.habana.ai/gaudi-docker/1.18.0/ubuntu22.04/habanalabs/pytorch-installer-2.4.0"

function get_latest_version() {
    repo_image=$1
    versions=$(skopeo list-tags ${dict[$repo_image]} | jq -r '.Tags[]')
    printf "version list:\n$versions\n"
    latest_version=$(printf "%s\n" "${versions[@]}" | grep -E '^[\.0-9\-]+$' | sort -V | tail -n 1)
    echo "latest version: $latest_version"
    replace_image_version $repo_image $latest_version
}

function replace_image_version() {
    repo_image=$1
    version=$2
    if [[ -z "$version" ]]; then
        echo "version is empty"
    else
        echo "replace $repo_image:latest with $repo_image:$version"
        find . -name "Dockerfile*" | xargs sed -i "s|$repo_image:latest[A-Za-z0-9\-]*|$repo_image:$version|g"
        find . -name "*.yaml" | xargs sed -i "s|$repo_image:latest[A-Za-z0-9\-]*|$repo_image:$version|g"
        find . -name "*.md" | xargs sed -i "s|$repo_image:latest[A-Za-z0-9\-]*|$repo_image:$version|g"
    fi
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
    for repo_image in "${!dict[@]}"; do
        echo "::group::check $repo_image"
        get_latest_version $repo_image
        echo "::endgroup::"
    done
}

main
