// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

"use client";

import React, { useState, useRef } from "react";
import {
  Upload,
  FileText,
  File,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  Loader,
} from "lucide-react";

interface UploadResult {
  success: boolean;
  filename?: string;
  file_type?: string;
  documents_added?: number;
  rows_processed?: number;
  pages_processed?: number;
  chunks_processed?: number;
  error?: string;
}

export default function FileUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const supportedTypes = {
    "text/csv": {
      icon: FileSpreadsheet,
      label: "CSV",
      color: "text-green-600",
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
      icon: FileSpreadsheet,
      label: "XLSX",
      color: "text-blue-600",
    },
    "application/pdf": { icon: FileText, label: "PDF", color: "text-red-600" },
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
      icon: File,
      label: "DOCX",
      color: "text-indigo-600",
    },
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setResult(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("/api/knowledge/upload-file", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setResult(data);

      if (data.success) {
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : "Upload failed",
      });
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (type: string) => {
    const fileType = supportedTypes[type as keyof typeof supportedTypes];
    if (fileType) {
      const Icon = fileType.icon;
      return <Icon size={48} className={fileType.color} />;
    }
    return <File size={48} className="text-gray-400" />;
  };

  const getProcessingStats = (result: UploadResult) => {
    if (result.rows_processed) {
      return `${result.rows_processed} rows processed`;
    }
    if (result.pages_processed) {
      return `${result.pages_processed} pages processed`;
    }
    if (result.chunks_processed) {
      return `${result.chunks_processed} chunks processed`;
    }
    return "Processed successfully";
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-black mb-2">
          Upload Knowledge Files
        </h2>
        <p className="text-black">
          Upload CSV, XLSX, PDF, or DOCX files to add to the knowledge base.
          Powered by{" "}
          <span className="font-semibold text-blue-600">
            Intel Xeon processors
          </span>{" "}
          for fast processing.
        </p>
      </div>

      {/* Supported Formats */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-black mb-4">
          Supported File Types
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(supportedTypes).map(([type, info]) => {
            const Icon = info.icon;
            return (
              <div
                key={type}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <Icon size={24} className={info.color} />
                <span className="font-medium text-black">{info.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
            dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-blue-400"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center">
                {getFileIcon(selectedFile.type)}
              </div>
              <div>
                <p className="text-lg font-semibold text-black">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-black">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 flex items-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader size={20} className="animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload size={20} />
                      Upload & Process
                    </>
                  )}
                </button>
                <button
                  onClick={() => setSelectedFile(null)}
                  disabled={uploading}
                  className="px-6 py-3 bg-gray-200 text-black rounded-lg font-semibold hover:bg-gray-300 transition-all disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <Upload size={64} className="mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-semibold text-black mb-2">
                Drag and drop your file here
              </p>
              <p className="text-sm text-black mb-4">or click to browse</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.pdf,.docx"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold cursor-pointer hover:bg-blue-700 transition-colors"
              >
                Choose File
              </label>
              <p className="text-xs text-black mt-4">
                Maximum file size: 100MB
              </p>
            </>
          )}
        </div>
      </div>

      {/* Upload Result */}
      {result && (
        <div
          className={`p-6 rounded-lg border-2 ${
            result.success
              ? "bg-green-50 border-green-200"
              : "bg-red-50 border-red-200"
          }`}
        >
          <div className="flex items-start gap-3">
            {result.success ? (
              <CheckCircle
                size={24}
                className="text-green-600 flex-shrink-0 mt-1"
              />
            ) : (
              <XCircle size={24} className="text-red-600 flex-shrink-0 mt-1" />
            )}
            <div className="flex-1">
              <h3
                className={`text-lg font-semibold ${
                  result.success ? "text-green-800" : "text-red-800"
                }`}
              >
                {result.success ? "Upload Successful!" : "Upload Failed"}
              </h3>
              {result.success ? (
                <div className="mt-2 space-y-1">
                  <p className="text-green-800">
                    <span className="font-semibold">{result.filename}</span> has
                    been processed
                  </p>
                  <p className="text-green-800">{getProcessingStats(result)}</p>
                  <p className="text-green-800">
                    <span className="font-semibold">
                      {result.documents_added}
                    </span>{" "}
                    documents added to knowledge base
                  </p>
                  <p className="text-sm text-green-700 mt-2">
                    ⚡ Processed using Intel Xeon acceleration
                  </p>
                </div>
              ) : (
                <p className="text-red-800 mt-2">
                  {result.error || "An error occurred during upload"}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Processing Info */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-black mb-3">
          🚀 Processing Features
        </h3>
        <ul className="space-y-2 text-black">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">✓</span>
            <span>
              <strong>Automatic Embedding:</strong> Files are automatically
              vectorized using OPEA embedding service
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">✓</span>
            <span>
              <strong>Semantic Search:</strong> Uploaded content becomes
              instantly searchable
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">✓</span>
            <span>
              <strong>Intel Xeon Optimized:</strong> Leverages Intel performance
              libraries for fast processing
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">✓</span>
            <span>
              <strong>Multiple Formats:</strong> Handles CSV, Excel, PDF, and
              Word documents
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}
