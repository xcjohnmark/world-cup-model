import type { Metadata } from "next";
import "./globals.css";
import { Bebas_Neue, Plus_Jakarta_Sans } from "next/font/google";
import { cn } from "@/lib/utils";

const bebasNeue = Bebas_Neue({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-heading",
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "WC2026 Predictor",
  description: "ML-powered 2026 FIFA World Cup prediction platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn(bebasNeue.variable, plusJakartaSans.variable)}>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
