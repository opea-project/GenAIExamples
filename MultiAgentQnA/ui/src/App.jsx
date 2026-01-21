import { useState } from 'react'
import Header from './components/Header'
import ChatInterface from './components/ChatInterface'
import SettingsPage from './components/SettingsPage'
import LogsPanel from './components/LogsPanel'

function App() {
  const [currentPage, setCurrentPage] = useState('chat')
  const [logsOpen, setLogsOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header 
        currentPage={currentPage} 
        onPageChange={setCurrentPage}
        onLogsToggle={() => setLogsOpen(!logsOpen)}
      />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {currentPage === 'chat' && <ChatInterface />}
        {currentPage === 'settings' && <SettingsPage />}
      </main>

      <LogsPanel isOpen={logsOpen} onClose={() => setLogsOpen(false)} />
    </div>
  )
}

export default App

