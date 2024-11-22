#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
cd ${WORKSPACE}
[[ -f ${WORKSPACE}/diff_file ]] && rm -f ${WORKSPACE}/diff_file
source .github/workflows/scripts/change_color
# docker control/rm/scp/rsync/git cmd
check_list=("docker stop.+?-q?a" "docker rm" "docker kill" "sudo rm" "git .* -f" "git .* --hard")

# exclude path
exclude_check_path=".github/workflows/scripts"

# get change file lists (exclude delete files)
git fetch origin main
change_files=$(git diff FETCH_HEAD --name-status -- :^$exclude_check_path | grep -v "D" | awk '{print $2}')

status="success"
for file in ${change_files};
do
    # check file type: shell yaml python
    if [[ ! $(echo ${file} | grep -E ".*\.sh") ]] && [[ ! $(echo ${file} | grep -E "*.ya?ml") ]] && [[ ! $(echo ${file} | grep -E ".*\.py") ]];
    then
        echo "This file ${file} no need to check, exit"
        exit 0
    fi
    # get added command
    git diff FETCH_HEAD ${file} | grep "^\+.*" | grep -v "^+++" | sed "s|\+||g" > ${WORKSPACE}/diff_file
    for (( i=0; i<${#check_list[@]}; i++)); do
        if [[ $(cat diff_file | grep -c -E "${check_list[$i]}") != 0 ]]; then
            cmd=$(cat diff_file | grep -E -o "${check_list[$i]}")
            $BOLD_RED && echo "Found Dangerous Command: [ ${cmd} ] in [ $file ], Please Check"
            status="failed"
        fi;
    done;
done
[[ -f ${WORKSPACE}/diff_file ]] && rm -f ${WORKSPACE}/diff_file
[[ $status == "failed" ]] && exit 1 || exit 0
