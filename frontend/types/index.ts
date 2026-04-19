// API Response Types
export interface UploadResponse {
  job_id: string;
  model_id: string;
  status: string;
}

export interface ProgressEvent {
  job_id: string;
  status: "pending" | "processing" | "complete" | "failed";
  progress_percent: number;
  current_stage?: string;
  action?: string;
  error_message?: string;
  eta_seconds?: number;
  timestamp?: string | null;
}

// Parts Types
export interface Part {
  id: string;
  part_type: string;
  quantity: number;
  volume?: number;
  dimensions?: {
    width: number;
    height: number;
    depth: number;
  };
  name?: string; // Generated at runtime based on part_type and dimensions
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
  part_indices: number[];
  part_roles?: Record<string, string>;
  context_part_indices?: number[];
  svg_diagram?: string;
  exploded_view_svg?: string;
  duration_minutes?: number;
  detail_description?: string;
  assembly_sequence?: string[];
  warnings?: string[];
  tips?: string[];
  confidence_score?: number;
  is_llm_generated?: boolean;
}

export interface AssemblyResponse {
  model_id: string;
  total_steps: number;
  steps: AssemblyStep[];
}

// Geometry Types
export interface BoundingBox {
  min: [number, number, number];
  max: [number, number, number];
}

export interface Solid {
  id?: string;
  bounding_box: BoundingBox;
}

export interface GeometryMetadata {
  solids: Solid[];
}

export interface Geometry {
  vertices: number[][];
  normals: number[][];
  indices: number[];
  metadata: GeometryMetadata;
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
  jobStatus: "idle" | "pending" | "processing" | "complete" | "failed";
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
