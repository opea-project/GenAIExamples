import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Volume2, ChevronLeft } from 'lucide-react';
import { setHostVoice, setGuestVoice, generateScript } from '@store/slices/scriptSlice';
import { voiceAPI } from '@services/api';
import { Button, Card, CardBody, Alert } from '@components/ui';
import { cn } from '@utils/helpers';

const voiceOptions = [
  { id: 'alloy', name: 'Alloy', description: 'Neutral and balanced', gender: 'neutral' },
  { id: 'echo', name: 'Echo', description: 'Clear and expressive', gender: 'male' },
  { id: 'fable', name: 'Fable', description: 'Warm and engaging', gender: 'neutral' },
  { id: 'onyx', name: 'Onyx', description: 'Deep and authoritative', gender: 'male' },
  { id: 'nova', name: 'Nova', description: 'Friendly and conversational', gender: 'female' },
  { id: 'shimmer', name: 'Shimmer', description: 'Bright and energetic', gender: 'female' },
];

export const VoiceSelector = ({ onBack, onNext }) => {
  const dispatch = useDispatch();
  const { hostVoice, guestVoice, generating, error } = useSelector((state) => state.script);
  const { jobId } = useSelector((state) => state.upload);
  const [playingVoice, setPlayingVoice] = useState(null);
  const [previewMessage, setPreviewMessage] = useState(null);

  // No cleanup needed anymore since we're using HTML5 audio

  const playSample = async (voiceId) => {
    const voice = voiceOptions.find(v => v.id === voiceId);

    try {
      setPlayingVoice(voiceId);
      setPreviewMessage(`Playing ${voice.name}...`);

      // Get audio URL from backend
      const response = await fetch(`http://localhost:8000/api/voice/sample/${voiceId}`);
      const data = await response.json();

      if (data.status === 'available' && data.audio_url) {
        // Play actual OpenAI TTS audio sample
        const audio = new Audio(data.audio_url);

        audio.onended = () => {
          setPlayingVoice(null);
          setPreviewMessage(null);
        };

        audio.onerror = () => {
          setPlayingVoice(null);
          setPreviewMessage('Error playing audio sample');
          setTimeout(() => setPreviewMessage(null), 3000);
        };

        await audio.play();
      } else {
        // Fallback if audio not available
        setPreviewMessage(`${voice.name}: ${voice.description}`);
        setTimeout(() => {
          setPlayingVoice(null);
          setPreviewMessage(null);
        }, 3000);
      }
    } catch (error) {
      console.error('Failed to play sample:', error);
      setPlayingVoice(null);
      setPreviewMessage('Error loading audio sample');
      setTimeout(() => setPreviewMessage(null), 3000);
    }
  };

  const handleGenerate = async () => {
    if (jobId) {
      const result = await dispatch(
        generateScript({ jobId, hostVoice, guestVoice })
      );
      if (result.type.endsWith('/fulfilled') && onNext) {
        onNext();
      }
    }
  };

  const VoiceCard = ({ voice, selected, onSelect, label }) => (
    <div
      onClick={() => onSelect(voice.id)}
      className={cn(
        'p-4 border-2 rounded-lg cursor-pointer transition-all',
        selected
          ? 'border-primary-500 bg-primary-50 shadow-md'
          : 'border-gray-200 hover:border-primary-300 hover:shadow-sm'
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-gray-900">{voice.name}</h4>
            <span className="text-xs px-2 py-0.5 bg-gray-200 text-gray-600 rounded-full">
              {voice.gender}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{voice.description}</p>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            playSample(voice.id);
          }}
          className={cn(
            'p-2 rounded-full transition-colors ml-4',
            playingVoice === voice.id
              ? 'bg-primary-500 text-white'
              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
          )}
          disabled={playingVoice !== null}
        >
          <Volume2
            className={cn(
              'w-5 h-5',
              playingVoice === voice.id && 'animate-pulse'
            )}
          />
        </button>
      </div>
    </div>
  );

  return (
    <Card>
      <CardBody>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Select Voice Actors
              </h2>
              <p className="text-gray-600">
                Choose voices for your podcast host and guest
              </p>
            </div>
          </div>

          {error && (
            <Alert variant="error" message={error} />
          )}

          {previewMessage && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800 flex items-center gap-2">
                <Volume2 className="w-4 h-4 animate-pulse" />
                <span>{previewMessage}</span>
              </p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {/* Host Voice */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Host Voice
              </label>
              <div className="space-y-2">
                {voiceOptions.map((voice) => (
                  <VoiceCard
                    key={`host-${voice.id}`}
                    voice={voice}
                    selected={hostVoice === voice.id}
                    onSelect={(id) => dispatch(setHostVoice(id))}
                    label="host"
                  />
                ))}
              </div>
            </div>

            {/* Guest Voice */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Guest Voice
              </label>
              <div className="space-y-2">
                {voiceOptions.map((voice) => (
                  <VoiceCard
                    key={`guest-${voice.id}`}
                    voice={voice}
                    selected={guestVoice === voice.id}
                    onSelect={(id) => dispatch(setGuestVoice(id))}
                    label="guest"
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Selected:</strong> Host -{' '}
              {voiceOptions.find((v) => v.id === hostVoice)?.name} | Guest -{' '}
              {voiceOptions.find((v) => v.id === guestVoice)?.name}
            </p>
          </div>

          <Button
            onClick={handleGenerate}
            fullWidth
            size="lg"
            loading={generating}
            disabled={!jobId || generating}
          >
            Generate Podcast Script
          </Button>
        </div>
      </CardBody>
    </Card>
  );
};

export default VoiceSelector;
