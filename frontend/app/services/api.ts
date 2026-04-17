import axios, { AxiosInstance } from 'axios';
import {
  UploadResponse,
  ProgressEvent,
  ModelData,
  PartsResponse,
  AssemblyResponse,
  JobStatusResponse,
} from '@/app/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Upload a STEP file for processing
   */
  async uploadStepFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<UploadResponse>('/step/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Get model data including geometry
   */
  async getModel(modelId: string): Promise<ModelData> {
    const response = await this.client.get<ModelData>(`/step/${modelId}`);
    return response.data;
  }

  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await this.client.get<JobStatusResponse>(`/jobs/${jobId}`);
    return response.data;
  }

  /**
   * Stream job progress via Server-Sent Events
   */
  streamProgress(jobId: string): EventSource {
    const url = `${API_BASE_URL}/step/progress/${jobId}/stream`;
    return new EventSource(url);
  }

  /**
   * Generate parts 2D drawings
   */
  async generateParts2D(modelId: string): Promise<PartsResponse> {
    const response = await this.client.post<PartsResponse>('/step/parts-2d', {
      model_id: modelId,
    });
    return response.data;
  }

  /**
   * Generate assembly analysis
   */
  async generateAssemblyAnalysis(
    modelId: string,
    previewOnly: boolean = false
  ): Promise<AssemblyResponse> {
    const response = await this.client.post<AssemblyResponse>(
      '/step/assembly-analysis',
      { model_id: modelId },
      {
        params: { preview_only: previewOnly },
      }
    );
    return response.data;
  }
}

export default new ApiService();
