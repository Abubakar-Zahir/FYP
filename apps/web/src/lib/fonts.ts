import { Geist, Geist_Mono, Inter } from "next/font/google";

// Shared so canvas components can use the real font name (canvas can't read CSS variables)
export const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const inter = Inter({
  variable: "--font-inter",
  weight: ["400", "500", "600", "700", "800", "900"],
  subsets: ["latin"],
});
