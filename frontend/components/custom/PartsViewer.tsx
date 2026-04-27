"use client";

import React, { useState } from "react";
import { GeometryViewer } from "./GeometryViewer";
import { PartHoverPreview } from "./PartHoverPreview";
import { ExplosionControl } from "./ExplosionControl";
import { Part } from "@/types";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface PartsViewerProps {
  modelId: string;
  parts: Part[];
  isLoading?: boolean;
  explosionValue: number;
  onExplosionChange: (value: number) => void;
  actions?: React.ReactNode;
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
  explosionValue,
  onExplosionChange,
  actions,
}: PartsViewerProps) {
  const [selectedPartIndex, setSelectedPartIndex] = useState<number | null>(null);
  const [hoveredPartId, setHoveredPartId] = useState<string | null>(null);
  const [hoveredAnchorRect, setHoveredAnchorRect] = useState<DOMRect | null>(null);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-3 h-full max-h-[calc(100vh-11.5rem)] min-h-[520px]">
      {/* Left: 3D Viewer with Controls (60% width) */}
      <div className="xl:col-span-2 space-y-2 min-h-0">
        <div className="relative">
          <GeometryViewer 
            modelId={modelId}
            explosionValue={explosionValue}
            selectedPartId={selectedPartIndex ?? undefined}
          />

          <div className="absolute top-3 left-3 w-[300px] max-w-[calc(100%-1.5rem)] z-20">
            <ExplosionControl value={explosionValue} onChange={onExplosionChange} />
          </div>
        </div>

         {actions ? <div className="rounded-3xl bg-gold-300 p-2">{actions}</div> : null}
        
         {/* Canvas Controls */}
         <div className="flex gap-2 px-3 py-2 bg-gold-300 rounded-3xl">
           <p className="text-xs text-black-700 flex-1">
            💡 Obróć: przeciągnij | Powiększ: scroll | Reset: 2x klik
          </p>
        </div>
      </div>

       {/* Right: Parts List (40% width) */}
       <div className="xl:col-span-1 min-h-0">
         <div className="h-full rounded-3xl bg-black-700 p-3 overflow-y-auto">
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
                onHoverRectChange={setHoveredAnchorRect}
                onHoverPreview={
                  <PartHoverPreview
                    modelId={modelId}
                    partIndex={index}
                    part={part}
                    visible={hoveredPartId === part.id}
                    anchorRect={hoveredPartId === part.id ? hoveredAnchorRect : null}
                    delay={500}
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
  onHoverRectChange: (rect: DOMRect | null) => void;
  onHoverPreview: React.ReactNode;
}

function PartListItem({
  part,
  index,
  isSelected,
  isHovered,
  onSelect,
  onHover,
  onHoverRectChange,
  onHoverPreview,
}: PartListItemProps) {
  return (
    <div className="relative">
      <Card
        onClick={onSelect}
        onMouseEnter={(event) => {
          onHover(true);
          onHoverRectChange(event.currentTarget.getBoundingClientRect());
        }}
        onMouseLeave={() => {
          onHover(false);
          onHoverRectChange(null);
        }}
        className={cn(
           "p-4 cursor-pointer transition-all rounded-3xl",
           isSelected
             ? "bg-gold-400 shadow-md"
             : isHovered
             ? "bg-gold-300 shadow-lg"
             : "bg-black-700 hover:bg-black-600"
         )}
      >
        <div className="flex items-start gap-3">
           {/* Part Icon/Number */}
           <div className={cn(
             "w-8 h-8 rounded-2xl flex items-center justify-center flex-shrink-0 text-sm font-semibold",
             isSelected
               ? "bg-gold-500 text-black-800"
               : isHovered
               ? "bg-gold-400 text-black-900"
               : "bg-gold-200 text-gold-700"
           )}>
            {index + 1}
          </div>

          {/* Part Info */}
          <div className="flex-1 min-w-0">
             <h4 className={cn(
               "text-sm font-semibold line-clamp-1",
               isSelected ? "text-gold-100" : "text-gold-300"
             )}>
              {part.name}
            </h4>
             <p className={cn(
               "text-xs mt-1",
               isSelected ? "text-gold-200" : "text-gold-300"
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
