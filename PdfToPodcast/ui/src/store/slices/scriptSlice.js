import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { scriptAPI } from '@services/api';

const initialState = {
  script: null,
  originalScript: null,
  hostVoice: 'alloy',
  guestVoice: 'echo',
  generating: false,
  updating: false,
  generationProgress: 0,
  statusMessage: '',
  error: null,
};

// Async thunks
export const generateScript = createAsyncThunk(
  'script/generateScript',
  async ({ jobId, hostVoice, guestVoice }, { rejectWithValue }) => {
    try {
      const response = await scriptAPI.generate(jobId, hostVoice, guestVoice);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to generate script');
    }
  }
);

export const pollScriptStatus = createAsyncThunk(
  'script/pollScriptStatus',
  async (jobId, { rejectWithValue, dispatch }) => {
    try {
      const response = await scriptAPI.getStatus(jobId);
      const data = response.data;

      dispatch(setGenerationProgress(data.progress || 0));
      dispatch(setStatusMessage(data.status_message || ''));

      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get status');
    }
  }
);

export const updateScript = createAsyncThunk(
  'script/updateScript',
  async ({ jobId, script }, { rejectWithValue }) => {
    try {
      const response = await scriptAPI.update(jobId, script);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update script');
    }
  }
);

const scriptSlice = createSlice({
  name: 'script',
  initialState,
  reducers: {
    setHostVoice: (state, action) => {
      state.hostVoice = action.payload;
    },
    setGuestVoice: (state, action) => {
      state.guestVoice = action.payload;
    },
    setScript: (state, action) => {
      state.script = action.payload;
    },
    setGenerationProgress: (state, action) => {
      state.generationProgress = action.payload;
    },
    setStatusMessage: (state, action) => {
      state.statusMessage = action.payload;
    },
    resetScript: (state) => {
      state.script = null;
      state.originalScript = null;
      state.generating = false;
      state.updating = false;
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
      // Generate script
      .addCase(generateScript.pending, (state) => {
        state.generating = true;
        state.generationProgress = 0;
        state.error = null;
      })
      .addCase(generateScript.fulfilled, (state, action) => {
        state.generating = false;
        state.generationProgress = 10;
        state.statusMessage = 'Script generation started';
      })
      .addCase(generateScript.rejected, (state, action) => {
        state.generating = false;
        state.error = action.payload;
      })
      // Poll status
      .addCase(pollScriptStatus.fulfilled, (state, action) => {
        const data = action.payload;
        if (data.status === 'script_generated' && data.script) {
          state.script = data.script;
          state.originalScript = JSON.parse(JSON.stringify(data.script));
          state.generating = false;
          state.generationProgress = 100;
        } else if (data.status === 'failed') {
          state.generating = false;
          state.error = data.error_message || 'Script generation failed';
        }
      })
      .addCase(pollScriptStatus.rejected, (state, action) => {
        state.generating = false;
        state.error = action.payload;
      })
      // Update script
      .addCase(updateScript.pending, (state) => {
        state.updating = true;
        state.error = null;
      })
      .addCase(updateScript.fulfilled, (state, action) => {
        state.updating = false;
        state.originalScript = JSON.parse(JSON.stringify(state.script));
      })
      .addCase(updateScript.rejected, (state, action) => {
        state.updating = false;
        state.error = action.payload;
      });
  },
});

export const {
  setHostVoice,
  setGuestVoice,
  setScript,
  setGenerationProgress,
  setStatusMessage,
  resetScript,
  clearError,
} = scriptSlice.actions;

export default scriptSlice.reducer;
