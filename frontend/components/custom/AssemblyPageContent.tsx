"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getAssembly } from "@/services/api";
import { AssemblyStep } from "@/types";
import {
  Download,
  AlertCircle,
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAssembly = async () => {
      try {
        setLoading(true);
        const response = await getAssembly(modelId);
        setSteps(response.steps);
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
    alert("Eksport PDF nie jest jeszcze dostępny. Ta funkcja będzie wkrótce dodana.");
  };

  const handleExportFullPDF = async () => {
    alert("Eksport PDF nie jest jeszcze dostępny. Ta funkcja będzie wkrótce dodana.");
  };

  return (
    <main className="flex-1 flex flex-col min-h-screen px-4 py-4 bg-gradient-to-br from-bright_snow-900 via-bright_snow-700 to-lilac_ash-800">
      <div className="w-full max-w-7xl mx-auto space-y-4 flex-1">
        {/* Breadcrumb Navigation */}
        <Breadcrumb 
          items={[
            { label: "Upload", href: "/upload" },
            { label: `Model ${modelId.slice(0, 8)}...`, href: `/model/${modelId}` },
          ]}
          currentPage="Instrukcje"
        />

        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-charcoal-800">
            🔧 Instrukcje montażu
          </h1>
          {steps && !loading && (
            <p className="text-charcoal-700">
              Krok {currentStep + 1} z {steps.length}
            </p>
          )}
        </div>

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
            <AssemblyViewer modelId={modelId} steps={steps} />
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

        {/* Action Buttons */}
        <div className="flex gap-3 justify-center xl:justify-end flex-wrap py-2">
          <Link href={`/parts/${modelId}`}>
            <Button className="px-7 py-5 bg-lilac_ash-600 hover:bg-lilac_ash-700 text-bright_snow-900 font-semibold rounded-3xl transition-colors shadow-md hover:shadow-lg">
              📦 Części
            </Button>
          </Link>

          <Button
            onClick={handleExportSingleStep}
            className="px-7 py-5 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors shadow-md hover:shadow-lg"
          >
            <span className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              PDF - Krok
            </span>
          </Button>

          <Button
            onClick={handleExportFullPDF}
            className="px-7 py-5 bg-lilac_ash-400 hover:bg-lilac_ash-500 text-charcoal-800 font-semibold rounded-3xl transition-colors shadow-md hover:shadow-lg"
          >
            <span className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              PDF - Wszystkie
            </span>
          </Button>
        </div>
      </div>
    </main>
  );
}
