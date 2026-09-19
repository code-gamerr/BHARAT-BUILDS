import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/healthz": "http://127.0.0.1:8080",
      "/ops": "http://127.0.0.1:8080",
      "/graph": "http://127.0.0.1:8080",
      "/cases": "http://127.0.0.1:8080",
      "/ingest": "http://127.0.0.1:8080",
      "/download": "http://127.0.0.1:8080",
    },
  },
});
