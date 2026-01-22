import axios from 'axios'

// API base URL - uses Vite proxy in development (proxies to localhost:5000)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Upload a PDF file to the API
 * @param {File} file - The PDF file to upload
 * @returns {Promise} Response with upload status and chunk count
 */
export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post('/upload-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    console.error('Upload error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to upload PDF. Please try again.'
    )
  }
}

/**
 * Query the uploaded document
 * @param {string} query - The question to ask
 * @returns {Promise} Response with the answer
 */
export const queryDocument = async (query) => {
  try {
    const response = await api.post('/query', { query })
    return response.data
  } catch (error) {
    console.error('Query error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to get response. Please try again.'
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
 * Delete the vector store
 * @returns {Promise} Deletion status
 */
export const deleteVectorStore = async () => {
  try {
    const response = await api.delete('/vectorstore')
    return response.data
  } catch (error) {
    console.error('Delete error:', error)
    throw new Error(
      error.response?.data?.detail || 'Failed to delete vector store'
    )
  }
}

export default api

