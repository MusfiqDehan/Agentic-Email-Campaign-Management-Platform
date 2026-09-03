import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Keep the dev indicator off the mobile bottom nav (default is bottom-left).
  devIndicators: {
    position: "top-left",
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'emailcampaign-api.musfiqdehan.com',
        pathname: '/media/**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8001',
        pathname: '/media/**',
      },
    ],
  },
};

export default nextConfig;
