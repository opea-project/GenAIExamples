#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# example: 'ChatQnA', 'CodeGen', ...
# hardware: 'xeon', 'gaudi', ...

set -e
changed_files=$changed_files
test_mode=$test_mode
run_matrix="{\"include\":["

examples=$(printf '%s\n' "${changed_files[@]}" | grep '/' | cut -d'/' -f1 | sort -u)
for example in ${examples}; do
    cd $WORKSPACE/$example
    if [[ ! $(find . -type f | grep ${test_mode}) ]]; then continue; fi
    cd tests
    ls -l
    if [[ "$test_mode" == "docker_image_build" ]]; then
        hardware_list="gaudi xeon"
    else
        find_name="test_${test_mode}*_on_*.sh"
        hardware_list=$(find . -type f -name "${find_name}" | cut -d/ -f2 | cut -d. -f1 | awk -F'_on_' '{print $2}'| sort -u)
    fi
    echo -e "Test supported hardware list: \n${hardware_list}"

    run_hardware=""
    if [[ $(printf '%s\n' "${changed_files[@]}" | grep ${example} | cut -d'/' -f2 | grep -E '\.py|Dockerfile*|ui|docker_image_build' ) ]]; then
        echo "run test on all hardware if megaservice or ui code change..."
        run_hardware=$hardware_list
    elif [[ $(printf '%s\n' "${changed_files[@]}" | grep ${example} | grep 'tests'| cut -d'/' -f3 | grep -vE '^test_|^_test' ) ]]; then
        echo "run test on all hardware if common test scripts change..."
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
