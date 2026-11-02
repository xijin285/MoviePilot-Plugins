import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

/**
 * 按 MoviePilot V3 联邦插件规范过滤依赖包样式：
 * 1、node_modules/vuetify 与 node_modules/@mdi 的整棵样式树直接清空；
 * 2、其余来源中带 .v- / .mdi- 的全局规则移除，只保留插件自身的 scoped 样式。
 * 详见 docs/Plugin_Development.md 第 8.3 节「联邦组件 CSS 不得污染主程序」。
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
      if (!rule.selector) return
      const filePath = (rule.source?.input?.file || '').replaceAll('\\', '/')
      // 插件自身 src 里的样式都是 scoped 的（不会污染全局），
      // 其中合法使用 .v-/.mdi- 选择器覆盖 Vuetify 组件内部样式，必须保留
      if (filePath.includes('/src/')) return
      // v-theme--dark 是插件自身深色主题适配的选择器，必须保留
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
      name: 'RandomPic', // 必须与插件类名完全一致
      filename: 'remoteEntry.js',
      exposes: {
        './AppPage': './src/components/AppPage.vue',
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
    target: 'esnext', // 必须，支持顶层await
    minify: false, // 开发时设为false便于调试
    cssCodeSplit: false,
  },
  server: {
    port: 3000,
    cors: true, // 启用CORS
    origin: 'http://localhost:3000',
  },
})
