import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// __dirname в ESM:
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
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
