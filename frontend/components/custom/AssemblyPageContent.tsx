"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getAssembly, exportAssemblyPDF } from "@/services/api";
import { AssemblyStep } from "@/types";
import {
  Download,
  AlertCircle,
  Loader,
} from "lucide-react";
import { StepCarouselSkeleton } from "@/components/custom/SkeletonComponents";
import { AssemblyViewer } from "@/components/custom/AssemblyViewer";
import { Breadcrumb } from "@/components/custom/Breadcrumb";

interface AssemblyPageContentProps {
  modelId: string;
}

export function AssemblyPageContent({ modelId }: AssemblyPageContentProps) {
  const [steps, setSteps] = useState<AssemblyStep[] | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedPartIndex, setSelectedPartIndex] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAssembly = async () => {
      try {
        setLoading(true);
        const response = await getAssembly(modelId);
        setSteps(response.steps);
        if (response.steps.length > 0) {
          const firstStep = response.steps[0];
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
    // TODO: Implement single step PDF export in future version
    alert("Eksport PDF pojedynczego kroku będzie dostępny w przyszłych wersjach.");
  };

  const handleExportFullPDF = async () => {
    try {
      setExporting(true);
      setExportError(null);
      
      await exportAssemblyPDF(modelId);
      
      // Success - file will be downloaded by the API
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Nie udało się wyeksportować PDF";
      setExportError(errorMessage);
    } finally {
      setExporting(false);
    }
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

  return (
    <main className="flex-1 flex flex-col min-h-screen px-4 py-4 bg-gradient-to-br from-bright_snow-900 via-bright_snow-700 to-lilac_ash-800">
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
                <Button className="h-9 px-4 bg-lilac_ash-600 hover:bg-lilac_ash-700 text-bright_snow-900 font-semibold rounded-2xl transition-colors">
                  📦 Części
                </Button>
              </Link>

              <Button
                onClick={handlePreviousStep}
                disabled={!steps || currentStep === 0}
                className="h-9 px-3 bg-lilac_ash-300 hover:bg-lilac_ash-400 text-charcoal-700 rounded-2xl disabled:opacity-50"
              >
                ←
              </Button>

              <Button
                onClick={handleNextStep}
                disabled={!steps || steps.length === 0 || currentStep >= steps.length - 1}
                className="h-9 px-3 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 rounded-2xl disabled:opacity-50"
              >
                →
              </Button>

              <Button
                onClick={handleExportSingleStep}
                className="h-9 px-4 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-2xl transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  PDF Krok
                </span>
              </Button>

              <Button
                onClick={handleExportFullPDF}
                disabled={exporting}
                className="h-9 px-4 bg-lilac_ash-400 hover:bg-lilac_ash-500 text-charcoal-800 font-semibold rounded-2xl transition-colors disabled:opacity-50"
              >
                <span className="flex items-center gap-2">
                  {exporting ? (
                    <Loader className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  {exporting ? "Generowanie..." : "PDF Wszystkie"}
                </span>
              </Button>
            </>
          }
        />

        {steps && !loading && (
          <div className="text-center">
            <p className="text-charcoal-700 text-sm">
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

        {/* Export Error State */}
        {exportError && (
          <Alert className="bg-red-50 rounded-3xl">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <AlertDescription className="text-red-800">{exportError}</AlertDescription>
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
            />
          </div>
        )}

        {/* Empty State */}
        {!loading && steps && steps.length === 0 && (
          <div className="rounded-3xl p-12 bg-lilac_ash-300 text-center">
            <p className="text-charcoal-700">
              Brak instrukcji montażu do wyświetlenia
            </p>
          </div>
        )}

      </div>
    </main>
  );
}
