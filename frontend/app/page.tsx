import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Package2 } from "lucide-react";

export default function Home() {
  return (
    <main className="flex-1 flex items-center justify-center min-h-screen px-4 bg-gradient-to-br from-bright_snow-800 via-bright_snow-700 to-lilac_ash-300">
      <div className="w-full max-w-2xl">
        {/* Hero Section */}
        <div className="text-center space-y-8">
          {/* Logo/Icon */}
          <div className="flex justify-center">
            <div className="p-6 bg-lilac_ash-500 rounded-3xl shadow-lg">
              <Package2 className="w-16 h-16 text-bright_snow-900" />
            </div>
          </div>

          {/* Title */}
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight text-charcoal-800">
              WEBLE
            </h1>
            <p className="text-2xl font-light text-charcoal-700">
              Inteligentne instrukcje składania mebli
            </p>
          </div>

          {/* Description */}
          <p className="text-lg text-charcoal-600 max-w-xl mx-auto leading-relaxed">
            Prześlij plik STEP swojego modelu i otrzymaj szczegółowe instrukcje
            montażu ze schematami, listą części oraz instrukcjami krok po kroku.
          </p>

          {/* CTA Button */}
          <div className="pt-4">
            <Link href="/upload">
              <Button
                size="lg"
                className="bg-lilac_ash-600 hover:bg-lilac_ash-700 text-bright_snow-900 px-8 py-6 text-lg font-semibold rounded-3xl transition-colors shadow-lg hover:shadow-xl"
              >
                Zacznij
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-20 grid grid-cols-3 gap-6">
          <div className="text-center p-6 rounded-3xl bg-lilac_ash-200 border border-lilac_ash-400 shadow-sm">
            <div className="text-3xl mb-2">📦</div>
            <p className="text-sm font-semibold text-charcoal-700">Analiza Części</p>
          </div>
          <div className="text-center p-6 rounded-3xl bg-lilac_ash-300 border border-lilac_ash-500 shadow-sm">
            <div className="text-3xl mb-2">🔧</div>
            <p className="text-sm font-semibold text-charcoal-800">Instrukcje Montażu</p>
          </div>
          <div className="text-center p-6 rounded-3xl bg-lilac_ash-200 border border-lilac_ash-400 shadow-sm">
            <div className="text-3xl mb-2">📄</div>
            <p className="text-sm font-semibold text-charcoal-700">Export PDF</p>
          </div>
        </div>
      </div>
    </main>
  );
}
