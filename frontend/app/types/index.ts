// API Response Types
export interface UploadResponse {
  job_id: string;
  model_id: string;
  status: string;
  estimated_time_seconds: number;
}

export interface ProgressEvent {
  job_id: string;
  status: string;
  progress_percent: number;
  current_stage: string;
  action: string;
  eta_seconds: number;
  error_message?: string;
  timestamp?: string;
}

export interface Geometry {
  vertices: number[][];
  normals: number[][];
  indices: number[];
  metadata?: Record<string, any>;
}

export interface ModelData {
  status: string;
  model_id: string;
  file_name: string;
  file_size: number;
  geometry_loaded: boolean;
  geometry?: Geometry;
}

export interface Part {
  id: string;
  part_type: string;
  quantity: number;
  volume: number;
  dimensions: Record<string, number>;
}

export interface PartsResponse {
  model_id: string;
  parts: Part[];
  total_parts: number;
}

export interface AssemblyStep {
  step_number: number;
  title: string;
  description: string;
  detail_description?: string;
  part_indices: number[];
  part_roles: Record<number, string>;
  context_part_indices: number[];
  duration_minutes: number;
  assembly_sequence?: string[];
  warnings?: string[];
  tips?: string[];
  confidence_score?: number;
  is_llm_generated?: boolean;
}

export interface AssemblyResponse {
  model_id: string;
  steps: AssemblyStep[];
  total_steps: number;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  progress_percent: number;
  current_stage: string;
  action?: string;
  eta_seconds?: number;
  error_message?: string;
}

// Application State Types
export interface ProcessingState {
  jobId: string | null;
  modelId: string | null;
  status: 'idle' | 'uploading' | 'processing' | 'complete' | 'error';
  progress: number;
  currentStage: string;
  errorMessage?: string;
}

export interface ModelState {
  modelId: string | null;
  geometry?: Geometry;
  parts?: Part[];
  assembly?: AssemblyResponse;
  isLoading: boolean;
  error?: string;
}
