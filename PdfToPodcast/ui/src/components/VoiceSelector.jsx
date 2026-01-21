import { useState } from 'react';
import { Volume2, ChevronLeft } from 'lucide-react';

const VoiceSelector = ({
  voices,
  hostVoice,
  guestVoice,
  onHostVoiceChange,
  onGuestVoiceChange,
  onGenerate,
  isLoading,
  onBack,
}) => {
  const [playingVoice, setPlayingVoice] = useState(null);

  const playSample = async (voiceId) => {
    try {
      setPlayingVoice(voiceId);

      // Access voice samples directly from public folder
      const audio = new Audio(`/voice-samples/${voiceId}.mp3`);

      audio.onended = () => {
        setPlayingVoice(null);
      };

      audio.onerror = () => {
        console.error(`Failed to play voice sample for ${voiceId}`);
        setPlayingVoice(null);
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing voice sample:', error);
      setPlayingVoice(null);
    }
  };

  const voiceOptions = [
    { id: 'alloy', name: 'Alloy', description: 'Neutral and balanced' },
    { id: 'echo', name: 'Echo', description: 'Clear and expressive' },
    { id: 'fable', name: 'Fable', description: 'Warm and engaging' },
    { id: 'onyx', name: 'Onyx', description: 'Deep and authoritative' },
    { id: 'nova', name: 'Nova', description: 'Friendly and conversational' },
    { id: 'shimmer', name: 'Shimmer', description: 'Bright and energetic' },
  ];

  return (
    <div className="card">
      <button
        onClick={onBack}
        className="flex items-center text-gray-600 hover:text-gray-800 mb-6"
      >
        <ChevronLeft className="w-5 h-5 mr-1" />
        Back
      </button>

      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Select Voice Actors
      </h2>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Host Voice */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Host Voice
          </label>
          <div className="space-y-2">
            {voiceOptions.map((voice) => (
              <div
                key={`host-${voice.id}`}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  hostVoice === voice.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => onHostVoiceChange(voice.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{voice.name}</p>
                    <p className="text-sm text-gray-500">{voice.description}</p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      playSample(voice.id);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-full"
                    disabled={playingVoice === voice.id}
                  >
                    <Volume2
                      className={`w-5 h-5 ${
                        playingVoice === voice.id
                          ? 'text-primary-500 animate-pulse'
                          : 'text-gray-400'
                      }`}
                    />
                  </button>
                </div>
              </div>
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
              <div
                key={`guest-${voice.id}`}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  guestVoice === voice.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => onGuestVoiceChange(voice.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{voice.name}</p>
                    <p className="text-sm text-gray-500">{voice.description}</p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      playSample(voice.id);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-full"
                    disabled={playingVoice === voice.id}
                  >
                    <Volume2
                      className={`w-5 h-5 ${
                        playingVoice === voice.id
                          ? 'text-primary-500 animate-pulse'
                          : 'text-gray-400'
                      }`}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <strong>Selected:</strong> Host - {voiceOptions.find(v => v.id === hostVoice)?.name} |
          Guest - {voiceOptions.find(v => v.id === guestVoice)?.name}
        </p>
      </div>

      <button
        onClick={onGenerate}
        className="btn-primary w-full text-lg py-3"
        disabled={isLoading || !hostVoice || !guestVoice}
      >
        {isLoading ? 'Generating Script...' : 'Generate Podcast Script'}
      </button>
    </div>
  );
};

export default VoiceSelector;
