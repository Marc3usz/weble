'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useModel } from '@/app/contexts/ModelContext';
import { useAssemblySteps } from '@/app/hooks/useApi';
import { Canvas3D } from '@/app/components/Canvas3D';
import { PDFExportModal } from '@/app/components/PDFExportModal';
import { LABELS } from '@/app/constants/labels';
import { formatDuration, formatConfidence } from '@/app/utils/helpers';

export default function AssemblyPage() {
  const params = useParams();
  const router = useRouter();
  const { tone, modelId } = useModel();
  const { steps, loading, error } = useAssemblySteps(modelId, tone);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPDFModalOpen, setIsPDFModalOpen] = useState<boolean>(false);

  useEffect(() => {
    if (!modelId || !tone) {
      router.push('/upload');
    }
  }, [modelId, tone, router]);

  if (!steps || loading) {
    return (
      <div className="min-h-screen bg-platinum flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-dim-grey">{LABELS.common.loading}</p>
        </div>
      </div>
    );
  }

  if (error || !Array.isArray(steps) || steps.length === 0) {
    return (
      <div className="min-h-screen bg-platinum flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-red-600 font-semibold mb-4">{LABELS.errors.apiError}</p>
          <button
            onClick={() => router.push('/upload')}
            className="px-6 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors"
          >
            {LABELS.errors.goHome}
          </button>
        </div>
      </div>
    );
  }

  const currentStep = steps[currentStepIndex];
  const totalSteps = steps.length;

  return (
    <div className="min-h-screen bg-platinum text-black">
      {/* Header */}
      <div className="bg-alabaster-grey border-b-2 border-alabaster-grey px-8 py-4">
        <h1 className="text-2xl font-bold">{LABELS.assembly.title}</h1>
        <p className="text-dim-grey text-sm">
          {LABELS.assembly.step} {currentStepIndex + 1} {LABELS.assembly.of} {totalSteps}
        </p>
      </div>

      {/* Main Content */}
      <div className="flex gap-4 p-4 h-[calc(100vh-100px)]">
        {/* Left Sidebar: Parts (20%) */}
        <div className="w-1/5 bg-platinum border-2 border-alabaster-grey rounded-lg p-4 overflow-y-auto">
          <h3 className="font-semibold text-black mb-3">{LABELS.assembly.partsForThisStep}</h3>
          <div className="space-y-2 mb-4">
            {currentStep.part_indices?.map((idx: number) => (
              <div key={idx} className="p-2 bg-alabaster-grey rounded border-l-4 border-black text-sm">
                <p className="font-semibold">Part {idx}</p>
                <p className="text-dim-grey text-xs">
                  {currentStep.part_roles?.[idx] || 'Unknown'}
                </p>
              </div>
            ))}
          </div>

          <div className="border-t-2 border-alabaster-grey pt-4">
            <h4 className="font-semibold text-black mb-3 text-sm">{LABELS.assembly.previouslyAssembled}</h4>
            <div className="space-y-2">
              {currentStep.context_part_indices?.map((idx) => (
                <div key={idx} className="p-2 bg-alabaster-grey rounded opacity-60 text-sm">
                  <p className="font-semibold">Part {idx}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center: Step Content (60%) */}
        <div className="w-3/5 flex flex-col gap-4">
          {/* Title */}
          <div className="bg-alabaster-grey border-2 border-alabaster-grey rounded-lg p-4">
            <h2 className="text-2xl font-bold text-black mb-1">{currentStep.title}</h2>
            <p className="text-dim-grey text-sm">
              {currentStep.is_llm_generated
                ? LABELS.assembly.llmGenerated
                : LABELS.assembly.rulesGenerated}
            </p>
          </div>

          {/* Exploded View SVG or placeholder */}
          <div className="bg-platinum border-2 border-alabaster-grey rounded-lg p-4 flex-1 flex items-center justify-center">
            {currentStep.exploded_view_svg ? (
              <div
                dangerouslySetInnerHTML={{ __html: currentStep.exploded_view_svg }}
                className="w-full h-full"
              />
            ) : (
              <div className="text-center text-dim-grey">
                <p className="text-sm">SVG View coming soon</p>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentStepIndex(Math.max(0, currentStepIndex - 1))}
              disabled={currentStepIndex === 0}
              className="px-6 py-2 bg-alabaster-grey text-black rounded-lg hover:bg-dim-grey disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {LABELS.assembly.previous}
            </button>

            {/* Step selector dropdown */}
            <select
              value={currentStepIndex}
              onChange={(e) => setCurrentStepIndex(parseInt(e.target.value))}
              className="flex-1 px-4 py-2 bg-alabaster-grey text-black rounded-lg border-2 border-alabaster-grey focus:border-dim-grey"
            >
              {steps.map((_, idx) => (
                <option key={idx} value={idx}>
                  {LABELS.assembly.step} {idx + 1}: {steps[idx].title}
                </option>
              ))}
            </select>

            <button
              onClick={() => setCurrentStepIndex(Math.min(totalSteps - 1, currentStepIndex + 1))}
              disabled={currentStepIndex === totalSteps - 1}
              className="px-6 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {LABELS.assembly.next}
            </button>
          </div>
        </div>

        {/* Right Sidebar: Details (20%) */}
        <div className="w-1/5 bg-platinum border-2 border-alabaster-grey rounded-lg p-4 overflow-y-auto space-y-4">
          {/* Description */}
          <div>
            <h4 className="font-semibold text-black mb-2 text-sm">{LABELS.assembly.description}</h4>
            <p className="text-sm text-dim-grey">{currentStep.description}</p>
          </div>

          {/* Detailed Description (LLM-generated) */}
          {currentStep.detail_description && (
            <div>
              <h4 className="font-semibold text-black mb-2 text-sm">{LABELS.assembly.detailedDescription}</h4>
              <p className="text-sm text-dim-grey">{currentStep.detail_description}</p>
            </div>
          )}

          {/* Sequence */}
          {currentStep.assembly_sequence && currentStep.assembly_sequence.length > 0 && (
            <div>
              <h4 className="font-semibold text-black mb-2 text-sm">{LABELS.assembly.sequence}</h4>
              <ol className="list-decimal list-inside space-y-1">
                {currentStep.assembly_sequence.map((action, idx) => (
                  <li key={idx} className="text-sm text-dim-grey">
                    {action}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Warnings */}
          {currentStep.warnings && currentStep.warnings.length > 0 && (
            <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded">
              <h4 className="font-semibold text-red-700 mb-2 text-sm">⚠️ {LABELS.assembly.warnings}</h4>
              <ul className="space-y-1">
                {currentStep.warnings.map((warning, idx) => (
                  <li key={idx} className="text-xs text-red-600">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Tips */}
          {currentStep.tips && currentStep.tips.length > 0 && (
            <div className="bg-blue-50 border-l-4 border-blue-500 p-3 rounded">
              <h4 className="font-semibold text-blue-700 mb-2 text-sm">💡 {LABELS.assembly.tips}</h4>
              <ul className="space-y-1">
                {currentStep.tips.map((tip, idx) => (
                  <li key={idx} className="text-xs text-blue-600">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Duration & Confidence */}
          <div className="border-t-2 border-alabaster-grey pt-3 space-y-2">
            {currentStep.duration_minutes > 0 && (
              <div>
                <p className="text-xs text-dim-grey">
                  <span className="font-semibold">⏱️ {LABELS.assembly.duration}:</span>{' '}
                  {formatDuration(currentStep.duration_minutes)}
                </p>
              </div>
            )}
            <div>
              <p className="text-xs text-dim-grey">
                <span className="font-semibold">{LABELS.assembly.confidence}:</span>{' '}
                {formatConfidence(currentStep.confidence_score)}
              </p>
            </div>
          </div>

          {/* Export buttons */}
          <div className="border-t-2 border-alabaster-grey pt-3 space-y-2">
            <button
              onClick={() => setIsPDFModalOpen(true)}
              className="w-full py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors text-sm font-semibold"
            >
              {LABELS.assembly.export}
            </button>
            <button
              onClick={() => window.print()}
              className="w-full py-2 bg-alabaster-grey text-black rounded-lg hover:bg-rosy-granite transition-colors text-sm font-semibold"
            >
              {LABELS.assembly.print}
            </button>
          </div>
        </div>
      </div>

      {/* PDF Export Modal */}
      <PDFExportModal
        isOpen={isPDFModalOpen}
        onClose={() => setIsPDFModalOpen(false)}
        step={currentStep}
        modelId={modelId || undefined}
      />
    </div>
  );
}
