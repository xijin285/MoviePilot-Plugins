import { createApp } from 'vue'
import App from './App.vue'
// 关键：从 'vuetify/lib/framework' 引入 createVuetify，且不引入 'vuetify/styles'。
// 'vuetify' 主入口会自动带上完整 main.css，联邦构建会把它注入宿主页面，
// 污染主程序界面，违反 MoviePilot V3 插件前端规范（宿主已提供 Vuetify 样式）。
import { createVuetify } from 'vuetify/lib/framework'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
  },
})

const app = createApp(App)

app.use(vuetify)
app.mount('#app')
