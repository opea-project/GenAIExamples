import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, AlertCircle } from 'lucide-react'
import { queryDocument } from '../services/api'

export default function ChatInterface({ documentUploaded, documentName }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Reset messages when document changes
    if (documentUploaded) {
      setMessages([
        {
          type: 'bot',
          content: `Document "${documentName}" has been uploaded successfully! You can now ask me questions about it.`,
          timestamp: new Date()
        }
      ])
    } else {
      setMessages([])
    }
  }, [documentUploaded, documentName])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim() || !documentUploaded) return

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await queryDocument(input)
      
      const botMessage = {
        type: 'bot',
        content: response.answer,
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

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Chat Header */}
      <div className="border-b border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
          <Bot className="w-5 h-5 text-purple-500" />
          <span>Chat Assistant</span>
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {documentUploaded 
            ? 'Ask questions about your document' 
            : 'Upload a document to start chatting'}
        </p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
        {!documentUploaded && messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-3">
              <Bot className="w-16 h-16 text-gray-300 mx-auto" />
              <p className="text-gray-500">Upload a PDF document to start chatting</p>
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
                <Bot className="w-5 h-5 text-gray-600" />
              )}
            </div>

            <div className={`flex-1 max-w-[80%] ${
              message.type === 'user' ? 'items-end' : 'items-start'
            }`}>
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
            placeholder={documentUploaded ? "Ask a question..." : "Upload a document first..."}
            disabled={!documentUploaded || isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!documentUploaded || !input.trim() || isLoading}
            className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-sm flex items-center space-x-2"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send • The AI will answer based on your uploaded document
        </p>
      </div>
    </div>
  )
}

