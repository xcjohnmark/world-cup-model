import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import { cn } from "@/lib/utils";
import { Analytics } from "@vercel/analytics/react";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "World Cup 2026 Prediction Model",
  description: "An ML-powered XGBoost simulator computing progression probabilities for all 48 participating countries.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn(inter.variable)}>
      <body className="antialiased font-sans">
        {children}
        <Analytics />
      </body>
    </html>
  );
}
