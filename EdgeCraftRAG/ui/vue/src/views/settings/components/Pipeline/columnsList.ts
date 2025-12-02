// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const getTableColumns = (t: (key: string) => string): TableColumns[] => [
  {
    title: t("pipeline.name"),
    key: "name",
    dataIndex: "name",
    fixed: "left",
    minWidth: 200,
    visible: true,
    disabled: true,
  },
  {
    title: t("pipeline.id"),
    dataIndex: "idx",
    key: "idx",
    minWidth: 100,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("pipeline.config.nodeParser"),
    key: "parser_type",
    dataIndex: ["node_parser", "parser_type"],
    minWidth: 100,
    visible: false,
  },
  {
    title: t("pipeline.config.indexer"),
    key: "indexer_type",
    dataIndex: ["indexer", "indexer_type"],
    minWidth: 100,
    visible: false,
  },
  {
    title: t("pipeline.config.embedding"),
    key: "embedding",
    dataIndex: ["indexer", "model", "model_id"],
    minWidth: 180,
    visible: true,
  },
  {
    title: t("pipeline.config.retriever"),
    key: "retriever_type",
    dataIndex: ["retriever", "retriever_type"],
    minWidth: 100,
    visible: false,
  },
  {
    title: t("pipeline.config.postProcessor"),
    key: "postProcessor",
    dataIndex: "postProcessor",
    minWidth: 220,
    visible: false,
  },
  {
    title: t("pipeline.config.rerank"),
    key: "rerank",
    dataIndex: "rerank",
    minWidth: 180,
    visible: true,
  },
  {
    title: t("pipeline.config.llm"),
    key: "inference_type",
    dataIndex: ["generator", "inference_type"],
    minWidth: 120,
    visible: true,
  },
  {
    title: t("pipeline.config.language"),
    key: "language",
    dataIndex: ["generator", "model", "model_id"],
    minWidth: 180,
    visible: true,
  },
  {
    title: t("pipeline.status"),
    key: "status",
    dataIndex: "status",
    minWidth: 120,
    visible: true,
  },
  {
    title: t("pipeline.operation"),
    key: "operation",
    dataIndex: "operation",
    fixed: "right",
    minWidth: 340,
    visible: true,
    disabled: true,
  },
];

export default getTableColumns;
