import { useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Play,
  Pause,
  Download,
  RotateCcw,
  SkipBack,
  SkipForward,
} from 'lucide-react';
import { useWaveSurfer } from '@hooks/useWaveSurfer';
import { downloadAudio } from '@store/slices/audioSlice';
import { Button, Card, CardBody, Spinner } from '@components/ui';
import { formatTime, downloadBlob } from '@utils/helpers';
import { cn } from '@utils/helpers';

export const AudioPlayer = ({ onReset }) => {
  const dispatch = useDispatch();
  const { audioUrl, audioBlob } = useSelector((state) => state.audio);
  const { jobId } = useSelector((state) => state.upload);
  const waveformRef = useRef(null);

  const {
    wavesurfer,
    isPlaying,
    currentTime,
    duration,
    playPause,
    seekTo,
    load,
  } = useWaveSurfer(waveformRef, {
    height: 100,
    waveColor: '#ddd',
    progressColor: '#0284c7',
  });

  useEffect(() => {
    if (audioUrl && wavesurfer) {
      const fullUrl = audioUrl.startsWith('http')
        ? audioUrl
        : `http://localhost:8000${audioUrl}`;
      load(fullUrl);
    }
  }, [audioUrl, wavesurfer, load]);

  const handleDownload = async () => {
    if (jobId) {
      let blob = audioBlob;

      if (!blob) {
        const result = await dispatch(downloadAudio(jobId));
        if (result.type.endsWith('/fulfilled')) {
          blob = result.payload;
        }
      }

      if (blob) {
        downloadBlob(blob, `podcast-${jobId}.mp3`);
      }
    }
  };

  const handleSkip = (seconds) => {
    if (wavesurfer) {
      const newTime = Math.max(
        0,
        Math.min(duration, currentTime + seconds)
      );
      seekTo(newTime / duration);
    }
  };

  if (!audioUrl) {
    return (
      <Card>
        <CardBody>
          <div className="text-center py-12">
            <Spinner size="lg" />
            <p className="mt-4 text-gray-600">
              Generating your podcast audio...
            </p>
          </div>
        </CardBody>
      </Card>
    );
  }

  // Check if TTS service is not available (placeholder URL)
  const isTTSAvailable = audioUrl && audioUrl !== 'placeholder' && !audioUrl.startsWith('http://localhost:8000/voice-samples');

  return (
    <Card>
      <CardBody>
        <div className="space-y-6">
          <div className="text-center">
            {/* Custom Success Image - Replace src with your actual image */}
            <img
              src="/success-icon.png"
              alt="Success"
              className="w-24 h-24 mx-auto mb-4 object-contain"
              onError={(e) => {
                // Fallback to gradient circle if image not found
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div
              className="w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full mx-auto mb-4 items-center justify-center shadow-lg hidden"
              style={{ display: 'none' }}
            >
              <div className="w-12 h-12 bg-white rounded-full" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {isTTSAvailable ? 'Your Podcast is Ready!' : 'Script Generation Complete!'}
            </h2>
            {isTTSAvailable ? (
              <p className="text-gray-600">
                Listen to your AI-generated podcast below
              </p>
            ) : (
              <p className="text-gray-600">
                Your podcast script has been successfully created
              </p>
            )}
          </div>

          {isTTSAvailable ? (
            <>
              {/* Waveform */}
              <div className="bg-gray-50 rounded-lg p-6">
                <div ref={waveformRef} className="mb-4" />

                {/* Time Display */}
                <div className="flex justify-between text-sm text-gray-600 mb-4">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>

                {/* Controls */}
                <div className="flex items-center justify-center gap-4">
                  <button
                    onClick={() => handleSkip(-10)}
                    className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                    title="Skip back 10s"
                  >
                    <SkipBack className="w-5 h-5" />
                  </button>

                  <button
                    onClick={playPause}
                    className="w-16 h-16 bg-primary-600 hover:bg-primary-700 text-white rounded-full flex items-center justify-center transition-colors shadow-lg"
                  >
                    {isPlaying ? (
                      <Pause className="w-8 h-8" />
                    ) : (
                      <Play className="w-8 h-8 ml-1" />
                    )}
                  </button>

                  <button
                    onClick={() => handleSkip(10)}
                    className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                    title="Skip forward 10s"
                  >
                    <SkipForward className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <p className="text-sm text-gray-600 mb-1">Duration</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatTime(duration)}
                  </p>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <p className="text-sm text-gray-600 mb-1">Format</p>
                  <p className="text-2xl font-bold text-gray-900">MP3</p>
                </div>
              </div>

              {/* Actions */}
              <div className="grid grid-cols-2 gap-4">
                <Button
                  onClick={handleDownload}
                  variant="primary"
                  size="lg"
                  icon={Download}
                  fullWidth
                >
                  Download Audio
                </Button>
                <Button
                  onClick={onReset}
                  variant="outline"
                  size="lg"
                  icon={RotateCcw}
                  fullWidth
                >
                  Create New Podcast
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* Success Summary */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-green-900 mb-3">
                  What's Been Created
                </h3>
                <div className="space-y-2 text-green-800">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>PDF text successfully extracted</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Podcast script generated with AI</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Voice actors selected</span>
                  </div>
                </div>
              </div>

              {/* TTS Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  Audio Generation
                </h3>
                <p className="text-blue-800 mb-3">
                  To generate the final podcast audio, you'll need to start the TTS (Text-to-Speech) service.
                </p>
                <div className="bg-white rounded-lg p-3 text-sm font-mono text-gray-700">
                  <p className="text-blue-900 font-semibold mb-2">Setup Instructions:</p>
                  <p>1. Install Python 3.11</p>
                  <p>2. Start TTS service on port 8003</p>
                  <p>3. Re-run the generation process</p>
                </div>
              </div>

              {/* Action */}
              <Button
                onClick={onReset}
                variant="primary"
                size="lg"
                icon={RotateCcw}
                fullWidth
              >
                Create New Podcast
              </Button>
            </>
          )}
        </div>
      </CardBody>
    </Card>
  );
};

export default AudioPlayer;
