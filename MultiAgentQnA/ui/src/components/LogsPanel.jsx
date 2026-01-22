import { useState, useEffect } from 'react'
import { Terminal, Copy, Check, X, RefreshCw } from 'lucide-react'
import { getLogs } from '../services/api'

export default function LogsPanel({ isOpen, onClose }) {
  const [logs, setLogs] = useState([])
  const [copied, setCopied] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchLogs = async () => {
    try {
      const response = await getLogs()
      if (response && response.logs) {
        setLogs(response.logs.reverse()) // Show newest first
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchLogs()
    }
  }, [isOpen])

  useEffect(() => {
    if (isOpen && autoRefresh) {
      const interval = setInterval(fetchLogs, 2000) // Refresh every 2 seconds
      return () => clearInterval(interval)
    }
  }, [isOpen, autoRefresh])

  const copyLogs = () => {
    const logsText = logs.map(log => {
      const timestamp = new Date(log.timestamp).toLocaleTimeString()
      return `[${timestamp}] ${log.type.toUpperCase()}: ${log.message}`
    }).join('\n')
    navigator.clipboard.writeText(logsText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const clearLogs = () => {
    setLogs([])
    fetchLogs()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-4xl h-[600px] flex flex-col border border-gray-700">
        {/* Header */}
        <div className="bg-gray-800 px-4 py-3 rounded-t-lg flex items-center justify-between border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <Terminal className="w-5 h-5 text-green-400" />
            <h2 className="text-lg font-semibold text-white">Agent Activity Logs</h2>
          </div>
            <div className="flex items-center space-x-2">
            <button
              onClick={fetchLogs}
              className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded transition-all flex items-center space-x-1"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={copyLogs}
              className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded transition-all flex items-center space-x-1"
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
            <button
              onClick={onClose}
              className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded transition-all flex items-center space-x-1"
            >
              <X className="w-4 h-4" />
              <span>Close</span>
            </button>
          </div>
        </div>

        {/* Logs Content */}
        <div className="flex-1 overflow-y-auto p-4 font-mono text-sm bg-gray-950 scrollbar-hide">
          {logs.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              No logs available yet
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div 
                  key={index} 
                  className="flex items-start space-x-2 text-gray-300 hover:bg-gray-800 px-2 py-1 rounded"
                >
                  <span className="text-gray-500 text-xs min-w-[70px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`font-semibold min-w-[80px] ${
                    log.type === 'info' ? 'text-blue-400' :
                    log.type === 'warning' ? 'text-yellow-400' :
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'success' ? 'text-green-400' :
                    'text-gray-400'
                  }`}>
                    [{log.type.toUpperCase()}]
                  </span>
                  <span className="flex-1">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-800 px-4 py-2 rounded-b-lg border-t border-gray-700 text-xs text-gray-400">
          💡 These logs show agent routing decisions and activity in real-time
        </div>
      </div>
    </div>
  )
}

