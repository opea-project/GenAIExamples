import { useState } from 'react';
import { FileText } from 'lucide-react';

const TextInput = ({ onSubmit, isLoading }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    const formData = new FormData();
    formData.append('type', 'text');
    formData.append('messages', text);
    formData.append('max_tokens', 1024);
    formData.append('language', 'en');
    formData.append('summary_type', 'auto');
    formData.append('stream', 'false');

    onSubmit(formData, false);
  };

  return (
    <div className="card animate-fadeIn">
      <div className="flex items-center mb-4">
        <FileText className="h-6 w-6 text-primary-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-800">Paste Text</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enter text to summarize
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows="8"
            placeholder="Paste your text here..."
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? 'Generating Summary...' : 'Generate Summary'}
        </button>
      </form>
    </div>
  );
};

export default TextInput;
