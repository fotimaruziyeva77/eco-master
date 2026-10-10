import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    strictPort: true,
    // Telegram needs HTTPS, so in development the app is opened through an
    // ngrok / cloudflared tunnel whose host name changes between runs.
    allowedHosts: true,
    // Same-origin API calls: one tunnel to Vite also reaches the backend.
    proxy: { "/api": "http://127.0.0.1:8090" },
  },
  test: {
    environment: "node",
  },
});
