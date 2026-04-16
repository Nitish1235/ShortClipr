import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: [
        '/dashboard/', /* Protect unified UI and private components */
        '/api/',       /* Next.js internal / proxy API routes */
        '/auth/'       /* Login handler */
      ],
    },
    sitemap: 'https://shortclipr.com/sitemap.xml',
  }
}
