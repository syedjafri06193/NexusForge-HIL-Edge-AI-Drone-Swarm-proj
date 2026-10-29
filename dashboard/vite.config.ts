import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    // three.js and recharts are vendor chunks that legitimately exceed 500 kB.
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // three.js and recharts are large and change rarely; separate chunks
        // keep the app bundle small and let browsers cache them.
        manualChunks: {
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          charts: ['recharts'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true, rewrite: p => p.replace(/^\/api/, '') },
      '/sessions': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
});
