// Copyright (c) 2024 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { env } from "$env/dynamic/public";

const DOC_BASE_URL = env.DOC_BASE_URL;

export async function fetchTextStream(query: string | Blob, params: string, file: Blob, fileName: string | undefined) {
  const url = `${DOC_BASE_URL}`; // Ensure the URL is constructed correctly
  const formData = new FormData();

  if (!file) {
    file = new Blob([""], { type: "text/plain" });
    fileName = "empty.txt";
  }

  if (params === "doc_id") {
    formData.append("files", file, fileName);
    formData.append("messages", query);
    formData.append("type", "text");
  } else if (params === "text") {
    formData.append("files", file, fileName);
    formData.append("messages", query);
    formData.append("type", "text");
  }

  // Initiate the POST request to upload the file
  const init = {
    method: "POST",
    body: formData,
  };

  const postResponse = await fetch(url, init);

  if (!postResponse.ok) {
    throw new Error(`Error uploading file: ${postResponse.status}`);
  }

  // Function to create an async iterator for the stream
  async function* streamGenerator() {
    if (!postResponse.body) {
      throw new Error("Response body is null");
    }
    const reader = postResponse.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done, value;

    let buffer = ""; // Initialize a buffer

    while (({ done, value } = await reader.read())) {
      if (done) break;

      // Decode chunk and append to buffer
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Use regex to clean and extract data
      const cleanedChunks = buffer
        .split("\n")
        .map((line) => {
          // Remove 'data: b' at the start and ' ' at the end
          return line.replace(/^data:\s*|^b'|'\s*$/g, "").trim(); // Clean unnecessary characters
        })
        .filter((line) => line); // Remove empty lines

      for (const cleanedChunk of cleanedChunks) {
        // Further clean to ensure all unnecessary parts are removed
        yield cleanedChunk.replace(/^b'|['"]$/g, ""); // Again clean 'b' and other single or double quotes
      }

      // If there is an incomplete message in the current buffer, keep it
      buffer = buffer.endsWith("\n") ? "" : cleanedChunks.pop() || ""; // Keep the last incomplete part
    }
  }

  return streamGenerator(); // Return the async generator
}
