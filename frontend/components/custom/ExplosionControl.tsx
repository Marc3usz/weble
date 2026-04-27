"use client";

import React from "react";

interface ExplosionControlProps {
  value: number;
  onChange: (value: number) => void;
}

/**
 * Explosion Control Slider
 * Allows users to adjust how spread apart the parts are (0-100)
 * 
 * 0 = All parts in original position
 * 100 = All parts spread outward from center
 */
export function ExplosionControl({ value, onChange }: ExplosionControlProps) {
  return (
    <div className="w-full space-y-2 px-3 py-3 bg-gold-300/95 backdrop-blur-sm rounded-2xl shadow-md">
      <div className="flex items-center justify-between">
         <label htmlFor="explosion-slider" className="text-xs font-semibold text-black-700">
          Rozłożenie części
        </label>
         <span className="text-xs text-black-700 bg-gold-100 px-2 py-0.5 rounded-xl">
          {value}%
        </span>
      </div>

      {/* Slider */}
      <input
        id="explosion-slider"
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(Number(e.currentTarget.value))}
        className="explosion-slider"
      />

      {/* Hint Text */}
       <p className="text-[11px] text-black-600">
        Przeciągnij suwak aby rozsunąć części
      </p>
    </div>
  );
}
