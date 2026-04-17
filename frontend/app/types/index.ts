// Type definitions matching backend schemas
export enum PartType {
  PANEL = 'panel',
  HARDWARE = 'hardware',
  FASTENER = 'fastener',
  STRUCTURAL = 'structural',
  OTHER = 'other',
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETE = 'complete',
  FAILED = 'failed',
}

export enum AssemblyTone {
  IKEA = 'ikea',
  TECHNICAL = 'technical',
  BEGINNER = 'beginner',
}

// API Response types
export interface UploadResponse {
  job_id: string;
  model_id: string;
  status: string;
  estimated_time_seconds: number;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  progress_percent: number;
  current_stage: string;
  action: string;
  eta_seconds: number;
  error_message: string | null;
}

export interface ProgressStreamResponse {
  job_id: string;
  status: string;
  progress_percent: number;
  current_stage: string;
  action: string;
  eta_seconds: number;
  timestamp: string;
}

export interface Part {
  id: string;
  part_type: PartType;
  quantity: number;
  volume: number;
  dimensions: {
    width: number;
    height: number;
    depth: number;
  };
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
  detail_description: string;
  part_indices: number[];
  part_roles: Record<number, string>;
  context_part_indices: number[];
  svg_diagram: string;
  exploded_view_svg: string;
  assembly_sequence: string[];
  warnings: string[];
  tips: string[];
  duration_minutes: number;
  confidence_score: number;
  is_llm_generated: boolean;
}

export interface AssemblyResponse {
  model_id: string;
  steps: AssemblyStep[];
  tone?: AssemblyTone;
}

// Context and State types
export interface ModelContextState {
  jobId: string | null;
  modelId: string | null;
  fileName: string | null;
  parts: Part[] | null;
  assemblySteps: AssemblyStep[] | null;
  tone: AssemblyTone | null;
  isDarkMode: boolean;
  setJobId: (id: string) => void;
  setModelId: (id: string) => void;
  setFileName: (name: string) => void;
  setParts: (parts: Part[]) => void;
  setAssemblySteps: (steps: AssemblyStep[]) => void;
  setTone: (tone: AssemblyTone) => void;
  toggleDarkMode: () => void;
}

export interface ProgressState {
  percent: number;
  stage: string;
  action: string;
  eta: number;
  status: ProcessingStatus;
}

export interface ErrorState {
  message: string;
  code?: string;
  retry?: () => void;
}

// API Error
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}
