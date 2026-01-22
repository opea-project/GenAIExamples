import { useState } from 'react';
import { Save, Info } from 'lucide-react';

const Settings = () => {
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem('openai_api_key', apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Configure your podcast generator settings</p>
      </div>

      <div className="card space-y-6">
        <h2 className="text-xl font-semibold text-gray-900">API Configuration</h2>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">OpenAI API Key</p>
            <p className="text-sm text-blue-700">
              Your API key is used to generate scripts and audio. It's stored locally in your browser.
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700">
            OpenAI API Key
          </label>
          <input
            id="apiKey"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <p className="text-sm text-gray-500">
            Get your API key from{' '}
            <a
              href="https://platform.openai.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              platform.openai.com
            </a>
          </p>
        </div>

        {saved && (
          <div className="bg-success-50 border border-success-200 rounded-lg p-4 text-success-800">
            Settings saved successfully!
          </div>
        )}

        <button onClick={handleSave} className="btn-primary inline-flex items-center gap-2">
          <Save className="w-4 h-4" />
          Save Settings
        </button>
      </div>

      <div className="card space-y-6">
        <h2 className="text-xl font-semibold text-gray-900">Preferences</h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Default Host Voice</p>
              <p className="text-sm text-gray-600">Choose your preferred host voice</p>
            </div>
            <select className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Alloy</option>
              <option>Echo</option>
              <option>Fable</option>
              <option>Onyx</option>
              <option>Nova</option>
              <option>Shimmer</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Default Guest Voice</p>
              <p className="text-sm text-gray-600">Choose your preferred guest voice</p>
            </div>
            <select className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Echo</option>
              <option>Alloy</option>
              <option>Fable</option>
              <option>Onyx</option>
              <option>Nova</option>
              <option>Shimmer</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">About</h2>

        <div className="space-y-3 text-gray-600">
          <p>
            <strong className="text-gray-900">Version:</strong> 1.0.0
          </p>

          <p>
            <strong className="text-gray-900">Description:</strong> Transform your PDF documents
            into engaging podcast conversations using AI
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
