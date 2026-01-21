import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useDispatch, useSelector } from 'react-redux';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { setFile, uploadPDF } from '@store/slices/uploadSlice';
import { validatePDFFile, formatFileSize } from '@utils/helpers';
import { Button, Card, CardBody, Progress, Alert } from '@components/ui';
import { cn } from '@utils/helpers';

export const PDFUploader = ({ onSuccess }) => {
  const dispatch = useDispatch();
  const { file, uploading, uploadProgress, uploadComplete, error } = useSelector(
    (state) => state.upload
  );

  const onDrop = useCallback(
    (acceptedFiles) => {
      const selectedFile = acceptedFiles[0];
      const errors = validatePDFFile(selectedFile);

      if (errors.length > 0) {
        // Handle validation errors
        return;
      }

      dispatch(setFile(selectedFile));
    },
    [dispatch]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleUpload = async () => {
    if (file) {
      const result = await dispatch(uploadPDF(file));
      if (result.type.endsWith('/fulfilled') && onSuccess) {
        onSuccess(result.payload);
      }
    }
  };

  const handleRemove = () => {
    dispatch(setFile(null));
  };

  return (
    <Card>
      <CardBody>
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Upload Your PDF
            </h2>
            <p className="text-gray-600">
              Upload a PDF document to transform it into an engaging podcast conversation.
            </p>
          </div>

          {error && (
            <Alert variant="error" message={error} />
          )}

          {!file && (
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all',
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
              )}
            >
              <input {...getInputProps()} />
              <Upload
                className={cn(
                  'w-16 h-16 mx-auto mb-4',
                  isDragActive ? 'text-primary-500' : 'text-gray-400'
                )}
              />
              <p className="text-lg font-medium text-gray-700 mb-2">
                {isDragActive
                  ? 'Drop your PDF here'
                  : 'Drag & drop your PDF here'}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                or click to browse files
              </p>
              <p className="text-xs text-gray-400">
                Maximum file size: 10MB | PDF format only
              </p>
            </div>
          )}

          {file && !uploadComplete && (
            <div className="border-2 border-primary-200 bg-primary-50 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3 flex-1">
                  <FileText className="w-10 h-10 text-primary-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-600">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                {!uploading && (
                  <button
                    onClick={handleRemove}
                    className="text-gray-400 hover:text-gray-600 p-1"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} showLabel />
                  <p className="text-sm text-gray-600 text-center">
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}

              {!uploading && !uploadComplete && (
                <Button
                  onClick={handleUpload}
                  fullWidth
                  size="lg"
                  icon={Upload}
                >
                  Upload & Continue
                </Button>
              )}
            </div>
          )}

          {uploadComplete && (
            <Alert
              variant="success"
              title="Upload Successful!"
              message="Your PDF has been uploaded and processed successfully."
            />
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Tips for best results:</p>
                <ul className="list-disc list-inside space-y-1 text-blue-700">
                  <li>Use PDFs with selectable text (not scanned images)</li>
                  <li>Documents between 2-10 pages work best</li>
                  <li>Clear formatting improves conversation quality</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default PDFUploader;
