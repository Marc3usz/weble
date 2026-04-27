import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function MarketingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-black-500 via-black-400 to-black-600">
      {/* Header with back button */}
      <div className="sticky top-0 z-10 bg-black-500/80 backdrop-blur-sm border-b border-gold-600">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center">
          <Link href="/">
            <Button
              variant="ghost"
              className="text-gold-400 hover:text-gold-300 hover:bg-black-600 flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Powrót
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center space-y-8 mb-24">
          <div className="space-y-4">
            <h1 className="text-6xl font-bold tracking-tight text-gold-300">
              WEBLE
            </h1>
            <p className="text-xl text-gold-200 max-w-3xl mx-auto">
              Narzędzie do automatycznego generowania instrukcji montażu mebli
              z plików CAD
            </p>
          </div>
        </div>

        {/* What is WEBLE Section */}
        <div className="bg-black-600 border border-gold-600 rounded-2xl p-8 mb-24">
          <h2 className="text-2xl font-bold text-gold-300 mb-6">Co robi WEBLE?</h2>
          <p className="text-gold-100 text-lg leading-relaxed mb-6">
            WEBLE to narzędzie, które przyjmuje plik STEP (format CAD) reprezentujący model mebla
            i automatycznie generuje szczegółowe instrukcje montażu. Program analizuje strukturę
            modelu, identyfikuje części oraz etapy montażu, a następnie tworzy instrukcje
            krok po kroku z wizualizacją 3D.
          </p>
        </div>

        {/* Key Features Section */}
        <div className="mb-24">
          <h2 className="text-3xl font-bold text-gold-300 text-center mb-12">
            Funkcjonalności
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-black-600 border border-gold-600 rounded-xl p-6 hover:border-gold-400 transition">
              <div className="text-3xl mb-3">📦</div>
              <h3 className="text-lg font-semibold text-gold-300 mb-2">Analiza Części</h3>
              <p className="text-gold-100 text-sm">
                Program automatycznie identyfikuje wszystkie części w modelu i tworzy
                ich spis wraz z opisami
              </p>
            </div>

            <div className="bg-black-600 border border-gold-600 rounded-xl p-6 hover:border-gold-400 transition">
              <div className="text-3xl mb-3">🔧</div>
              <h3 className="text-lg font-semibold text-gold-300 mb-2">Instrukcje Montażu</h3>
              <p className="text-gold-100 text-sm">
                Generuje szczegółowe instrukcje krok po kroku z wizualizacją 3D
                każdego etapu montażu
              </p>
            </div>

            <div className="bg-black-600 border border-gold-600 rounded-xl p-6 hover:border-gold-400 transition">
              <div className="text-3xl mb-3">📄</div>
              <h3 className="text-lg font-semibold text-gold-300 mb-2">Export PDF</h3>
              <p className="text-gold-100 text-sm">
                Instrukcje mogą być wyeksportowane do formatu PDF gotowego
                do dystrybucji
              </p>
            </div>
          </div>
        </div>

        {/* How it works */}
        <div className="bg-black-600 border border-gold-600 rounded-2xl p-8 mb-24">
          <h2 className="text-2xl font-bold text-gold-300 mb-6">Jak to działa?</h2>
          <ol className="space-y-4 text-gold-100">
            <li className="flex gap-4">
              <span className="text-gold-500 font-bold text-lg">1.</span>
              <span>Przesyłasz plik STEP (format CAD mebla)</span>
            </li>
            <li className="flex gap-4">
              <span className="text-gold-500 font-bold text-lg">2.</span>
              <span>Program analizuje strukturę i części mebla</span>
            </li>
            <li className="flex gap-4">
              <span className="text-gold-500 font-bold text-lg">3.</span>
              <span>Generuje instrukcje montażu z wizualizacją 3D</span>
            </li>
            <li className="flex gap-4">
              <span className="text-gold-500 font-bold text-lg">4.</span>
              <span>Wyeksportuj instrukcje do PDF lub przeglądaj online</span>
            </li>
          </ol>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gold-600 bg-black-600 mt-24">
        <div className="max-w-6xl mx-auto px-4 py-8 text-center text-gold-300">
          <p>Weble</p>
        </div>
      </footer>
    </main>
  );
}
