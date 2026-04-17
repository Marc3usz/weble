'use client';

import { useState } from 'react';
import { LABELS } from '@/app/constants/labels';
import { AssemblyStep } from '@/app/types';

interface PDFExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  step?: AssemblyStep;
  modelId?: string;
}

export function PDFExportModal({
  isOpen,
  onClose,
  step,
  modelId,
}: PDFExportModalProps) {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [colorMode, setColorMode] = useState<'color' | 'bw'>('color');
  const [includeOptions, setIncludeOptions] = useState({
    include3DPreview: false,
    includePartsList: true,
    includeSteps: true,
  });

  const handleToggleOption = (key: keyof typeof includeOptions) => {
    setIncludeOptions((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleDownload = async () => {
    setIsGenerating(true);
    try {
      // Placeholder for PDF generation logic
      // In a real app, this would call an API or use a library like @react-pdf/renderer
      console.log('PDF Export Options:', {
        colorMode,
        includeOptions,
        step,
        modelId,
      });

      // Simulate PDF generation delay
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Create a simple PDF file for now
      const pdfContent = `
        WEBLE - Instrukcja Montażu
        
        Krok ${step?.step_number}: ${step?.title}
        
        Opis: ${step?.description}
        
        Części na tym kroku: ${step?.part_indices?.join(', ')}
        
        Ostrzeżenia: ${step?.warnings?.join(', ') || 'Brak'}
        
        Wskazówki: ${step?.tips?.join(', ') || 'Brak'}
        
        Czas montażu: ${step?.duration_minutes || 0} minut
      `;

      // For now, just create a text file as a placeholder
      const element = document.createElement('a');
      element.setAttribute(
        'href',
        'data:text/plain;charset=utf-8,' + encodeURIComponent(pdfContent)
      );
      element.setAttribute('download', `step-${step?.step_number}.txt`);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);

      onClose();
    } catch (error) {
      console.error('PDF generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-platinum rounded-lg shadow-lg max-w-md w-full mx-4 border-2 border-alabaster-grey">
        {/* Header */}
        <div className="bg-alabaster-grey border-b-2 border-alabaster-grey px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-black">{LABELS.pdf.title}</h2>
          <button
            onClick={onClose}
            disabled={isGenerating}
            className="text-dim-grey hover:text-black transition-colors disabled:opacity-50"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Options */}
          <div>
            <h3 className="font-semibold text-black mb-3 text-sm">
              {LABELS.pdf.options}
            </h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeOptions.include3DPreview}
                  onChange={() => handleToggleOption('include3DPreview')}
                  disabled={isGenerating}
                  className="w-4 h-4 cursor-pointer"
                />
                <span className="text-sm text-black">
                  {LABELS.pdf.include3DPreview}
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeOptions.includePartsList}
                  onChange={() => handleToggleOption('includePartsList')}
                  disabled={isGenerating}
                  className="w-4 h-4 cursor-pointer"
                />
                <span className="text-sm text-black">
                  {LABELS.pdf.includePartsList}
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeOptions.includeSteps}
                  onChange={() => handleToggleOption('includeSteps')}
                  disabled={isGenerating}
                  className="w-4 h-4 cursor-pointer"
                />
                <span className="text-sm text-black">
                  {LABELS.pdf.includeSteps}
                </span>
              </label>
            </div>
          </div>

          {/* Color Mode */}
          <div>
            <h3 className="font-semibold text-black mb-3 text-sm">
              Tryb kolorów
            </h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="colorMode"
                  value="color"
                  checked={colorMode === 'color'}
                  onChange={() => setColorMode('color')}
                  disabled={isGenerating}
                  className="w-4 h-4 cursor-pointer"
                />
                <span className="text-sm text-black">{LABELS.pdf.colorMode}</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="colorMode"
                  value="bw"
                  checked={colorMode === 'bw'}
                  onChange={() => setColorMode('bw')}
                  disabled={isGenerating}
                  className="w-4 h-4 cursor-pointer"
                />
                <span className="text-sm text-black">{LABELS.pdf.bwMode}</span>
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-alabaster-grey border-t-2 border-alabaster-grey px-6 py-4 flex gap-2 justify-end">
          <button
            onClick={onClose}
            disabled={isGenerating}
            className="px-4 py-2 text-black bg-platinum border-2 border-alabaster-grey rounded-lg hover:bg-alabaster-grey transition-colors disabled:opacity-50 text-sm font-semibold"
          >
            {LABELS.pdf.cancel}
          </button>
          <button
            onClick={handleDownload}
            disabled={isGenerating}
            className="px-4 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors disabled:opacity-50 text-sm font-semibold flex items-center gap-2"
          >
            {isGenerating && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-platinum"></div>
            )}
            {isGenerating ? LABELS.pdf.generating : LABELS.pdf.download}
          </button>
        </div>
      </div>
    </div>
  );
}
