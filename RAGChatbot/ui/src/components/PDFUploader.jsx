import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { uploadPDF } from '../services/api'

export default function PDFUploader({ onUploadSuccess, onUploadStart, onUploadProgress, documentUploaded }) {
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = async (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file) => {
    setError('')
    
    // Validate file type
    if (!file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file')
      return
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB')
      return
    }

    onUploadStart()
    
    try {
      // Simulate progress
      onUploadProgress(30)
      
      const result = await uploadPDF(file)
      
      onUploadProgress(90)
      
      onUploadSuccess(file.name, result.num_chunks)
      setError('')
    } catch (err) {
      setError(err.message || 'Failed to upload file')
      onUploadProgress(0)
    }
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
          <FileText className="w-5 h-5 text-blue-500" />
          <span>Upload Document</span>
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Upload a PDF to start asking questions
        </p>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : documentUploaded
            ? 'border-green-300 bg-green-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf"
          onChange={handleChange}
        />

        {documentUploaded ? (
          <div className="space-y-3">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
            <p className="text-green-700 font-medium">Document uploaded successfully!</p>
            <button
              onClick={handleButtonClick}
              className="mt-2 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              Upload another document
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload className="w-12 h-12 text-gray-400 mx-auto" />
            <div>
              <p className="text-gray-600 font-medium">Drop your PDF here</p>
              <p className="text-sm text-gray-500">or</p>
            </div>
            <button
              onClick={handleButtonClick}
              className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-medium shadow-sm"
            >
              Browse Files
            </button>
            <p className="text-xs text-gray-500">PDF files only, max 50MB</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="mt-6 space-y-2">
        <h3 className="text-sm font-medium text-gray-700">Instructions:</h3>
        <ul className="text-xs text-gray-600 space-y-1 list-disc list-inside">
          <li>Upload a PDF document (max 50MB)</li>
          <li>Wait for processing to complete</li>
          <li>Start asking questions in the chat</li>
          <li>Get intelligent answers based on your document</li>
        </ul>
      </div>
    </div>
  )
}

