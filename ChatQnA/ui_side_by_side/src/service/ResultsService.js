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

const { VITE_WITH_RAG_BASE_URL } = import.meta.env;
const endpoint = {
  uploadDoc: "/upload_doc",
  uploadLink: "/upload_link",
  downloadFile: "/download_file",
};

class ResultsService {
  uploadFile(file, fileName) {
    const url = VITE_WITH_RAG_BASE_URL + endpoint.uploadDoc;
    const formData = new FormData();
    formData.append("file", file, fileName);
    return fetch(url, {
      method: "POST",
      body: formData,
    });
  }

  uploadFileLink(fileLink) {
    const url = VITE_WITH_RAG_BASE_URL + endpoint.uploadLink;
    return fetch(url, {
      method: "POST",
      body: JSON.stringify({ link_list: [...fileLink] }),
    });
  }

  downloadFile(filePath) {
    const url = VITE_WITH_RAG_BASE_URL + endpoint.downloadFile;
    const queryParams = {
      file_path: filePath,
    };
    const queryString = new URLSearchParams(queryParams);
    const fullURL = `${url}?${queryString}`;
    return fetch(fullURL);
  }
}

export default new ResultsService();
