// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
import { getChatSessionId } from "@/utils/common";
import { message } from "ant-design-vue";

export const handleMessageSend = async (
  url: string,
  postData: any,
  onDisplay: (data: any) => void,
  onEnd?: () => void,
): Promise<void> => {
  let reader: ReadableStreamDefaultReader | undefined;

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
      let errorMessage = "";
      try {
        const errorText = await response.text();
        if (errorText) {
          errorMessage = errorText;
        }
      } catch (parseError) {
        console.warn("Failed to read error response:", parseError);
      }
      message.error(errorMessage);
      throw new Error(errorMessage);
    }

    reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Readable stream is not available");
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        onEnd?.();
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      onDisplay(buffer);
    }
  } catch (error: any) {
    console.error("Request or stream error:", error);
    onEnd?.();
  } finally {
    if (reader) {
      try {
        await reader.cancel();
      } catch (cancelError) {
        console.warn("Failed to cancel reader:", cancelError);
      }
    }
  }
};
