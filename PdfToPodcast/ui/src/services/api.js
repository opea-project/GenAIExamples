import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes for long-running operations
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Upload API
export const uploadAPI = {
  uploadFile: (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        if (onProgress) onProgress(percentCompleted);
      },
    });
  },
};

// Script API
export const scriptAPI = {
  generate: (jobId, hostVoice, guestVoice) => {
    return apiClient.post('/api/generate-script', {
      job_id: jobId,
      host_voice: hostVoice,
      guest_voice: guestVoice,
    });
  },

  update: (jobId, script) => {
    return apiClient.put(`/api/script/${jobId}`, {
      script,
    });
  },

  getStatus: (jobId) => {
    return apiClient.get(`/api/job/${jobId}`);
  },
};

// Audio API
export const audioAPI = {
  generate: (jobId, script) => {
    return apiClient.post('/api/generate-audio', {
      job_id: jobId,
      script: script,
    });
  },

  getStatus: (jobId) => {
    return apiClient.get(`/api/job/${jobId}`);
  },

  download: async (jobId) => {
    const response = await apiClient.get(`/api/download/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Voice API
export const voiceAPI = {
  getAll: () => {
    return apiClient.get('/api/voices');
  },

  getSample: (voiceId) => {
    return apiClient.get(`/api/voice/sample/${voiceId}`, {
      responseType: 'blob',
    });
  },
};

// Project API (for future use)
export const projectAPI = {
  getAll: () => {
    return apiClient.get('/api/projects');
  },

  getById: (id) => {
    return apiClient.get(`/api/projects/${id}`);
  },

  create: (data) => {
    return apiClient.post('/api/projects', data);
  },

  update: (id, data) => {
    return apiClient.put(`/api/projects/${id}`, data);
  },

  delete: (id) => {
    return apiClient.delete(`/api/projects/${id}`);
  },
};

// Job API
export const jobAPI = {
  getStatus: (jobId) => {
    return apiClient.get(`/api/job/${jobId}`);
  },

  cancel: (jobId) => {
    return apiClient.post(`/api/job/${jobId}/cancel`);
  },
};

// Convenience exports for backward compatibility
export const uploadPDF = (file, onProgress) => {
  return uploadAPI.uploadFile(file, onProgress).then(res => res.data);
};

export const getVoices = () => {
  return voiceAPI.getAll().then(res => res.data);
};

export const generateScript = (jobId, hostVoice, guestVoice) => {
  return scriptAPI.generate(jobId, hostVoice, guestVoice).then(res => res.data);
};

export const generateAudio = (jobId, script) => {
  return audioAPI.generate(jobId, script).then(res => res.data);
};

export const getJobStatus = (jobId) => {
  return jobAPI.getStatus(jobId).then(res => res.data);
};

export const downloadAudio = (jobId) => {
  return audioAPI.download(jobId);
};

export default apiClient;
