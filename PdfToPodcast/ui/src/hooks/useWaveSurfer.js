import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';

/**
 * Custom hook for WaveSurfer.js integration
 * @param {string} containerRef - Ref to the container element
 * @param {Object} options - WaveSurfer options
 */
export const useWaveSurfer = (containerRef, options = {}) => {
  const wavesurferRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;

    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#ddd',
      progressColor: '#0284c7',
      cursorColor: '#0ea5e9',
      barWidth: 2,
      barRadius: 3,
      cursorWidth: 1,
      height: 80,
      barGap: 2,
      ...options,
    });

    wavesurferRef.current = wavesurfer;

    wavesurfer.on('ready', () => {
      setDuration(wavesurfer.getDuration());
    });

    wavesurfer.on('audioprocess', () => {
      setCurrentTime(wavesurfer.getCurrentTime());
    });

    wavesurfer.on('play', () => {
      setIsPlaying(true);
    });

    wavesurfer.on('pause', () => {
      setIsPlaying(false);
    });

    wavesurfer.on('finish', () => {
      setIsPlaying(false);
      setCurrentTime(0);
    });

    return () => {
      wavesurfer.destroy();
    };
  }, [containerRef, options]);

  const play = () => {
    wavesurferRef.current?.play();
  };

  const pause = () => {
    wavesurferRef.current?.pause();
  };

  const playPause = () => {
    wavesurferRef.current?.playPause();
  };

  const seekTo = (progress) => {
    wavesurferRef.current?.seekTo(progress);
  };

  const load = (url) => {
    wavesurferRef.current?.load(url);
  };

  const loadBlob = (blob) => {
    if (wavesurferRef.current) {
      const url = URL.createObjectURL(blob);
      wavesurferRef.current.load(url);
    }
  };

  return {
    wavesurfer: wavesurferRef.current,
    isPlaying,
    currentTime,
    duration,
    play,
    pause,
    playPause,
    seekTo,
    load,
    loadBlob,
  };
};

export default useWaveSurfer;
