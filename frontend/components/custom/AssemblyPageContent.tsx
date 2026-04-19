"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getAssembly } from "@/services/api";
import { AssemblyStep } from "@/types";
import {
  Download,
  AlertCircle,
  ChevronLeft,
} from "lucide-react";
import { StepCarouselSkeleton } from "@/components/custom/SkeletonComponents";
import { AssemblyViewer } from "@/components/custom/AssemblyViewer";
import { Breadcrumb } from "@/components/custom/Breadcrumb";

interface AssemblyPageContentProps {
  modelId: string;
}

export function AssemblyPageContent({ modelId }: AssemblyPageContentProps) {
  const router = useRouter();
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
    <main className="flex-1 flex flex-col min-h-screen px-4 py-8">
      <div className="w-full max-w-7xl mx-auto space-y-6 flex-1">
        {/* Breadcrumb Navigation */}
        <Breadcrumb 
          items={[
            { label: "Upload", href: "/upload" },
            { label: `Model ${modelId.slice(0, 8)}...`, href: `/parts/${modelId}` },
          ]}
          currentPage="Instrukcje"
        />

        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-black-DEFAULT">
            🔧 Instrukcje montażu
          </h1>
          {steps && !loading && (
            <p className="text-charcoal-600">
              Krok {currentStep + 1} z {steps.length}
            </p>
          )}
        </div>

        {/* Error State */}
        {error && (
          <Alert className="border-red-200 bg-red-50 rounded-3xl">
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
          <div className="rounded-3xl p-12 bg-bright_snow-700 border border-lilac_ash-200 text-center">
            <p className="text-charcoal-500">
              Brak instrukcji montażu do wyświetlenia
            </p>
          </div>
        )}

        {/* Action Buttons - Bottom Centered */}
        <div className="flex gap-4 justify-center flex-wrap pt-8 border-t border-lilac_ash-100">
          <Link href={`/parts/${modelId}`}>
            <Button className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors">
              📦 Części
            </Button>
          </Link>

          <Button
            onClick={handleExportSingleStep}
            className="px-8 py-6 bg-lilac_ash-400 hover:bg-lilac_ash-500 text-black-DEFAULT font-semibold rounded-3xl transition-colors"
          >
            <span className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              PDF - Krok
            </span>
          </Button>

          <Button
            onClick={handleExportFullPDF}
            className="px-8 py-6 bg-lilac_ash-300 hover:bg-lilac_ash-400 text-black-DEFAULT font-semibold rounded-3xl transition-colors"
          >
            <span className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              PDF - Wszystkie
            </span>
          </Button>
        </div>

        {/* Back Button - Top Right */}
        <button
          onClick={() => router.push("/upload")}
          className="hidden md:flex fixed top-8 right-8 items-center gap-2 px-6 py-3 text-charcoal-500 hover:text-lilac_ash-600 transition-colors text-sm"
        >
          <ChevronLeft className="w-4 h-4" />
          Powrót do uploadu
        </button>
      </div>
    </main>
  );
}
