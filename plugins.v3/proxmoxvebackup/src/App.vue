<template>
  <v-app>
    <v-main>
      <v-container fluid>
        <!-- 本地预览壳：联邦模式下由宿主直接加载 components 下的组件 -->
        <div class="text-h6 mb-3">PVE虚拟机守护神 · 本地预览</div>
        <v-tabs v-model="tab" class="mb-3">
          <v-tab value="page">状态页</v-tab>
          <v-tab value="config">配置</v-tab>
          <v-tab value="dash">仪表盘组件</v-tab>
        </v-tabs>
        <v-window v-model="tab">
          <v-window-item value="page">
            <Page :api="mockApi" />
          </v-window-item>
          <v-window-item value="config">
            <Config :initial-config="{}" :api="mockApi" />
          </v-window-item>
          <v-window-item value="dash">
            <Dashboard :api="mockApi" />
          </v-window-item>
        </v-window>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import Page from './components/Page.vue'
import Config from './components/Config.vue'
import Dashboard from './components/Dashboard.vue'

const tab = ref('page')

const mockApi = {
  get: async () => ({}),
  post: async () => ({}),
}
</script>
