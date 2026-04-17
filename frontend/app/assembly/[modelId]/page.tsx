'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAppStore } from '@/app/store/appStore';
import apiService from '@/app/services/api';
import { AssemblyStep } from '@/app/types';
import { AssemblyInstructionsPDFDownload } from '@/app/utils/pdfExport';
import {
  AlertCircle,
  Loader2,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Download,
} from 'lucide-react';

export default function AssemblyPage() {
  const router = useRouter();
  const params = useParams();
  const modelId = params.modelId as string;

  const { model, setAssembly } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [currentStep, setCurrentStep] = useState(0);

  // Load assembly instructions on mount
  useEffect(() => {
    const loadAssembly = async () => {
      if (!modelId) return;

      try {
        setIsLoading(true);
        const response = await apiService.generateAssemblyAnalysis(modelId, false);
        setAssembly(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Błąd wczytywania instrukcji';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    if (!model.assembly) {
      loadAssembly();
    }
  }, [modelId, model.assembly, setAssembly]);

  const steps = model.assembly?.steps || [];
  const step = steps[currentStep];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Note: PDF download link is rendered separately in the header

  const handleBack = () => {
    router.push(`/parts/${modelId}`);
  };

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-4">
        <div className="text-center max-w-sm">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h3 className="font-semibold mb-2">Błąd</h3>
          <p className="text-sm text-slate-400 mb-6">{error}</p>
          <button
            onClick={handleBack}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm font-medium"
          >
            Wróć
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Instrukcja montażu</h1>
            <p className="text-sm text-slate-400 mt-1">
              {steps.length > 0
                ? `Krok ${currentStep + 1} z ${steps.length}`
                : 'Brak instrukcji'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {model.parts && model.assembly && (
              <AssemblyInstructionsPDFDownload
                fileName={`instrukcja-${modelId}`}
                parts={model.parts}
                steps={model.assembly.steps}
              />
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {isLoading && !model.assembly ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-400" />
              <p>Generowanie instrukcji montażu...</p>
            </div>
          </div>
        ) : !steps || steps.length === 0 ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p>Brak instrukcji do wyświetlenia</p>
            </div>
          </div>
        ) : (
          <>
            {/* Step Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Diagram Area */}
              <div className="lg:col-span-2">
                <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 h-96 flex items-center justify-center">
                  <div className="text-center">
                    <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400">Diagram montażu (SVG)</p>
                    <p className="text-xs text-slate-500 mt-2">
                      Wyrysowanie będzie generowane dla każdego kroku
                    </p>
                  </div>
                </div>
              </div>

              {/* Step Details */}
              <div className="space-y-4">
                {/* Step Info */}
                <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-6 border border-blue-700">
                  <h2 className="text-2xl font-bold mb-2">{step.title}</h2>
                  <p className="text-blue-200 text-sm mb-4">{step.description}</p>

                  {step.detail_description && (
                    <div className="mt-4 p-4 bg-blue-950 rounded border border-blue-700">
                      <p className="text-xs text-blue-300 leading-relaxed">
                        {step.detail_description}
                      </p>
                    </div>
                  )}
                </div>

                {/* Parts Involved */}
                <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <h3 className="font-semibold mb-3 text-sm">Części zaangażowane</h3>
                  <div className="space-y-2">
                    {step.part_indices.map((partIdx) => (
                      <div
                        key={partIdx}
                        className="p-2 bg-slate-700 rounded text-sm flex justify-between items-center"
                      >
                        <span>Część {partIdx}</span>
                        <span className="text-slate-400">
                          {step.part_roles[partIdx] || 'nieznana rola'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Assembly Sequence */}
                {step.assembly_sequence && step.assembly_sequence.length > 0 && (
                  <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                    <h3 className="font-semibold mb-3 text-sm">Sekwencja</h3>
                    <ol className="space-y-2">
                      {step.assembly_sequence.map((seq, idx) => (
                        <li key={idx} className="text-sm text-slate-300 flex gap-2">
                          <span className="font-semibold text-blue-400">{idx + 1}.</span>
                          {seq}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Tips */}
                {step.tips && step.tips.length > 0 && (
                  <div className="bg-emerald-900 bg-opacity-30 rounded-lg p-4 border border-emerald-700 border-opacity-50">
                    <h3 className="font-semibold mb-2 text-sm text-emerald-300">Wskazówki</h3>
                    <ul className="space-y-1">
                      {step.tips.map((tip, idx) => (
                        <li key={idx} className="text-xs text-emerald-200">
                          • {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings */}
                {step.warnings && step.warnings.length > 0 && (
                  <div className="bg-red-900 bg-opacity-30 rounded-lg p-4 border border-red-700 border-opacity-50">
                    <h3 className="font-semibold mb-2 text-sm text-red-300">Ostrzeżenia</h3>
                    <ul className="space-y-1">
                      {step.warnings.map((warn, idx) => (
                        <li key={idx} className="text-xs text-red-200">
                          ⚠ {warn}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Navigation */}
            <div className="flex gap-3 justify-center items-center">
              <button
                onClick={handleBack}
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-semibold flex items-center gap-2 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Wróć do części
              </button>

              <div className="flex gap-2">
                <button
                  onClick={handlePrev}
                  disabled={currentStep === 0}
                  className="p-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:opacity-50 rounded-lg transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>

                <div className="px-6 py-3 bg-slate-800 rounded-lg border border-slate-700 min-w-fit">
                  <p className="font-semibold text-center">
                    {currentStep + 1} / {steps.length}
                  </p>
                </div>

                <button
                  onClick={handleNext}
                  disabled={currentStep === steps.length - 1}
                  className="p-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:opacity-50 rounded-lg transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>

              {currentStep === steps.length - 1 && (
                <button
                  onClick={() => router.push('/upload')}
                  className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 rounded-lg font-semibold transition-all"
                >
                  Nowy projekt
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
