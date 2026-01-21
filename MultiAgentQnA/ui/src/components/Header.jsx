import { Bot, Terminal } from 'lucide-react'

export default function Header({ currentPage, onPageChange, onLogsToggle }) {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-purple-700 shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-white rounded-lg p-2">
              <Bot className="w-8 h-8 text-purple-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Multi-Agent Q&A</h1>
              <p className="text-blue-100 text-sm">Intelligent question answering with specialized agents</p>
            </div>
          </div>
          
          <nav className="flex space-x-4">
            <button
              onClick={() => onPageChange('chat')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                currentPage === 'chat'
                  ? 'bg-white text-purple-700 shadow-md'
                  : 'text-white hover:bg-white/20'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => onPageChange('settings')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                currentPage === 'settings'
                  ? 'bg-white text-purple-700 shadow-md'
                  : 'text-white hover:bg-white/20'
              }`}
            >
              Settings
            </button>
            <button
              onClick={onLogsToggle}
              className="px-4 py-2 rounded-lg font-medium transition-all text-white hover:bg-white/20 flex items-center space-x-2"
              title="View agent logs"
            >
              <Terminal className="w-4 h-4" />
              <span>Logs</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}

