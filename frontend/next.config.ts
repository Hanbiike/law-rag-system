import path from 'path';
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // Explicitly set the project root so Next.js does not pick up lockfiles
  // from parent directories (e.g. /Users/han/pnpm-lock.yaml).
  outputFileTracingRoot: path.resolve(__dirname),
  reactStrictMode: false,
  pageExtensions: ['ts', 'tsx', 'js', 'jsx'],
  serverExternalPackages: ['@napi-rs/canvas'],
  logging: {
    fetches: {
      fullUrl: true
    }
  },
  experimental: {
    optimizePackageImports: ['lucide-react'],
    serverActions: {
      allowedOrigins: []
    }
  },
  turbopack: {
    // Pin workspace root to the frontend directory so Turbopack does not
    // walk up to /Users/han/pnpm-lock.yaml and use /Users/han as the root.
    root: path.resolve(__dirname),
    // Explicitly map CSS-side packages to their local node_modules locations.
    // This ensures correct resolution regardless of the detected workspace root.
    resolveAlias: {
      tailwindcss: path.resolve(__dirname, 'node_modules/tailwindcss'),
      'tailwindcss-animate': path.resolve(
        __dirname,
        'node_modules/tailwindcss-animate',
      ),
      '@tailwindcss/typography': path.resolve(
        __dirname,
        'node_modules/@tailwindcss/typography',
      ),
      '@tailwindcss/postcss': path.resolve(
        __dirname,
        'node_modules/@tailwindcss/postcss',
      ),
    },
  },
};

export default nextConfig;
