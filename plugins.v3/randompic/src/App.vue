<template>
  <div class="app-container">
    <v-app>
      <v-main>
        <v-container fluid class="pa-0">
          <page-component v-if="currentView === 'page'" :api="mockPluginApiWrapper" @switch="currentView = 'config'" />
          <config-component v-else :api="mockPluginApiWrapper" :initial-config="mockDatabase.config" @switch="currentView = 'page'" />
        </v-container>
      </v-main>
    </v-app>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="snackbar.timeout" location="top end">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false"> 关闭 </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import PageComponent from './components/Page.vue'
import ConfigComponent from './components/Config.vue'

const currentView = ref('page');

const mockDatabase = reactive({
  config: {
    enable: false,
    pc_path: "",
    mobile_path: "",
    default_pc_path: "/data/plugins/RandomPic/PC",
    default_mobile_path: "/data/plugins/RandomPic/Mobile",
    download_count: 20,
  },
  status: {
    enable: true,
    api_status: "available",
    access_mode: "moviepilot",
    pc_path: "/data/plugins/RandomPic/landscape",
    pc_path_custom: false,
    mobile_path: "/data/custom/portrait",
    mobile_path_custom: true,
    pc_count: 156,
    mobile_count: 89,
    total_count: 245,
    today_visits: 42,
  },
});

const mockPluginApiWrapper = {
  get: async (url) => {
    if (url.includes('config')) {
      return JSON.parse(JSON.stringify(mockDatabase.config));
    }
    if (url.includes('status')) {
      return JSON.parse(JSON.stringify(mockDatabase.status));
    }
    return {};
  },
  post: async (url, data) => {
    if (url.includes('config')) {
      Object.assign(mockDatabase.config, data);
      showNotification('配置已更新', 'success');
      return { message: '配置已成功保存', saved_config: JSON.parse(JSON.stringify(mockDatabase.config)) };
    }
    if (url.includes('preview/save')) {
      showNotification('图片已保存到本地目录（模拟）', 'success');
      return { success: true, msg: '已保存为横屏图片（模拟）' };
    }
    return {};
  }
};

const snackbar = reactive({
  show: false,
  text: '',
  color: 'success',
  timeout: 3000
});

const showNotification = (text, color = 'success') => {
  snackbar.text = text;
  snackbar.color = color;
  snackbar.show = true;
};
</script>

<style scoped>
.app-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}
</style> 