import type { NextConfig } from 'next';

const backendURL =
  process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:4000';
const IsDEV = backendURL.startsWith('http://localhost');

const nextConfig: NextConfig = {
  reactStrictMode: false,
  poweredByHeader: false,
  compress: true,
  productionBrowserSourceMaps: false,
  output: 'standalone',
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  images: {
    dangerouslyAllowLocalIP: IsDEV,
    dangerouslyAllowSVG: true,
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'api.insights.globalct.com',
      },
      {
        protocol: IsDEV ? 'http' : 'https',
        hostname: new URL(backendURL).hostname, // ✅ only your backend
      },
    ],
  },
};

export default nextConfig;
