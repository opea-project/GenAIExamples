import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { uploadAPI } from '@services/api';

const initialState = {
  file: null,
  jobId: null,
  uploadProgress: 0,
  uploading: false,
  uploadComplete: false,
  error: null,
};

// Async thunks
export const uploadPDF = createAsyncThunk(
  'upload/uploadPDF',
  async (file, { rejectWithValue, dispatch }) => {
    try {
      const response = await uploadAPI.uploadFile(file, (progress) => {
        dispatch(setUploadProgress(progress));
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to upload PDF');
    }
  }
);

const uploadSlice = createSlice({
  name: 'upload',
  initialState,
  reducers: {
    setFile: (state, action) => {
      state.file = action.payload;
      state.error = null;
    },
    setUploadProgress: (state, action) => {
      state.uploadProgress = action.payload;
    },
    resetUpload: (state) => {
      state.file = null;
      state.jobId = null;
      state.uploadProgress = 0;
      state.uploading = false;
      state.uploadComplete = false;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadPDF.pending, (state) => {
        state.uploading = true;
        state.uploadComplete = false;
        state.error = null;
      })
      .addCase(uploadPDF.fulfilled, (state, action) => {
        state.uploading = false;
        state.uploadComplete = true;
        state.jobId = action.payload.job_id;
        state.uploadProgress = 100;
      })
      .addCase(uploadPDF.rejected, (state, action) => {
        state.uploading = false;
        state.uploadComplete = false;
        state.error = action.payload;
        state.uploadProgress = 0;
      });
  },
});

export const { setFile, setUploadProgress, resetUpload, clearError } = uploadSlice.actions;
export default uploadSlice.reducer;
