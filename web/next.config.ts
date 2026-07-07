import type { NextConfig } from "next";

// basePath is set on the VM (NEXT_BASE_PATH=/ecoti) so the app can be served
// under http://<host>/ecoti behind nginx; unset locally => served at root.
const basePath = process.env.NEXT_BASE_PATH || undefined;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  basePath,
  assetPrefix: basePath,
};

export default nextConfig;
