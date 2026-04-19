"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getParts, exportAssemblyPDF } from "@/services/api";
import { Part } from "@/types";
import { Package2, Download, AlertCircle, Loader } from "lucide-react";
import { PartGridSkeleton } from "@/components/custom/SkeletonComponents";

interface PartsPageProps {
  params: {
    modelId: string;
  };
}

export default function PartsPage({ params }: PartsPageProps) {
  const [parts, setParts] = useState<Part[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const fetchParts = async () => {
      try {
        setLoading(true);
        const response = await getParts(params.modelId);
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
  }, [params.modelId]);

  const handleExportPDF = async () => {
    try {
      setExporting(true);
      const blob = await exportAssemblyPDF(params.modelId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `parts-${params.modelId}.pdf`;
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
      <div className="w-full max-w-6xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-black-DEFAULT">📦 Części</h1>
          {parts && !loading && (
            <p className="text-charcoal-500">
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

        {/* Parts Grid */}
        {!loading && parts && parts.length > 0 && (
          <div className="grid grid-cols-3 gap-6 animate-in fade-in duration-500">
            {parts.map((part) => (
              <Card
                key={part.id}
                className="rounded-3xl p-6 bg-bright_snow-600 border-lilac_ash-200 hover:border-lilac_ash-500 transition-all hover:shadow-md"
              >
                {/* Part Image Placeholder */}
                <div className="w-full h-32 bg-lilac_ash-50 rounded-2xl mb-4 flex items-center justify-center">
                  {part.svg_url ? (
                    <img
                      src={part.svg_url}
                      alt={part.name}
                      className="w-full h-full object-contain p-2"
                    />
                  ) : (
                    <Package2 className="w-8 h-8 text-lilac_ash-300" />
                  )}
                </div>

                {/* Part Info */}
                <div className="space-y-3">
                  <div>
                    <h3 className="font-semibold text-black-DEFAULT line-clamp-2">
                      {part.name}
                    </h3>
                    <Badge variant="secondary" className="mt-2 rounded-full bg-lilac_ash-100 text-lilac_ash-600">
                      ×{part.quantity}
                    </Badge>
                  </div>

                  <div className="space-y-1 text-sm">
                    {part.type && (
                      <p className="text-charcoal-500">
                        <span className="font-medium text-black-DEFAULT">Typ:</span>{" "}
                        {part.type}
                      </p>
                    )}
                    {part.volume && (
                      <p className="text-charcoal-500">
                        <span className="font-medium text-black-DEFAULT">
                          Objętość:
                        </span>{" "}
                        {part.volume.toFixed(2)} cm³
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && parts && parts.length === 0 && (
          <Card className="rounded-3xl p-12 bg-bright_snow-600 border-lilac_ash-200 text-center">
            <Package2 className="w-12 h-12 text-lilac_ash-300 mx-auto mb-4" />
            <p className="text-charcoal-500">Brak części do wyświetlenia</p>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center flex-wrap pt-4">
          <Link href={`/assembly/${params.modelId}`}>
            <Button className="px-8 py-6 bg-lilac_ash-500 hover:bg-lilac_ash-600 text-bright_snow-900 font-semibold rounded-3xl transition-colors">
              🔧 Instrukcje montażu
            </Button>
          </Link>

          <Button
            onClick={handleExportPDF}
            disabled={exporting || !parts}
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
                Pobierz PDF
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
