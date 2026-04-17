import { APIError, UploadResponse, JobStatusResponse, PartsResponse, AssemblyResponse, AssemblyTone } from '@/app/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to make API calls
async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new APIError(
        response.status,
        data.detail || `HTTP ${response.status}`,
        data.code
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(0, 'Network error', 'NETWORK_ERROR');
  }
}

export const api = {
  // Upload STEP file
  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/api/v1/step/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new APIError(
        response.status,
        data.detail || `HTTP ${response.status}`,
        data.code
      );
    }

    return response.json();
  },

  // Get job status
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    return apiCall<JobStatusResponse>(`/api/v1/jobs/${jobId}`);
  },

  // Get model
  getModel: async (modelId: string) => {
    return apiCall(`/api/v1/step/${modelId}`);
  },

  // Extract parts
  extractParts: async (modelId: string): Promise<PartsResponse> => {
    return apiCall<PartsResponse>('/api/v1/step/parts-2d', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId }),
    });
  },

  // Generate assembly instructions
  generateAssembly: async (
    modelId: string,
    tone: AssemblyTone,
    preview_only: boolean = false
  ): Promise<AssemblyResponse> => {
    return apiCall<AssemblyResponse>('/api/v1/step/assembly-analysis', {
      method: 'POST',
      body: JSON.stringify({
        model_id: modelId,
        tone: tone,
        preview_only: preview_only,
      }),
    });
  },

  // Health check
  healthCheck: async () => {
    return apiCall('/api/v1/health');
  },
};

// SSE subscription for progress updates
export function subscribeToProgress(
  jobId: string,
  onMessage: (data: any) => void,
  onError: (error: Error) => void
): () => void {
  const url = `${API_BASE_URL}/api/v1/step/progress/${jobId}/stream`;
  
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      onError(new Error('Failed to parse progress data'));
    }
  };

  eventSource.onerror = () => {
    eventSource.close();
    onError(new Error('SSE connection error'));
  };

  // Return unsubscribe function
  return () => {
    eventSource.close();
  };
}
