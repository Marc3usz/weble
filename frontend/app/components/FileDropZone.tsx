'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { LABELS } from '@/app/constants/labels';
import { validateStepFile } from '@/app/utils/helpers';

interface FileDropZoneProps {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function FileDropZone({ onFile, disabled = false }: FileDropZoneProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null);

      if (acceptedFiles.length === 0) {
        setError(LABELS.upload.error);
        return;
      }

      const file = acceptedFiles[0];

      if (!validateStepFile(file)) {
        setError('Plik musi być typu .STEP lub .STP');
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        setError(LABELS.upload.error);
        return;
      }

      onFile(file);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'model/step': ['.step', '.stp'],
    },
    disabled,
    multiple: false,
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          p-12 border-2 border-dashed rounded-lg text-center cursor-pointer transition-all
          ${isDragActive
            ? 'border-dim-grey bg-alabaster-grey'
            : 'border-alabaster-grey hover:border-dim-grey'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="space-y-2">
          <p className="text-xl font-semibold">{LABELS.upload.drag}</p>
          <p className="text-dim-grey">{LABELS.upload.size}</p>
          <button
            type="button"
            className="mt-4 px-6 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors"
          >
            {LABELS.upload.button}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-100 border-l-4 border-red-500 text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
