import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import path from 'path';

export default defineConfig({
  plugins: [preact()],
  root: path.join(__dirname, './static/'),
  base: '/static/dist/',
  build: {
    outDir: path.join(__dirname, '../app/static/dist/'),
    manifest: 'manifest.json',
    assetsDir: 'assets',
    rollupOptions: {
      input: ['./static/main.jsx', './static/style.css'],
    },
    emptyOutDir: true,
    copyPublicDir: false,
  },
});
