import { X, Bot, CheckCircle, AlertCircle, Info, Zap } from 'lucide-react'

function AgentLogPanel({ isOpen, onClose, logs, currentJob }) {
  if (!isOpen) return null

  const getLogIcon = (logType) => {
    switch (logType) {
      case 'agent_start':
        return <Bot className="w-4 h-4 text-blue-500" />
      case 'agent_complete':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'agent_thinking':
        return <Zap className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getLogColor = (logType) => {
    switch (logType) {
      case 'agent_start':
        return 'bg-blue-50 border-blue-200'
      case 'agent_complete':
        return 'bg-green-50 border-green-200'
      case 'agent_thinking':
        return 'bg-yellow-50 border-yellow-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'success':
        return 'bg-green-50 border-green-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Agent Activity Log</h2>
            {currentJob && (
              <p className="text-sm text-gray-500 mt-1">Job ID: {currentJob}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Logs Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Bot className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">No activity yet</p>
              <p className="text-sm">Agent logs will appear here during generation</p>
            </div>
          ) : (
            logs.map((log, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${getLogColor(log.log_type)}`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getLogIcon(log.log_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      {log.agent_name && (
                        <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          {log.agent_name}
                        </span>
                      )}
                      {log.timestamp && (
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(log.timestamp)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{log.message}</p>

                    {/* Metadata */}
                    {log.metadata && Object.keys(log.metadata).length > 0 && (
                      <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs font-mono">
                        {JSON.stringify(log.metadata, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer Stats */}
        {logs.length > 0 && (
          <div className="border-t border-gray-200 p-4 bg-gray-50">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                Total Events: <span className="font-semibold text-gray-800">{logs.length}</span>
              </span>
              <div className="flex space-x-4">
                <span className="text-gray-600">
                  Agents: <span className="font-semibold text-blue-600">
                    {new Set(logs.filter(l => l.agent_name).map(l => l.agent_name)).size}
                  </span>
                </span>
                {logs.filter(l => l.log_type === 'error').length > 0 && (
                  <span className="text-gray-600">
                    Errors: <span className="font-semibold text-red-600">
                      {logs.filter(l => l.log_type === 'error').length}
                    </span>
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AgentLogPanel
