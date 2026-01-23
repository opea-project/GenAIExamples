import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import PDFUploader from './components/PDFUploader'
import Header from './components/Header'
import StatusBar from './components/StatusBar'

function App() {
  const [documentUploaded, setDocumentUploaded] = useState(false)
  const [documentName, setDocumentName] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  const handleUploadSuccess = (fileName, numChunks) => {
    setDocumentUploaded(true)
    setDocumentName(fileName)
    setUploadProgress(100)
    setTimeout(() => {
      setIsUploading(false)
      setUploadProgress(0)
    }, 1000)
  }

  const handleUploadStart = () => {
    setIsUploading(true)
    setUploadProgress(0)
  }

  const handleUploadProgress = (progress) => {
    setUploadProgress(progress)
  }

  const handleReset = () => {
    setDocumentUploaded(false)
    setDocumentName('')
    setUploadProgress(0)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Status Bar */}
        <StatusBar 
          documentUploaded={documentUploaded}
          documentName={documentName}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          onReset={handleReset}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Left Panel - PDF Upload */}
          <div className="lg:col-span-1">
            <PDFUploader
              onUploadSuccess={handleUploadSuccess}
              onUploadStart={handleUploadStart}
              onUploadProgress={handleUploadProgress}
              documentUploaded={documentUploaded}
            />
          </div>

          {/* Right Panel - Chat Interface */}
          <div className="lg:col-span-2">
            <ChatInterface 
              documentUploaded={documentUploaded}
              documentName={documentName}
            />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App

