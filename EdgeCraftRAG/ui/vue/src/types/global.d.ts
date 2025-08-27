// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Declaration of External npm Plugin Modules
declare module "js-cookie";
declare module "qs";
declare module "vite-plugin-vue-setup-extend-plus";
declare module "vue3-markdown-it";
declare module "event-source-polyfill";
declare module "@kangc/v-md-editor/lib/preview";
declare module "prismjs";

// Declaration module to prevent errors when importing files
declare module "*.json";
declare module "*.png";
declare module "*.jpg";
declare module "*.less";
declare module "*.ts";
declare module "*.js";
declare module "lodash";

// Declaration vue file
declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

// Global Variable
/* eslint-disable */
declare interface Window {
  nextLoading: boolean;
  BMAP_SATELLITE_MAP: any;
  BMap: any;
}

// Declaration Router
declare type RouteItem<T = any> = {
  path: string;
  name?: string | symbol | undefined | null;
  redirect?: string;
  k?: T;
  meta?: {
    title?: string;
    isLink?: string;
    isHide?: boolean;
    isKeepAlive?: boolean;
    isAffix?: boolean;
    isIframe?: boolean;
    roles?: string[];
    icon?: string;
    isDynamic?: boolean;
    isDynamicPath?: string;
    isIframeOpen?: string;
    loading?: boolean;
  };
  children: T[];
  query?: { [key: string]: T };
  params?: { [key: string]: T };
  contextMenuClickId?: string | number;
  commonUrl?: string;
  isFnClick?: boolean;
  url?: string;
  transUrl?: string;
  title?: string;
  id?: string | number;
};

// Route to from
declare interface RouteToFrom<T = any> extends RouteItem {
  path?: string;
  children?: T[];
}

// RouteItems
declare type RouteItems<T extends RouteItem = any> = T[];

//  ref
declare type RefType<T = any> = T | null;

//  HTMLElement
declare type HtmlType = HTMLElement | string | undefined | null;

// Array
declare type EmptyArrayType<T = any> = T[];

// Object
declare type EmptyObjectType<T = any> = {
  [key: string]: T;
};

//  Select option
declare type SelectOptionType = {
  value: string | number;
  label: string | number;
};

// Table
declare interface TableType<T = any> {
  total: number;
  data: T[];
  param: {
    pageNum: number;
    pageSize: number;
    [key: string]: T;
  };
}

// Table Pagination
declare interface paginationType<T = any> {
  total: number;
  pageNum: number;
  pageSize: number;
  [key: string]: T;
}

// Table Columns
declare type TableColumns<T = any> = {
  title: string;
  key?: string;
  dataIndex: string | string[];
  width?: number | string;
  align?: "left" | "center" | "right";
  ellipsis?: boolean;
  visible?: boolean;
  fixed?: "left" | "right" | true | undefined;
} & {
  [key: string]: any;
};

// Dialog
declare interface DialogType<T = any> {
  visible: boolean;
  [key: string]: T;
}
