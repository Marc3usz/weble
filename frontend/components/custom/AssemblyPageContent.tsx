"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import html2canvas from "html2canvas";
import { getAssembly, getParts } from "@/services/api";
import { AssemblyStep, Part } from "@/types";
import {
  Download,
  AlertCircle,
} from "lucide-react";
import { StepCarouselSkeleton } from "@/components/custom/SkeletonComponents";
import { AssemblyViewer } from "@/components/custom/AssemblyViewer";
import { Breadcrumb } from "@/components/custom/Breadcrumb";
import { exportAssemblyPdf } from "@/lib/pdf/exportAssemblyPdf";
import { extractViewerCanvasDataUrl } from "@/lib/pdf/viewer-capture.mjs";

interface AssemblyPageContentProps {
  modelId: string;
}

export function AssemblyPageContent({ modelId }: AssemblyPageContentProps) {
  const [steps, setSteps] = useState<AssemblyStep[] | null>(null);
  const [parts, setParts] = useState<Part[] | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedPartIndex, setSelectedPartIndex] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const geometryCaptureRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const fetchAssembly = async () => {
      try {
        setLoading(true);
        const [assemblyResponse, partsResponse] = await Promise.all([
          getAssembly(modelId),
          getParts(modelId),
        ]);
        setSteps(assemblyResponse.steps);
        setParts(partsResponse.parts);
        if (assemblyResponse.steps.length > 0) {
          const firstStep = assemblyResponse.steps[0];
          const initialPart =
            firstStep.part_indices?.[0] ?? firstStep.context_part_indices?.[0];
          setSelectedPartIndex(initialPart);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Nie udało się załadować instrukcji";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchAssembly();
  }, [modelId]);

  const handleExportSingleStep = async () => {
    await handleExportPdf(currentStep);
  };

  const handleExportFullPDF = async () => {
    await handleExportPdf();
  };

  const handlePreviousStep = () => {
    if (!steps || steps.length === 0) return;
    setCurrentStep((prev) => {
      const next = Math.max(0, prev - 1);
      const step = steps[next];
      const defaultPart = step?.part_indices?.[0] ?? step?.context_part_indices?.[0];
      setSelectedPartIndex(defaultPart);
      return next;
    });
  };

  const handleNextStep = () => {
    if (!steps || steps.length === 0) return;
    setCurrentStep((prev) => {
      const next = Math.min(steps.length - 1, prev + 1);
      const step = steps[next];
      const defaultPart = step?.part_indices?.[0] ?? step?.context_part_indices?.[0];
      setSelectedPartIndex(defaultPart);
      return next;
    });
  };

  const getDefaultPartIndex = (step: AssemblyStep | undefined) => {
    return step?.part_indices?.[0] ?? step?.context_part_indices?.[0];
  };

  const waitForViewerFrame = async () => {
    await new Promise((resolve) => window.requestAnimationFrame(() => resolve(undefined)));
    await new Promise((resolve) => window.requestAnimationFrame(() => resolve(undefined)));
    await new Promise((resolve) => window.setTimeout(resolve, 120));
  };

  const captureCurrentViewer = async (): Promise<string | null> => {
    const containerNode = geometryCaptureRef.current;
    const directCanvasCapture = extractViewerCanvasDataUrl(containerNode);
    if (directCanvasCapture) {
      return directCanvasCapture;
    }

    const node = containerNode?.querySelector<HTMLElement>(
      '[data-pdf-capture="geometry-surface"]'
    ) ?? containerNode;
    if (!node) {
      return null;
    }

    const canvas = await html2canvas(node, {
      backgroundColor: "#f8faf9",
      scale: 2,
      useCORS: true,
      logging: false,
    });

    return canvas.toDataURL("image/png");
  };

  const captureStepScreenshot = async (stepIndex: number): Promise<string | null> => {
    if (!steps || stepIndex < 0 || stepIndex >= steps.length) {
      return null;
    }

    const previousStep = currentStep;
    const previousPart = selectedPartIndex;

    setCurrentStep(stepIndex);
    setSelectedPartIndex(getDefaultPartIndex(steps[stepIndex]));
    await waitForViewerFrame();

    try {
      return await captureCurrentViewer();
    } finally {
      setCurrentStep(previousStep);
      setSelectedPartIndex(previousPart);
      await waitForViewerFrame();
    }
  };

  const handleExportPdf = async (stepIndex?: number) => {
    if (!steps || !parts) {
      return;
    }

    try {
      setIsExportingPdf(true);
      setError(null);
      await exportAssemblyPdf({
        modelId,
        steps,
        parts,
        stepIndex,
        captureStepScreenshot,
      });
    } catch (exportError) {
      const message = exportError instanceof Error
        ? exportError.message
        : "Nie udało się wyeksportować PDF";
      setError(message);
    } finally {
      setIsExportingPdf(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col min-h-screen px-4 py-4 bg-gradient-to-br from-black-500 via-black-400 to-black-600">
      <div className="w-full max-w-7xl mx-auto space-y-4 flex-1">
        {/* Breadcrumb Navigation */}
        <Breadcrumb 
          items={[
            { label: "📤 Upload", href: "/upload" },
            { label: `🧩 Model ${modelId.slice(0, 8)}...`, href: `/model/${modelId}` },
          ]}
          currentPage="🔧 Instrukcje"
          actions={
            <>
              <Link href={`/parts/${modelId}`}>
                <Button className="h-9 px-4 bg-gold-600 hover:bg-gold-700 text-black-900 font-semibold rounded-2xl transition-colors">
                  📦 Części
                </Button>
              </Link>

              <Button
                onClick={handlePreviousStep}
                disabled={!steps || currentStep === 0 || isExportingPdf}
                className="h-9 px-3 bg-gold-300 hover:bg-gold-400 text-black-700 rounded-2xl disabled:opacity-50"
              >
                ←
              </Button>

              <Button
                onClick={handleNextStep}
                disabled={!steps || steps.length === 0 || currentStep >= steps.length - 1 || isExportingPdf}
                className="h-9 px-3 bg-gold-500 hover:bg-gold-600 text-black-900 rounded-2xl disabled:opacity-50"
              >
                →
              </Button>

              <Button
                onClick={handleExportSingleStep}
                disabled={!steps || steps.length === 0 || isExportingPdf}
                className="h-9 px-4 bg-gold-500 hover:bg-gold-600 text-black-900 font-semibold rounded-2xl transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  {isExportingPdf ? "Eksport..." : "PDF Krok"}
                </span>
              </Button>

              <Button
                onClick={handleExportFullPDF}
                disabled={!steps || steps.length === 0 || isExportingPdf}
                className="h-9 px-4 bg-gold-400 hover:bg-gold-500 text-black-800 font-semibold rounded-2xl transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  {isExportingPdf ? "Eksport..." : "PDF Wszystkie"}
                </span>
              </Button>
            </>
          }
        />

        {steps && !loading && (
          <div className="text-center">
            <p className="text-gold-200 text-sm">
              Krok {currentStep + 1} z {steps.length}
            </p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <Alert className="bg-red-50 rounded-3xl">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Loading State - Skeleton */}
        {loading && <StepCarouselSkeleton />}

        {/* Assembly Viewer - Two Column Layout with Step Carousel */}
        {!loading && steps && steps.length > 0 && (
          <div className="animate-in fade-in duration-500">
            <AssemblyViewer
              modelId={modelId}
              steps={steps}
              currentStepIndex={currentStep}
              onPreviousStep={handlePreviousStep}
              onNextStep={handleNextStep}
              currentPartIndex={selectedPartIndex}
              onSelectPartIndex={setSelectedPartIndex}
              geometryCaptureRef={geometryCaptureRef}
            />
          </div>
        )}

        {/* Empty State */}
        {!loading && steps && steps.length === 0 && (
          <div className="rounded-3xl p-12 bg-gold-300 text-center">
            <p className="text-black-700">
              Brak instrukcji montażu do wyświetlenia
            </p>
          </div>
        )}

      </div>
    </main>
  );
}
