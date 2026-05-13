// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const getTableColumns = (t: (key: string) => string): TableColumns[] => [
  {
    title: t("agent.name"),
    key: "name",
    dataIndex: "name",
    fixed: "left",
    width: 100,
    visible: true,
    disabled: true,
  },
  {
    title: t("agent.id"),
    dataIndex: "idx",
    key: "idx",
    width: 200,
    ellipsis: true,
  },
  {
    title: t("agent.pipeline"),
    dataIndex: "pipeline_name",
    key: "pipeline_name",
    width: 100,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("agent.type"),
    dataIndex: "type",
    key: "type",
    width: 100,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("agent.configs"),
    dataIndex: "configs",
    key: "configs",
    width: 80,
    visible: true,
  },
  {
    title: t("agent.status"),
    dataIndex: "active",
    key: "active",
    width: 80,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("pipeline.operation"),
    key: "operation",
    dataIndex: "operation",
    fixed: "right",
    width: 200,
    visible: true,
    disabled: true,
  },
];

export default getTableColumns;
