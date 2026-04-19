"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getParts } from "@/services/api";
import { Part } from "@/types";
import { Download, AlertCircle, ChevronLeft } from "lucide-react";
import { PartGridSkeleton } from "@/components/custom/SkeletonComponents";
import { PartsViewer } from "@/components/custom/PartsViewer";
import { Breadcrumb } from "@/components/custom/Breadcrumb";

interface PartsPageContentProps {
  modelId: string;
}

export function PartsPageContent({ modelId }: PartsPageContentProps) {
  const router = useRouter();
  const [parts, setParts] = useState<Part[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          currentPage="Części"
        />

        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-black-DEFAULT">📦 Części</h1>
          {parts && !loading && (
            <p className="text-charcoal-600">
              Razem {parts.length} unikalnych części
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

        {/* Loading State - Skeleton Grid */}
        {loading && <PartGridSkeleton />}

        {/* Parts Viewer - Two Column Layout */}
        {!loading && parts && parts.length > 0 && (
          <div className="animate-in fade-in duration-500">
            <PartsViewer modelId={modelId} parts={parts} />
          </div>
        )}

        {/* Empty State */}
        {!loading && parts && parts.length === 0 && (
          <div className="rounded-3xl p-12 bg-bright_snow-700 border border-lilac_ash-200 text-center">
            <p className="text-charcoal-500">Brak części do wyświetlenia</p>
          </div>
        )}

        {/* Action Buttons - Bottom Centered */}
        <div className="flex gap-4 justify-center flex-wrap pt-8 border-t border-lilac_ash-100">
          <Link href={`/assembly/${modelId}`}>
            <Button className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors">
              🔧 Instrukcje montażu
            </Button>
          </Link>

          <Button
            onClick={handleExportPDF}
            className="px-8 py-6 bg-lilac_ash-400 hover:bg-lilac_ash-500 text-black-DEFAULT font-semibold rounded-3xl transition-colors"
          >
            <span className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              Pobierz PDF
            </span>
          </Button>
        </div>

        {/* Back Button - Top Right (via breadcrumb or floating) */}
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
