// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@mui/material/styles";
import { PaletteChip, PaletteColor } from "@mui/material/styles";

declare module "@mui/material/styles" {
  interface Theme {
    customStyles: Record<string, Record<string, any>>;
  }

  interface ThemeOptions {
    customStyles?: Record<string, Record<string, any>>;
  }

  interface Palette {
    header?: PaletteColor;
    aside?: PaletteColor;
    customDivider?: PaletteColor;
    input?: PaletteColor;
    icon?: PaletteColor;
    user?: PaletteColor;
    code?: PaletteColor;
    gradientBlock?: PaletteColor;
    audioProgress?: PaletteColor;
    primaryInput?: PaletteColor;
    actionButtons?: PaletteColor;
    themeToggle?: PaletteColor;
    dropDown?: PaletteColor;
  }

  interface PaletteOptions {
    header?: PaletteColorOptions;
    aside?: PaletteColorOptions;
    customDivider?: PaletteColorOptions;
    input?: PaletteColorOptions;
    icon?: PaletteColorOptions;
    user?: PaletteColorOptions;
    code?: PaletteColorOptions;
    gradientBlock?: PaletteColorOptions;
    audioProgress?: PaletteColorOptions;
    primaryInput?: PaletteColorOptions;
    actionButtons?: PaletteColorOptions;
    themeToggle?: PaletteColorOptions;
    dropDown?: PaletteColorOptions;
  }
}
