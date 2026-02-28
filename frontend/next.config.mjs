/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    domains: ["minio", "localhost"],
  },
};

export default nextConfig;
