import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import tailwindcss from '@tailwindcss/vite'

const apiProxyTarget =
  process.env.BACKEND_URL ?? `http://127.0.0.1:${process.env.BACKEND_PORT || "8000"}`;

const apiProxyTarget = process.env.BACKEND_URL ?? "http://localhost:8000";

// Proxies /api calls to the FastAPI backend during local dev,
// so the frontend can just call fetch("/api/...").
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": apiProxyTarget,
    },
  },
});
