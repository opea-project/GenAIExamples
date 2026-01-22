import { useState } from 'react';
import { toast } from 'react-hot-toast';
import TextInput from '../components/TextInput';
import FileUpload from '../components/FileUpload';
import { generateSummary, generateSummaryStreaming } from '../services/api';

export const Generate = () => {
  const [activeTab, setActiveTab] = useState('text');
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const tabs = [
    { id: 'text', label: 'Paste Text' },
    { id: 'file', label: 'Upload File' },
  ];

  const handleSubmit = async (formData, isStreaming) => {
    setIsLoading(true);
    setSummary('');

    try {
      if (isStreaming) {
        await generateSummaryStreaming(formData, (chunk) => {
          setSummary((prev) => prev + chunk);
        });
        toast.success('Summary generated successfully!');
      } else {
        const result = await generateSummary(formData);
        setSummary(result);
        toast.success('Summary generated successfully!');
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to generate summary. Please try again.');
      setSummary('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Generate Summary
        </h1>
        <p className="text-gray-600">
          Choose your input method and generate concise summaries
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="card animate-slide-up">
            <div className="flex border-b border-gray-200 mb-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab ${activeTab === tab.id ? 'tab-active' : ''}`}
                  disabled={isLoading}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === 'text' && (
              <TextInput onSubmit={handleSubmit} isLoading={isLoading} />
            )}

            {activeTab === 'file' && (
              <FileUpload
                onSubmit={handleSubmit}
                isLoading={isLoading}
                acceptedTypes={['.pdf', '.doc', '.docx']}
                fileType="text"
                title="Upload Document"
                maxFileSize="50 MB"
              />
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card animate-slide-up">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Summary Output
            </h2>

            {isLoading && !summary && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            )}

            {summary && (
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 min-h-[400px] max-h-[600px] overflow-y-auto border border-primary-100">
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {summary}
                </p>
              </div>
            )}

            {!isLoading && !summary && (
              <div className="text-center py-12">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-gray-500">
                  Your summary will appear here once generated
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

export default Generate;
