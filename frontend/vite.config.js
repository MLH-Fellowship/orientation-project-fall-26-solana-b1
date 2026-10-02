import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Proxies /api calls to the FastAPI backend during local dev,
// so the frontend can just call fetch("/api/...").
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
