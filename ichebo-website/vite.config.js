import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        about: resolve(__dirname, 'about.html'),
        training: resolve(__dirname, 'training.html'),
        platform: resolve(__dirname, 'platform.html'),
        programme: resolve(__dirname, 'programme.html'),
      },
    },
  },
})
