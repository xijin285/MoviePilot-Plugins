import { createApp } from 'vue'
import App from './App.vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
// 说明：这里仅用于本地独立预览（index.html）。
// 依赖包带入的 Vuetify / MDI 全局样式会在构建时由 vite.config.js 的
// vuetify-filter（PostCSS）统一剔除，不会进入联邦产物、也不会污染宿主界面。
// 不要显式引入 'vuetify/styles'（MoviePilot V3 插件前端强制要求）。

// 创建Vuetify实例 - 随机图库主题配置
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          primary: '#667eea',    // 随机图库主题色 - 渐变紫色
          secondary: '#764ba2',  // 随机图库辅助色 - 渐变蓝色
          accent: '#f093fb',     // 随机图库强调色 - 粉色
          info: '#4facfe',       // 信息色 - 蓝色
          success: '#43e97b',    // 成功色 - 绿色
          warning: '#fa709a',    // 警告色 - 粉色
          error: '#ff6b6b',      // 错误色 - 红色
        }
      }
    }
  }
})

// 创建随机图库Vue应用
const app = createApp(App)

// 使用Vuetify插件
app.use(vuetify)

// 挂载应用到DOM - 随机图库界面
app.mount('#app') 
 