import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        about: resolve(__dirname, 'about.html'),
        contact: resolve(__dirname, 'contact.html'),
        platform: resolve(__dirname, 'platform.html'),
        programme: resolve(__dirname, 'programme.html'),
        training: resolve(__dirname, 'training.html'),
        watch: resolve(__dirname, 'watch.html'),
        'find-a-church': resolve(__dirname, 'find-a-church.html'),
      },
    },
  },
})
