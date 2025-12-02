// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getChatSessionId } from "@/utils/common";
import { message } from "ant-design-vue";

export interface StreamController {
  cancel: () => void;
}

export const handleMessageSend = (
  url: string,
  postData: any,
  onDisplay: (data: string) => void,
  onEnd?: () => void,
): StreamController => {
  let reader: ReadableStreamDefaultReader | undefined;
  const controller = new AbortController();

  const execute = async () => {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          sessionid: getChatSessionId(),
        },
        body: JSON.stringify(postData),
        signal: controller.signal,
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
        message.error(errorMessage || "Request failed");
        onEnd?.();
        return;
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
      if (error.name === "AbortError") {
        console.log("Stream was aborted by user.");
      } else {
        console.error("Request or stream error:", error);
        if (error.message !== "Request failed") {
          message.error(error.message || "Stream error");
        }
      }
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

  execute().catch(console.error);

  return {
    cancel: () => {
      if (!controller.signal.aborted) {
        controller.abort();
      }
    },
  };
};
