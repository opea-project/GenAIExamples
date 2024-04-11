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
