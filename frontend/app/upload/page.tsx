'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropZone } from '@/app/components/FileDropZone';
import { ToneModal } from '@/app/components/ToneModal';
import { useFileUpload } from '@/app/hooks/useApi';
import { useModel } from '@/app/contexts/ModelContext';
import { AssemblyTone } from '@/app/types';
import { LABELS } from '@/app/constants/labels';
import { formatBytes } from '@/app/utils/helpers';

export default function UploadPage() {
  const router = useRouter();
  const { upload, uploading, error } = useFileUpload();
  const { setJobId, setModelId, setFileName, setTone } = useModel();
  const [showToneModal, setShowToneModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectingTone, setSelectingTone] = useState(false);

  const handleFileSelected = async (file: File) => {
    setSelectedFile(file);
    
    try {
      const response = await upload(file);
      setJobId(response.job_id);
      setModelId(response.model_id);
      setFileName(file.name);
      setShowToneModal(true);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  const handleToneSelected = (tone: AssemblyTone) => {
    setSelectingTone(true);
    setTone(tone);
    
    // Delay to show loading state
    setTimeout(() => {
      router.push(`/viewer/${selectedFile?.name?.split('.')[0]}`);
    }, 500);
  };

  return (
    <div className="min-h-screen bg-platinum flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-black mb-2">{LABELS.app.title}</h1>
          <p className="text-dim-grey text-lg">{LABELS.app.subtitle}</p>
        </div>

        {/* File Upload Section */}
        <div className="bg-platinum rounded-lg p-8 border-2 border-alabaster-grey">
          <h2 className="text-2xl font-bold text-black mb-6">{LABELS.upload.title}</h2>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
              <p className="text-red-700 font-semibold">{LABELS.errors.fileInvalid}</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          )}

          <FileDropZone onFile={handleFileSelected} disabled={uploading} />

          {selectedFile && !uploading && (
            <div className="mt-6 p-4 bg-alabaster-grey rounded-lg">
              <p className="text-sm text-dim-grey">
                <span className="font-semibold">Wybrany plik:</span> {selectedFile.name}
              </p>
              <p className="text-sm text-dim-grey">
                <span className="font-semibold">Rozmiar:</span> {formatBytes(selectedFile.size)}
              </p>
            </div>
          )}

          {uploading && (
            <div className="mt-6 text-center">
              <div className="inline-block">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              </div>
              <p className="text-dim-grey mt-3">{LABELS.upload.submitting}</p>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="mt-8 text-center text-sm text-dim-grey">
          <p>Obsługiwane formaty: .STEP, .STP</p>
          <p className="mt-2">Maksymalny rozmiar pliku: 50 MB</p>
        </div>
      </div>

      {/* Tone Selection Modal */}
      <ToneModal
        isOpen={showToneModal}
        onSelect={handleToneSelected}
        isLoading={selectingTone}
      />
    </div>
  );
}
