import { useEffect, useState, useCallback } from "react";
import { subscribeToProgress, getJobStatus } from "@/services/api";
import { ProgressEvent } from "@/types";
import { useAppStore } from "@/store/appStore";

interface UseProgressOptions {
  jobId: string;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

export function useProgress({
  jobId,
  onComplete,
  onError,
}: UseProgressOptions) {
  const [percentage, setPercentage] = useState(0);
  const [status, setStatus] = useState<ProgressEvent["status"]>("pending");
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const storeSetProgress = useAppStore((state) => state.setProgress);
  const storeSetJobStatus = useAppStore((state) => state.setJobStatus);
  const storeSetError = useAppStore((state) => state.setError);

  const handleUpdate = useCallback((event: ProgressEvent) => {
    setPercentage(event.percentage);
    setStatus(event.status);
    storeSetProgress(event.percentage);
    storeSetJobStatus(event.status);

    if (event.error) {
      setError(event.error);
      storeSetError(event.error);
    }
  }, [storeSetProgress, storeSetJobStatus, storeSetError]);

  const handleError = useCallback(
    (err: Error) => {
      setError(err.message);
      setIsConnected(false);
      storeSetError(err.message);
      onError?.(err);
    },
    [onError, storeSetError]
  );

  const handleComplete = useCallback(() => {
    setIsConnected(false);
    onComplete?.();
  }, [onComplete]);

  useEffect(() => {
    setIsConnected(true);

    // Try to get initial status
    getJobStatus(jobId)
      .then(handleUpdate)
      .catch((err) => {
        console.error("Failed to get initial status:", err);
      });

    // Subscribe to progress
    const unsubscribe = subscribeToProgress(
      jobId,
      handleUpdate,
      handleError,
      handleComplete
    );

    return () => {
      unsubscribe();
    };
  }, [jobId, handleUpdate, handleError, handleComplete]);

  return {
    percentage,
    status,
    error,
    isConnected,
    isComplete: status === "completed",
    isFailed: status === "failed",
  };
}
