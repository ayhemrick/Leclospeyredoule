import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    // Reachable from a phone on the same network, which is how the QR code
    // gets tested in practice.
    host: true,
    strictPort: true,
  },
  preview: { port: 4173, strictPort: true },
  build: {
    target: 'es2023',
    sourcemap: true,
    rollupOptions: {
      output: {
        // Split the three big vendors so a content change does not invalidate
        // the framework bundles in the visitor's cache.
        manualChunks: (id: string) => {
          if (id.includes('node_modules/react') || id.includes('node_modules/scheduler')) {
            return 'react';
          }
          if (id.includes('@tanstack/react-router')) return 'router';
          if (id.includes('@tanstack/react-query')) return 'query';
          return undefined;
        },
      },
    },
  },
});
