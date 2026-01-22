import { useState, useEffect } from 'react'
import { Save, Code, FileText, MessageCircle, Settings as SettingsIcon } from 'lucide-react'
import { getAgentConfig, updateAgentConfig } from '../services/api'

export default function SettingsPage() {
  const [config, setConfig] = useState({
    orchestration: {
      role: '',
      goal: '',
      backstory: '',
      max_iter: 15,
      verbose: true
    },
    code: {
      role: '',
      goal: '',
      backstory: '',
      max_iter: 15,
      verbose: true
    },
    rag: {
      role: '',
      goal: '',
      backstory: '',
      max_iter: 15,
      verbose: true
    },
    normal: {
      role: '',
      goal: '',
      backstory: '',
      max_iter: 15,
      verbose: true
    }
  })

  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setIsLoading(true)
    try {
      const response = await getAgentConfig()
      setConfig(response.config)
    } catch (error) {
      setMessage('Failed to load configuration. Using defaults.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage('')
    
    try {
      await updateAgentConfig(config)
      setMessage('Configuration saved successfully!')
    } catch (error) {
      setMessage('Failed to save configuration.')
    } finally {
      setIsSaving(false)
      setTimeout(() => setMessage(''), 3000)
    }
  }

  const handleAgentConfigChange = (agentType, field, value) => {
    setConfig(prev => ({
      ...prev,
      [agentType]: {
        ...prev[agentType],
        [field]: value
      }
    }))
  }

  const AgentConfigCard = ({ agentType, agentName, icon: Icon, color }) => {
    const colorClasses = {
      purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
      blue: { bg: 'bg-blue-100', text: 'text-blue-600' },
      green: { bg: 'bg-green-100', text: 'text-green-600' }
    }
    const classes = colorClasses[color] || colorClasses.purple
    
    return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center space-x-3 mb-4 pb-4 border-b border-gray-200">
        <div className={`p-2 rounded-lg ${classes.bg}`}>
          <Icon className={`w-6 h-6 ${classes.text}`} />
        </div>
        <h3 className="text-lg font-semibold text-gray-800">{agentName}</h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Role
          </label>
          <input
            type="text"
            value={config[agentType].role}
            onChange={(e) => handleAgentConfigChange(agentType, 'role', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="e.g., Senior Software Developer"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Goal
          </label>
          <textarea
            value={config[agentType].goal}
            onChange={(e) => handleAgentConfigChange(agentType, 'goal', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Agent's primary goal"
            rows="2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Backstory
          </label>
          <textarea
            value={config[agentType].backstory}
            onChange={(e) => handleAgentConfigChange(agentType, 'backstory', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Agent's background and expertise"
            rows="3"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Iterations
            </label>
            <input
              type="number"
              value={config[agentType].max_iter}
              onChange={(e) => handleAgentConfigChange(agentType, 'max_iter', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              min="1"
              max="50"
            />
          </div>

          <div className="flex items-center pt-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config[agentType].verbose}
                onChange={(e) => handleAgentConfigChange(agentType, 'verbose', e.target.checked)}
                className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
              />
              <span className="text-sm font-medium text-gray-700">Verbose</span>
            </label>
          </div>
        </div>
      </div>
    </div>
    )
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading configuration...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <SettingsIcon className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-bold text-gray-800">Agent Configuration</h2>
          </div>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-sm flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving...' : 'Save Configuration'}</span>
          </button>
        </div>

        {message && (
          <div className={`p-3 rounded-lg mb-4 ${
            message.includes('success') 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message}
          </div>
        )}

        <p className="text-gray-600 text-sm">
          Configure the behavior and expertise of each agent in the multi-agent system.
          Changes will be applied to new conversations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentConfigCard
          agentType="orchestration"
          agentName="Orchestration Agent"
          icon={SettingsIcon}
          color="purple"
        />
        <AgentConfigCard
          agentType="code"
          agentName="Code Agent"
          icon={Code}
          color="blue"
        />
        <AgentConfigCard
          agentType="rag"
          agentName="RAG Agent"
          icon={FileText}
          color="purple"
        />
        <AgentConfigCard
          agentType="normal"
          agentName="General Agent"
          icon={MessageCircle}
          color="green"
        />
      </div>
    </div>
  )
}

