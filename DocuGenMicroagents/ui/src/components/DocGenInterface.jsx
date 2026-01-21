import { useState, useEffect } from 'react'
import { Github, Play, Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { api } from '../services/api'

function DocGenInterface({ onJobStart, onLogReceived, currentJob, workflowStatus, workflowError }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sseConnection, setSseConnection] = useState(null)

  // Update local error when workflow error changes
  useEffect(() => {
    if (workflowError) {
      setError(workflowError)
      setLoading(false)
    }
  }, [workflowError])

  // Clean up SSE connection on unmount
  useEffect(() => {
    return () => {
      if (sseConnection) {
        sseConnection.close()
      }
    }
  }, [sseConnection])

  // Connect to SSE stream when job starts
  useEffect(() => {
    if (currentJob && !sseConnection) {
      console.log('Connecting to SSE for job:', currentJob)

      const eventSource = api.connectToLogs(
        currentJob,
        (log) => {
          console.log('Received log:', log)
          onLogReceived(log)

          // Stop loading when workflow completes or fails
          if (log.log_type === 'success' && log.message.includes('complete')) {
            setLoading(false)
          } else if (log.log_type === 'error') {
            setLoading(false)
          }
        },
        (error) => {
          console.error('SSE connection error:', error)
          setError('Connection to the server was lost. Please try again.')
          setLoading(false)
        }
      )

      setSseConnection(eventSource)

      return () => {
        console.log('Closing SSE connection')
        eventSource.close()
      }
    }
  }, [currentJob])

  // Stop loading when workflow status changes to completed or failed
  useEffect(() => {
    if (workflowStatus === 'completed' || workflowStatus === 'failed') {
      setLoading(false)
    }
  }, [workflowStatus])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      // Validate URL
      if (!repoUrl.trim()) {
        throw new Error('Please enter a GitHub repository URL.')
      }

      if (!repoUrl.includes('github.com')) {
        throw new Error('Please provide a valid GitHub repository URL (e.g., https://github.com/username/repository)')
      }

      // Note: Subfolder URLs are now supported! (e.g., /tree/main/path/to/folder)

      // Start documentation generation
      const response = await api.generateDocs(repoUrl)
      onJobStart(response.job_id)

    } catch (err) {
      // Extract error message from axios error response or use default
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to start documentation generation. Please try again.'
      setError(errorMessage)
      setLoading(false)
    }
  }

  const isDisabled = loading || workflowStatus === 'running'

  const getStatusMessage = () => {
    switch (workflowStatus) {
      case 'running':
        return {
          icon: <Clock className="w-4 h-4 text-blue-500 animate-spin" />,
          bg: 'bg-blue-50 border-blue-200',
          text: 'text-blue-800',
          message: 'AI agents are analyzing your repository and generating documentation. Click "Agent Logs" in the header to watch the progress.'
        }
      case 'completed':
        return {
          icon: <CheckCircle className="w-4 h-4 text-green-500" />,
          bg: 'bg-green-50 border-green-200',
          text: 'text-green-800',
          message: 'Documentation generation complete! Check the generated README below.'
        }
      case 'failed':
        return {
          icon: <AlertCircle className="w-4 h-4 text-red-500" />,
          bg: 'bg-red-50 border-red-200',
          text: 'text-red-800',
          message: workflowError || 'Documentation generation failed. Please check the Agent Logs for details.'
        }
      default:
        return null
    }
  }

  const statusInfo = getStatusMessage()

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Generate Documentation</h2>
        <p className="text-gray-600">Enter a GitHub repository URL to generate comprehensive documentation</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Repository URL Input */}
        <div>
          <label htmlFor="repoUrl" className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Github className="w-5 h-5 text-gray-400" />
            </div>
            <input
              type="text"
              id="repoUrl"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repository"
              disabled={isDisabled}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Max repo size: 10GB. Analyzes up to 500 files (1MB max each, upto 500 lines/file). All limits configurable in backend .env
          </p>
        </div>


        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-600 text-xl leading-none"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isDisabled}
          className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading || workflowStatus === 'running' ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Generate Documentation</span>
            </>
          )}
        </button>
      </form>

      {/* Workflow Status */}
      {currentJob && statusInfo && (
        <div className={`mt-6 p-4 rounded-lg border ${statusInfo.bg}`}>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 mt-0.5">
              {statusInfo.icon}
            </div>
            <div className="flex-1">
              <p className={`text-sm ${statusInfo.text}`}>
                {statusInfo.message}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DocGenInterface
