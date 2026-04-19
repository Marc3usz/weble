import { create } from "zustand";
import { AppState, Part, AssemblyStep, Geometry } from "@/types";

export const useAppStore = create<AppState>((set) => ({
  currentJobId: null,
  currentModelId: null,
  progressPercentage: 0,
  jobStatus: "idle",
  parts: null,
  assembly: null,
  geometry: null,
  error: null,

  setJobId: (jobId: string, modelId: string) =>
    set({
      currentJobId: jobId,
      currentModelId: modelId,
      jobStatus: "pending",
      error: null,
    }),

  setProgress: (percentage: number) =>
    set({
      progressPercentage: Math.min(100, Math.max(0, percentage)),
    }),

  setJobStatus: (status: AppState["jobStatus"]) =>
    set({ jobStatus: status }),

  setParts: (parts: Part[]) =>
    set({ parts }),

  setAssembly: (assembly: AssemblyStep[]) =>
    set({ assembly }),

  setGeometry: (geometry: Geometry) =>
    set({ geometry }),

  setError: (error: string | null) =>
    set({ error }),

  reset: () =>
    set({
      currentJobId: null,
      currentModelId: null,
      progressPercentage: 0,
      jobStatus: "idle",
      parts: null,
      assembly: null,
      geometry: null,
      error: null,
    }),
}));
