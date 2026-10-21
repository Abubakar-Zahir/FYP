import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";

import { AmbientBackground } from "@/components/layout/ambient-background";

import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Reelmind · Know what goes viral before you post",
  description:
    "Reelmind reads why reels work, writes scripts in your voice in English, Urdu or Roman Urdu, and tests 3 versions as Instagram Trial Reels before your followers see one.",
};

export const viewport: Viewport = {
  themeColor: "#07060f",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${instrumentSerif.variable} h-full scroll-smooth antialiased motion-reduce:scroll-auto`}>
      <body className="min-h-full font-sans">
        <AmbientBackground />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
