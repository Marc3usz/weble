import axios from "axios";
import {
  UploadResponse,
  PartsResponse,
  AssemblyResponse,
  Geometry,
  ProgressEvent,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Upload a STEP file
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<UploadResponse>(
    "/api/v1/jobs/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

// Get progress updates via SSE
export function subscribeToProgress(
  jobId: string,
  onUpdate: (event: ProgressEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void
): () => void {
  const eventSource = new EventSource(
    `${API_BASE_URL}/api/v1/jobs/${jobId}/progress`
  );

  const handleMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as ProgressEvent;
      onUpdate(data);

      if (data.status === "completed" || data.status === "failed") {
        onComplete();
      }
    } catch (error) {
      onError(new Error("Failed to parse progress event"));
    }
  };

  const handleError = () => {
    onError(new Error("SSE connection lost"));
    eventSource.close();
  };

  eventSource.addEventListener("message", handleMessage);
  eventSource.addEventListener("error", handleError);

  // Return cleanup function
  return () => {
    eventSource.close();
  };
}

// Get parts for a model
export async function getParts(modelId: string): Promise<PartsResponse> {
  const response = await apiClient.post<PartsResponse>(
    "/api/v1/step/parts-2d",
    { model_id: modelId }
  );

  return response.data;
}

// Get assembly steps for a model
export async function getAssembly(modelId: string): Promise<AssemblyResponse> {
  const response = await apiClient.post<AssemblyResponse>(
    "/api/v1/step/assembly-analysis",
    { model_id: modelId }
  );

  return response.data;
}

// Get geometry (3D model)
export async function getGeometry(modelId: string): Promise<Geometry> {
  const response = await apiClient.get<Geometry>(
    `/api/v1/models/${modelId}/geometry`
  );

  return response.data;
}

// Export assembly as PDF
export async function exportAssemblyPDF(
  modelId: string,
  stepIndex?: number
): Promise<Blob> {
  const response = await apiClient.post(
    "/api/v1/step/export-pdf",
    {
      model_id: modelId,
      step_index: stepIndex,
    },
    {
      responseType: "blob",
    }
  );

  return response.data;
}

// Check job status
export async function getJobStatus(jobId: string): Promise<ProgressEvent> {
  const response = await apiClient.get<ProgressEvent>(
    `/api/v1/jobs/${jobId}/status`
  );

  return response.data;
}

export default apiClient;
