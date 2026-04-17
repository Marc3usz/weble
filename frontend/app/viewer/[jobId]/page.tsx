'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Canvas3D } from '@/app/components/Canvas3D';
import { ProgressBar } from '@/app/components/ProgressBar';
import { useJobProgress } from '@/app/hooks/useApi';
import { useModel } from '@/app/contexts/ModelContext';
import { api } from '@/app/services/api';
import { LABELS } from '@/app/constants/labels';
import { Geometry3D, Part } from '@/app/types';

export default function ViewerPage() {
  const params = useParams();
  const router = useRouter();
  const { modelId, jobId } = useModel();
  const { progress, error: progressError } = useJobProgress(jobId);
  const [geometry, setGeometry] = useState<Geometry3D | null>(null);
  const [tabIndex, setTabIndex] = useState<number>(0);
  const [parts, setParts] = useState<Part[] | null>(null);

  // Fetch geometry when job completes
  useEffect(() => {
    if (progress.status === 'complete' && modelId) {
      fetchModelData();
    }
  }, [progress.status, modelId]);

  const fetchModelData = async () => {
    try {
      const modelData = await api.getModel(modelId!);
      if (modelData.geometry_loaded && modelData.geometry) {
        setGeometry(modelData.geometry);
      }

      // Fetch parts
      const partsData = await api.extractParts(modelId!);
      setParts(partsData.parts);
    } catch (err) {
      console.error('Failed to fetch model data:', err);
    }
  };

  if (!jobId || !modelId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-platinum">
        <div className="text-center">
          <p className="text-red-600 font-semibold">{LABELS.errors.apiError}</p>
          <button
            onClick={() => router.push('/upload')}
            className="mt-4 px-6 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors"
          >
            {LABELS.errors.goHome}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-platinum text-black">
      {/* Main Container */}
      <div className="flex h-screen gap-4 p-4">
        {/* Left: 3D Canvas (50%) */}
        <div className="w-1/2 bg-alabaster-grey rounded-lg overflow-hidden border-2 border-alabaster-grey">
          {geometry ? (
            <Canvas3D geometry={geometry} />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-platinum">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
                <p className="text-dim-grey">{LABELS.viewer.progress.replace('{{percent}}', progress.percent.toString())}</p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Progress & Tabs (50%) */}
        <div className="w-1/2 flex flex-col gap-4">
          {/* Progress Section */}
          <div className="bg-platinum border-2 border-alabaster-grey rounded-lg p-6">
            <h2 className="text-xl font-bold text-black mb-4">{LABELS.viewer.title}</h2>
            <ProgressBar
              percent={progress.percent}
              stage={progress.stage}
              action={progress.action}
              eta={progress.eta}
            />

            {progressError && (
              <div className="mt-4 p-3 bg-red-100 border-l-4 border-red-500 text-red-700">
                {progressError}
              </div>
            )}
          </div>

          {/* Tabs */}
          {progress.percent > 0 && (
            <div className="bg-platinum border-2 border-alabaster-grey rounded-lg p-4 flex-1 overflow-hidden flex flex-col">
              {/* Tab buttons */}
              <div className="flex gap-2 mb-4 border-b-2 border-alabaster-grey pb-2">
                <button
                  onClick={() => setTabIndex(0)}
                  className={`px-4 py-2 font-semibold transition-colors ${
                    tabIndex === 0
                      ? 'text-black border-b-2 border-black'
                      : 'text-dim-grey hover:text-black'
                  }`}
                >
                  {LABELS.viewer.tabs.overview}
                </button>
                <button
                  onClick={() => setTabIndex(1)}
                  disabled={!parts}
                  className={`px-4 py-2 font-semibold transition-colors disabled:opacity-50 ${
                    tabIndex === 1
                      ? 'text-black border-b-2 border-black'
                      : 'text-dim-grey hover:text-black'
                  }`}
                >
                  {LABELS.viewer.tabs.parts}
                </button>
              </div>

              {/* Tab content */}
              <div className="flex-1 overflow-y-auto">
                {tabIndex === 0 && (
                  <div className="space-y-3 text-sm">
                    <p><span className="font-semibold">Status:</span> {progress.status}</p>
                    <p><span className="font-semibold">Postęp:</span> {progress.percent}%</p>
                    <p><span className="font-semibold">Etap:</span> {progress.stage}</p>
                    {progress.eta > 0 && (
                      <p><span className="font-semibold">ETA:</span> {progress.eta}s</p>
                    )}
                  </div>
                )}

                {tabIndex === 1 && parts && (
                  <div className="space-y-2">
                    {Array.isArray(parts) && parts.map((part: Part, idx: number) => (
                      <div
                        key={idx}
                        className="p-2 bg-alabaster-grey rounded border-l-4 border-black"
                      >
                        <p className="font-semibold text-sm">{part.id}</p>
                        <p className="text-xs text-dim-grey">{part.part_type} × {part.quantity}</p>
                      </div>
                    ))}
                  </div>
                )}

                {tabIndex === 1 && !parts && (
                  <p className="text-dim-grey text-sm">{LABELS.common.loading}</p>
                )}
              </div>

              {/* Navigation button */}
              {progress.status === 'complete' && tabIndex === 0 && (
                <button
                  onClick={() => router.push(`/assembly/${modelId}`)}
                  className="mt-4 w-full py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors font-semibold"
                >
                  {LABELS.viewer.next}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
