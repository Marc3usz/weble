import { useEffect, useRef, useState } from 'react';
import { ProgressEvent } from '@/app/types';
import apiService from '@/app/services/api';

interface UseProgressOptions {
  onProgress?: (event: ProgressEvent) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useProgress(jobId: string | null, options: UseProgressOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;

    try {
      const eventSource = apiService.streamProgress(jobId);
      eventSourceRef.current = eventSource;
      setIsConnected(true);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as ProgressEvent;
          options.onProgress?.(data);

          if (data.status === 'complete' || data.status === 'failed') {
            if (data.status === 'complete') {
              options.onComplete?.();
            } else {
              options.onError?.(data.error_message || 'Processing failed');
            }
            eventSource.close();
            setIsConnected(false);
          }
        } catch (error) {
          console.error('Error parsing progress event:', error);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        eventSource.close();
        options.onError?.('Connection lost');
      };

      return () => {
        eventSource.close();
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Error setting up progress stream:', error);
      options.onError?.('Failed to connect to progress stream');
      setIsConnected(false);
    }
  }, [jobId, options]);

  return { isConnected };
}
