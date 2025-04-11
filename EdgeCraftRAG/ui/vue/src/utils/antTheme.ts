// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { theme } from "ant-design-vue";
export const antTheme = {
  black: {
    token: {
      colorPrimary: "#111111",
    },
  },
  subTheme: {
    token: {
      colorPrimary: "#0054AE",
    },
  },
  success: {
    token: {
      colorPrimary: "#008A00",
    },
  },
  danger: {
    token: {
      colorPrimary: "#ce0000",
    },
  },
  light: {
    algorithm: theme.defaultAlgorithm,
    inherit: false,
    token: {
      colorPrimary: "#00377C",
      colorPrimaryBg: "#E0EAFF",
      colorError: "#EA0000",
      colorInfo: "#AAAAAA",
      colorSuccess: "#179958",
      colorWarning: "#faad14",
      colorTextBase: "#131313",
      colorSuccessBg: "#D6FFE8",
      colorWarningBg: "#feefd0",
      colorErrorBg: "#FFA3A3",
      colorInfoBg: "#EEEEEE",
    },
    cssVar: true,
  },
  dark: {
    algorithm: theme.darkAlgorithm,
    inherit: false,
    // token: {
    //   colorPrimary: "#0054ae",
    //   colorPrimaryBg: "#0068B5",
    //   colorError: "#EA0000",
    //   colorInfo: "#AAAAAA",
    //   colorSuccess: "#179958",
    //   colorWarning: "#faad14",
    //   colorTextBase: "#ffffff",
    //   colorSuccessBg: "#D6FFE8",
    //   colorWarningBg: "#feefd0",
    //   colorErrorBg: "#FFA3A3",
    //   colorInfoBg: "#EEEEEE",
    // },
    cssVar: true,
  },
};
