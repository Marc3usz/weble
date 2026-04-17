'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { useAppStore } from '@/app/store/appStore';
import { useProgress } from '@/app/hooks/useProgress';
import apiService from '@/app/services/api';
import { AlertCircle, CheckCircle2, Upload } from 'lucide-react';

export default function UploadPage() {
  const router = useRouter();
  const {
    processing,
    setJobId,
    setModelId,
    setStatus,
    setProgress,
    setCurrentStage,
    setError: setProcessingError,
    resetProcessing,
  } = useAppStore();

  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState<string>('');

  // Stream progress
  useProgress(processing.jobId, {
    onProgress: (event) => {
      setProgress(event.progress_percent);
      setCurrentStage(event.current_stage);
    },
    onComplete: () => {
      setStatus('complete');
      // Redirect to viewer
      setTimeout(() => {
        router.push(`/viewer/${processing.modelId}`);
      }, 1500);
    },
    onError: (error) => {
      setStatus('error');
      setProcessingError(error);
    },
  });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];

      // Validate file type
      if (!file.name.toLowerCase().match(/\.(step|stp)$/)) {
        setProcessingError('Please upload a valid STEP/STP file');
        return;
      }

      try {
        setIsUploading(true);
        setFileName(file.name);
        setStatus('uploading');

        // Upload file
        const uploadResponse = await apiService.uploadStepFile(file);

        setJobId(uploadResponse.job_id);
        setModelId(uploadResponse.model_id);
        setStatus('processing');
      } catch (error) {
        setStatus('error');
        const message = error instanceof Error ? error.message : 'Upload failed';
        setProcessingError(message);
      } finally {
        setIsUploading(false);
      }
    },
    [setJobId, setModelId, setStatus, setProcessingError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'model/step': ['.step', '.stp'],
    },
    disabled: isUploading || processing.status === 'processing',
    multiple: false,
  });

  const handleReset = () => {
    resetProcessing();
    setFileName('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">WEBLE</h1>
          <p className="text-slate-600">Instrukcje montażu mebli wspierane sztuczną inteligencją</p>
        </div>

        {/* Upload Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {processing.status === 'idle' || processing.status === 'error' ? (
            <>
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-slate-300 hover:border-slate-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                <p className="text-lg font-semibold text-slate-900 mb-2">
                  Przeciągnij plik STEP/STP tutaj
                </p>
                <p className="text-sm text-slate-600 mb-4">
                  lub kliknij, aby wybrać plik (max. 50 MB)
                </p>
                <p className="text-xs text-slate-500">Obsługiwane formaty: .step, .stp</p>
              </div>

              {/* Error Message */}
              {processing.status === 'error' && processing.errorMessage && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-red-900">Błąd</p>
                    <p className="text-sm text-red-700">{processing.errorMessage}</p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Processing Status */}
              <div className="space-y-6">
                {/* File Info */}
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Przetwarzany plik:</p>
                  <p className="font-semibold text-slate-900 truncate">{fileName}</p>
                </div>

                {/* Progress Bar */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-slate-900">Postęp przetwarzania</p>
                    <p className="text-sm font-semibold text-blue-600">{processing.progress}%</p>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-full transition-all duration-300"
                      style={{ width: `${processing.progress}%` }}
                    />
                  </div>
                </div>

                {/* Current Stage */}
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Aktualny etap:</p>
                  <p className="font-semibold text-slate-900">{processing.currentStage}</p>
                </div>

                {/* Completion Message */}
                {processing.status === 'complete' && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-green-900">Przetwarzanie ukończone!</p>
                      <p className="text-sm text-green-700">Przekierowanie do podglądu...</p>
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {processing.errorMessage && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-red-900">Błąd przetwarzania</p>
                      <p className="text-sm text-red-700">{processing.errorMessage}</p>
                    </div>
                  </div>
                )}

                {/* Reset Button (on error) */}
                {processing.errorMessage && (
                  <button
                    onClick={handleReset}
                    className="w-full px-4 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors"
                  >
                    Spróbuj ponownie
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500">
          <p>WEBLE &copy; 2024 - Instrukcje montażu mebli</p>
        </div>
      </div>
    </div>
  );
}
