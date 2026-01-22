import { useState } from 'react'
import CodeTranslator from './components/CodeTranslator'
import PDFUploader from './components/PDFUploader'
import Header from './components/Header'
import StatusBar from './components/StatusBar'

function App() {
  const [translationStatus, setTranslationStatus] = useState('idle') // idle, translating, success, error
  const [sourceLanguage, setSourceLanguage] = useState('python')
  const [targetLanguage, setTargetLanguage] = useState('java')
  const [pdfExtractedCode, setPdfExtractedCode] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const handleTranslationStart = () => {
    setTranslationStatus('translating')
  }

  const handleTranslationSuccess = () => {
    setTranslationStatus('success')
    setTimeout(() => setTranslationStatus('idle'), 3000)
  }

  const handleTranslationError = () => {
    setTranslationStatus('error')
    setTimeout(() => setTranslationStatus('idle'), 3000)
  }

  const handlePDFUploadSuccess = (extractedCode) => {
    setPdfExtractedCode(extractedCode)
    setIsUploading(false)
  }

  const handlePDFUploadStart = () => {
    setIsUploading(true)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Status Bar */}
        <StatusBar
          translationStatus={translationStatus}
          isUploading={isUploading}
          sourceLanguage={sourceLanguage}
          targetLanguage={targetLanguage}
        />

        {/* Main Code Translator - Side by Side */}
        <div className="mt-6">
          <CodeTranslator
            onTranslationStart={handleTranslationStart}
            onTranslationSuccess={handleTranslationSuccess}
            onTranslationError={handleTranslationError}
            pdfExtractedCode={pdfExtractedCode}
            sourceLanguage={sourceLanguage}
            targetLanguage={targetLanguage}
            onSourceLanguageChange={setSourceLanguage}
            onTargetLanguageChange={setTargetLanguage}
          />
        </div>

        {/* PDF Uploader at Bottom */}
        <div className="mt-6">
          <PDFUploader
            onUploadSuccess={handlePDFUploadSuccess}
            onUploadStart={handlePDFUploadStart}
          />
        </div>
      </main>
    </div>
  )
}

export default App
