'use client';

import React, { createContext, useState, useContext, ReactNode } from 'react';
import { ModelContextState, Part, AssemblyStep, AssemblyTone } from '@/app/types';

const ModelContext = createContext<ModelContextState | undefined>(undefined);

export function ModelProvider({ children }: { children: ReactNode }) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [modelId, setModelId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [parts, setParts] = useState<Part[] | null>(null);
  const [assemblySteps, setAssemblySteps] = useState<AssemblyStep[] | null>(null);
  const [tone, setTone] = useState<AssemblyTone | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const value: ModelContextState = {
    jobId,
    modelId,
    fileName,
    parts,
    assemblySteps,
    tone,
    isDarkMode,
    setJobId,
    setModelId,
    setFileName,
    setParts,
    setAssemblySteps,
    setTone,
    toggleDarkMode: () => setIsDarkMode(!isDarkMode),
  };

  return (
    <ModelContext.Provider value={value}>
      {children}
    </ModelContext.Provider>
  );
}

export function useModel() {
  const context = useContext(ModelContext);
  if (context === undefined) {
    throw new Error('useModel must be used within ModelProvider');
  }
  return context;
}
