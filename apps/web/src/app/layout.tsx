import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AmbientBackground } from "@/components/layout/ambient-background";
import { geistMono, geistSans, inter } from "@/lib/fonts";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Reelmind · Know what goes viral before you post",
  description:
    "Reelmind reads why reels work, writes scripts in your voice in English, Urdu or Roman Urdu, and tests 3 versions as Instagram Trial Reels before your followers see one.",
};

export const viewport: Viewport = {
  themeColor: "#ffffff",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${inter.variable} h-full scroll-smooth antialiased motion-reduce:scroll-auto`}>
      <body className="min-h-full font-sans">
        <AmbientBackground />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
