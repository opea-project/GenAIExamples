import { useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';

const FileUpload = ({ onSubmit, isLoading, acceptedTypes, fileType, title, maxFileSize }) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const fileExtension = '.' + droppedFile.name.split('.').pop().toLowerCase();

      if (acceptedTypes.includes(fileExtension)) {
        setFile(droppedFile);
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('type', fileType);
    formData.append('messages', '');
    formData.append('files', file);
    formData.append('max_tokens', 1024);
    formData.append('language', 'en');
    formData.append('summary_type', 'auto');
    formData.append('stream', 'false');

    onSubmit(formData, false);
  };

  return (
    <div className="card animate-fadeIn">
      <div className="flex items-center mb-4">
        <Upload className="h-6 w-6 text-primary-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          className={`file-drop-zone ${dragActive ? 'file-drop-zone-active' : 'file-drop-zone-inactive'}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {!file ? (
            <>
              <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drop your file here or click to browse
              </p>
              <p className="text-sm text-gray-500 mb-2">
                Supported formats: {acceptedTypes.join(', ')}
              </p>
              <p className="text-xs text-gray-400 mb-4">
                Maximum file size: {maxFileSize || '50 MB'}
              </p>
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept={acceptedTypes.join(',')}
                onChange={handleChange}
                disabled={isLoading}
              />
              <label
                htmlFor="file-upload"
                className="btn-secondary cursor-pointer inline-block"
              >
                Browse Files
              </label>
            </>
          ) : (
            <div className="flex items-center justify-between bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center space-x-3">
                <FileText className="h-8 w-8 text-primary-600" />
                <div>
                  <p className="font-medium text-gray-800">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleRemoveFile}
                className="text-gray-400 hover:text-red-500 transition-colors"
                disabled={isLoading}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={!file || isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? 'Generating Summary...' : 'Generate Summary'}
        </button>
      </form>
    </div>
  );
};

export default FileUpload;
