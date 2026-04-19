import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WEBLE - Intelligent Furniture Assembly Instructions",
  description:
    "Intelligent instructions for assembling furniture with step-by-step guidance",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen flex flex-col bg-bright_snow-900 text-black-DEFAULT antialiased">
        {children}
      </body>
    </html>
  );
}
