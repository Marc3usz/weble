import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Package2 } from "lucide-react";

export default function Home() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center min-h-screen px-4 bg-gradient-to-br from-black-500 via-black-400 to-black-600">
      <div className="w-full max-w-2xl flex-1 flex items-center justify-center">
        {/* Hero Section */}
        <div className="text-center space-y-8">
          {/* Logo/Icon */}
          <div className="flex justify-center">
            <div className="p-6 bg-gold-500 rounded-3xl shadow-lg">
              <Package2 className="w-16 h-16 text-black-500" />
            </div>
          </div>

          {/* Title */}
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight text-gold-300">
              WEBLE
            </h1>
            <p className="text-2xl font-light text-gold-200">
              Inteligentne instrukcje składania mebli
            </p>
          </div>

          {/* Description */}
          <p className="text-lg text-gold-100 max-w-xl mx-auto leading-relaxed">
            Prześlij plik STEP swojego modelu i otrzymaj szczegółowe instrukcje
            montażu ze schematami, listą części oraz instrukcjami krok po kroku.
          </p>

          {/* CTA Button */}
          <div className="pt-4">
            <Link href="/upload">
              <Button
                size="lg"
                className="bg-gold-500 hover:bg-gold-600 text-black-500 px-8 py-6 text-lg font-semibold rounded-3xl transition-colors shadow-lg hover:shadow-xl"
              >
                Zacznij
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="w-full max-w-4xl mb-12">
        <div className="mt-20 grid grid-cols-3 gap-6">
          <div className="text-center p-6 rounded-3xl bg-black-600 border border-gold-600 shadow-sm">
            <div className="text-3xl mb-2">📦</div>
            <p className="text-sm font-semibold text-gold-200">Analiza Części</p>
          </div>
          <div className="text-center p-6 rounded-3xl bg-black-600 border border-gold-600 shadow-sm">
            <div className="text-3xl mb-2">🔧</div>
            <p className="text-sm font-semibold text-gold-200">Instrukcje Montażu</p>
          </div>
          <div className="text-center p-6 rounded-3xl bg-black-600 border border-gold-600 shadow-sm">
            <div className="text-3xl mb-2">📄</div>
            <p className="text-sm font-semibold text-gold-200">Export PDF</p>
          </div>
        </div>
      </div>

      {/* Marketing Page Button */}
      <div className="w-full max-w-4xl pb-8 border-t border-gold-700 pt-8">
        <div className="text-center">
          <Link href="/marketing">
            <Button
              size="lg"
              variant="outline"
              className="border-gold-500 text-gold-400 hover:bg-gold-500 hover:text-black-500 px-8 py-3 text-base font-semibold rounded-2xl transition-colors"
            >
              Nasz pomysł
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
