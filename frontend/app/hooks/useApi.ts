'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api, subscribeToProgress } from '@/app/services/api';
import { JobStatusResponse, ProgressStreamResponse, APIError } from '@/app/types';

// Hook for tracking job progress via SSE
export function useJobProgress(jobId: string | null) {
  const [progress, setProgress] = useState({
    percent: 0,
    stage: '',
    action: '',
    eta: 0,
    status: 'pending',
  });
  const [error, setError] = useState<string | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Subscribe to SSE
    unsubscribeRef.current = subscribeToProgress(
      jobId,
      (data: ProgressStreamResponse) => {
        setProgress({
          percent: data.progress_percent,
          stage: data.current_stage,
          action: data.action,
          eta: data.eta_seconds,
          status: data.status,
        });
        setError(null);
      },
      (err: Error) => {
        setError(err.message);
        // Fall back to polling on SSE error
        startPolling();
      }
    );

    const startPolling = () => {
      const interval = setInterval(async () => {
        try {
          const status = await api.getJobStatus(jobId);
          setProgress({
            percent: status.progress_percent,
            stage: status.current_stage,
            action: status.action,
            eta: status.eta_seconds,
            status: status.status,
          });
          
          if (status.status === 'complete' || status.status === 'failed') {
            clearInterval(interval);
          }
          
          if (status.error_message) {
            setError(status.error_message);
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      }, 2000);

      return () => clearInterval(interval);
    };

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [jobId]);

  return { progress, error };
}

// Hook for file upload
export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const upload = useCallback(async (file: File) => {
    setUploading(true);
    setError(null);
    
    try {
      setUploadedFile(file);
      const response = await api.uploadFile(file);
      return response;
    } catch (err) {
      const errorMsg = err instanceof APIError ? err.message : 'Upload failed';
      setError(errorMsg);
      throw err;
    } finally {
      setUploading(false);
    }
  }, []);

  return { uploading, error, uploadedFile, upload };
}

// Hook for fetching parts
export function useParts(modelId: string | null) {
  const [parts, setParts] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!modelId) return;

    const fetchParts = async () => {
      setLoading(true);
      try {
        const response = await api.extractParts(modelId);
        setParts(response.parts);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch parts');
      } finally {
        setLoading(false);
      }
    };

    fetchParts();
  }, [modelId]);

  return { parts, loading, error };
}

// Hook for fetching assembly steps
export function useAssemblySteps(modelId: string | null, tone: string | null) {
  const [steps, setSteps] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!modelId || !tone) return;

    const fetchSteps = async () => {
      setLoading(true);
      try {
        const response = await api.generateAssembly(modelId, tone as any);
        setSteps(response.steps);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch assembly steps');
      } finally {
        setLoading(false);
      }
    };

    fetchSteps();
  }, [modelId, tone]);

  return { steps, loading, error };
}
