import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  // Dev only: lets teammates and phones on the same Wi-Fi open the Network URL.
  // Without it Next blocks its dev scripts there and no button works.
  allowedDevOrigins: ["192.168.*.*", "10.*.*.*"],
  partialPrefetching: true,
  // A config redirect instead of a page that only calls redirect(): such a page never
  // renders, which trips instant-navigation validation in dev.
  async redirects() {
    return [{ source: "/", destination: "/login", permanent: false }];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
