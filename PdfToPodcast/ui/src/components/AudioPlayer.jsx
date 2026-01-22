import { useState, useRef } from 'react';
import { Play, Pause, Download, RotateCcw, Volume2, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import { downloadAudio } from '../services/api';

const AudioPlayer = ({ audioUrl, jobId, onReset, pdfName, hostVoice, guestVoice }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e) => {
    const seekTime = (e.target.value / 100) * duration;
    if (audioRef.current) {
      audioRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  const handleDownload = () => {
    // Create download link using the audioUrl
    const a = document.createElement('a');
    a.href = audioUrl;
    a.download = `podcast-${jobId}.mp3`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Save to projects after downloading
    handleSaveProject();
  };

  const handleSaveProject = () => {
    try {
      const project = {
        id: jobId,
        pdfName: pdfName || 'Untitled',
        audioUrl: audioUrl,
        hostVoice,
        guestVoice,
        createdAt: new Date().toISOString(),
        status: 'completed'
      };

      const projects = JSON.parse(localStorage.getItem('podcastProjects') || '[]');

      // Check if project already exists
      const existingIndex = projects.findIndex(p => p.id === jobId);
      if (existingIndex !== -1) {
        // Update existing project
        projects[existingIndex] = project;
      } else {
        // Add new project
        projects.unshift(project);
      }

      localStorage.setItem('podcastProjects', JSON.stringify(projects.slice(0, 20)));
      toast.success('Project saved to Projects!');
    } catch (error) {
      console.error('Error saving project:', error);
      toast.error('Failed to save project');
    }
  };

  const formatTime = (time) => {
    if (isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="card">
      <div className="text-center mb-8">
        <div className="w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full mx-auto mb-4 flex items-center justify-center">
          <Volume2 className="w-12 h-12 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Your Podcast is Ready!
        </h2>
        <p className="text-gray-600">
          Listen to your AI-generated podcast below
        </p>
      </div>

      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-gray-600">{formatTime(currentTime)}</span>
          <span className="text-sm text-gray-600">{formatTime(duration)}</span>
        </div>

        <input
          type="range"
          min="0"
          max="100"
          value={duration ? (currentTime / duration) * 100 : 0}
          onChange={handleSeek}
          className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
        />

        <div className="flex justify-center mt-6">
          <button
            onClick={togglePlay}
            className="w-16 h-16 bg-primary-600 hover:bg-primary-700 text-white rounded-full flex items-center justify-center transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-8 h-8" />
            ) : (
              <Play className="w-8 h-8 ml-1" />
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <button
          onClick={handleDownload}
          className="btn-primary flex items-center justify-center"
        >
          <Download className="w-5 h-5 mr-2" />
          Download
        </button>
        <button
          onClick={handleSaveProject}
          className="btn-primary flex items-center justify-center"
        >
          <Save className="w-5 h-5 mr-2" />
          Save Project
        </button>
        <button
          onClick={onReset}
          className="btn-secondary flex items-center justify-center"
        >
          <RotateCcw className="w-5 h-5 mr-2" />
          New Podcast
        </button>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          background: #0284c7;
          cursor: pointer;
          border-radius: 50%;
        }

        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          background: #0284c7;
          cursor: pointer;
          border-radius: 50%;
          border: none;
        }
      `}</style>
    </div>
  );
};

export default AudioPlayer;
