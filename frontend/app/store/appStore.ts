import { create } from 'zustand';
import { ProcessingState, ModelState, Geometry, Part, AssemblyResponse } from '@/app/types';

interface AppStore {
  // Processing state
  processing: ProcessingState;
  setJobId: (jobId: string) => void;
  setModelId: (modelId: string) => void;
  setStatus: (status: ProcessingState['status']) => void;
  setProgress: (progress: number) => void;
  setCurrentStage: (stage: string) => void;
  setError: (error?: string) => void;
  resetProcessing: () => void;

  // Model state
  model: ModelState;
  setGeometry: (geometry: Geometry) => void;
  setParts: (parts: Part[]) => void;
  setAssembly: (assembly: AssemblyResponse) => void;
  setModelLoading: (loading: boolean) => void;
  setModelError: (error?: string) => void;
  resetModel: () => void;

  // Navigation
  currentView: 'upload' | 'viewer' | 'parts' | 'assembly';
  setCurrentView: (view: 'upload' | 'viewer' | 'parts' | 'assembly') => void;
}

const initialProcessingState: ProcessingState = {
  jobId: null,
  modelId: null,
  status: 'idle',
  progress: 0,
  currentStage: '',
};

const initialModelState: ModelState = {
  modelId: null,
  isLoading: false,
};

export const useAppStore = create<AppStore>((set) => ({
  // Processing state
  processing: initialProcessingState,
  setJobId: (jobId) =>
    set((state) => ({
      processing: { ...state.processing, jobId },
    })),
  setModelId: (modelId) =>
    set((state) => ({
      processing: { ...state.processing, modelId },
    })),
  setStatus: (status) =>
    set((state) => ({
      processing: { ...state.processing, status },
    })),
  setProgress: (progress) =>
    set((state) => ({
      processing: { ...state.processing, progress },
    })),
  setCurrentStage: (currentStage) =>
    set((state) => ({
      processing: { ...state.processing, currentStage },
    })),
  setError: (errorMessage) =>
    set((state) => ({
      processing: { ...state.processing, errorMessage },
    })),
  resetProcessing: () => set({ processing: initialProcessingState }),

  // Model state
  model: initialModelState,
  setGeometry: (geometry) =>
    set((state) => ({
      model: { ...state.model, geometry },
    })),
  setParts: (parts) =>
    set((state) => ({
      model: { ...state.model, parts },
    })),
  setAssembly: (assembly) =>
    set((state) => ({
      model: { ...state.model, assembly },
    })),
  setModelLoading: (isLoading) =>
    set((state) => ({
      model: { ...state.model, isLoading },
    })),
  setModelError: (error) =>
    set((state) => ({
      model: { ...state.model, error },
    })),
  resetModel: () => set({ model: initialModelState }),

  // Navigation
  currentView: 'upload',
  setCurrentView: (currentView) => set({ currentView }),
}));
