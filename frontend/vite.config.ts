import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path'; // 👈 добавить импорт path

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'), // 👈 псевдоним @ → src
    },
    conditions: ['development'],
  },
  optimizeDeps: {
    include: ['@excalidraw/excalidraw'],
  },
  server: {
      host: true,             // разрешаем доступ извне
    port: 5173,             // (если используешь стандартный порт Vite)
    allowedHosts: ['.ngrok-free.app'], // 👈 разрешаем все поддомены ngrok
    proxy: {
      // 🔁 Для /api/* запросов
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // 🔁 Для web-интерфейса (если нужен)
      '/schedule': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/schedule/, '/schedule'),
      },
    },
  },
});
