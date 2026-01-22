import axios from 'axios'

// Use environment variable or default to /api for production (nginx proxy)
// In development: http://localhost:5001/api
// In production Docker: /api (proxied by nginx)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = {
  /**
   * Start documentation generation workflow
   * @param {string} repoUrl - GitHub repository URL
   * @returns {Promise<{job_id: string, status: string}>}
   */
  generateDocs: async (repoUrl) => {
    const response = await axios.post(`${API_BASE_URL}/generate-docs`, {
      repo_url: repoUrl
    })
    return response.data
  },

  /**
   * Get job status
   * @param {string} jobId - Job ID
   * @returns {Promise<object>}
   */
  getJobStatus: async (jobId) => {
    const response = await axios.get(`${API_BASE_URL}/status/${jobId}`)
    return response.data
  },

  /**
   * Connect to SSE stream for real-time logs
   * @param {string} jobId - Job ID
   * @param {function} onMessage - Callback for log messages
   * @param {function} onError - Callback for errors
   * @returns {EventSource} SSE connection
   */
  connectToLogs: (jobId, onMessage, onError) => {
    const eventSource = new EventSource(`${API_BASE_URL}/logs/${jobId}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error)
      if (onError) onError(error)
      eventSource.close()
    }

    return eventSource
  },

  /**
   * Approve agent output and continue workflow
   * @param {string} jobId - Job ID
   */
  approveStep: async (jobId) => {
    const response = await axios.post(`${API_BASE_URL}/approve/${jobId}`)
    return response.data
  },

  /**
   * Reject agent output and retry with feedback
   * @param {string} jobId - Job ID
   * @param {string} feedback - Feedback for retry
   */
  rejectStep: async (jobId, feedback) => {
    const response = await axios.post(`${API_BASE_URL}/reject/${jobId}`, {
      feedback
    })
    return response.data
  },

  /**
   * Download generated README
   * @param {string} jobId - Job ID
   */
  downloadReadme: async (jobId) => {
    const response = await axios.get(`${API_BASE_URL}/download/${jobId}`, {
      responseType: 'blob'
    })
    return response.data
  },

  /**
   * Submit project selection
   * @param {string} jobId - Job ID
   * @param {string[]} selectedProjectPaths - Array of selected project paths
   */
  selectProjects: async (jobId, selectedProjectPaths) => {
    const response = await axios.post(`${API_BASE_URL}/select-projects/${jobId}`, {
      selected_project_paths: selectedProjectPaths
    })
    return response.data
  },

  /**
   * Create GitHub Pull Request with generated README
   * @param {string} jobId - Job ID
   * @returns {Promise<{status: string, message: string, pr_url?: string}>}
   */
  createPullRequest: async (jobId) => {
    const response = await axios.post(`${API_BASE_URL}/create-pr/${jobId}`)
    return response.data
  }
}
