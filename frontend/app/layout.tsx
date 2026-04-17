import type { Metadata } from "next";
import { Courier_Prime, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";
import { ModelProvider } from "@/app/contexts/ModelContext";

const courierPrime = Courier_Prime({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "700"],
});

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "WEBLE - Instrukcje Montazu",
  description: "AI-wspierane instrukcje montazu mebli",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body className={`${courierPrime.variable} ${plex.variable} min-h-screen`}>
        <ModelProvider>
          {children}
        </ModelProvider>
      </body>
    </html>
  );
}
