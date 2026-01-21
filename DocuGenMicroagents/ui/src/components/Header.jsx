import { FileText, Activity, CheckCircle, XCircle, Clock } from 'lucide-react'

function Header({ onLogsToggle, hasActiveJob, workflowStatus }) {
  const getStatusIcon = () => {
    switch (workflowStatus) {
      case 'running':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return null
    }
  }

  const getStatusText = () => {
    switch (workflowStatus) {
      case 'running':
        return 'Generating...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      default:
        return 'Ready'
    }
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4 max-w-7xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                DocuGen AI
              </h1>
              <p className="text-sm text-gray-500">Automatic Documentation Generator</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Status Indicator */}
            {hasActiveJob && (
              <div className="flex items-center space-x-2 px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
                {getStatusIcon()}
                <span className="text-sm font-medium text-gray-700">{getStatusText()}</span>
              </div>
            )}

            {/* Agent Logs Button */}
            <button
              onClick={onLogsToggle}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <Activity className="w-5 h-5" />
              <span>Agent Logs</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
