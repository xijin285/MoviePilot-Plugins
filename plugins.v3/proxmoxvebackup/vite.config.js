import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

/**
 * 按 MoviePilot V3 联邦插件规范过滤依赖包样式：
 * 1、node_modules/vuetify 与 node_modules/@mdi 的整棵样式树直接清空；
 * 2、其余来源中带 .v- / .mdi- 的全局规则移除，只保留插件自身的 scoped 样式。
 */
const vuetifyFilter = {
  postcssPlugin: 'vuetify-filter',
  Root(root) {
    const sourcePath = (root.source?.input?.file || '').replaceAll('\\', '/')
    if (
      sourcePath.includes('/node_modules/vuetify/') ||
      sourcePath.includes('/node_modules/@mdi/')
    ) {
      root.nodes = []
      return
    }
    root.walkRules((rule) => {
      const filePath = rule.source?.input?.file || ''
      if (filePath.replaceAll('\\', '/').includes('/src/')) return
      if (rule.selector.includes('v-theme--dark')) return
      if (rule.selector.includes('.v-') || rule.selector.includes('.mdi-')) {
        rule.remove()
      }
    })
  },
}

export default defineConfig({
  plugins: [
    vue(),
    federation({
      // 联邦容器名必须与插件类名完全一致
      name: 'ProxmoxVEBackup',
      filename: 'remoteEntry.js',
      exposes: {
        './Page': './src/components/Page.vue',
        './Config': './src/components/Config.vue',
        './Dashboard': './src/components/Dashboard.vue',
      },
      shared: {
        vue: { requiredVersion: false, generate: false, singleton: true },
        vuetify: { requiredVersion: false, generate: false, singleton: true },
        'vuetify/styles': { requiredVersion: false, generate: false, singleton: true },
      },
      format: 'esm',
    }),
  ],
  css: {
    postcss: {
      plugins: [vuetifyFilter],
    },
  },
  build: {
    target: 'esnext', // 必须，支持顶层 await
    minify: false, // 开发时设为 false 便于调试
    cssCodeSplit: false,
  },
  server: {
    port: 5001,
    cors: true,
    origin: 'http://localhost:5001',
  },
})
