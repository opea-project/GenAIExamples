import { useState, useEffect } from 'react'
import Header from './components/Header'
import DocGenInterface from './components/DocGenInterface'
import AgentLogPanel from './components/AgentLogPanel'
import ResultsViewer from './components/ResultsViewer'
import ProjectSelector from './components/ProjectSelector'
import { api } from './services/api'

function App() {
  const [currentJob, setCurrentJob] = useState(null)
  const [logs, setLogs] = useState([])
  const [logsOpen, setLogsOpen] = useState(false)
  const [generatedReadme, setGeneratedReadme] = useState(null)
  const [workflowStatus, setWorkflowStatus] = useState('idle') // idle, running, completed, failed
  const [workflowError, setWorkflowError] = useState(null) // Store error message from backend
  const [awaitingProjectSelection, setAwaitingProjectSelection] = useState(false)
  const [detectedProjects, setDetectedProjects] = useState(null)
  const [skippedFolders, setSkippedFolders] = useState(null)

  // Poll job status to check for project selection
  useEffect(() => {
    if (!currentJob || workflowStatus === 'completed' || workflowStatus === 'failed') {
      return
    }

    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getJobStatus(currentJob)

        if (status.awaiting_project_selection && !awaitingProjectSelection) {
          // Only update once when state changes to awaiting_selection
          console.log('DEBUG: API Status Response:', status)
          console.log('DEBUG: Skipped Folders from API:', status.skipped_folders)
          setAwaitingProjectSelection(true)
          setDetectedProjects(status.detected_projects)
          setSkippedFolders(status.skipped_folders || [])
          setWorkflowStatus('awaiting_selection')
        }

        // Check for error in job status
        if (status.error_message && status.status === 'failed') {
          setWorkflowError(status.error_message)
          setWorkflowStatus('failed')
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [currentJob, workflowStatus, awaitingProjectSelection])

  const handleJobStart = (jobId) => {
    setCurrentJob(jobId)
    setLogs([])
    setGeneratedReadme(null)
    setWorkflowStatus('running')
    setWorkflowError(null) // Clear previous errors
    setAwaitingProjectSelection(false)
    setDetectedProjects(null)
    setSkippedFolders(null)
    // Don't auto-open logs panel - let user click to open
  }

  const handleLogReceived = (log) => {
    setLogs(prevLogs => [...prevLogs, log])

    // Check if workflow is complete - ONLY match the final completion message
    if (log.log_type === 'success' && log.message.includes('Documentation generation complete')) {
      setWorkflowStatus('completed')
    } else if (log.log_type === 'error') {
      setWorkflowStatus('failed')
      // Errors are already shown in agent logs, no need for additional alert
    }
  }

  const handleReadmeGenerated = (readme) => {
    setGeneratedReadme(readme)
  }

  const handleProjectsSelected = () => {
    setAwaitingProjectSelection(false)
    setDetectedProjects(null)
    setSkippedFolders(null)
    setWorkflowStatus('running')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header
        onLogsToggle={() => setLogsOpen(!logsOpen)}
        hasActiveJob={!!currentJob}
        workflowStatus={workflowStatus}
      />

      <main className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="space-y-6">
          {/* Top: Input Interface */}
          <DocGenInterface
            onJobStart={handleJobStart}
            onLogReceived={handleLogReceived}
            currentJob={currentJob}
            workflowStatus={workflowStatus}
            workflowError={workflowError}
          />

          {/* Middle: Project Selection (shown when multiple projects detected) */}
          {awaitingProjectSelection && detectedProjects && (
            <ProjectSelector
              currentJob={currentJob}
              detectedProjects={detectedProjects}
              skippedFolders={skippedFolders}
              onProjectsSelected={handleProjectsSelected}
            />
          )}

          {/* Bottom: Results Viewer */}
          <ResultsViewer
            readme={generatedReadme}
            onReadmeGenerated={handleReadmeGenerated}
            currentJob={currentJob}
            workflowStatus={workflowStatus}
          />
        </div>
      </main>

      <AgentLogPanel
        isOpen={logsOpen}
        onClose={() => setLogsOpen(false)}
        logs={logs}
        currentJob={currentJob}
      />
    </div>
  )
}

export default App
