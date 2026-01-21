import { useState, useEffect } from 'react'
import { Download, Copy, Check, FileText, Loader2, AlertCircle, GitPullRequest, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import Mermaid from 'react-mermaid2'
import { api } from '../services/api'

// Import GitHub markdown CSS and syntax highlighting theme
import 'github-markdown-css/github-markdown.css'
import 'highlight.js/styles/github.css'

function ResultsViewer({ readme, onReadmeGenerated, currentJob, workflowStatus }) {
  const [copied, setCopied] = useState(false)
  const [markdownContent, setMarkdownContent] = useState(null)
  const [projectTitle, setProjectTitle] = useState(null)
  const [creatingPR, setCreatingPR] = useState(false)
  const [prUrl, setPrUrl] = useState(null)
  const [prError, setPrError] = useState(null)

  // Helper function to convert title to proper case
  const toTitleCase = (str) => {
    return str
      .split(/[-_\s]+/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
  }

  // Extract project title from markdown content
  useEffect(() => {
    if (markdownContent) {
      const lines = markdownContent.split('\n')
      // Look for H2 (## Title) in first 15 lines
      for (let i = 0; i < Math.min(15, lines.length); i++) {
        const line = lines[i].trim()
        if (line.startsWith('## ')) {
          const title = line.substring(3).trim()
          setProjectTitle(toTitleCase(title))
          break
        } else if (line.startsWith('# ') && !line.startsWith('## ')) {
          const title = line.substring(2).trim()
          setProjectTitle(toTitleCase(title))
          break
        }
      }
    }
  }, [markdownContent])

  // Fetch final README when workflow completes
  useEffect(() => {
    console.log('[ResultsViewer] useEffect triggered:', { workflowStatus, currentJob, hasMarkdown: !!markdownContent })
    if (workflowStatus === 'completed' && currentJob && !markdownContent) {
      console.log('[ResultsViewer] Conditions met - starting fetch')
      const fetchReadme = async () => {
        try {
          console.log('Fetching job status for:', currentJob)
          const jobStatus = await api.getJobStatus(currentJob)
          console.log('Job status:', jobStatus)

          // Check if README is ready in job storage
          if (jobStatus.readme_preview || jobStatus.status === 'completed') {
            // Try to download the full README
            try {
              const readmeBlob = await api.downloadReadme(currentJob)
              const readmeText = await readmeBlob.text()
              console.log('Downloaded README:', readmeText.substring(0, 100))
              setMarkdownContent(readmeText)
              if (onReadmeGenerated) {
                onReadmeGenerated(readmeText)
              }
            } catch (err) {
              console.warn('Could not download README, using preview:', err)
              // Fallback to preview if download fails
              if (jobStatus.readme_preview) {
                setMarkdownContent(jobStatus.readme_preview)
                if (onReadmeGenerated) {
                  onReadmeGenerated(jobStatus.readme_preview)
                }
              }
            }
          }
        } catch (error) {
          console.error('Failed to fetch README:', error)
        }
      }

      // Small delay to let backend finish processing
      const timer = setTimeout(fetchReadme, 1000)
      return () => clearTimeout(timer)
    }
  }, [workflowStatus, currentJob, markdownContent])

  const handleCopy = async () => {
    if (markdownContent) {
      await navigator.clipboard.writeText(markdownContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownload = () => {
    if (markdownContent) {
      const blob = new Blob([markdownContent], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'README.md'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  const handleCreatePR = async () => {
    if (!currentJob) return

    setCreatingPR(true)
    setPrError(null)

    try {
      const result = await api.createPullRequest(currentJob)

      if (result.status === 'success') {
        setPrUrl(result.pr_url)
        console.log('PR created successfully:', result.pr_url)
      } else {
        setPrError(result.message || 'Failed to create PR')
      }
    } catch (error) {
      console.error('Failed to create PR:', error)
      setPrError(error.response?.data?.detail || error.message || 'Failed to create pull request')
    } finally {
      setCreatingPR(false)
    }
  }

  // Only render the component when README is completed and ready
  if (workflowStatus !== 'completed' || !markdownContent) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <FileText className="w-6 h-6 text-purple-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">README</h2>
            {projectTitle && (
              <p className="text-sm text-gray-600 mt-0.5">{projectTitle}</p>
            )}
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={handleCopy}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <Check className="w-5 h-5 text-green-500" />
            ) : (
              <Copy className="w-5 h-5 text-gray-600" />
            )}
          </button>
          <button
            onClick={handleDownload}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Download README.md"
          >
            <Download className="w-5 h-5 text-gray-600" />
          </button>

          {/* Create PR Button */}
          {prUrl ? (
            <a
              href={prUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              title="View Pull Request"
            >
              <Check className="w-4 h-4" />
              <span className="text-sm font-medium">View PR</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          ) : (
            <button
              onClick={handleCreatePR}
              disabled={creatingPR}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-purple-400 disabled:cursor-not-allowed transition-colors"
              title="Create Pull Request on GitHub"
            >
              {creatingPR ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm font-medium">Creating PR...</span>
                </>
              ) : (
                <>
                  <GitPullRequest className="w-4 h-4" />
                  <span className="text-sm font-medium">Create PR</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="overflow-y-auto border border-gray-200 rounded-lg bg-white" style={{ maxHeight: '70vh' }}>
        {/* Markdown Content with GitHub styling */}
        <div className="markdown-body" style={{ backgroundColor: 'white', padding: '24px' }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                const language = match ? match[1] : null

                // Render Mermaid diagrams
                if (!inline && language === 'mermaid') {
                  return (
                    <div className="my-4 bg-white p-4 rounded-lg border border-gray-300 flex items-center justify-center">
                      <Mermaid chart={String(children).replace(/\n$/, '')} />
                    </div>
                  )
                }

                // Regular code blocks
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      </div>

      {/* Footer Info */}
      {markdownContent && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Lines: <span className="font-semibold">{markdownContent.split('\n').length}</span>
            </span>
            <span>
              Characters: <span className="font-semibold">{markdownContent.length}</span>
            </span>
            <span>
              Words: <span className="font-semibold">{markdownContent.split(/\s+/).length}</span>
            </span>
          </div>
        </div>
      )}

      {/* PR Error Display */}
      {prError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-red-800">Failed to Create Pull Request</h3>
            <p className="text-sm text-red-700 mt-1">{prError}</p>
            {prError.includes('GITHUB_TOKEN') && (
              <p className="text-xs text-red-600 mt-2">
                Make sure GITHUB_TOKEN is configured in your backend environment variables.
              </p>
            )}
          </div>
          <button
            onClick={() => setPrError(null)}
            className="text-red-400 hover:text-red-600"
          >
            ×
          </button>
        </div>
      )}
    </div>
  )
}

export default ResultsViewer
