import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      // Любой import "axios" -> ваш клиент
      'axios': path.resolve(__dirname, 'src/api/axios.ts'),
      // Только для внутреннего использования в http.ts:
      // import axiosRaw from "axios-raw"
      'axios-raw': path.resolve(__dirname, 'node_modules/axios/index.js'),
    },
    conditions: ['development'],
  },
  optimizeDeps: {
    include: ['@excalidraw/excalidraw'],
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: ['.ngrok-free.app'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },

    },
  },
});
