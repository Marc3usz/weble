'use client';

import { LABELS } from '@/app/constants/labels';
import { ErrorState } from '@/app/types';

interface ErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  error: ErrorState | null;
}

export function ErrorModal({ isOpen, onClose, error }: ErrorModalProps) {
  if (!isOpen || !error) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-platinum rounded-lg shadow-lg max-w-md w-full mx-4 border-2 border-alabaster-grey">
        {/* Header */}
        <div className="bg-red-100 border-b-2 border-red-200 px-6 py-4 flex justify-between items-center rounded-t-lg">
          <h2 className="text-xl font-bold text-red-700">⚠️ {LABELS.common.error}</h2>
          <button
            onClick={onClose}
            className="text-red-700 hover:text-red-900 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div>
            <p className="text-sm text-dim-grey mb-2">{LABELS.common.error}</p>
            <p className="text-base font-semibold text-red-700">{error.message}</p>
          </div>

          {error.code && (
            <div className="bg-red-50 p-3 rounded border-l-4 border-red-500">
              <p className="text-xs text-red-600">
                <span className="font-semibold">Error Code:</span> {error.code}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-alabaster-grey border-t-2 border-alabaster-grey px-6 py-4 flex gap-2 justify-end rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-platinum text-black border-2 border-alabaster-grey rounded-lg hover:bg-red-50 transition-colors text-sm font-semibold"
          >
            {LABELS.common.close}
          </button>
          {error.retry && (
            <button
              onClick={() => {
                error.retry?.();
                onClose();
              }}
              className="px-4 py-2 bg-black text-platinum rounded-lg hover:bg-dim-grey transition-colors text-sm font-semibold"
            >
              {LABELS.errors.tryAgain}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
