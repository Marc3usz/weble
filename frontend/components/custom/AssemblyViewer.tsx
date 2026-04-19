"use client";

import React, { useState } from "react";
import { GeometryViewer } from "./GeometryViewer";
import { SvgViewer } from "./SvgViewer";
import { AssemblyStep } from "@/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface AssemblyViewerProps {
  modelId: string;
  steps: AssemblyStep[];
  currentStepIndex: number;
  onPreviousStep: () => void;
  onNextStep: () => void;
  currentPartIndex?: number;
  onSelectPartIndex?: (partIndex: number) => void;
  isLoading?: boolean;
}

/**
 * Assembly Viewer Component
 * 
 * Left: 3D Geometry Viewer showing cumulative assembly state
 * Right: Step carousel with step navigation
 * 
 * Features:
 * - Navigate through assembly steps
 * - 3D viewer shows parts added in current step + previous steps
 * - Step details including title, description, part roles
 * 
 * TODO: Add step highlighting to show only parts for current step in 3D
 * TODO: Add context part graying out (show previous steps in light color)
 * TODO: Add part role indicators (fastener, support, etc.)
 * TODO: Add animated transitions when stepping forward/backward
 * TODO: Add keyboard navigation (arrow keys, Enter)
 */
export function AssemblyViewer({
  modelId,
  steps,
  currentStepIndex,
  onPreviousStep,
  onNextStep,
  currentPartIndex,
  onSelectPartIndex,
  isLoading = false,
}: AssemblyViewerProps) {
  const currentStep = steps[currentStepIndex];

  const activePartIndex =
    currentPartIndex ??
    currentStep.part_indices?.[0] ??
    currentStep.context_part_indices?.[0];

  const highlightedPartIndices = Array.from(
    new Set([...(currentStep.context_part_indices ?? []), ...(currentStep.part_indices ?? [])])
  );

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 h-full max-h-[calc(100vh-15rem)] min-h-[560px]">
      {/* Left: 3D Viewer (60% width) */}
      <div className="xl:col-span-2 min-h-0">
        <GeometryViewer
          modelId={modelId}
          selectedPartId={activePartIndex}
          selectedPartIds={highlightedPartIndices}
        />
      </div>

      {/* Right: Step Carousel (40% width) */}
      <div className="xl:col-span-1 min-h-0">
        <Card className="h-full rounded-3xl p-5 bg-bright_snow-700 flex flex-col overflow-y-auto">
          {/* Step Header */}
          <div className="mb-4">
            <h3 className="text-sm font-medium text-charcoal-600 uppercase tracking-wide">
              Krok {currentStep.step_number}
            </h3>
            <h2 className="text-xl font-bold text-black-DEFAULT mt-2 line-clamp-2">
              {currentStep.title}
            </h2>
          </div>

           {/* Step Description */}
           <div className="flex-1 mb-6">
             <p className="text-sm text-charcoal-600 leading-relaxed">
               {currentStep.description}
             </p>

             {/* Part Roles if available */}
             {currentStep.part_roles && Object.keys(currentStep.part_roles).length > 0 && (
               <div className="mt-4 space-y-2">
                 <p className="text-xs font-medium text-charcoal-600 uppercase">
                   Role części
                 </p>
           <div className="flex flex-wrap gap-2">
              {Object.entries(currentStep.part_roles).map(([index, role]) => (
                <Badge
                  key={index}
                  variant="secondary"
                  onClick={() => onSelectPartIndex?.(Number(index))}
                  className="rounded-full bg-lilac_ash-300 text-charcoal-700 text-xs cursor-pointer hover:bg-lilac_ash-400"
                >
                  {role}
                </Badge>
              ))}
                  </div>
                </div>
              )}

              {currentStep.detail_description && (
                <div className="mt-4 p-3 rounded-2xl bg-bright_snow-800">
                  <p className="text-xs text-charcoal-700 leading-relaxed">
                    {currentStep.detail_description}
                  </p>
                </div>
              )}

              {currentStep.assembly_sequence && currentStep.assembly_sequence.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-medium text-charcoal-600 uppercase">Sekwencja</p>
                  <ol className="text-xs text-charcoal-700 space-y-1 list-decimal pl-4">
                    {currentStep.assembly_sequence.map((item, idx) => (
                      <li key={`${item}-${idx}`}>{item}</li>
                    ))}
                  </ol>
                </div>
              )}

              {currentStep.warnings && currentStep.warnings.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-medium text-charcoal-600 uppercase">Uwagi</p>
                  <ul className="text-xs text-charcoal-700 space-y-1 list-disc pl-4">
                    {currentStep.warnings.map((item, idx) => (
                      <li key={`${item}-${idx}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {currentStep.tips && currentStep.tips.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-medium text-charcoal-600 uppercase">Wskazówki</p>
                  <ul className="text-xs text-charcoal-700 space-y-1 list-disc pl-4">
                    {currentStep.tips.map((item, idx) => (
                      <li key={`${item}-${idx}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

             {/* SVG Diagram Viewer */}
              {(currentStep.exploded_view_svg || currentStep.svg_diagram) && (
                <div className="mt-4">
                  <SvgViewer
                    svgContent={currentStep.exploded_view_svg || currentStep.svg_diagram || ""}
                    title={`Diagram - ${currentStep.title}`}
                    triggerLabel="📊 Diagram"
                  />
                </div>
              )}
           </div>

          {/* Step Counter & Navigation */}
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="w-full bg-lilac_ash-300 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-lilac_ash-500 transition-all duration-300"
                style={{
                  width: `${((currentStepIndex + 1) / steps.length) * 100}%`,
                }}
              />
            </div>

            {/* Step Counter */}
            <div className="text-center">
              <p className="text-xs text-charcoal-600 font-medium">
                Krok {currentStepIndex + 1} z {steps.length}
              </p>
            </div>

            {/* Navigation Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={onPreviousStep}
                disabled={currentStepIndex === 0}
                className="flex-1 rounded-3xl bg-lilac_ash-200 hover:bg-lilac_ash-300 text-charcoal-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>

              <Button
                onClick={onNextStep}
                disabled={currentStepIndex === steps.length - 1}
                className="flex-1 rounded-3xl bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
