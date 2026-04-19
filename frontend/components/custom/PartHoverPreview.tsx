"use client";

import React, { useEffect, useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Part } from "@/types";
import { Package2 } from "lucide-react";

interface PartHoverPreviewProps {
  part: Part;
  visible: boolean;
  delay?: number; // Delay in milliseconds before showing preview
}

/**
 * Part Hover Preview Popup
 * 
 * Shows detailed part information next to the hovered part card.
 * Appears after 2s mouse idle (configurable via delay prop).
 * 
 * Features:
 * - Fade in/fade out animation
 * - Positioned next to parent part card
 * - Shows part type, volume, dimensions
 * - Part image/SVG if available
 * 
 * TODO: Add caching to prevent recreating preview on repeated hovers
 * TODO: Add keyboard support (show/hide with arrow keys)
 * TODO: Add smooth position transitions as scroll changes
 */
export function PartHoverPreview({
  part,
  visible,
  delay = 2000,
}: PartHoverPreviewProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [mouseIdle, setMouseIdle] = useState(false);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!visible) {
      setShowPreview(false);
      setMouseIdle(false);
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
      return;
    }

    // Start idle timer when hovering
    idleTimerRef.current = setTimeout(() => {
      setMouseIdle(true);
      setShowPreview(true);
    }, delay);

    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, [visible, delay]);

  if (!showPreview) return null;

  return (
    <div
      className="absolute left-full top-0 ml-3 z-50 animate-in fade-in duration-300 pointer-events-none"
    >
      <Card className="rounded-3xl p-4 bg-bright_snow-800 border border-lilac_ash-400 shadow-lg min-w-[250px]">
         {/* Part Image - Placeholder Icon (no SVG in backend) */}
         <div className="w-full h-32 bg-lilac_ash-300 rounded-2xl mb-3 flex items-center justify-center">
           <Package2 className="w-12 h-12 text-lilac_ash-500" />
         </div>

         {/* Part Details */}
         <div className="space-y-2">
           <h4 className="font-semibold text-charcoal-700 text-sm line-clamp-2">
             {part.name}
           </h4>

           {/* Quantity Badge */}
           <Badge
             variant="secondary"
             className="rounded-full bg-lilac_ash-300 text-charcoal-700 text-xs"
           >
             Ilość: ×{part.quantity}
           </Badge>

           {/* Part Type */}
           {part.part_type && (
             <div className="text-xs">
               <span className="font-medium text-charcoal-700">Typ:</span>{" "}
               <span className="text-charcoal-600">{part.part_type}</span>
             </div>
           )}

          {/* Dimensions */}
          {part.dimensions && (
            <div className="text-xs space-y-1">
              <p className="font-medium text-charcoal-700">Wymiary:</p>
              <ul className="text-charcoal-600 pl-3">
                <li>
                  • Szerokość: {part.dimensions.width.toFixed(2)} mm
                </li>
                <li>
                  • Wysokość: {part.dimensions.height.toFixed(2)} mm
                </li>
                <li>
                  • Głębokość: {part.dimensions.depth.toFixed(2)} mm
                </li>
              </ul>
            </div>
          )}

          {/* Volume */}
          {part.volume && (
            <div className="text-xs">
              <span className="font-medium text-charcoal-700">Objętość:</span>{" "}
              <span className="text-charcoal-600">
                {part.volume.toFixed(2)} cm³
              </span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
