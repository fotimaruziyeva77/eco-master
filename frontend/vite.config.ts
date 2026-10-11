import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

/** /admin/... deep links load the admin page (a second entry point), not the Mini App. */
function adminFallback(): Plugin {
  const rewrite = (req: unknown, _res: unknown, next: () => void) => {
    const request = req as { url?: string };
    const path = (request.url ?? "").split("?")[0];
    if (/^\/admin(\/|$)/.test(path) && !/\.\w+$/.test(path)) request.url = "/admin/index.html";
    next();
  };
  return {
    name: "admin-fallback",
    configureServer: (server) => void server.middlewares.use(rewrite),
    configurePreviewServer: (server) => void server.middlewares.use(rewrite),
  };
}

export default defineConfig({
  plugins: [react(), adminFallback()],
  server: {
    port: 5180,
    strictPort: true,
    // Telegram needs HTTPS, so in development the app is opened through an
    // ngrok / cloudflared tunnel whose host name changes between runs.
    allowedHosts: true,
    // Same-origin API calls: one tunnel to Vite also reaches the backend, which in
    // development also serves the pictures and videos uploaded in the admin panel.
    proxy: { "/api": "http://127.0.0.1:8090", "/media": "http://127.0.0.1:8090" },
  },
  build: {
    rollupOptions: {
      // The admin panel is its own page, so the Mini App bundle does not grow.
      input: { main: "index.html", admin: "admin/index.html" },
    },
  },
  test: {
    environment: "node",
    // The contrast test reads the design tokens as text (src/theme.test.ts).
    css: { include: [/tokens\.css/] },
  },
});
