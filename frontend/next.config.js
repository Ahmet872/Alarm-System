// frontend/next.config.js
// ✅ FIXED - Add standalone output mode

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker optimization
  output: 'standalone',
  
  // Optimize production builds
  productionBrowserSourceMaps: false,
  
  // API rewrites for local development
  async rewrites() {
    return {
      beforeFiles: [
        // Rewrite API calls to backend
        {
          source: '/api/:path*',
          destination: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/:path*` : 'http://localhost:8000/:path*',
        },
      ],
    };
  },

  // Image optimization
  images: {
    unoptimized: true, // Required for standalone output
  },

  // Logging
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
};

module.exports = nextConfig;