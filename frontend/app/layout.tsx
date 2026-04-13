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
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' }
    ],
    apple: [
      { url: '/favicon.svg', type: 'image/svg+xml' }
    ]
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@graph": [
                {
                  "@type": "WebSite",
                  "@id": "https://shortclipr.com/#website",
                  "url": "https://shortclipr.com",
                  "name": "ShortClipr",
                  "publisher": { "@id": "https://shortclipr.com/#organization" }
                },
                {
                  "@type": "Organization",
                  "@id": "https://shortclipr.com/#organization",
                  "name": "ShortClipr",
                  "url": "https://shortclipr.com",
                  "logo": "https://shortclipr.com/favicon.svg",
                  "image": "https://shortclipr.com/favicon.svg"
                }
              ]
            })
          }}
        />
        {children}
      </body>
    </html>
  );
}
