import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, AlertCircle, Code, FileText, MessageCircle, Upload, Check, X } from 'lucide-react'
import { sendChatMessage, uploadPDF, getRAGStatus } from '../services/api'

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [ragStatus, setRagStatus] = useState(null)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadRAGStatus()
  }, [])

  const loadRAGStatus = async () => {
    try {
      const status = await getRAGStatus()
      setRagStatus(status)
    } catch (error) {
      console.error('Error loading RAG status:', error)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    console.log('File selected:', file)
    
    if (!file) {
      console.log('No file selected')
      return
    }

    if (!file.type.includes('pdf')) {
      alert('Only PDF files are supported')
      return
    }

    console.log('Starting upload for:', file.name)
    setUploading(true)
    setUploadStatus(null)

    try {
      const result = await uploadPDF(file)
      console.log('Upload successful:', result)
      setUploadStatus({ success: true, message: result.message, chunks: result.chunks })
      await loadRAGStatus()
      
      // Show success message in chat
      const successMsg = {
        type: 'assistant',
        content: `✅ PDF uploaded successfully! Indexed ${result.chunks} chunks. You can now ask questions about this document.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, successMsg])
    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus({ success: false, message: error.message })
      const errorMsg = {
        type: 'error',
        content: `Failed to upload PDF: ${error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setUploading(false)
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim()) return

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendChatMessage(input)
      
      const botMessage = {
        type: 'assistant',
        content: response.response,
        agent: response.agent,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.message || 'Failed to get response. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const getAgentIcon = (agent) => {
    switch (agent) {
      case 'code_agent':
        return <Code className="w-4 h-4" />
      case 'rag_agent':
        return <FileText className="w-4 h-4" />
      case 'normal_agent':
        return <MessageCircle className="w-4 h-4" />
      default:
        return <Bot className="w-4 h-4" />
    }
  }

  const getAgentBadge = (agent) => {
    switch (agent) {
      case 'code_agent':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
          Code Agent
        </span>
      case 'rag_agent':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
          RAG Agent
        </span>
      case 'normal_agent':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
          General Agent
        </span>
      default:
        return null
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Chat Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
            <Bot className="w-5 h-5 text-purple-500" />
            <span>Multi-Agent Chat</span>
          </h2>
          {ragStatus && ragStatus.index_exists && (
            <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full font-medium">
              📄 {ragStatus.num_documents} docs indexed
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500">
          Ask anything - code questions, document queries, or general questions
        </p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-4 max-w-md">
              <Bot className="w-20 h-20 text-gray-300 mx-auto" />
              <div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Get Started</h3>
                <p className="text-gray-500 mb-4">Our intelligent multi-agent system will route your question to the best specialist:</p>
                <div className="flex flex-col space-y-2 text-sm">
                  <div className="flex items-center space-x-2 text-gray-600">
                    <Code className="w-4 h-4 text-blue-500" />
                    <span><strong>Code Agent</strong> - Programming, algorithms, debugging</span>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <FileText className="w-4 h-4 text-purple-500" />
                    <span><strong>RAG Agent</strong> - Document retrieval and research</span>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <MessageCircle className="w-4 h-4 text-green-500" />
                    <span><strong>General Agent</strong> - Everything else</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-start space-x-3 ${
              message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
            }`}
          >
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
              message.type === 'user' 
                ? 'bg-gradient-to-br from-blue-500 to-purple-600' 
                : message.type === 'error'
                ? 'bg-red-500'
                : 'bg-gray-200'
            }`}>
              {message.type === 'user' ? (
                <User className="w-5 h-5 text-white" />
              ) : message.type === 'error' ? (
                <AlertCircle className="w-5 h-5 text-white" />
              ) : (
                getAgentIcon(message.agent)
              )}
            </div>

            <div className={`flex-1 max-w-[80%] ${
              message.type === 'user' ? 'items-end' : 'items-start'
            }`}>
              {message.agent && message.type !== 'error' && (
                <div className="mb-1">
                  {getAgentBadge(message.agent)}
                </div>
              )}
              <div className={`rounded-lg p-3 ${
                message.type === 'user'
                  ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                  : message.type === 'error'
                  ? 'bg-red-50 border border-red-200 text-red-700'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <Bot className="w-5 h-5 text-gray-600" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isLoading || uploading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            type="button"
            onClick={(e) => {
              console.log('Upload button clicked!', fileInputRef.current)
              e.preventDefault()
              fileInputRef.current?.click()
            }}
            disabled={isLoading || uploading}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-sm flex items-center space-x-2"
          >
            {uploading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              </>
            ) : (
              <Upload className="w-4 h-4" />
            )}
          </button>
          <button
            type="submit"
            disabled={!input.trim() || isLoading || uploading}
            className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-sm flex items-center space-x-2"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send • Upload PDFs for document questions • The AI will route your question to the best specialist
        </p>
      </div>
    </div>
  )
}

