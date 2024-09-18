#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

function freeze() {
    local file=$1
    local folder=$(dirname "$file")
    local keep_origin_packages="true"
    echo "::group::Check $file ..."
    pip-compile \
        --no-upgrade \
        --no-annotate \
        --no-header \
        --output-file "$folder/freeze.txt" \
        "$file"
    echo "::endgroup::"

    if [[ -e "$folder/freeze.txt" ]]; then
        if [[ "$keep_origin_packages" == "true" ]]; then
            # fix corner cases
            sed -i '/^\s*#/d; s/#.*//; /^\s*$/d; s/ //g' "$file"
            sed -i '/^\s*#/d; s/#.*//; /^\s*$/d; s/ //g; s/huggingface-hub\[inference\]/huggingface-hub/g; s/uvicorn\[standard\]/uvicorn/g' "$folder/freeze.txt"
            if grep -q '^transformers$' $file && ! grep -q '^transformers\[sentencepiece\]$' $file; then
                sed -i "s/transformers\[sentencepiece\]/transformers/" "$folder/freeze.txt"
            fi
            packages1=$(tr '><' '=' <"$file" | cut -d'=' -f1 | tr '[:upper:]' '[:lower:]' | sed 's/[-_]/-/g')
            packages2=$(cut -d'=' -f1 "$folder/freeze.txt" | tr '[:upper:]' '[:lower:]' | sed 's/[-_]/-/g')
            common_packages=$(comm -12 <(echo "$packages2" | sort) <(echo "$packages1" | sort))
            grep '^git\+' "$file" >temp_file || touch temp_file
            rm -rf "$file" && mv temp_file "$file"
            while IFS= read -r line; do
                package=$(echo "$line" | cut -d'=' -f1)
                package_transformed=$(echo "$package" | tr '[:upper:]' '[:lower:]' | sed 's/[_-]/-/g')
                pattern=$(echo "$package_transformed" | sed 's/\[/\\\[/g; s/\]/\\\]/g')
                if echo "$common_packages" | grep -q "^$pattern$"; then
                    echo "$line" >>"$file"
                fi
            done <"$folder/freeze.txt"
            rm "$folder/freeze.txt"
        else
            mv "$folder/freeze.txt" "$file"
        fi
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
    echo "::group::pip install --no-cache-dir pip-tools" && pip install --no-cache-dir pip-tools --upgrade && echo "::endgroup::"
    export -f freeze
    find . -name "requirements.txt" | xargs -n 1 -I {} bash -c 'freeze "$@"' _ {}
    find . -name "requirements-runtime.txt" | xargs -n 1 -I {} bash -c 'freeze "$@"' _ {}
}

main
