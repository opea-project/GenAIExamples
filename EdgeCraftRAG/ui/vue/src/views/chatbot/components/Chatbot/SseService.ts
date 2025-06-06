// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
import { getChatSessionId } from "@/utils/common";

export const handleMessageSend = async (
  url: string,
  postData: any,
  onDisplay: (data: any) => void,
  onEnd?: () => void,
): Promise<void> => {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        sessionid: getChatSessionId(),
      },
      body: JSON.stringify(postData),
    });

    if (!response.ok) {
      throw new Error(`Network response was not ok: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          onEnd?.();
          break;
        }
        buffer += decoder.decode(value, { stream: true });

        onDisplay(buffer);
      }
    } catch (error) {
      console.error(error);
      onEnd?.();
    }
  } catch (error) {
    console.error(error);
    onEnd?.();
  }
};
