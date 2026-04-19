"use client";

import React, { useState } from "react";
import { GeometryViewer } from "./GeometryViewer";
import { PartHoverPreview } from "./PartHoverPreview";
import { ExplosionControl } from "./ExplosionControl";
import { Part } from "@/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface PartsViewerProps {
  modelId: string;
  parts: Part[];
  isLoading?: boolean;
}

/**
 * Two-Column Parts Viewer
 * 
 * Left: 3D Geometry Viewer with Explosion Control
 * Right: Scrollable parts list with hover preview
 * 
 * Features:
 * - Parts list synchronized with 3D viewer
 * - Hover preview shows after 2s mouse idle
 * - Click on part to highlight in 3D
 * - Explosion slider to spread parts apart
 * - Double-click to reset camera view
 */
export function PartsViewer({
  modelId,
  parts,
  isLoading = false,
}: PartsViewerProps) {
  const [selectedPartIndex, setSelectedPartIndex] = useState<number | null>(null);
  const [hoveredPartId, setHoveredPartId] = useState<string | null>(null);
  const [explosionValue, setExplosionValue] = useState(0);

  return (
    <div className="grid grid-cols-3 gap-6 h-full max-h-[70vh]">
      {/* Left: 3D Viewer with Controls (60% width) */}
      <div className="col-span-2 space-y-3">
        <GeometryViewer 
          modelId={modelId}
          explosionValue={explosionValue}
          selectedPartId={selectedPartIndex ?? undefined}
        />
        <ExplosionControl
          value={explosionValue}
          onChange={setExplosionValue}
        />
        
        {/* Canvas Controls */}
        <div className="flex gap-2 px-4 py-3 bg-lilac_ash-200 rounded-3xl border border-lilac_ash-400">
          <p className="text-xs text-charcoal-700 flex-1">
            💡 Obróć: przeciągnij | Powiększ: scroll | Reset: 2x klik
          </p>
        </div>
      </div>

      {/* Right: Parts List (40% width) */}
      <div className="col-span-1">
        <div className="h-full rounded-3xl bg-bright_snow-700 border border-lilac_ash-300 p-4 overflow-y-auto">
          <div className="space-y-3">
            {parts.map((part, index) => (
              <PartListItem
                key={part.id}
                part={part}
                index={index}
                isSelected={selectedPartIndex === index}
                isHovered={hoveredPartId === part.id}
                onSelect={() => setSelectedPartIndex(index)}
                onHover={(isHovered) => {
                  setHoveredPartId(isHovered ? part.id : null);
                }}
                onHoverPreview={
                  <PartHoverPreview
                    part={part}
                    visible={hoveredPartId === part.id}
                  />
                }
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Individual Part List Item with Hover Preview
 */
interface PartListItemProps {
  part: Part;
  index: number;
  isSelected: boolean;
  isHovered: boolean;
  onSelect: () => void;
  onHover: (isHovered: boolean) => void;
  onHoverPreview: React.ReactNode;
}

function PartListItem({
  part,
  index,
  isSelected,
  isHovered,
  onSelect,
  onHover,
  onHoverPreview,
}: PartListItemProps) {
  return (
    <div className="relative">
      <Card
        onClick={onSelect}
        onMouseEnter={() => onHover(true)}
        onMouseLeave={() => onHover(false)}
        className={cn(
          "p-4 cursor-pointer transition-all rounded-3xl border-2",
          isSelected
            ? "bg-lilac_ash-300 border-lilac_ash-500 shadow-md"
            : isHovered
            ? "bg-lilac_ash-200 border-lilac_ash-400 shadow-lg"
            : "bg-bright_snow-800 border-lilac_ash-300 hover:border-lilac_ash-400"
        )}
      >
        <div className="flex items-start gap-3">
          {/* Part Icon/Number */}
          <div className={cn(
            "w-8 h-8 rounded-2xl flex items-center justify-center flex-shrink-0 text-sm font-semibold",
            isSelected
              ? "bg-lilac_ash-500 text-bright_snow-800"
              : isHovered
              ? "bg-lilac_ash-400 text-bright_snow-900"
              : "bg-lilac_ash-200 text-lilac_ash-600"
          )}>
            {index + 1}
          </div>

          {/* Part Info */}
          <div className="flex-1 min-w-0">
            <h4 className={cn(
              "text-sm font-semibold line-clamp-1",
              isSelected ? "text-lilac_ash-900" : "text-charcoal-700"
            )}>
              {part.name}
            </h4>
            <p className={cn(
              "text-xs mt-1",
              isSelected ? "text-lilac_ash-700" : "text-charcoal-600"
            )}>
              ×{part.quantity}
            </p>
          </div>
        </div>
      </Card>

      {/* Hover Preview Popup */}
      {onHoverPreview}
    </div>
  );
}
