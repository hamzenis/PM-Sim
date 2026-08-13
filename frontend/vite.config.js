import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  test: {
    exclude: ['tests/visual/**', 'node_modules/**', 'dist/**'],
    environment: 'jsdom',
    globals: true,
    restoreMocks: true,
    setupFiles: './src/setupTests.js',
  },
});
