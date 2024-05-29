// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export function scrollToBottom(scrollToDiv: HTMLElement) {
  if (scrollToDiv) {
    setTimeout(
      () =>
        scrollToDiv.scroll({
          behavior: "auto",
          top: scrollToDiv.scrollHeight,
        }),
      100,
    );
  }
}
