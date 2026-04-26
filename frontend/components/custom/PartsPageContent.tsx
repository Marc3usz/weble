"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getParts, exportAssemblyPDF } from "@/services/api";
import { Part } from "@/types";
import { Download, AlertCircle, Loader } from "lucide-react";
import { PartGridSkeleton } from "@/components/custom/SkeletonComponents";
import { PartsViewer } from "@/components/custom/PartsViewer";
import { Breadcrumb } from "@/components/custom/Breadcrumb";

interface PartsPageContentProps {
  modelId: string;
}

export function PartsPageContent({ modelId }: PartsPageContentProps) {
  const [parts, setParts] = useState<Part[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [explosionValue, setExplosionValue] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    const fetchParts = async () => {
      try {
        setLoading(true);
        const response = await getParts(modelId);
        setParts(response.parts);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Nie udało się załadować części";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchParts();
  }, [modelId]);

  const handleExportPDF = async () => {
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

  return (
    <main className="flex-1 flex flex-col min-h-screen px-4 py-4 bg-gradient-to-br from-bright_snow-900 via-bright_snow-700 to-lilac_ash-800">
      <div className="w-full max-w-7xl mx-auto space-y-3 flex-1">
        {/* Breadcrumb Navigation */}
        <Breadcrumb 
          items={[
            { label: "📤 Upload", href: "/upload" },
            { label: `🧩 Model ${modelId.slice(0, 8)}...`, href: `/model/${modelId}` },
          ]}
          currentPage="📦 Części"
          actions={
            <>
              <Link href={`/assembly/${modelId}`}>
                <Button className="h-9 px-4 bg-lilac_ash-600 hover:bg-lilac_ash-700 text-bright_snow-900 font-semibold rounded-2xl transition-colors">
                  🔧 Instrukcje
                </Button>
              </Link>

              <Button
                onClick={handleExportPDF}
                disabled={exporting}
                className="h-9 px-4 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-2xl transition-colors disabled:opacity-50"
              >
                <span className="flex items-center gap-2">
                  {exporting ? (
                    <Loader className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  {exporting ? "Generowanie..." : "PDF"}
                </span>
              </Button>
            </>
          }
        />

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

        {/* Loading State - Skeleton Grid */}
        {loading && <PartGridSkeleton />}

        {/* Parts Viewer - Two Column Layout */}
        {!loading && parts && parts.length > 0 && (
          <div className="animate-in fade-in duration-500">
            <PartsViewer
              modelId={modelId}
              parts={parts}
              explosionValue={explosionValue}
              onExplosionChange={setExplosionValue}
            />
          </div>
        )}

        {/* Empty State */}
        {!loading && parts && parts.length === 0 && (
          <div className="rounded-3xl p-12 bg-lilac_ash-300 text-center">
            <p className="text-charcoal-700">Brak części do wyświetlenia</p>
          </div>
        )}
      </div>
    </main>
  );
}
