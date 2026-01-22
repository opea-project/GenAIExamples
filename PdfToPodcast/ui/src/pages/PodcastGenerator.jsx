import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import FileUpload from '../components/FileUpload';
import VoiceSelector from '../components/VoiceSelector';
import ProgressTracker from '../components/ProgressTracker';
import ScriptEditor from '../components/ScriptEditor';
import AudioPlayer from '../components/AudioPlayer';
import { uploadPDF, getVoices, generateScript, generateAudio, getJobStatus } from '../services/api';

const PodcastGenerator = () => {
  const [step, setStep] = useState(1); // 1: Upload, 2: Voice Selection, 3: Generating, 4: Script Edit, 5: Audio
  const [jobId, setJobId] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [voices, setVoices] = useState([]);
  const [hostVoice, setHostVoice] = useState('alloy');
  const [guestVoice, setGuestVoice] = useState('echo');
  const [script, setScript] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [audioUrl, setAudioUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchVoices();
  }, []);

  const fetchVoices = async () => {
    try {
      const voicesData = await getVoices();
      setVoices(voicesData.voices);
    } catch (error) {
      toast.error('Failed to load voices');
      console.error(error);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      setIsLoading(true);
      setPdfFile(file);
      const response = await uploadPDF(file);
      setJobId(response.job_id);
      setStep(2);
      toast.success('PDF uploaded successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload PDF');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateScript = async () => {
    // Prevent duplicate calls
    if (isLoading) {
      console.log('Script generation already in progress, ignoring duplicate call');
      return;
    }

    try {
      setIsLoading(true);
      setStep(3);
      setProgress(10);
      setProgressMessage('Analyzing PDF content...');

      await generateScript(jobId, hostVoice, guestVoice);

      // Poll for script generation status with error tolerance
      let errorCount = 0;
      const MAX_ERRORS = 3;
      const pollInterval = setInterval(async () => {
        try {
          const status = await getJobStatus(jobId);
          console.log('Script generation status:', status);
          console.log('Status value:', status.status);
          console.log('Script present:', !!status.script);

          // Reset error count on successful poll
          errorCount = 0;

          setProgress(status.progress || 0);
          setProgressMessage(status.status_message || 'Generating script...');

          if (status.status === 'script_generated') {
            console.log('Moving to step 4 - Script Editor');
            clearInterval(pollInterval);
            setScript(status.script);
            setStep(4);
            setIsLoading(false);
            toast.success('Script generated successfully!');
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsLoading(false);
            toast.error(status.error_message || 'Script generation failed');
            setStep(2);
          }
        } catch (error) {
          console.error('Polling error:', error);
          errorCount++;

          // Only stop polling after multiple consecutive errors
          if (errorCount >= MAX_ERRORS) {
            console.error('Max polling errors reached, stopping');
            clearInterval(pollInterval);
            setIsLoading(false);
            toast.error('Failed to check status');
            setStep(2);
          }
        }
      }, 2000);
    } catch (error) {
      setIsLoading(false);
      toast.error(error.response?.data?.detail || 'Failed to generate script');
      console.error(error);
      setStep(2);
    }
  };

  const handleGenerateAudio = async () => {
    // Prevent duplicate calls
    if (isLoading) {
      console.log('Audio generation already in progress, ignoring duplicate call');
      return;
    }

    try {
      setIsLoading(true);
      setStep(3);
      setProgress(10);
      setProgressMessage('Generating audio...');

      // Send the current (possibly edited) script to backend
      await generateAudio(jobId, script);

      // Poll for audio generation status with error tolerance
      let errorCount = 0;
      const MAX_ERRORS = 3;
      const pollInterval = setInterval(async () => {
        try {
          const status = await getJobStatus(jobId);
          console.log('Audio generation status:', status);

          // Reset error count on successful poll
          errorCount = 0;

          setProgress(status.progress || 0);
          setProgressMessage(status.status_message || 'Creating podcast audio...');

          if (status.status === 'completed' || status.status === 'audio_generated') {
            clearInterval(pollInterval);

            // Check if audio URL exists
            if (!status.audio_url) {
              console.error('Audio completed but no audio_url provided:', status);
              setIsLoading(false);
              toast.error('Audio generation completed but no audio file available');
              setStep(4);
              return;
            }

            // Convert relative URL to absolute URL
            const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const fullAudioUrl = status.audio_url.startsWith('http')
              ? status.audio_url
              : `${apiBaseUrl}${status.audio_url}`;
            console.log('Setting audio URL:', fullAudioUrl);

            setAudioUrl(fullAudioUrl);
            setStep(5);
            setIsLoading(false);
            toast.success('Podcast generated successfully!');
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsLoading(false);
            toast.error(status.error_message || 'Audio generation failed');
            setStep(4);
          }
        } catch (error) {
          console.error('Polling error:', error);
          errorCount++;

          // Only stop polling after multiple consecutive errors
          if (errorCount >= MAX_ERRORS) {
            console.error('Max polling errors reached, stopping');
            clearInterval(pollInterval);
            setIsLoading(false);
            toast.error('Failed to check status');
            setStep(4);
          }
        }
      }, 2000);
    } catch (error) {
      setIsLoading(false);
      toast.error(error.response?.data?.detail || 'Failed to generate audio');
      console.error(error);
      setStep(4);
    }
  };

  const handleReset = () => {
    setStep(1);
    setJobId(null);
    setPdfFile(null);
    setScript(null);
    setProgress(0);
    setProgressMessage('');
    setAudioUrl(null);
    setHostVoice('alloy');
    setGuestVoice('echo');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            PDF to Podcast Generator
          </h1>
          <p className="text-gray-600">
            Transform your PDF documents into engaging podcast conversations
          </p>
        </header>

        {step === 1 && (
          <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading} />
        )}

        {step === 2 && (
          <VoiceSelector
            voices={voices}
            hostVoice={hostVoice}
            guestVoice={guestVoice}
            onHostVoiceChange={setHostVoice}
            onGuestVoiceChange={setGuestVoice}
            onGenerate={handleGenerateScript}
            isLoading={isLoading}
            onBack={() => setStep(1)}
          />
        )}

        {step === 3 && (
          <ProgressTracker
            progress={progress}
            message={progressMessage}
          />
        )}

        {step === 4 && script && (
          <ScriptEditor
            script={script}
            onScriptChange={setScript}
            onGenerate={handleGenerateAudio}
            isLoading={isLoading}
            onBack={() => setStep(2)}
          />
        )}

        {step === 5 && audioUrl && (
          <AudioPlayer
            audioUrl={audioUrl}
            jobId={jobId}
            onReset={handleReset}
            pdfName={pdfFile?.name}
            hostVoice={hostVoice}
            guestVoice={guestVoice}
          />
        )}
      </div>
    </div>
  );
};

export default PodcastGenerator;
