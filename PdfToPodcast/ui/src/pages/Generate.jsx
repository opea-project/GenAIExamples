import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setCurrentStep, nextStep, previousStep } from '@store/slices/uiSlice';
import { pollScriptStatus } from '@store/slices/scriptSlice';
import { pollAudioStatus, generateAudio } from '@store/slices/audioSlice';
import { resetUpload } from '@store/slices/uploadSlice';
import { resetScript } from '@store/slices/scriptSlice';
import { resetAudio } from '@store/slices/audioSlice';
import { resetUI } from '@store/slices/uiSlice';
import { usePolling } from '@hooks/usePolling';

import { StepIndicator } from '@components/ui';
import PDFUploader from '@components/features/PDFUploader';
import VoiceSelector from '@components/features/VoiceSelector';
import ProgressTracker from '@components/features/ProgressTracker';
import ScriptEditor from '@components/features/ScriptEditor';
import AudioPlayer from '@components/features/AudioPlayer';

const steps = [
  { id: 1, title: 'Upload PDF', subtitle: 'Select your document' },
  { id: 2, title: 'Choose Voices', subtitle: 'Pick AI voices' },
  { id: 3, title: 'Review Script', subtitle: 'Edit conversation' },
  { id: 4, title: 'Generate Audio', subtitle: 'Download podcast' },
];

export const Generate = () => {
  const dispatch = useDispatch();
  const currentStep = useSelector((state) => state.ui.currentStep);
  const { jobId } = useSelector((state) => state.upload);
  const {
    script,
    generating: scriptGenerating,
    generationProgress: scriptProgress,
    statusMessage: scriptMessage,
  } = useSelector((state) => state.script);
  const {
    audioUrl,
    generating: audioGenerating,
    generationProgress: audioProgress,
    statusMessage: audioMessage,
  } = useSelector((state) => state.audio);

  // Poll for script status
  usePolling(
    () => {
      if (jobId) {
        return dispatch(pollScriptStatus(jobId));
      }
    },
    2000,
    scriptGenerating && !script,
    [jobId, scriptGenerating, script]
  );

  // Poll for audio status
  usePolling(
    () => {
      if (jobId) {
        return dispatch(pollAudioStatus(jobId));
      }
    },
    2000,
    audioGenerating && !audioUrl,
    [jobId, audioGenerating, audioUrl]
  );

  // Move to next step when script is generated
  useEffect(() => {
    if (script && scriptGenerating === false && currentStep === 2) {
      dispatch(setCurrentStep(3));
    }
  }, [script, scriptGenerating, currentStep, dispatch]);

  // Move to next step when audio is generated
  useEffect(() => {
    if (audioUrl && audioGenerating === false && currentStep === 3) {
      dispatch(setCurrentStep(4));
    }
  }, [audioUrl, audioGenerating, currentStep, dispatch]);

  const handleUploadSuccess = () => {
    dispatch(nextStep());
  };

  const handleVoiceNext = () => {
    // Script generation will be triggered by VoiceSelector component
    // Progress tracker will be shown automatically
  };

  const handleScriptNext = async () => {
    if (jobId) {
      await dispatch(generateAudio(jobId));
    }
  };

  const handleReset = () => {
    dispatch(resetUpload());
    dispatch(resetScript());
    dispatch(resetAudio());
    dispatch(resetUI());
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Generate Your Podcast
        </h1>
        <p className="text-gray-600">
          Follow the steps below to create your AI-powered podcast
        </p>
      </div>

      <StepIndicator steps={steps} currentStep={currentStep} />

      <div className="animate-fade-in">
        {currentStep === 1 && (
          <PDFUploader onSuccess={handleUploadSuccess} />
        )}

        {currentStep === 2 && !scriptGenerating && (
          <VoiceSelector
            onBack={() => dispatch(previousStep())}
            onNext={handleVoiceNext}
          />
        )}

        {scriptGenerating && !script && (
          <ProgressTracker
            progress={scriptProgress}
            message={scriptMessage || 'Generating podcast script...'}
          />
        )}

        {currentStep === 3 && script && !audioGenerating && (
          <ScriptEditor
            onBack={() => dispatch(setCurrentStep(2))}
            onNext={handleScriptNext}
          />
        )}

        {audioGenerating && !audioUrl && (
          <ProgressTracker
            progress={audioProgress}
            message={audioMessage || 'Generating podcast audio...'}
          />
        )}

        {currentStep === 4 && audioUrl && (
          <AudioPlayer onReset={handleReset} />
        )}
      </div>
    </div>
  );
};

export default Generate;
