import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ShortClipr – One upload. Multiple viral-ready shorts.",
  description: "Smart AI finds the moments worth sharing. Turn long videos into viral short clips in seconds with auto captions, reframing, and editing.",
  keywords: ["short clips", "viral video", "AI video editing", "video to shorts", "content creator"],
  openGraph: {
    title: "ShortClipr – One upload. Multiple viral-ready shorts.",
    description: "Smart AI finds the moments worth sharing.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
