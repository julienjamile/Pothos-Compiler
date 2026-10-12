import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: path.resolve(__dirname, 'frontend'), 
  resolve: {
    alias: {
      '~material-icons': path.resolve(__dirname, 'node_modules/material-icons'),
    }
  },
  build: {
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true, // Forces Vite to empty the dist folder on build
  },
});
