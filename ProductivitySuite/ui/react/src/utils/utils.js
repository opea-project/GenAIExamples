// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import React from "react";

export const smartTrim = (string, maxLength) => {
  if (!string) {
    return string;
  }
  if (maxLength < 1) {
    return string;
  }
  if (string.length <= maxLength) {
    return string;
  }
  if (maxLength === 1) {
    return string.substring(0, 1) + "...";
  }
  var midpoint = Math.ceil(string.length / 2);
  var toremove = string.length - maxLength;
  var lstrip = Math.ceil(toremove / 2);
  var rstrip = toremove - lstrip;
  return string.substring(0, midpoint - lstrip) + "..." + string.substring(midpoint + rstrip);
};

export const QueryStringFromArr = (paramsArr = []) => {
  const queryString = [];

  for (const param of paramsArr) {
    queryString.push(`${param.name}=${param.value}`);
  }

  return queryString.join("&");
};

export const isAuthorized = (
  allowedRoles = [],
  userRole,
  isPreviewOnlyFeature = false,
  isPreviewUser = false,
  isNotAllowed = false,
) => {
  return (
    (allowedRoles.length === 0 || allowedRoles.includes(userRole)) &&
    (!isPreviewOnlyFeature || isPreviewUser) &&
    !isNotAllowed
  );
};

function addPropsToReactElement(element, props, i) {
  if (React.isValidElement(element)) {
    return React.cloneElement(element, { key: i, ...props });
  }
  return element;
}

export function addPropsToChildren(children, props) {
  if (!Array.isArray(children)) {
    return addPropsToReactElement(children, props);
  }
  return children.map((childElement, i) => addPropsToReactElement(childElement, props, i));
}

export const getCurrentTimeStamp = () => {
  return Math.floor(Date.now() / 1000);
};

export const uuidv4 = () => {
  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
    (+c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (+c / 4)))).toString(16),
  );
};

export const readFilesAndSummarize = async (sourceFiles) => {
  let summaryMessage = "";

  if (sourceFiles.length) {
    const readFilePromises = sourceFiles.map((fileWrapper) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const text = reader.result?.toString() || "";
          resolve(text);
        };
        reader.onerror = () => reject(new Error("Error reading file"));
        reader.readAsText(fileWrapper.file);
      });
    });

    const fileContents = await Promise.all(readFilePromises);

    summaryMessage = fileContents.join("\n");
  }

  return summaryMessage;
};
