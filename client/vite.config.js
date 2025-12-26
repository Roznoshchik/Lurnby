import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import path from 'path';

export default defineConfig({
  plugins: [preact()],
  root: path.join(__dirname, './static/'),
  base: '/static/dist/',
  server: {
    origin: 'http://localhost:5173',
    cors: true,
  },
  build: {
    outDir: path.join(__dirname, '../app/static/dist/'),
    manifest: 'manifest.json',
    assetsDir: 'bundled',
    rollupOptions: {
      input: ['./static/login.jsx', './static/articles.jsx', './static/style.css'],
    },
    emptyOutDir: true,
    copyPublicDir: false,
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './test-setup.js',
  },
});
