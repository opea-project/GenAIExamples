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

const UPLOAD_FILE_BASE_URL = env.UPLOAD_FILE_BASE_URL;
const GET_FILE = env.GET_FILE;
const DELETE_FILE = env.DELETE_FILE;

async function fetchFunc(url, init) {
	try {
		const response = await fetch(url, init);
		if (!response.ok) throw response.status;

		return await response.json();
	} catch (error) {
		console.error("network error: ", error);

		return undefined;
	}
}

export async function fetchKnowledgeBaseId(file: Blob, fileName: string) {
	const url = `${UPLOAD_FILE_BASE_URL}`;
	const formData = new FormData();
	formData.append("files", file, fileName);
	const init: RequestInit = {
		method: "POST",
		body: formData,
	};

	return fetchFunc(url, init);
}

export async function fetchKnowledgeBaseIdByPaste(pasteUrlList: any) {
	const url = `${UPLOAD_FILE_BASE_URL}`;
	const formData = new FormData();
	formData.append("link_list", JSON.stringify(pasteUrlList));
	const init: RequestInit = {
		method: "POST",
		body: formData,
	};

	return fetchFunc(url, init);
}

export async function fetchAllFile() {
	const url = `${GET_FILE}`;
	const init: RequestInit = {
		method: "POST",
		headers: { "Content-Type": "application/json" },
	};

	return fetchFunc(url, init);
}

export async function deleteFiles(path) {
	const UploadKnowledge_URL = DELETE_FILE;

	const data = {
		file_path: path,
	};

	const init: RequestInit = {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data),
	};

	return fetchFunc(UploadKnowledge_URL, init);
}
