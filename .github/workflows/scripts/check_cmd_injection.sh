#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
cd ${WORKSPACE}
[[ -f ${WORKSPACE}/diff_file ]] && rm -f ${WORKSPACE}/diff_file
# docker control/rm/scp/rsync/git cmd
check_list=("docker stop" "docker rm" "docker kill" "sudo rm" "git .* -f")

# exclude path
exclude_check_path="${WORKSPACE}/.github/workflows/scripts"

# get change file lists (exclude delete files)
git fetch origin main
change_files=$(git diff main --name-status -- :^$exclude_check_path | grep -v "D" | awk '{print $2}')

status="success"
for file in ${change_files};
do
    echo "file name is ${file}"
    # check file type: shell yaml python
    if [[ ! $(echo ${file} | grep -E ".*\.sh") ]] && [[ ! $(echo ${file} | grep -E "*.ya?ml") ]] && [[ ! $(echo ${file} | grep -E ".*\.py") ]];
    then
        echo "This file ${file} no need to check, exit"
        exit 0
    fi
    # get added command
    git diff main ${file} | grep "^\+.*" | grep -v "^+++" | sed "s|\+||g" > ${WORKSPACE}/diff_file
    #cat diff_file | while read line; do 
    #    echo $line; 
    #    for (( i=0; i<${#check_list[@]}; i++)); do 
    #        if [[ $line == *"${check_list[$i]}"* ]]; then
    #            echo "Found Dangerous Command: $line in $file, Please Check"
    #            status="failed"
    #        fi; 
    #    done; 
    #done
    for (( i=0; i<${#check_list[@]}; i++)); do 
        if [[ $(cat diff_file | grep -c "${check_list[$i]}") != 0 ]]; then
            echo "Found Dangerous Command: $line in $file, Please Check"
            status="failed"
        fi; 
    done; 
done
[[ -f ${WORKSPACE}/diff_file ]] && rm -f ${WORKSPACE}/diff_file
[[ $status == "failed" ]] && exit 1 || exit 0
