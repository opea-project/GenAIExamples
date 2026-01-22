import { configureStore } from '@reduxjs/toolkit';
import projectReducer from './slices/projectSlice';
import uploadReducer from './slices/uploadSlice';
import scriptReducer from './slices/scriptSlice';
import audioReducer from './slices/audioSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    project: projectReducer,
    upload: uploadReducer,
    script: scriptReducer,
    audio: audioReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['upload/setFile'],
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.file'],
        // Ignore these paths in the state
        ignoredPaths: ['upload.file'],
      },
    }),
});

export default store;
