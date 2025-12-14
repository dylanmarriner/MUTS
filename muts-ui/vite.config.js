import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  
  // Build configuration
  build: {
    outDir: 'dist/renderer',
    emptyOutDir: true,
  },
  
  // Development server
  server: {
    port: 5173,
    strictPort: true,
  },
  
  // Resolve paths
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  // CSS configuration
  css: {
    postcss: './postcss.config.js',
  },
  
  // Base path for Electron
  base: './',
  
  // Environment variables
  define: {
    __IS_ELECTRON__: JSON.stringify(true),
  },
});
