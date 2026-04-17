'use client';

import { LABELS } from '@/app/constants/labels';
import { interpolate } from '@/app/utils/helpers';

interface ProgressBarProps {
  percent: number;
  stage: string;
  action: string;
  eta: number;
}

const STAGE_ICONS = {
  loading_geometry: '📦',
  extracting_parts: '🔍',
  generating_drawings: '✏️',
  assembly: '🔧',
};

const STAGE_LABELS = {
  loading_geometry: LABELS.viewer.stages.loading,
  extracting_parts: LABELS.viewer.stages.extracting,
  generating_drawings: LABELS.viewer.stages.drawing,
  assembly: LABELS.viewer.stages.assembly,
};

export function ProgressBar({ percent, stage, action, eta }: ProgressBarProps) {
  const stageIcon = STAGE_ICONS[stage as keyof typeof STAGE_ICONS] || '⏳';
  const stageLabel = STAGE_LABELS[stage as keyof typeof STAGE_LABELS] || stage;

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="w-full bg-alabaster-grey rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-black transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Percentage */}
      <div className="text-center">
        <p className="text-2xl font-bold text-black">
          {interpolate(LABELS.viewer.progress, { percent })}
        </p>
      </div>

      {/* Stage indicator */}
      <div className="flex items-center gap-3">
        <span className="text-2xl">{stageIcon}</span>
        <div className="flex-1">
          <p className="font-semibold text-black">{stageLabel}</p>
          <p className="text-sm text-dim-grey">{action}</p>
        </div>
      </div>

      {/* ETA */}
      {eta > 0 && (
        <div className="text-center text-sm text-dim-grey">
          {interpolate(LABELS.viewer.eta, { seconds: eta })}
        </div>
      )}

      {/* Stage dots */}
      <div className="flex justify-between gap-2 mt-6">
        {[
          { key: 'loading_geometry', label: 'Geometria' },
          { key: 'extracting_parts', label: 'Części' },
          { key: 'generating_drawings', label: 'Rysunki' },
          { key: 'assembly', label: 'Instrukcja' },
        ].map((s) => (
          <div key={s.key} className="flex-1 text-center">
            <div
              className={`
                h-3 rounded-full mb-2 transition-colors
                ${
                  percent >= (s.key === 'loading_geometry' ? 25 : s.key === 'extracting_parts' ? 50 : s.key === 'generating_drawings' ? 75 : 100)
                    ? 'bg-black'
                    : 'bg-alabaster-grey'
                }
              `}
            />
            <p className="text-xs text-dim-grey">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
