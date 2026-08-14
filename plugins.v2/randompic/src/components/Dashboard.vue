<template>
  <div class="dashboard-widget">
    <v-card :flat="!props.config?.attrs?.border" :loading="loading" class="fill-height d-flex flex-column">
      <v-card-item v-if="props.config?.attrs?.title || props.config?.attrs?.subtitle">
        <v-card-title>{{ props.config?.attrs?.title || '随机图库状态' }}</v-card-title>
        <v-card-subtitle v-if="props.config?.attrs?.subtitle">{{ props.config.attrs.subtitle }}</v-card-subtitle>
      </v-card-item>

      <v-card-text class="flex-grow-1 pa-3">
        <!-- 加载中状态 -->
        <div v-if="loading && !initialDataLoaded" class="text-center py-2">
          <v-progress-circular indeterminate color="primary" size="small"></v-progress-circular>
        </div>
        
        <!-- 错误状态 -->
        <div v-else-if="error" class="text-error text-caption d-flex align-center">
          <v-icon size="small" color="error" class="mr-1">mdi-alert-circle-outline</v-icon>
          {{ error || '数据加载失败' }}
        </div>
        
        <!-- 数据显示 -->
        <div v-else-if="initialDataLoaded && summaryData">
          <v-list density="compact" class="py-0">
            <!-- 服务状态 -->
            <v-list-item class="pa-0">
              <template v-slot:prepend>
                <v-icon size="small" :color="summaryData.server_status === 'running' ? 'success' : 'grey'" class="mr-2">
                  {{ summaryData.server_status === 'running' ? 'mdi-server-network' : 'mdi-server-off' }}
                </v-icon>
              </template>
              <v-list-item-title class="text-caption">
                服务状态: <span :class="summaryData.server_status === 'running' ? 'text-success' : 'text-grey'">
                  {{ summaryData.server_status === 'running' ? '运行中' : '已停止' }}
                </span>
              </v-list-item-title>
            </v-list-item>

            <!-- 分隔线 -->
            <v-divider class="my-1"></v-divider>

            <!-- 图片统计 -->
            <v-list-item class="pa-0">
              <template v-slot:prepend>
                <v-icon size="small" color="info" class="mr-2">mdi-image-multiple</v-icon>
              </template>
              <v-list-item-title class="text-caption">
                总图片: {{ summaryData.total_count || 0 }}
              </v-list-item-title>
            </v-list-item>

            <v-list-item class="pa-0">
              <template v-slot:prepend>
                <v-icon size="small" color="primary" class="mr-2">mdi-monitor</v-icon>
              </template>
              <v-list-item-title class="text-caption">
                横屏: {{ summaryData.pc_count || 0 }}
              </v-list-item-title>
            </v-list-item>

            <v-list-item class="pa-0">
              <template v-slot:prepend>
                <v-icon size="small" color="success" class="mr-2">mdi-cellphone</v-icon>
              </template>
              <v-list-item-title class="text-caption">
                竖屏: {{ summaryData.mobile_count || 0 }}
              </v-list-item-title>
            </v-list-item>

            <!-- 分隔线 -->
            <v-divider class="my-1"></v-divider>

            <!-- 访问统计 -->
            <v-list-item class="pa-0">
              <template v-slot:prepend>
                <v-icon size="small" color="warning" class="mr-2">mdi-chart-line</v-icon>
              </template>
              <v-list-item-title class="text-caption">
                今日访问: {{ summaryData.today_visits || 0 }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </div>
        
        <!-- 空数据状态 -->
        <div v-else class="text-caption text-disabled text-center py-2">
          暂无数据
        </div>
      </v-card-text>

      <!-- 刷新按钮 -->
      <v-divider v-if="props.allowRefresh"></v-divider>
      <v-card-actions v-if="props.allowRefresh" class="px-3 py-1">
        <span class="text-caption text-disabled">{{ lastRefreshedTimeDisplay }}</span>
        <v-spacer></v-spacer>
        <v-btn icon variant="text" size="small" @click="fetchData" :loading="loading">
          <v-icon size="small">mdi-refresh</v-icon>
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';

// 接收props
const props = defineProps({
  // API对象，用于调用插件API
  api: { 
    type: Object,
    required: true,
  },
  // 配置参数，来自get_dashboard方法的第二个返回值
  config: {
    type: Object,
    default: () => ({ attrs: {} }),
  },
  // 是否允许手动刷新
  allowRefresh: {
    type: Boolean,
    default: false,
  },
  // 自动刷新间隔（秒）
  refreshInterval: {
    type: Number,
    default: 0, // 0表示不自动刷新
  },
});

// 状态变量
const loading = ref(false);
const error = ref(null);
const initialDataLoaded = ref(false);
const summaryData = reactive({
  server_status: 'stopped',
  total_count: 0,
  pc_count: 0,
  mobile_count: 0,
  today_visits: 0,
});
const lastRefreshedTimestamp = ref(null);

// 刷新计时器
let refreshTimer = null;

// 获取数据的函数
async function fetchData() {
  loading.value = true;
  error.value = null;
  
  try {
    // 调用插件API获取数据
    const data = await props.api.get('plugin/RandomPic/status');
    
    if (data) {
      // 更新数据
      summaryData.server_status = data.server_status || 'stopped';
      summaryData.total_count = data.total_count || 0;
      summaryData.pc_count = data.pc_count || 0;
      summaryData.mobile_count = data.mobile_count || 0;
      summaryData.today_visits = data.today_visits || 0;
      
      initialDataLoaded.value = true;
      lastRefreshedTimestamp.value = Date.now();
    } else {
      throw new Error('获取数据响应无效');
    }
  } catch (err) {
    console.error('获取仪表盘数据失败:', err);
    error.value = err.message || '获取数据失败';
  } finally {
    loading.value = false;
  }
}

// 最后刷新时间显示
const lastRefreshedTimeDisplay = computed(() => {
  if (!lastRefreshedTimestamp.value) return '';
  return `上次更新: ${new Date(lastRefreshedTimestamp.value).toLocaleTimeString()}`;
});

// 组件挂载时获取数据
onMounted(() => {
  fetchData();
  
  // 设置自动刷新
  if (props.allowRefresh && props.refreshInterval > 0) {
    refreshTimer = setInterval(fetchData, props.refreshInterval * 1000);
  }
});

// 组件卸载时清除计时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<style scoped>
.dashboard-widget {
  height: 100%;
  width: 100%;
}
.v-card-item {
  padding-bottom: 8px;
}
.v-list-item {
  min-height: 28px;
}
</style> 