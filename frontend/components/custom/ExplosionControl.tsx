"use client";

import React from "react";
import { cn } from "@/lib/utils";

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
    <div className="w-full space-y-3 px-4 py-4 bg-lilac_ash-200 rounded-3xl border border-lilac_ash-400">
      <div className="flex items-center justify-between">
        <label htmlFor="explosion-slider" className="text-sm font-semibold text-charcoal-700">
          Rozłożenie części
        </label>
        <span className="text-xs text-charcoal-700 bg-lilac_ash-100 px-3 py-1 rounded-2xl">
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
        className={cn(
          "w-full h-2 bg-lilac_ash-400 rounded-full appearance-none cursor-pointer",
          "accent-lilac_ash-600",
          "[&::-webkit-slider-thumb]:appearance-none",
          "[&::-webkit-slider-thumb]:w-5",
          "[&::-webkit-slider-thumb]:h-5",
          "[&::-webkit-slider-thumb]:rounded-full",
          "[&::-webkit-slider-thumb]:bg-lilac_ash-600",
          "[&::-webkit-slider-thumb]:cursor-pointer",
          "[&::-webkit-slider-thumb]:shadow-md",
          "[&::-webkit-slider-thumb]:transition-all",
          "[&::-webkit-slider-thumb]:hover:bg-lilac_ash-700",
          "[&::-webkit-slider-thumb]:hover:shadow-lg",
          "[&::-moz-range-thumb]:w-5",
          "[&::-moz-range-thumb]:h-5",
          "[&::-moz-range-thumb]:rounded-full",
          "[&::-moz-range-thumb]:bg-lilac_ash-600",
          "[&::-moz-range-thumb]:cursor-pointer",
          "[&::-moz-range-thumb]:border-0",
          "[&::-moz-range-thumb]:shadow-md",
          "[&::-moz-range-thumb]:transition-all",
          "[&::-moz-range-thumb]:hover:bg-lilac_ash-700",
          "[&::-moz-range-thumb]:hover:shadow-lg",
        )}
      />

      {/* Hint Text */}
      <p className="text-xs text-charcoal-600">
        Przeciągnij suwak aby rozsunąć części
      </p>
    </div>
  );
}
