import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8002',
        pathname: '/media/**',
      },
      {
        protocol: 'https',
        hostname: 'emailcampaign-api.musfiqdehan.com',
        pathname: '/media/**',
      },
    ],
  },
};

export default nextConfig;
