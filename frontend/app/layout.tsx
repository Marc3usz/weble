import type { Metadata } from "next";
import "./globals.css";
import { ModelProvider } from "@/app/contexts/ModelContext";

export const metadata: Metadata = {
  title: "WEBLE - Instrukcje Montażu",
  description: "AI-wspierane instrukcje montażu mebli",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body className="min-h-screen bg-platinum text-black transition-colors">
        <ModelProvider>
          {children}
        </ModelProvider>
      </body>
    </html>
  );
}
