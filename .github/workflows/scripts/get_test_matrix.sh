#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# example: 'ChatQnA', 'CodeGen', ...
# hardware: 'xeon', 'gaudi', ...

set -e
changed_files=$changed_files
deploy_method=$deploy_method
run_matrix="{\"include\":["
hardware_list="xeon gaudi" # current support hardware list

examples=$(printf '%s\n' "${changed_files[@]}" | grep '/' | cut -d'/' -f1 | sort -u)
for example in ${examples}; do
    cd $WORKSPACE/$example
    if [[ ! $(find . -type f | grep ${deploy_method}) ]]; then continue; fi

    run_hardware=""
    if [[ $(printf '%s\n' "${changed_files[@]}" | grep ${example} | cut -d'/' -f2 | grep -E '*.py|Dockerfile*|ui|docker_image_build' ) ]]; then
        # run test on all hardware if megaservice or ui code change
        run_hardware=$hardware_list
    else
        for hardware in ${hardware_list}; do
            if [[ $(printf '%s\n' "${changed_files[@]}" | grep ${example} | grep -c ${hardware}) != 0 ]]; then
                run_hardware="${hardware} ${run_hardware}"
            fi
        done
    fi
    for hw in ${run_hardware}; do
        run_matrix="${run_matrix}{\"example\":\"${example}\",\"hardware\":\"${hw}\"},"
    done
done

run_matrix=$run_matrix"]}"
echo "run_matrix=${run_matrix}"
echo "run_matrix=${run_matrix}" >> $GITHUB_OUTPUT
