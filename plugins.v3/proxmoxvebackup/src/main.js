import { createApp } from 'vue'
import App from './App.vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
// 说明：这里仅用于本地独立预览（index.html）。
// 依赖包带入的 Vuetify / MDI 全局样式会在构建时由 vite.config.js 的
// vuetify-filter（PostCSS）统一剔除，不会进入联邦产物、也不会污染宿主界面。
// 不要显式引入 'vuetify/styles'（MoviePilot V3 插件前端强制要求）。

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark'
  }
})

const app = createApp(App)
app.use(vuetify)
app.mount('#app')
