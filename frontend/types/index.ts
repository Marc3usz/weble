// API Response Types
export interface UploadResponse {
  job_id: string;
  model_id: string;
  status: string;
}

export interface ProgressEvent {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  percentage: number;
  message?: string;
  error?: string;
}

// Parts Types
export interface Part {
  id: string;
  name: string;
  type: string;
  quantity: number;
  volume?: number;
  dimensions?: {
    width: number;
    height: number;
    depth: number;
  };
  svg_url?: string;
}

export interface PartsResponse {
  model_id: string;
  parts: Part[];
}

// Assembly Types
export interface AssemblyStep {
  step_number: number;
  title: string;
  description: string;
  parts: Array<{
    id: string;
    name: string;
    quantity: number;
  }>;
  context_part_indices?: number[];
  svg_url?: string;
  image_url?: string;
}

export interface AssemblyResponse {
  model_id: string;
  total_steps: number;
  steps: AssemblyStep[];
}

// Geometry Types
export interface Geometry {
  model_id: string;
  glb_url: string;
  scale?: number;
  center?: [number, number, number];
}

// PDF Export
export interface PDFExportOptions {
  modelId: string;
  stepIndex?: number;
  includeStepNumber?: boolean;
}

// App State Types
export interface AppState {
  currentJobId: string | null;
  currentModelId: string | null;
  progressPercentage: number;
  jobStatus: "idle" | "pending" | "processing" | "completed" | "failed";
  parts: Part[] | null;
  assembly: AssemblyStep[] | null;
  geometry: Geometry | null;
  error: string | null;

  // Actions
  setJobId: (jobId: string, modelId: string) => void;
  setProgress: (percentage: number) => void;
  setJobStatus: (status: AppState["jobStatus"]) => void;
  setParts: (parts: Part[]) => void;
  setAssembly: (assembly: AssemblyStep[]) => void;
  setGeometry: (geometry: Geometry) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}
