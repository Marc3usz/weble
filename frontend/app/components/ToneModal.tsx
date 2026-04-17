'use client';

import { AssemblyTone } from '@/app/types';
import { LABELS } from '@/app/constants/labels';
import { useState } from 'react';

interface ToneModalProps {
  isOpen: boolean;
  onSelect: (tone: AssemblyTone) => void;
  isLoading?: boolean;
}

export function ToneModal({ isOpen, onSelect, isLoading = false }: ToneModalProps) {
  const [selected, setSelected] = useState<AssemblyTone | null>(null);

  const tones = [
    {
      value: AssemblyTone.IKEA,
      label: LABELS.tone.ikea.label,
      description: LABELS.tone.ikea.description,
      icon: '🎈',
    },
    {
      value: AssemblyTone.TECHNICAL,
      label: LABELS.tone.technical.label,
      description: LABELS.tone.technical.description,
      icon: '🔧',
    },
    {
      value: AssemblyTone.BEGINNER,
      label: LABELS.tone.beginner.label,
      description: LABELS.tone.beginner.description,
      icon: '📚',
    },
  ];

  const handleConfirm = () => {
    if (selected) {
      onSelect(selected);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-platinum rounded-lg p-8 max-w-md w-full mx-4 shadow-lg">
        <h2 className="text-2xl font-bold mb-2 text-black">{LABELS.tone.title}</h2>
        <p className="text-dim-grey mb-6">{LABELS.tone.subtitle}</p>

        <div className="space-y-3 mb-6">
          {tones.map((tone) => (
            <button
              key={tone.value}
              onClick={() => setSelected(tone.value as AssemblyTone)}
              className={`
                w-full p-4 rounded-lg border-2 transition-all text-left
                ${
                  selected === tone.value
                    ? 'border-black bg-alabaster-grey'
                    : 'border-alabaster-grey hover:border-dim-grey'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl mt-1">{tone.icon}</span>
                <div className="flex-1">
                  <h3 className="font-semibold text-black">{tone.label}</h3>
                  <p className="text-sm text-dim-grey">{tone.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

        <button
          onClick={handleConfirm}
          disabled={!selected || isLoading}
          className={`
            w-full py-3 rounded-lg font-semibold transition-colors
            ${
              selected && !isLoading
                ? 'bg-black text-platinum hover:bg-dim-grey cursor-pointer'
                : 'bg-alabaster-grey text-dim-grey cursor-not-allowed opacity-50'
            }
          `}
        >
          {isLoading ? LABELS.common.loading : LABELS.tone.confirm}
        </button>
      </div>
    </div>
  );
}
