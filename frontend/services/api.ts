import axios from "axios";
import {
  UploadResponse,
  PartsResponse,
  AssemblyResponse,
  AssemblyStep,
  Geometry,
  ProgressEvent,
  Part,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Generate readable name for a part based on type and dimensions
function generatePartName(part: any): string {
  const { id, part_type, dimensions } = part;

  // If no type, just use the id
  if (!part_type) return id;

  // Part type mappings with readable names
  const typeMap: Record<string, string> = {
    panel: "Panel",
    fastener: "Screw",
    hardware: "Hardware",
    structural: "Bracket",
    other: "Part",
  };

  const typeName = typeMap[part_type] || part_type;

  // Try to extract dimension info for better naming
  if (dimensions && typeof dimensions === "object") {
    const dims = dimensions as Record<string, number>;
    const width = dims.width || dims.w;
    const height = dims.height || dims.h;
    const depth = dims.depth || dims.d;

    // Generate names based on type and dimensions
    if (part_type === "fastener") {
      // Fasteners: try to extract size (e.g., "M4 Screw")
      if (width) return `M${Math.round(width)} ${typeName}`;
      return typeName;
    } else if (part_type === "panel") {
      // Panels: use dimensions for description
      if (width && height)
        return `${Math.round(width)}×${Math.round(height)} ${typeName}`;
      return typeName;
    } else if (part_type === "structural") {
      // Structural: add size info
      if (width) return `${Math.round(width)}mm ${typeName}`;
      return typeName;
    }
  }

  return typeName;
}

function generateAssemblyRoleLabel(part: any): string {
  const partName = generatePartName(part);
  const dims = part.dimensions || {};
  const width = Math.round(dims.width || dims.w || 0);
  const height = Math.round(dims.height || dims.h || 0);
  const depth = Math.round(dims.depth || dims.d || 0);
  if (width && height && depth) {
    return `${partName} (${width}×${height}×${depth})`;
  }
  return partName;
}

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
    "/api/v1/step/upload",
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
    `${API_BASE_URL}/api/v1/step/progress/${jobId}/stream`
  );

  const handleMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as ProgressEvent;
      onUpdate(data);

      if (data.status === "complete" || data.status === "failed") {
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
  const response = await apiClient.post<any>(
    "/api/v1/step/parts-2d",
    { model_id: modelId }
  );

  // Transform parts to add generated names
  const transformedResponse: PartsResponse = {
    model_id: response.data.model_id,
    parts: response.data.parts.map((part: any) => ({
      ...part,
      name: generatePartName(part),
    })) as Part[],
  };

  return transformedResponse;
}

// Get assembly steps for a model
export async function getAssembly(modelId: string): Promise<AssemblyResponse> {
  const response = await apiClient.post<AssemblyResponse>(
    "/api/v1/step/assembly-analysis?force_regenerate=true",
    { model_id: modelId }
  );

  const partsResponse = await getParts(modelId);
  const partByIndex = new Map<number, Part>();
  partsResponse.parts.forEach((part, index) => {
    partByIndex.set(index, part);
  });

  const enrichedSteps: AssemblyStep[] = response.data.steps.map((step) => {
    const partRoles: Record<string, string> = {};
    if (step.part_roles) {
      Object.entries(step.part_roles).forEach(([key]) => {
        const part = partByIndex.get(Number(key));
        partRoles[key] = part ? generateAssemblyRoleLabel(part) : step.part_roles?.[key] || `Part ${key}`;
      });
    }

    return {
      ...step,
      part_roles: Object.keys(partRoles).length > 0 ? partRoles : step.part_roles,
    };
  });

  return {
    ...response.data,
    steps: enrichedSteps,
  };
}

// Get geometry (3D model)
export async function getGeometry(modelId: string): Promise<Geometry> {
  const response = await apiClient.get<any>(
    `/api/v1/step/${modelId}`
  );

  // Backend wraps geometry in response object - extract the geometry field
  return response.data.geometry || response.data;
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
