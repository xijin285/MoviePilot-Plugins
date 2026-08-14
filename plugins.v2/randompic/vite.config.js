import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'RandomPic', // 必须与插件类名完全一致
      filename: 'remoteEntry.js',
      exposes: {
        './Page': './src/components/Page.vue',
        './Config': './src/components/Config.vue',
        './Dashboard': './src/components/Dashboard.vue',
      },
      shared: {
        vue: { requiredVersion: false },
        vuetify: { requiredVersion: false },
        'vuetify/styles': { requiredVersion: false }
      },
      format: 'esm'
    })
  ],
  build: {
    target: 'esnext',   // 必须，支持顶层await
    minify: false,      // 开发时设为false便于调试
    cssCodeSplit: false,
  },
  server: {
    port: 3000,
    cors: true,   // 启用CORS
    origin: 'http://localhost:3000'
  },
}) 