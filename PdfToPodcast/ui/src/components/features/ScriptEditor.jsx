import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Edit2, Save, X, ChevronLeft, Trash2, Plus } from 'lucide-react';
import { setScript, updateScript } from '@store/slices/scriptSlice';
import { Button, Card, CardBody, Alert, Input } from '@components/ui';
import { cn } from '@utils/helpers';

export const ScriptEditor = ({ onBack, onNext }) => {
  const dispatch = useDispatch();
  const { script, updating, error } = useSelector((state) => state.script);
  const { jobId } = useSelector((state) => state.upload);
  const [isEditing, setIsEditing] = useState(false);
  const [editedScript, setEditedScript] = useState(script || []);

  const handleEdit = () => {
    setEditedScript(JSON.parse(JSON.stringify(script)));
    setIsEditing(true);
  };

  const handleCancel = () => {
    setEditedScript(script);
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (jobId) {
      dispatch(setScript(editedScript));
      const result = await dispatch(
        updateScript({ jobId, script: editedScript })
      );
      if (result.type.endsWith('/fulfilled')) {
        setIsEditing(false);
      }
    }
  };

  const handleDialogueChange = (index, field, value) => {
    const newScript = [...editedScript];
    newScript[index] = { ...newScript[index], [field]: value };
    setEditedScript(newScript);
  };

  const handleAddDialogue = (index) => {
    const newScript = [...editedScript];
    newScript.splice(index + 1, 0, {
      speaker: 'host',
      text: '',
    });
    setEditedScript(newScript);
  };

  const handleDeleteDialogue = (index) => {
    if (editedScript.length > 1) {
      const newScript = editedScript.filter((_, i) => i !== index);
      setEditedScript(newScript);
    }
  };

  const currentScript = isEditing ? editedScript : script;

  if (!script) {
    return (
      <Card>
        <CardBody>
          <Alert
            variant="warning"
            message="No script available. Please generate a script first."
          />
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardBody>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Review & Edit Script
                </h2>
                <p className="text-gray-600">
                  Review the generated conversation and make any changes
                </p>
              </div>
            </div>

            {!isEditing ? (
              <Button onClick={handleEdit} variant="outline" icon={Edit2}>
                Edit Script
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button onClick={handleCancel} variant="ghost" icon={X}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  loading={updating}
                  icon={Save}
                >
                  Save Changes
                </Button>
              </div>
            )}
          </div>

          {error && <Alert variant="error" message={error} />}

          <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
            {currentScript.map((dialogue, index) => (
              <div
                key={index}
                className={cn(
                  'p-4 rounded-lg border-l-4 transition-all',
                  dialogue.speaker === 'host'
                    ? 'bg-blue-50 border-blue-500'
                    : 'bg-green-50 border-green-500',
                  isEditing && 'ring-2 ring-gray-200'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    {isEditing ? (
                      <div className="space-y-2">
                        <select
                          value={dialogue.speaker}
                          onChange={(e) =>
                            handleDialogueChange(index, 'speaker', e.target.value)
                          }
                          className="text-sm font-semibold text-gray-700 border-none bg-transparent focus:outline-none capitalize"
                        >
                          <option value="host">Host</option>
                          <option value="guest">Guest</option>
                        </select>
                        <textarea
                          value={dialogue.text}
                          onChange={(e) =>
                            handleDialogueChange(index, 'text', e.target.value)
                          }
                          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                          rows={3}
                        />
                      </div>
                    ) : (
                      <>
                        <div className="text-sm font-semibold text-gray-700 mb-1 capitalize">
                          {dialogue.speaker}
                        </div>
                        <p className="text-gray-800">{dialogue.text}</p>
                      </>
                    )}
                  </div>

                  {isEditing && (
                    <div className="flex flex-col gap-1">
                      <button
                        onClick={() => handleAddDialogue(index)}
                        className="p-1.5 text-green-600 hover:bg-green-100 rounded transition-colors"
                        title="Add dialogue after this"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                      {currentScript.length > 1 && (
                        <button
                          onClick={() => handleDeleteDialogue(index)}
                          className="p-1.5 text-red-600 hover:bg-red-100 rounded transition-colors"
                          title="Delete this dialogue"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>Tip:</strong> Review the script carefully and make any
              necessary edits before generating the audio. This is your last
              chance to perfect the conversation!
            </p>
          </div>

          <Button
            onClick={onNext}
            fullWidth
            size="lg"
            disabled={isEditing}
          >
            Continue to Audio Generation
          </Button>
        </div>
      </CardBody>
    </Card>
  );
};

export default ScriptEditor;
