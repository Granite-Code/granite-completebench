import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { plugin as markdownPlugin, Mode } from 'vite-plugin-markdown';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    markdownPlugin({
      mode: [Mode.REACT]
    })],
})
