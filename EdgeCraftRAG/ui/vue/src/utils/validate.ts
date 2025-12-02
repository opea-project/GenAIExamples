// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const validateIpPort = (ipPortStr: string) => {
  if (typeof ipPortStr !== "string" || !ipPortStr.includes(":")) {
    return false;
  }

  const [ip, portStr] = ipPortStr.split(":");

  const ipRegex =
    /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  if (!ipRegex.test(ip)) {
    return false;
  }

  const port = parseInt(portStr, 10);
  if (isNaN(port)) {
    return false;
  }
  if (port < 1 || port > 65535) {
    return false;
  }

  return true;
};

export const isValidName = (name: string): boolean => {
  const pattern = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
  return pattern.test(name);
};

export const isValidPipelineName = (name: string): boolean => {
  const validPattern = /^[a-zA-Z0-9_]+$/;
  return validPattern.test(name);
};

export const validateServiceAddress = (url: string): boolean => {
  const regex =
    /^(http:\/\/)(([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}|localhost|[0-9]{1,3}(\.[0-9]{1,3}){3})(:[0-9]+)?$/;

  return regex.test(url);
};
