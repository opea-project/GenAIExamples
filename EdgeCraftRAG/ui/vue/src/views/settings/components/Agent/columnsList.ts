// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const getTableColumns = (t: (key: string) => string): TableColumns[] => [
  {
    title: t("agent.name"),
    key: "name",
    dataIndex: "name",
    fixed: "left",
    minWidth: 100,
    visible: true,
    disabled: true,
  },
  {
    title: t("agent.id"),
    dataIndex: "idx",
    key: "idx",
    minWidth: 100,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("agent.pipeline"),
    dataIndex: "pipeline_idx",
    key: "pipeline_idx",
    minWidth: 100,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("agent.label.type"),
    dataIndex: "type",
    key: "type",
    minWidth: 60,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("agent.configs"),
    dataIndex: "configs",
    key: "configs",
    minWidth: 120,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("agent.status"),
    dataIndex: "active",
    key: "active",
    minWidth: 80,
    ellipsis: true,
    visible: true,
  },
  {
    title: t("pipeline.operation"),
    key: "operation",
    dataIndex: "operation",
    fixed: "right",
    visible: true,
    disabled: true,
  },
];

export default getTableColumns;
