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
  isLoading = false,
}: AssemblyViewerProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const currentStep = steps[currentStepIndex];

  const handlePreviousStep = () => {
    setCurrentStepIndex(Math.max(0, currentStepIndex - 1));
  };

  const handleNextStep = () => {
    setCurrentStepIndex(Math.min(steps.length - 1, currentStepIndex + 1));
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 h-full max-h-[calc(100vh-15rem)] min-h-[560px]">
      {/* Left: 3D Viewer (60% width) */}
      <div className="xl:col-span-2 min-h-0">
        <GeometryViewer modelId={modelId} />
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
                  className="rounded-full bg-lilac_ash-300 text-charcoal-700 text-xs"
                >
                  {role}
                </Badge>
              ))}
                 </div>
               </div>
             )}

             {/* SVG Diagram Viewer */}
             {currentStep.svg_diagram && (
               <div className="mt-4">
                 <SvgViewer
                   svgContent={currentStep.svg_diagram}
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
                onClick={handlePreviousStep}
                disabled={currentStepIndex === 0}
                className="flex-1 rounded-3xl bg-lilac_ash-200 hover:bg-lilac_ash-300 text-charcoal-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>

              <Button
                onClick={handleNextStep}
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
