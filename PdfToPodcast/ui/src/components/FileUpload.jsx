import { useState, useRef } from 'react';
import { Upload, FileText } from 'lucide-react';

const FileUpload = ({ onFileUpload, isLoading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (file.type !== 'application/pdf') {
      alert('Please upload a PDF file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = () => {
    if (selectedFile) {
      onFileUpload(selectedFile);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="card">
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 bg-gray-50'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          className="hidden"
        />

        {!selectedFile ? (
          <>
            <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              Drop your PDF here or click to browse
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Maximum file size: 10MB
            </p>
            <button
              onClick={handleButtonClick}
              className="btn-primary"
              disabled={isLoading}
            >
              Choose File
            </button>
          </>
        ) : (
          <>
            <FileText className="mx-auto h-16 w-16 text-primary-500 mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              {selectedFile.name}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleButtonClick}
                className="btn-secondary"
                disabled={isLoading}
              >
                Change File
              </button>
              <button
                onClick={handleUpload}
                className="btn-primary"
                disabled={isLoading}
              >
                {isLoading ? 'Uploading...' : 'Upload & Continue'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
