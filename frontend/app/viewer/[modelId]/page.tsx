'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAppStore } from '@/app/store/appStore';
import apiService from '@/app/services/api';
import GeometryViewer from '@/app/components/GeometryViewer';
import { AlertCircle, Loader2, ArrowRight } from 'lucide-react';

export default function ViewerPage() {
  const router = useRouter();
  const params = useParams();
  const modelId = params.modelId as string;

  const { model, setGeometry, setModelLoading, setModelError, setParts, setAssembly } =
    useAppStore();
  const [isGeneratingParts, setIsGeneratingParts] = useState(false);
  const [isGeneratingAssembly, setIsGeneratingAssembly] = useState(false);

  // Load model geometry on mount
  useEffect(() => {
    const loadModel = async () => {
      if (!modelId) return;

      try {
        setModelLoading(true);
        const data = await apiService.getModel(modelId);

        if (data.geometry_loaded && data.geometry) {
          setGeometry(data.geometry);
        } else {
          setModelError('Geometria modelu nie jest dostępna');
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Błąd wczytywania modelu';
        setModelError(message);
      } finally {
        setModelLoading(false);
      }
    };

    loadModel();
  }, [modelId, setGeometry, setModelLoading, setModelError]);

  const handleGenerateParts = async () => {
    try {
      setIsGeneratingParts(true);
      const response = await apiService.generateParts2D(modelId);
      setParts(response.parts);
      router.push(`/parts/${modelId}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Błąd generowania części';
      setModelError(message);
    } finally {
      setIsGeneratingParts(false);
    }
  };

  const handleGenerateAssembly = async () => {
    try {
      setIsGeneratingAssembly(true);
      // Preview only for now, then full analysis
      const response = await apiService.generateAssemblyAnalysis(modelId, false);
      setAssembly(response);
      router.push(`/assembly/${modelId}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Błąd generowania instrukcji';
      setModelError(message);
    } finally {
      setIsGeneratingAssembly(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">WEBLE - Podgląd modelu</h1>
            <p className="text-sm text-slate-400 mt-1">Model ID: {modelId}</p>
          </div>
          <button
            onClick={() => router.push('/upload')}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm font-medium"
          >
            Nowy plik
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex gap-6 p-6 max-w-7xl mx-auto w-full">
        {/* 3D Viewer */}
        <div className="flex-1 rounded-lg overflow-hidden bg-slate-800 border border-slate-700 shadow-xl">
          {model.isLoading ? (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-400" />
                <p>Wczytywanie geometrii...</p>
              </div>
            </div>
          ) : model.error ? (
            <div className="w-full h-full flex items-center justify-center p-4">
              <div className="text-center max-w-sm">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
                <h3 className="font-semibold mb-2">Błąd wczytywania modelu</h3>
                <p className="text-sm text-slate-400">{model.error}</p>
              </div>
            </div>
          ) : (
            <GeometryViewer geometry={model.geometry} />
          )}
        </div>

        {/* Sidebar - Actions */}
        <div className="w-64 space-y-4">
          {/* Model Info */}
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="font-semibold mb-3">Informacje</h3>
            <div className="space-y-2 text-sm">
              <div>
                <p className="text-slate-400">Status:</p>
                <p className="font-medium text-green-400">Gotowy</p>
              </div>
              {model.geometry && (
                <div>
                  <p className="text-slate-400">Wierzchołki:</p>
                  <p className="font-medium">{model.geometry.vertices.length}</p>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <button
              onClick={handleGenerateParts}
              disabled={isGeneratingParts || !model.geometry}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-slate-600 disabled:to-slate-600 disabled:opacity-50 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all"
            >
              {isGeneratingParts ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generowanie...
                </>
              ) : (
                <>
                  Rozłóż na części
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            <button
              onClick={handleGenerateAssembly}
              disabled={isGeneratingAssembly || !model.geometry}
              className="w-full px-4 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 disabled:from-slate-600 disabled:to-slate-600 disabled:opacity-50 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all"
            >
              {isGeneratingAssembly ? (
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

          {/* Tips */}
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h4 className="font-semibold mb-2 text-sm">Wskazówki</h4>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>• Kliknij i przeciągnij, aby obracać model</li>
              <li>• Scroll, aby powiększać/pomniejszać</li>
              <li>• Prawy klawisz myszki, aby przesuwać</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
