import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { audioAPI } from '@services/api';

const initialState = {
  audioUrl: null,
  audioBlob: null,
  generating: false,
  generationProgress: 0,
  statusMessage: '',
  error: null,
};

// Async thunks
export const generateAudio = createAsyncThunk(
  'audio/generateAudio',
  async (jobId, { rejectWithValue }) => {
    try {
      const response = await audioAPI.generate(jobId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to generate audio');
    }
  }
);

export const pollAudioStatus = createAsyncThunk(
  'audio/pollAudioStatus',
  async (jobId, { rejectWithValue, dispatch }) => {
    try {
      const response = await audioAPI.getStatus(jobId);
      const data = response.data;

      dispatch(setGenerationProgress(data.progress || 0));
      dispatch(setStatusMessage(data.status_message || ''));

      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get status');
    }
  }
);

export const downloadAudio = createAsyncThunk(
  'audio/downloadAudio',
  async (jobId, { rejectWithValue }) => {
    try {
      const blob = await audioAPI.download(jobId);
      return blob;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to download audio');
    }
  }
);

const audioSlice = createSlice({
  name: 'audio',
  initialState,
  reducers: {
    setGenerationProgress: (state, action) => {
      state.generationProgress = action.payload;
    },
    setStatusMessage: (state, action) => {
      state.statusMessage = action.payload;
    },
    resetAudio: (state) => {
      state.audioUrl = null;
      state.audioBlob = null;
      state.generating = false;
      state.generationProgress = 0;
      state.statusMessage = '';
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Generate audio
      .addCase(generateAudio.pending, (state) => {
        state.generating = true;
        state.generationProgress = 0;
        state.error = null;
      })
      .addCase(generateAudio.fulfilled, (state, action) => {
        state.generating = false;
        state.generationProgress = 10;
        state.statusMessage = 'Audio generation started';
      })
      .addCase(generateAudio.rejected, (state, action) => {
        state.generating = false;
        state.error = action.payload;
      })
      // Poll status
      .addCase(pollAudioStatus.fulfilled, (state, action) => {
        const data = action.payload;
        if (data.status === 'completed' && data.audio_url) {
          state.audioUrl = data.audio_url;
          state.generating = false;
          state.generationProgress = 100;
        } else if (data.status === 'audio_generated') {
          // Audio generation complete (even if URL is null for TTS not available)
          state.audioUrl = data.audio_url || 'placeholder';
          state.generating = false;
          state.generationProgress = 100;
          state.statusMessage = data.audio_status || 'Audio generation complete';
        } else if (data.status === 'failed') {
          state.generating = false;
          state.error = data.error_message || 'Audio generation failed';
        }
      })
      .addCase(pollAudioStatus.rejected, (state, action) => {
        state.generating = false;
        state.error = action.payload;
      })
      // Download audio
      .addCase(downloadAudio.fulfilled, (state, action) => {
        state.audioBlob = action.payload;
      })
      .addCase(downloadAudio.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export const {
  setGenerationProgress,
  setStatusMessage,
  resetAudio,
  clearError,
} = audioSlice.actions;

export default audioSlice.reducer;
