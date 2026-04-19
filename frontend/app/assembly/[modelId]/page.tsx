"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getAssembly, exportAssemblyPDF } from "@/services/api";
import { AssemblyStep } from "@/types";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  AlertCircle,
  Loader,
} from "lucide-react";
import { StepCarouselSkeleton } from "@/components/custom/SkeletonComponents";

interface AssemblyPageProps {
  params: {
    modelId: string;
  };
}

export default function AssemblyPage({ params }: AssemblyPageProps) {
  const [steps, setSteps] = useState<AssemblyStep[] | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const fetchAssembly = async () => {
      try {
        setLoading(true);
        const response = await getAssembly(params.modelId);
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
  }, [params.modelId]);

  const step = steps ? steps[currentStep] : null;

  const handlePrevStep = () => {
    setCurrentStep((prev) => Math.max(0, prev - 1));
  };

  const handleNextStep = () => {
    if (steps) {
      setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1));
    }
  };

  const handleExportSingleStep = async () => {
    try {
      setExporting(true);
      const blob = await exportAssemblyPDF(params.modelId, currentStep);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `step-${currentStep + 1}-${params.modelId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Nie udało się wyeksportować PDF"
      );
    } finally {
      setExporting(false);
    }
  };

  const handleExportFullPDF = async () => {
    try {
      setExporting(true);
      const blob = await exportAssemblyPDF(params.modelId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `assembly-${params.modelId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Nie udało się wyeksportować PDF"
      );
    } finally {
      setExporting(false);
    }
  };

  return (
    <main className="flex-1 flex items-center justify-center min-h-screen px-4 py-8">
      <div className="w-full max-w-4xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-black-DEFAULT">
            🔧 Instrukcje montażu
          </h1>
          {steps && !loading && (
            <p className="text-charcoal-500">
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

        {/* Step Content */}
        {!loading && step && (
          <div className="space-y-6 animate-in fade-in duration-500">
            {/* Step Counter Badge */}
            <div className="flex justify-center">
              <Badge className="rounded-full px-4 py-2 bg-lilac_ash-100 text-lilac_ash-600 text-sm font-semibold">
                Krok {currentStep + 1} z {steps?.length || 0}
              </Badge>
            </div>

            {/* Step Image/SVG */}
            <Card className="rounded-3xl overflow-hidden bg-bright_snow-600 border-lilac_ash-200 aspect-video flex items-center justify-center">
              {step.svg_url || step.image_url ? (
                <img
                  src={step.svg_url || step.image_url}
                  alt={`Krok ${step.step_number}`}
                  className="w-full h-full object-contain p-4"
                />
              ) : (
                <div className="text-center text-charcoal-400">
                  <p>Brak diagramu dla tego kroku</p>
                </div>
              )}
            </Card>

            {/* Step Title & Description */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-black-DEFAULT">
                {step.title}
              </h2>
              <p className="text-charcoal-600 leading-relaxed whitespace-pre-wrap">
                {step.description}
              </p>
            </div>

            {/* Parts for This Step */}
            {step.parts && step.parts.length > 0 && (
              <Card className="rounded-3xl p-6 bg-bright_snow-600 border-lilac_ash-200">
                <h3 className="font-semibold text-black-DEFAULT mb-4">
                  Części w tym kroku
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {step.parts.map((part) => (
                    <div
                      key={part.id}
                      className="flex items-center gap-2 text-charcoal-600"
                    >
                      <Badge
                        variant="secondary"
                        className="rounded-full bg-lilac_ash-100 text-lilac_ash-600 flex-shrink-0"
                      >
                        ×{part.quantity}
                      </Badge>
                      <span className="truncate">{part.name}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Context Parts (Grayed out) */}
            {step.context_part_indices &&
              step.context_part_indices.length > 0 && (
                <Card className="rounded-3xl p-6 bg-bright_snow-700 border-lilac_ash-100">
                  <h3 className="font-semibold text-charcoal-500 mb-4">
                    Części z poprzednich kroków
                  </h3>
                  <div className="grid grid-cols-2 gap-3 opacity-60">
                    {step.context_part_indices.map((idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 text-charcoal-500"
                      >
                        <Badge
                          variant="secondary"
                          className="rounded-full bg-lilac_ash-100 text-lilac_ash-500"
                        >
                          {idx + 1}
                        </Badge>
                        <span className="truncate">Część #{idx + 1}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

            {/* Navigation Controls */}
            <div className="flex gap-4 items-center justify-center pt-4">
              <Button
                onClick={handlePrevStep}
                disabled={currentStep === 0}
                variant="outline"
                className="px-6 py-3 rounded-3xl border-lilac_ash-300 text-charcoal-500 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Poprzedni
              </Button>

              <div className="px-4 py-2 bg-bright_snow-600 rounded-3xl text-sm font-medium text-charcoal-600">
                {currentStep + 1} / {steps?.length || 0}
              </div>

              <Button
                onClick={handleNextStep}
                disabled={!!(steps && currentStep === steps.length - 1)}
                variant="outline"
                className="px-6 py-3 rounded-3xl border-lilac_ash-300 text-charcoal-500 disabled:opacity-50"
              >
                Następny
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && steps && steps.length === 0 && (
          <Card className="rounded-3xl p-12 bg-bright_snow-600 border-lilac_ash-200 text-center">
            <p className="text-charcoal-500">
              Brak instrukcji montażu do wyświetlenia
            </p>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center flex-wrap pt-4">
          <Link href={`/parts/${params.modelId}`}>
            <Button className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors">
              📦 Części
            </Button>
          </Link>

          <Button
            onClick={handleExportSingleStep}
            disabled={exporting || !step}
            className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors disabled:opacity-50"
          >
            {exporting ? (
              <span className="flex items-center gap-2">
                <Loader className="w-4 h-4 animate-spin" />
                Eksport...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                PDF - Krok
              </span>
            )}
          </Button>

          <Button
            onClick={handleExportFullPDF}
            disabled={exporting || !steps}
            className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors disabled:opacity-50"
          >
            {exporting ? (
              <span className="flex items-center gap-2">
                <Loader className="w-4 h-4 animate-spin" />
                Eksport...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                PDF - Wszystkie
              </span>
            )}
          </Button>

          <Link href="/upload">
            <Button
              variant="outline"
              className="px-8 py-6 rounded-3xl border-lilac_ash-300 text-charcoal-500"
            >
              ← Powrót
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
