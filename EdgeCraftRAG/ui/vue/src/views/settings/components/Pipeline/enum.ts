// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const NodeParser = [
  {
    name: "Simple",
    value: "simple",
    describe: "pipeline.desc.simple",
  },
  {
    name: "Hierarchical",
    value: "hierarchical",
    describe: "pipeline.desc.hierarchical",
  },
  {
    name: "Sentencewindow",
    value: "sentencewindow",
    describe: "pipeline.desc.sentencewindow",
  },
  {
    name: "Unstructured",
    value: "unstructured",
    describe: "pipeline.desc.unstructured",
  },
  {
    name: "kbadmin",
    value: "kbadmin_parser",
    describe: "pipeline.desc.kbadmin",
  },
] as const;

export const Indexer = [
  {
    name: "FaissVector",
    value: "faiss_vector",
    describe: "pipeline.desc.faissVector",
  },
  {
    name: "Vector",
    value: "vector",
    describe: "pipeline.desc.vector",
  },
  {
    name: "MilvusVector",
    value: "milvus_vector",
    describe: "pipeline.desc.milvusVector",
  },
  {
    name: "kbadmin",
    value: "kbadmin_indexer",
    describe: "pipeline.desc.kbadmin",
  },
] as const;
export const Retriever = [
  {
    name: "Vectorsimilarity",
    value: "vectorsimilarity",
    describe: "pipeline.desc.vectorsimilarity",
  },
  {
    name: "Auto Merge",
    value: "auto_merge",
    describe: "pipeline.desc.autoMerge",
  },
  {
    name: "Bm25",
    value: "bm25",
    describe: "pipeline.desc.bm25",
  },
  {
    name: "kbadmin",
    value: "kbadmin_retriever",
    describe: "pipeline.desc.kbadmin",
  },
] as const;

export const PostProcessor = [
  {
    name: "Reranker",
    value: "reranker",
    describe: "pipeline.desc.reranker",
  },
  {
    name: "MetadataReplace",
    value: "metadata_replace",
    describe: "pipeline.desc.metadataReplace",
  },
] as const;

export const Generator = [
  {
    name: "ChatQnA",
    value: "chatqna",
    describe: "pipeline.desc.chatQnA",
  },
  {
    name: "FreeChat",
    value: "freechat",
    describe: "pipeline.desc.freeChat",
  },
] as const;
