import axios from 'axios'

// API base URL - uses Vite proxy in development (proxies to localhost:5001)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Send a chat message to the multi-agent system
 * @param {string} message - The user message
 * @param {Object} agentConfig - Optional agent configuration
 * @returns {Promise} Response with the answer and agent used
 */
export const sendChatMessage = async (message, agentConfig = null) => {
  try {
    const response = await api.post('/chat', { 
      message,
      agent_config: agentConfig
    })
    return response.data
  } catch (error) {
    console.error('Chat error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to get response. Please try again.'
    )
  }
}

/**
 * Get current agent configuration
 * @returns {Promise} Agent configuration
 */
export const getAgentConfig = async () => {
  try {
    const response = await api.get('/config')
    return response.data
  } catch (error) {
    console.error('Config fetch error:', error)
    throw new Error('Failed to fetch configuration')
  }
}

/**
 * Update agent configuration
 * @param {Object} config - Agent configuration
 * @returns {Promise} Update status
 */
export const updateAgentConfig = async (config) => {
  try {
    const response = await api.post('/config', config)
    return response.data
  } catch (error) {
    console.error('Config update error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to update configuration'
    )
  }
}

/**
 * Check API health
 * @returns {Promise} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check error:', error)
    throw new Error('API is not available')
  }
}

/**
 * Get agent activity logs
 * @returns {Promise} Agent logs
 */
export const getLogs = async () => {
  try {
    const response = await api.get('/logs')
    return response.data
  } catch (error) {
    console.error('Logs fetch error:', error)
    throw new Error('Failed to fetch logs')
  }
}

/**
 * Upload a PDF file for RAG indexing
 * @param {File} file - PDF file to upload
 * @returns {Promise} Upload result
 */
export const uploadPDF = async (file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/rag/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    console.error('PDF upload error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to upload PDF'
    )
  }
}

/**
 * Get RAG index status
 * @returns {Promise} RAG status
 */
export const getRAGStatus = async () => {
  try {
    const response = await api.get('/rag/status')
    return response.data
  } catch (error) {
    console.error('RAG status error:', error)
    throw new Error('Failed to fetch RAG status')
  }
}

export default api

