import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enables Docker standalone build
  output: "standalone",

  // Image optimisation — allow GCS public URLs
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
        pathname: "/shortclipr-output-clips/**",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",  // Google profile photos
        pathname: "/**",
      },
    ],
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options",   value: "nosniff" },
          { key: "X-Frame-Options",           value: "DENY" },
          { key: "X-XSS-Protection",          value: "1; mode=block" },
          { key: "Referrer-Policy",           value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  // required by Next.js
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https://storage.googleapis.com https://lh3.googleusercontent.com",
              "connect-src 'self' https://*.run.app https://*.googleapis.com https://api.dodopayments.com",
              "media-src 'self' blob: https://storage.googleapis.com",
            ].join("; "),
          },
        ],
      },
    ];
  },

  // Strict mode catches common React mistakes
  reactStrictMode: true,

  // Compress output
  compress: true,

  // Poweredby header disabled
  poweredByHeader: false,
};

export default nextConfig;
