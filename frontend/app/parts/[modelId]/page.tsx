'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useModel } from '@/app/contexts/ModelContext';
import { useParts } from '@/app/hooks/useApi';
import { LABELS } from '@/app/constants/labels';
import { Part } from '@/app/types';

export default function PartsPage() {
  const router = useRouter();
  const { modelId } = useModel();
  const { parts, loading, error } = useParts(modelId);
  const [selectedPart, setSelectedPart] = useState<Part | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    if (!modelId) {
      router.push('/upload');
    }
  }, [modelId, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-platinum flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-dim-grey">{LABELS.common.loading}</p>
        </div>
      </div>
    );
  }

  if (error || !Array.isArray(parts) || parts.length === 0) {
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

  // Filter parts based on search term
  const filteredParts = parts.filter((part: Part) =>
    part.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Calculate totals
  const totalParts = parts.reduce((sum: number, part: Part) => sum + part.quantity, 0);
  const totalVolume = parts.reduce((sum: number, part: Part) => sum + part.volume, 0);

  return (
    <div className="min-h-screen bg-platinum text-black">
      {/* Header */}
      <div className="bg-alabaster-grey border-b-2 border-alabaster-grey px-8 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">{LABELS.parts.title}</h1>
            <p className="text-dim-grey text-sm mt-1">
              {parts.length} {LABELS.parts.uniqueParts} · {totalParts} {LABELS.parts.totalParts}
            </p>
          </div>
          <button
            onClick={() => router.push('/assembly/[modelId]'.replace('[modelId]', modelId!))}
            className="px-6 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors font-semibold"
          >
            {LABELS.parts.goToAssembly}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex gap-4 p-4 h-[calc(100vh-100px)]">
        {/* Left Sidebar: Parts List (40%) */}
        <div className="w-2/5 bg-platinum border-2 border-alabaster-grey rounded-lg overflow-hidden flex flex-col">
          {/* Search */}
          <div className="p-4 border-b-2 border-alabaster-grey">
            <input
              type="text"
              placeholder={LABELS.parts.searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border-2 border-alabaster-grey rounded-lg focus:border-black outline-none bg-platinum"
            />
          </div>

          {/* Parts List */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-2">
              {filteredParts.map((part: Part, idx: number) => (
                <button
                  key={part.id}
                  onClick={() => setSelectedPart(part)}
                  className={`w-full text-left p-3 rounded-lg transition-colors border-l-4 ${
                    selectedPart?.id === part.id
                      ? 'bg-alabaster-grey border-black'
                      : 'border-transparent bg-platinum hover:bg-alabaster-grey'
                  }`}
                >
                  <p className="font-semibold text-sm">{part.id}</p>
                  <p className="text-xs text-dim-grey">
                    {LABELS.parts.quantity}: {part.quantity}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Content: Part Details (60%) */}
        <div className="w-3/5 flex flex-col gap-4">
          {selectedPart ? (
            <>
              {/* Part Header */}
              <div className="bg-alabaster-grey border-2 border-alabaster-grey rounded-lg p-4">
                <h2 className="text-2xl font-bold text-black mb-2">{selectedPart.id}</h2>
                <p className="text-dim-grey text-sm">{selectedPart.part_type}</p>
              </div>

              {/* Part Details */}
              <div className="bg-platinum border-2 border-alabaster-grey rounded-lg p-4 flex-1 overflow-y-auto">
                <div className="space-y-6">
                  {/* Basic Info */}
                  <div>
                    <h3 className="font-semibold text-black mb-3">{LABELS.parts.basicInfo}</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between p-2 bg-alabaster-grey rounded">
                        <span className="text-dim-grey">{LABELS.parts.type}:</span>
                        <span className="font-semibold">{selectedPart.part_type}</span>
                      </div>
                      <div className="flex justify-between p-2 bg-alabaster-grey rounded">
                        <span className="text-dim-grey">{LABELS.parts.quantity}:</span>
                        <span className="font-semibold">{selectedPart.quantity}</span>
                      </div>
                      <div className="flex justify-between p-2 bg-alabaster-grey rounded">
                        <span className="text-dim-grey">{LABELS.parts.volume}:</span>
                        <span className="font-semibold">{selectedPart.volume.toFixed(2)} mm³</span>
                      </div>
                    </div>
                  </div>

                  {/* Dimensions */}
                  <div>
                    <h3 className="font-semibold text-black mb-3">{LABELS.parts.dimensions}</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between p-2 bg-alabaster-grey rounded">
                        <span className="text-dim-grey">{LABELS.parts.width}:</span>
                        <span className="font-semibold">{selectedPart.dimensions.width.toFixed(2)} mm</span>
                      </div>
                      <div className="flex justify-between p-2 bg-alabaster-grey rounded">
                        <span className="text-dim-grey">{LABELS.parts.height}:</span>
                        <span className="font-semibold">{selectedPart.dimensions.height.toFixed(2)} mm</span>
                      </div>
                      <div className="flex justify-between p-2 bg-alabaster-grey rounded">
                        <span className="text-dim-grey">{LABELS.parts.depth}:</span>
                        <span className="font-semibold">{selectedPart.dimensions.depth.toFixed(2)} mm</span>
                      </div>
                    </div>
                  </div>

                  {/* SVG Diagram Placeholder */}
                  <div className="border-t-2 border-alabaster-grey pt-4">
                    <h3 className="font-semibold text-black mb-3">{LABELS.parts.svgDiagram}</h3>
                    <div className="bg-alabaster-grey rounded-lg p-8 flex items-center justify-center min-h-48 text-dim-grey">
                      <p className="text-sm text-center">{LABELS.parts.svgComingSoon}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    // Copy part details to clipboard
                    const details = `${selectedPart.id}\nType: ${selectedPart.part_type}\nQuantity: ${selectedPart.quantity}\nVolume: ${selectedPart.volume.toFixed(2)} mm³\nDimensions: ${selectedPart.dimensions.width.toFixed(2)}×${selectedPart.dimensions.height.toFixed(2)}×${selectedPart.dimensions.depth.toFixed(2)} mm`;
                    navigator.clipboard.writeText(details);
                    alert('Part details copied to clipboard!');
                  }}
                  className="flex-1 py-2 bg-alabaster-grey text-black rounded-lg hover:bg-rosy-granite transition-colors font-semibold text-sm"
                >
                  {LABELS.parts.copy}
                </button>
                <button
                  onClick={() => window.print()}
                  className="flex-1 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors font-semibold text-sm"
                >
                  {LABELS.parts.print}
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-platinum border-2 border-alabaster-grey rounded-lg">
              <p className="text-dim-grey text-center">
                {LABELS.parts.selectPart}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
