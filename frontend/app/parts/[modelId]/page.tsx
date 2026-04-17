'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAppStore } from '@/app/store/appStore';
import apiService from '@/app/services/api';
import { Part } from '@/app/types';
import { AlertCircle, Loader2, ArrowLeft, ArrowRight } from 'lucide-react';

export default function PartsPage() {
  const router = useRouter();
  const params = useParams();
  const modelId = params.modelId as string;

  const { model, setParts } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [selectedPartId, setSelectedPartId] = useState<string | null>(null);

  // Load parts on mount
  useEffect(() => {
    const loadParts = async () => {
      if (!modelId) return;

      try {
        setIsLoading(true);
        const response = await apiService.generateParts2D(modelId);
        setParts(response.parts);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Błąd wczytywania części';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    if (!model.parts) {
      loadParts();
    }
  }, [modelId, model.parts, setParts]);

  const handleGoToAssembly = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.generateAssemblyAnalysis(modelId, false);
      router.push(`/assembly/${modelId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Błąd generowania instrukcji';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    router.push(`/viewer/${modelId}`);
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
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold">Części komponenty</h1>
          <p className="text-sm text-slate-400 mt-1">
            Znaleziono {model.parts?.length || 0} typu części
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {isLoading && !model.parts ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-400" />
              <p>Wczytywanie części...</p>
            </div>
          </div>
        ) : !model.parts || model.parts.length === 0 ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p>Brak części do wyświetlenia</p>
            </div>
          </div>
        ) : (
          <>
            {/* Parts Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {model.parts.map((part: Part) => (
                <div
                  key={part.id}
                  onClick={() => setSelectedPartId(part.id)}
                  className={`p-4 rounded-lg border transition-all cursor-pointer ${
                    selectedPartId === part.id
                      ? 'bg-blue-900 border-blue-500 ring-2 ring-blue-400'
                      : 'bg-slate-800 border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">Część {part.id}</h3>
                      <p className="text-xs text-slate-400 mt-1">{part.part_type}</p>
                    </div>
                    {part.quantity > 1 && (
                      <span className="bg-blue-600 px-2 py-1 rounded text-xs font-semibold">
                        ×{part.quantity}
                      </span>
                    )}
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Objętość:</span>
                      <span className="font-medium">{part.volume.toFixed(2)} cm³</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Wymiary:</span>
                      <span className="font-medium text-right">
                        {Object.entries(part.dimensions)
                          .map(([key, val]) => `${key}: ${val.toFixed(1)}`)
                          .join(' | ')}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleBack}
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-semibold flex items-center gap-2 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Wróć do podglądu
              </button>

              <button
                onClick={handleGoToAssembly}
                disabled={isLoading}
                className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 disabled:from-slate-600 disabled:to-slate-600 disabled:opacity-50 rounded-lg font-semibold flex items-center gap-2 transition-all"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generowanie...
                  </>
                ) : (
                  <>
                    Instrukcja montażu
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
