import { CheckCircle, AlertCircle, Loader, ArrowRight } from 'lucide-react'

export default function StatusBar({ translationStatus, isUploading, sourceLanguage, targetLanguage }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {isUploading && (
            <>
              <Loader className="w-5 h-5 text-blue-500 animate-spin" />
              <p className="text-sm font-medium text-gray-700">Extracting code from PDF...</p>
            </>
          )}

          {!isUploading && translationStatus === 'translating' && (
            <>
              <Loader className="w-5 h-5 text-blue-500 animate-spin" />
              <div className="flex items-center space-x-2">
                <p className="text-sm font-medium text-gray-700">Translating</p>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{sourceLanguage}</span>
                <ArrowRight className="w-4 h-4 text-gray-400" />
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">{targetLanguage}</span>
              </div>
            </>
          )}

          {!isUploading && translationStatus === 'success' && (
            <>
              <CheckCircle className="w-5 h-5 text-green-500" />
              <p className="text-sm font-medium text-gray-700">Translation completed successfully</p>
            </>
          )}

          {!isUploading && translationStatus === 'error' && (
            <>
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm font-medium text-gray-700">Translation failed</p>
            </>
          )}

          {!isUploading && translationStatus === 'idle' && (
            <>
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <p className="text-sm font-medium text-gray-700">Ready to translate code</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
