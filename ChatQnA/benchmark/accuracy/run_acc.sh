#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

function main {

  init_params "$@"
  # run_benchmark
  echo $dataset
  if [[ ${dataset} == "MultiHop" ]]; then
    run_multihop
  elif [[ ${dataset} == "crud" ]]; then
    run_crud
  fi

}

# init params
function init_params {
  for var in "$@"
  do
    case $var in
      --dataset=*)
          dataset=$(  echo $var |cut -f2 -d=)
      ;;
      *)
          echo "Error: No such parameter: ${var}"
          exit 1
      ;;
    esac
  done
}

# run_multihop
function run_multihop {
  git clone https://github.com/yixuantt/MultiHop-RAG.git

  python eval_multihop.py \
      --docs_path MultiHop-RAG/dataset/corpus.json \
      --dataset_path MultiHop-RAG/dataset/MultiHopRAG.json \
      --ingest_docs \
      --retrieval_metrics

}

# run_crud
function run_crud {

  git clone https://github.com/IAAR-Shanghai/CRUD_RAG
  mkdir data/
  cp CRUD_RAG/data/crud_split/split_merged.json data/
  cp -r CRUD_RAG/data/80000_docs/ data/
  python process_crud_dataset.py

  python eval_crud.py \
      --dataset_path ./data/split_merged.json \
      --docs_path ./data/80000_docs \
      --ingest_docs
}


main "$@"
