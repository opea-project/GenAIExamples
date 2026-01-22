import { useState } from 'react'
import { Upload, FileText, AlertCircle } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export default function PDFUploader({ onUploadSuccess, onUploadStart }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState('')

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleFileUpload = async (file) => {
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are allowed')
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB')
      return
    }

    setError('')
    setIsUploading(true)
    onUploadStart()

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_URL}/upload-pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      onUploadSuccess(response.data.extracted_code)
    } catch (error) {
      console.error('Upload error:', error)
      setError(error.response?.data?.detail || 'Failed to extract code from PDF')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-800">Alternative: Upload PDF</h3>
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Don't have code ready? Upload a PDF containing code and it will be automatically extracted
        and placed in the source code box for translation.
      </p>

      <div className="flex items-center gap-4">
        {/* Compact Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex-1 border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          {isUploading ? (
            <div className="flex items-center justify-center space-x-3">
              <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm text-gray-600">Extracting code from PDF...</p>
            </div>
          ) : (
            <div className="flex items-center justify-center space-x-4">
              <Upload className={`w-8 h-8 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
              <div className="text-left">
                <p className="text-sm text-gray-700 mb-1">
                  Drag and drop your PDF here, or{' '}
                  <label className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
                    browse
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </label>
                </p>
                <p className="text-xs text-gray-500">
                  Max 10MB • Supports Java, C, C++, Python, Rust, Go
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex-shrink-0 w-64 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}
