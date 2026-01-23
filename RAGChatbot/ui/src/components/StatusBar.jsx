import { CheckCircle, AlertCircle, Loader, Trash2 } from 'lucide-react'

export default function StatusBar({ documentUploaded, documentName, isUploading, uploadProgress, onReset }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {isUploading && (
            <>
              <Loader className="w-5 h-5 text-blue-500 animate-spin" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700">Uploading and processing...</p>
                <div className="w-64 bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            </>
          )}
          
          {!isUploading && documentUploaded && (
            <>
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium text-gray-700">Document Ready</p>
                <p className="text-xs text-gray-500">{documentName}</p>
              </div>
            </>
          )}
          
          {!isUploading && !documentUploaded && (
            <>
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <p className="text-sm font-medium text-gray-700">No document uploaded</p>
            </>
          )}
        </div>

        {documentUploaded && !isUploading && (
          <button
            onClick={onReset}
            className="flex items-center space-x-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear</span>
          </button>
        )}
      </div>
    </div>
  )
}

