// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const NodeParser = [
  {
    name: "Simple",
    value: "simple",
    describe: "Parse text with a preference for complete sentences.",
  },
  {
    name: "Hierarchical",
    value: "hierarchical",
    describe: "Splits a document into a recursive hierarchy Nodes using a NodeParser.",
  },
  {
    name: "Sentencewindow",
    value: "sentencewindow",
    describe:
      "Sentence window node parser. Splits a document into Nodes, with each node being a sentence. Each node contains a window from the surrounding sentences in the metadata.",
  },
  {
    name: "Unstructured",
    value: "unstructured",
    describe: "UnstructedNodeParser is a component that processes unstructured data.",
  },
] as const;

export const Indexer = [
  {
    name: "FaissVector",
    value: "faiss_vector",
    describe: "Embeddings are stored within a Faiss index.",
  },
  {
    name: "Vector",
    value: "vector",
    describe: "Vector Store Index.",
  },
] as const;
export const Retriever = [
  {
    name: "Vectorsimilarity",
    value: "vectorsimilarity",
    describe: "retrieval according to vector similarity",
  },
  {
    name: "Auto Merge",
    value: "auto_merge",
    describe: "This retriever will try to merge context into parent context.",
  },
  {
    name: "Bm25",
    value: "bm25",
    describe: "A BM25 retriever that uses the BM25 algorithm to retrieve nodes.",
  },
] as const;

export const PostProcessor = [
  {
    name: "Reranker",
    value: "reranker",
    describe: "The model for reranking.",
  },
  {
    name: "MetadataReplace",
    value: "metadata_replace",
    describe: "Used to replace the node content with a field from the node metadata.",
  },
] as const;

export const Generator = [
  {
    name: "Chatqna",
    value: "chatqna",
  },
] as const;
