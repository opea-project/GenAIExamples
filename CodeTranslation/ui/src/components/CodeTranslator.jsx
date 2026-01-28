import { useState, useEffect } from 'react'
import { ArrowRight, Code, Copy, Check } from 'lucide-react'
import axios from 'axios'

const LANGUAGES = ['java', 'c', 'cpp', 'python', 'rust', 'go']

const LANGUAGE_LABELS = {
  'java': 'JAVA',
  'c': 'C',
  'cpp': 'C++',
  'python': 'PYTHON',
  'rust': 'RUST',
  'go': 'GO'
}

const API_URL = import.meta.env.VITE_API_URL || '/api'

export default function CodeTranslator({
  onTranslationStart,
  onTranslationSuccess,
  onTranslationError,
  pdfExtractedCode,
  sourceLanguage,
  targetLanguage,
  onSourceLanguageChange,
  onTargetLanguageChange
}) {
  const [sourceCode, setSourceCode] = useState('')
  const [translatedCode, setTranslatedCode] = useState('')
  const [isTranslating, setIsTranslating] = useState(false)
  const [copied, setCopied] = useState(false)

  // When PDF code is extracted, set it as source code
  useEffect(() => {
    if (pdfExtractedCode) {
      setSourceCode(pdfExtractedCode)
    }
  }, [pdfExtractedCode])

  const handleTranslate = async () => {
    if (!sourceCode.trim()) {
      alert('Please enter code to translate')
      return
    }

    if (sourceLanguage === targetLanguage) {
      alert('Source and target languages must be different')
      return
    }

    setIsTranslating(true)
    onTranslationStart()

    try {
      const response = await axios.post(`${API_URL}/translate`, {
        source_code: sourceCode,
        source_language: sourceLanguage,
        target_language: targetLanguage
      })

      setTranslatedCode(response.data.translated_code)
      onTranslationSuccess()
    } catch (error) {
      console.error('Translation error:', error)
      onTranslationError()
      alert(error.response?.data?.detail || 'Translation failed')
    } finally {
      setIsTranslating(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(translatedCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Code className="w-5 h-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-800">Code Translator</h2>
      </div>

      {/* Language Selection */}
      <div className="flex items-center space-x-3 mb-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Source Language</label>
          <select
            value={sourceLanguage}
            onChange={(e) => onSourceLanguageChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {LANGUAGES.map(lang => (
              <option key={lang} value={lang}>
                {LANGUAGE_LABELS[lang]}
              </option>
            ))}
          </select>
        </div>

        <div className="pt-6">
          <ArrowRight className="w-5 h-5 text-gray-400" />
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Target Language</label>
          <select
            value={targetLanguage}
            onChange={(e) => onTargetLanguageChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {LANGUAGES.map(lang => (
              <option key={lang} value={lang}>
                {LANGUAGE_LABELS[lang]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Side by Side Code Boxes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Source Code Input */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">
              Source Code ({LANGUAGE_LABELS[sourceLanguage]})
            </label>
            <span className={`text-xs ${sourceCode.length > 10000 ? 'text-red-600 font-semibold' : 'text-gray-500'}`}>
              {sourceCode.length.toLocaleString()} / 10,000 characters
            </span>
          </div>
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            placeholder={`Enter your ${sourceLanguage} code here...`}
            className={`w-full h-96 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-none ${
              sourceCode.length > 10000 ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {sourceCode.length > 10000 && (
            <p className="text-xs text-red-600 mt-1">
              Code exceeds maximum length. Please reduce to 10,000 characters or less.
            </p>
          )}
        </div>

        {/* Translated Code Output */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">
              Translated Code ({LANGUAGE_LABELS[targetLanguage]})
            </label>
            {translatedCode && (
              <button
                onClick={handleCopy}
                className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            )}
          </div>
          <textarea
            value={translatedCode}
            readOnly
            placeholder="Translated code will appear here..."
            className="w-full h-96 px-3 py-2 border border-gray-300 bg-gray-50 rounded-lg font-mono text-sm resize-none"
          />
        </div>
      </div>

      {/* Translate Button */}
      <button
        onClick={handleTranslate}
        disabled={isTranslating || !sourceCode.trim() || sourceCode.length > 10000}
        className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
      >
        {isTranslating ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>Translating...</span>
          </>
        ) : (
          <>
            <ArrowRight className="w-5 h-5" />
            <span>Translate Code</span>
          </>
        )}
      </button>

      {/* Info Note */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-gray-600">
          <span className="font-semibold">Note:</span> The 10,000 character limit is due to CodeLlama-34b's
          context window (16K tokens). This ensures optimal translation quality and prevents timeouts.
          For larger files, consider breaking them into smaller modules.
        </p>
      </div>
    </div>
  )
}
