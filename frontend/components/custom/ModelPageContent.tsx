"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Breadcrumb } from "@/components/custom/Breadcrumb";
import { GeometryViewer } from "@/components/custom/GeometryViewer";
import { Package2, Wrench } from "lucide-react";

interface ModelPageContentProps {
  modelId: string;
}

export function ModelPageContent({ modelId }: ModelPageContentProps) {
  return (
    <main className="flex-1 flex flex-col min-h-screen px-4 py-4 bg-gradient-to-br from-black-500 via-black-400 to-black-600">
      <div className="w-full max-w-7xl mx-auto space-y-4 flex-1">
        <Breadcrumb
          items={[{ label: "Upload", href: "/upload" }]}
          currentPage={`Model ${modelId.slice(0, 8)}...`}
        />

        <div className="text-center space-y-1">
           <h1 className="text-3xl md:text-4xl font-bold text-gold-200">
            Podgląd modelu
          </h1>
           <p className="text-gold-300">Wybierz następny krok pracy z modelem</p>
        </div>

         <div className="rounded-3xl bg-black-700 p-3">
          <GeometryViewer modelId={modelId} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Link href={`/parts/${modelId}`}>
             <Button className="w-full py-6 bg-gold-500 hover:bg-gold-600 text-black-900 font-semibold rounded-3xl transition-colors">
              <Package2 className="w-4 h-4 mr-2" />
              Lista części
            </Button>
          </Link>

          <Link href={`/assembly/${modelId}`}>
             <Button className="w-full py-6 bg-gold-600 hover:bg-gold-700 text-black-900 font-semibold rounded-3xl transition-colors">
              <Wrench className="w-4 h-4 mr-2" />
              Instrukcje montażu
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
