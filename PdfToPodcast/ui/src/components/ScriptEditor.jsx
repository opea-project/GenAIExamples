import { useState } from 'react';
import { ChevronLeft, Edit2, Save } from 'lucide-react';

const ScriptEditor = ({ script, onScriptChange, onGenerate, isLoading, onBack }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedScript, setEditedScript] = useState(script);

  const handleSave = () => {
    onScriptChange(editedScript);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedScript(script);
    setIsEditing(false);
  };

  const handleDialogueChange = (index, field, value) => {
    const newScript = [...editedScript];
    newScript[index][field] = value;
    setEditedScript(newScript);
  };

  return (
    <div className="card">
      <button
        onClick={onBack}
        className="flex items-center text-gray-600 hover:text-gray-800 mb-6"
      >
        <ChevronLeft className="w-5 h-5 mr-1" />
        Back
      </button>

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          Podcast Script
        </h2>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center btn-secondary"
          >
            <Edit2 className="w-4 h-4 mr-2" />
            Edit Script
          </button>
        )}
      </div>

      <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
        {(isEditing ? editedScript : script).map((dialogue, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg ${
              dialogue.speaker === 'host'
                ? 'bg-blue-50 border-l-4 border-blue-500'
                : 'bg-green-50 border-l-4 border-green-500'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <span className="font-semibold text-gray-700 capitalize">
                {dialogue.speaker}
              </span>
              {isEditing && (
                <select
                  value={dialogue.speaker}
                  onChange={(e) =>
                    handleDialogueChange(index, 'speaker', e.target.value)
                  }
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="host">Host</option>
                  <option value="guest">Guest</option>
                </select>
              )}
            </div>
            {isEditing ? (
              <textarea
                value={dialogue.text}
                onChange={(e) =>
                  handleDialogueChange(index, 'text', e.target.value)
                }
                className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={3}
              />
            ) : (
              <p className="text-gray-800">{dialogue.text}</p>
            )}
          </div>
        ))}
      </div>

      {isEditing && (
        <div className="flex gap-3 mb-6">
          <button onClick={handleCancel} className="btn-secondary flex-1">
            Cancel
          </button>
          <button onClick={handleSave} className="btn-primary flex-1">
            <Save className="w-4 h-4 mr-2 inline" />
            Save Changes
          </button>
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-yellow-800">
          <strong>Tip:</strong> Review and edit the script to ensure accuracy before generating audio.
          This is your last chance to make changes!
        </p>
      </div>

      <button
        onClick={onGenerate}
        className="btn-primary w-full text-lg py-3"
        disabled={isLoading || isEditing}
      >
        {isLoading ? 'Generating Audio...' : 'Generate Podcast Audio'}
      </button>
    </div>
  );
};

export default ScriptEditor;
