"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { useProgress } from "@/hooks/useProgress";
import { useAppStore } from "@/store/appStore";
import { ProgressCard } from "@/components/custom/ProgressCard";
import { GeometryViewer } from "@/components/custom/GeometryViewer";
import { Breadcrumb } from "@/components/custom/Breadcrumb";
import {
  ProgressCardsSkeleton,
  GeometryViewerSkeleton,
} from "@/components/custom/SkeletonComponents";
import { Package2, Wrench, FileText, AlertCircle, RotateCcw } from "lucide-react";

interface ProgressPageContentProps {
  jobId: string;
  modelId: string | null;
}

export function ProgressPageContent({
  jobId,
  modelId,
}: ProgressPageContentProps) {
  const router = useRouter();

  const { percentage, status, error, isComplete, isFailed } = useProgress({
    jobId: jobId,
  });

  const [showViewer, setShowViewer] = useState(false);

  const setModelId = useAppStore((state) => state.setJobId);

  // Auto-transition to viewer on completion
  useEffect(() => {
    if (isComplete && !showViewer) {
      // Fade in transition
      const timer = setTimeout(() => {
        setShowViewer(true);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isComplete, showViewer]);

  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <main className="flex-1 flex flex-col min-h-screen px-4 py-8">
      <div className="w-full max-w-4xl mx-auto space-y-6 flex-1">
        {/* Breadcrumb - Only show when viewer is ready */}
        {showViewer && modelId && (
          <Breadcrumb 
            items={[
              { label: "Upload", href: "/upload" },
            ]}
            currentPage={`Model ${modelId.slice(0, 8)}...`}
          />
        )}

        {/* Centering container for progress state */}
        <div className="flex items-center justify-center flex-1">
          {/* Header */}
          <div className="w-full space-y-8">
            <div className="text-center space-y-4">
              {!showViewer ? (
                <>
                  <h1 className="text-4xl font-bold text-black-DEFAULT">
                    Przetwarzanie pliku...
                  </h1>
                  <p className="text-charcoal-600">Proszę czekać, może to chwilę potrwać</p>
                </>
              ) : (
                <>
                  <h1 className="text-4xl font-bold text-black-DEFAULT">
                    ✓ Model gotowy
                  </h1>
                  <p className="text-charcoal-600">Twój model jest gotowy do przeglądania</p>
                </>
              )}
            </div>
        {/* Error State */}
        {isFailed && error && (
          <>
            <Alert className="border-red-200 bg-red-50 rounded-3xl">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <AlertDescription className="text-red-800 font-medium">
                {error}
              </AlertDescription>
            </Alert>

            <div className="flex gap-4 justify-center">
              <Button
                onClick={handleRetry}
                className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Spróbuj ponownie
              </Button>

              <Link href="/upload">
                <Button
                  variant="outline"
                  className="px-8 py-6 rounded-3xl border-lilac_ash-300 text-charcoal-500"
                >
                  Prześlij nowy plik
                </Button>
              </Link>
            </div>
          </>
        )}

        {/* Loading State - Progress Bar & Cards */}
        {!showViewer && !isFailed && (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* Progress Bar */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-charcoal-600">
                  Postęp
                </span>
                <Badge variant="secondary" className="rounded-full bg-lilac_ash-100 text-lilac_ash-600">
                  {percentage}%
                </Badge>
              </div>
              <Progress
                value={percentage}
                className="h-3 rounded-full bg-lilac_ash-100"
              />
            </div>

            {/* Status Cards with Skeleton Suspense */}
            <div className="space-y-4">
              {/* Parts Card */}
              <ProgressCard
                icon={<Package2 className="w-5 h-5" />}
                title="Analiza części"
                status={percentage >= 33 ? "completed" : "pending"}
                details={percentage >= 33 ? "Znaleziono części" : "Trwa analiza..."}
                isLoading={percentage < 33 && !isComplete}
              />

              {/* Assembly Card */}
              <ProgressCard
                icon={<Wrench className="w-5 h-5" />}
                title="Instrukcje montażu"
                status={
                  percentage >= 66 ? "completed" : percentage >= 33 ? "processing" : "pending"
                }
                details={
                  percentage >= 66
                    ? "Instrukcje wygenerowane"
                    : percentage >= 33
                      ? "Generowanie instrukcji..."
                      : "Oczekiwanie..."
                }
                isLoading={percentage < 66 && !isComplete}
              />

              {/* PDF Card */}
              <ProgressCard
                icon={<FileText className="w-5 h-5" />}
                title="Eksport PDF"
                status={percentage >= 90 ? "completed" : percentage >= 66 ? "processing" : "pending"}
                details={
                  percentage >= 90
                    ? "PDF gotowy"
                    : percentage >= 66
                      ? "Generowanie PDF..."
                      : "Oczekiwanie..."
                }
                isLoading={percentage < 90 && !isComplete}
              />
            </div>
          </div>
        )}

        {/* Viewer State - 3D Model & Action Buttons */}
        {showViewer && !isFailed && modelId && (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* 3D Viewer */}
            <GeometryViewer modelId={modelId} />

            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-4">
              <Link href={`/parts/${modelId}`}>
                <Button
                  className="w-full py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors"
                >
                  <Package2 className="w-4 h-4 mr-2" />
                  Zobacz części
                </Button>
              </Link>

              <Link href={`/assembly/${modelId}`}>
                <Button
                  className="w-full py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors"
                >
                  <Wrench className="w-4 h-4 mr-2" />
                  Instrukcje montażu
                </Button>
              </Link>
            </div>

            {/* Back Button */}
            <Link href="/upload" className="block">
              <Button
                variant="outline"
                className="w-full py-4 rounded-3xl border-lilac_ash-300 text-charcoal-500 font-medium"
              >
                ← Prześlij nowy plik
              </Button>
            </Link>
          </div>
        )}

        {/* Fallback - Show skeletons if still loading */}
        {!showViewer && !isFailed && percentage < 10 && (
          <div className="space-y-8">
            <ProgressCardsSkeleton count={3} />
            <GeometryViewerSkeleton />
          </div>
        )}
          </div>
        </div>
      </div>
    </main>
  );
}
