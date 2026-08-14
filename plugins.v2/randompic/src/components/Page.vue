<template>
  <v-card flat class="gallery-page">
    <!-- 顶部标题栏 -->
    <v-card-title class="section-title d-flex align-center mb-4">
      <v-icon class="mr-2" color="primary" size="28">mdi-image-multiple</v-icon>
      <span class="text-h5 font-weight-bold">随机图库状态</span>
      <v-spacer />
      <div class="title-actions">
        <v-btn class="btn-gradient-status" size="small" @click="$emit('switch')">
          <v-icon class="btn-icon">mdi-cog</v-icon>
          <span class="btn-text">插件配置</span>
        </v-btn>
        <v-btn class="btn-gradient-close" size="small" @click="$emit('close')">
          <v-icon class="btn-icon">mdi-close</v-icon>
          <span class="btn-text">关闭</span>
        </v-btn>
      </div>
    </v-card-title>

    <!-- 主要内容区域：图片预览 + 状态卡片 -->
    <v-row class="main-content" align="stretch">
      <!-- 图片预览区域 - 左侧 -->
      <v-col cols="12" md="8">
        <v-card class="glass-card preview-card" elevation="4">
          <v-card-title class="preview-title-container">
            <div class="preview-title-left">
              <v-icon color="primary" size="24" class="mr-2">mdi-image-search</v-icon>
              <span>图片预览</span>
            </div>
            <div class="preview-title-right">
              <div class="preview-mode-selector">
                <button
                  :class="['mode-btn', previewType === 'pc' ? 'mode-btn-active' : '']"
                  @click="switchPreviewType('pc')"
                >
                  <v-icon size="16" class="mode-icon">mdi-monitor</v-icon>
                  <span class="mode-text">横屏</span>
                </button>
                <button
                  :class="['mode-btn', previewType === 'mobile' ? 'mode-btn-active' : '']"
                  @click="switchPreviewType('mobile')"
                >
                  <v-icon size="16" class="mode-icon">mdi-cellphone</v-icon>
                  <span class="mode-text">竖屏</span>
                </button>
                <button
                  :class="['mode-btn', previewType === 'auto' ? 'mode-btn-active' : '']"
                  @click="switchPreviewType('auto')"
                >
                  <v-icon size="16" class="mode-icon">mdi-auto-fix</v-icon>
                  <span class="mode-text">自动</span>
                </button>
                <div class="mode-separator"></div>
                <button
                  class="mode-btn mode-btn-refresh"
                  @click="loadPreview"
                  :disabled="previewLoading"
                >
                  <v-icon size="16" class="mode-icon" :class="{ 'rotating': previewLoading }">mdi-refresh</v-icon>
                  <span class="mode-text">刷新</span>
                </button>
                <button
                  class="mode-btn"
                  @click="openPreviewInNewTab"
                  :disabled="!previewImageUrl || previewLoading"
                >
                  <v-icon size="16" class="mode-icon">mdi-open-in-new</v-icon>
                  <span class="mode-text">打开</span>
                </button>
                <button
                  class="mode-btn"
                  @click="downloadPreview"
                  :disabled="!previewImageUrl || previewLoading"
                >
                  <v-icon size="16" class="mode-icon">mdi-download</v-icon>
                  <span class="mode-text">下载</span>
                </button>
              </div>
            </div>
          </v-card-title>
          <v-card-text>
            <div class="preview-container">
              <div v-if="previewLoading && !previewImageUrl" class="preview-loading">
                <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
                <div class="mt-4">正在加载图片...</div>
              </div>
              <div v-else-if="previewError" class="preview-error">
                <v-icon color="error" size="64">mdi-image-broken</v-icon>
                <div class="mt-4 text-error">{{ previewError }}</div>
                <v-btn color="primary" @click="loadPreview" class="mt-4">重试</v-btn>
              </div>
              <div v-else class="preview-image-container">
                <img
                  v-if="previewImageUrl"
                  :src="previewImageUrl"
                  :alt="'随机图片预览 - ' + previewType"
                  class="preview-image"
                  @load="previewLoading = false"
                  @error="handlePreviewError"
                />
                <div v-else class="preview-placeholder">
                  <v-icon color="grey" size="64">mdi-image</v-icon>
                  <div class="mt-4 text-grey">点击下方按钮预览图片</div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 状态卡片区域 - 右侧垂直排列 -->
      <v-col cols="12" md="4" style="height: 600px;">
        <v-row class="status-cards-vertical" dense>
          <!-- API 状态 -->
          <v-col cols="12">
            <v-card class="glass-card" elevation="4" style="height: 189px !important; min-height: 189px !important;">
              <v-card-title class="d-flex align-center">
                <v-icon :color="status.enable ? 'success' : 'grey'" size="24" class="mr-2">
                  {{ status.enable ? 'mdi-api' : 'mdi-api-off' }}
                </v-icon>
                <span>API 状态</span>
                <v-spacer />
                <button
                  class="mode-btn status-refresh-btn"
                  @click="refreshStatus"
                  :disabled="refreshing"
                >
                  <v-icon size="16" class="mode-icon" :class="{ 'rotating': refreshing }">mdi-refresh</v-icon>
                </button>
              </v-card-title>
              <v-card-text>
                <div class="api-runtime-row">
                  <span class="label">运行状态：</span>
                  <v-chip :color="status.enable ? 'success' : 'grey'" size="small">
                    {{ status.enable ? '可用' : '已禁用' }}
                  </v-chip>
                </div>
                <div class="api-health-grid">
                  <div
                    v-for="endpoint in apiHealthItems"
                    :key="endpoint.key"
                    class="api-health-item"
                  >
                    <div class="api-health-name">
                      <v-icon size="16" :color="endpoint.available ? 'success' : 'grey'">
                        {{ endpoint.icon }}
                      </v-icon>
                      <span>{{ endpoint.label }}</span>
                    </div>
                    <v-chip :color="endpoint.available ? 'success' : 'grey'" size="x-small">
                      {{ endpoint.available ? '正常' : '不可用' }}
                    </v-chip>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 目录监控 -->
          <v-col cols="12">
            <v-card class="glass-card" elevation="4" style="height: 189px !important; min-height: 189px !important;">
              <v-card-title class="d-flex align-center">
                <v-icon color="info" size="24" class="mr-2">mdi-folder-check</v-icon>
                <span>目录监控</span>
              </v-card-title>
              <v-card-text>
                <div class="source-monitor-grid">
                  <div
                    v-for="source in sourceMonitorItems"
                    :key="source.key"
                    class="source-monitor-item"
                  >
                    <div class="source-monitor-name">
                      <v-icon size="15" :color="source.configured ? 'success' : 'grey'">
                        {{ source.icon }}
                      </v-icon>
                      <span>{{ source.label }}</span>
                    </div>
                    <v-chip :color="source.configured ? 'success' : 'grey'" size="x-small">
                      {{ source.configured ? '已配置' : '未配置' }}
                    </v-chip>
                  </div>
                </div>
                <div class="source-complete-row">
                  <span class="label">配置完整性：</span>
                  <v-chip :color="sourceConfigComplete ? 'success' : 'warning'" size="small">
                    {{ sourceConfigComplete ? '完整' : '不完整' }}
                  </v-chip>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 图片统计 -->
          <v-col cols="12">
            <v-card class="glass-card" elevation="4" style="height: 190px !important; min-height: 190px !important;">
              <v-card-title class="d-flex align-center">
                <v-icon color="info" size="24" class="mr-2">mdi-image</v-icon>
                <span>图片统计</span>
              </v-card-title>
              <v-card-text>
                <div class="stats-grid">
                  <div class="stat-item">
                    <div class="stat-number">
                      {{ status.total_count || 0 }}
                    </div>
                    <div class="stat-label">总图片数</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-number">
                      {{ status.pc_count || 0 }}
                    </div>
                    <div class="stat-label">横屏图片</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-number">
                      {{ status.mobile_count || 0 }}
                    </div>
                    <div class="stat-label">竖屏图片</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-number" style="color:#ff9800;">{{ status.today_visits }}</div>
                    <div class="stat-label">今日访问</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!-- API 接口信息 -->
    <v-row class="mb-6 api-row">
      <v-col cols="12">
        <v-card class="glass-card" elevation="4">
          <v-card-title class="d-flex align-center">
            <v-icon color="success" size="24" class="mr-2">mdi-api</v-icon>
            <span>API 接口</span>
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="3">
                <div class="api-endpoint-card">
                  <div class="api-endpoint-header">
                    <div class="api-endpoint-icon">
                      <v-icon color="primary" size="24">mdi-web</v-icon>
                    </div>
                    <div class="api-endpoint-info">
                      <h3 class="api-endpoint-title">自动识别设备</h3>
                      <p class="api-endpoint-desc">根据设备类型自动返回横屏或竖屏图片</p>
                    </div>
                  </div>
                  <div class="api-url-container">
                    <div class="api-url">{{ getApiUrl('/random') }}</div>
                    <button class="api-copy-btn" @click="copyToClipboard(getApiUrl('/random'))" title="复制链接">
                      <v-icon size="16">mdi-content-copy</v-icon>
                    </button>
                  </div>
                </div>
              </v-col>
              <v-col cols="12" md="3">
                <div class="api-endpoint-card">
                  <div class="api-endpoint-header">
                    <div class="api-endpoint-icon">
                      <v-icon color="success" size="24">mdi-monitor</v-icon>
                    </div>
                    <div class="api-endpoint-info">
                      <h3 class="api-endpoint-title">指定横屏图片</h3>
                      <p class="api-endpoint-desc">强制返回横屏图片</p>
                    </div>
                  </div>
                  <div class="api-url-container">
                    <div class="api-url">{{ getApiUrl('/random?type=pc') }}</div>
                    <button class="api-copy-btn" @click="copyToClipboard(getApiUrl('/random?type=pc'))" title="复制链接">
                      <v-icon size="16">mdi-content-copy</v-icon>
                    </button>
                  </div>
                </div>
              </v-col>
              <v-col cols="12" md="3">
                <div class="api-endpoint-card">
                  <div class="api-endpoint-header">
                    <div class="api-endpoint-icon">
                      <v-icon color="warning" size="24">mdi-cellphone</v-icon>
                    </div>
                    <div class="api-endpoint-info">
                      <h3 class="api-endpoint-title">指定竖屏图片</h3>
                      <p class="api-endpoint-desc">强制返回竖屏图片</p>
                    </div>
                  </div>
                  <div class="api-url-container">
                    <div class="api-url">{{ getApiUrl('/random?type=mobile') }}</div>
                    <button class="api-copy-btn" @click="copyToClipboard(getApiUrl('/random?type=mobile'))" title="复制链接">
                      <v-icon size="16">mdi-content-copy</v-icon>
                    </button>
                  </div>
                </div>
              </v-col>
              <v-col cols="12" md="3">
                <div class="api-endpoint-card">
                  <div class="api-endpoint-header">
                    <div class="api-endpoint-icon">
                      <v-icon color="info" size="24">mdi-chart-bar</v-icon>
                    </div>
                    <div class="api-endpoint-info">
                      <h3 class="api-endpoint-title">统计数据</h3>
                      <p class="api-endpoint-desc">获取图片数量和访问统计</p>
                    </div>
                  </div>
                  <div class="api-url-container">
                    <div class="api-url">{{ getApiUrl('/stats') }}</div>
                    <button class="api-copy-btn" @click="copyToClipboard(getApiUrl('/stats'))" title="复制链接">
                      <v-icon size="16">mdi-content-copy</v-icon>
                    </button>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 更紧凑的底部操作栏 -->
    <v-divider></v-divider>

    <!-- 通知 -->
    <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>
    <v-alert v-if="errorMessage" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ errorMessage }}</v-alert>
  </v-card>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';

const props = defineProps({
  api: { type: Object, required: true }
});

defineEmits(['close', 'switch']);

// 响应式数据
const status = reactive({
  enable: false,
  api_status: "disabled",
  api_endpoints: {
    auto: false,
    pc: false,
    mobile: false,
    stats: false,
  },
  pc_path: "",
  mobile_path: "",
  pc_count: 0,
  mobile_count: 0,
  total_count: 0,
  today_visits: 0,
  network_image_url_pc: "",
  network_image_url_mobile: "",
  network_image_url: "",
});

// 新增：详细统计
const statusDetail = ref({
  local: { pc: 0, mobile: 0 },
  network: { pc: 0, mobile: 0 }
});

const apiHealthItems = computed(() => [
  {
    key: 'auto',
    label: '自动识别',
    icon: 'mdi-auto-fix',
    available: Boolean(status.api_endpoints?.auto),
  },
  {
    key: 'pc',
    label: '横屏图片',
    icon: 'mdi-monitor',
    available: Boolean(status.api_endpoints?.pc),
  },
  {
    key: 'mobile',
    label: '竖屏图片',
    icon: 'mdi-cellphone',
    available: Boolean(status.api_endpoints?.mobile),
  },
  {
    key: 'stats',
    label: '统计数据',
    icon: 'mdi-chart-box-outline',
    available: Boolean(status.api_endpoints?.stats),
  },
]);

const sourceMonitorItems = computed(() => {
  const commonNetworkConfigured = Boolean(status.network_image_url);
  return [
    {
      key: 'local-pc',
      label: '本地横屏',
      icon: 'mdi-monitor',
      configured: Boolean(status.pc_path),
    },
    {
      key: 'local-mobile',
      label: '本地竖屏',
      icon: 'mdi-cellphone',
      configured: Boolean(status.mobile_path),
    },
    {
      key: 'network-pc',
      label: '网络横屏',
      icon: 'mdi-cloud-outline',
      configured: Boolean(status.network_image_url_pc || commonNetworkConfigured),
    },
    {
      key: 'network-mobile',
      label: '网络竖屏',
      icon: 'mdi-cloud-outline',
      configured: Boolean(status.network_image_url_mobile || commonNetworkConfigured),
    },
  ];
});

const sourceConfigComplete = computed(() => {
  const pcConfigured = Boolean(
    status.pc_path || status.network_image_url_pc || status.network_image_url,
  );
  const mobileConfigured = Boolean(
    status.mobile_path || status.network_image_url_mobile || status.network_image_url,
  );
  return pcConfigured && mobileConfigured;
});

const previewType = ref('auto');
const previewImageUrl = ref('');
const previewObjectUrl = ref('');
const previewLoading = ref(false);
const previewError = ref('');

const refreshing = ref(false);

const successMessage = ref(null);
const errorMessage = ref(null);

const showNotification = (text, type = 'success') => {
  if (type === 'success') {
    successMessage.value = text;
    errorMessage.value = null;
  } else {
    errorMessage.value = text;
    successMessage.value = null;
  }
  // 3秒后自动清除消息
  setTimeout(() => {
    successMessage.value = null;
    errorMessage.value = null;
  }, 3000);
};

const getApiUrl = (endpoint) => {
  return `${window.location.origin}/api/v1/plugin/RandomPic${endpoint}`;
};

const refreshStatus = async () => {
  refreshing.value = true;
  try {
    const statusData = await props.api.get('plugin/RandomPic/status');
    Object.assign(status, statusData);
    if (statusData.detail) {
      statusDetail.value = statusData.detail;
    }
    showNotification('状态已刷新', 'success');
  } catch (error) {
    showNotification('刷新状态失败', 'error');
  } finally {
    refreshing.value = false;
  }
};

const loadPreview = async () => {
  if (!status.enable) {
    previewError.value = '插件未启用';
    previewLoading.value = false;
    return;
  }
  previewLoading.value = true;
  previewError.value = '';
  try {
    const params = previewType.value === 'auto' ? {} : { type: previewType.value };
    const image = await props.api.get('plugin/RandomPic/preview', {
      params: { ...params, t: Date.now() },
      responseType: 'blob',
    });
    if (previewObjectUrl.value) {
      URL.revokeObjectURL(previewObjectUrl.value);
    }
    previewObjectUrl.value = URL.createObjectURL(image);
    previewImageUrl.value = previewObjectUrl.value;
  } catch (error) {
    previewError.value = error?.response?.data?.detail || '加载预览失败';
    showNotification(previewError.value, 'error');
  } finally {
    previewLoading.value = false;
  }
};

const handlePreviewError = () => {
  previewLoading.value = false;
  previewError.value = '图片加载失败';
};

const switchPreviewType = (type) => {
  if (previewType.value === type) {
    // 如果点击的是当前已选中的类型，则刷新图片
    loadPreview();
  } else {
    // 如果点击的是不同的类型，则切换类型并自动刷新
    previewType.value = type;
    loadPreview();
  }
};

const downloadPreview = () => {
  // 直接取页面上 img 的 src，保证和显示一致
  const img = document.querySelector('.preview-image');
  if (!img || !img.src) return;
  const link = document.createElement('a');
  link.href = img.src;
  link.download = `random-image-${Date.now()}.jpg`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showNotification('图片下载已开始', 'success');
};

const openPreviewInNewTab = () => {
  const img = document.querySelector('.preview-image');
  if (!img || !img.src) return;
  window.open(img.src, '_blank');
};

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    showNotification('链接已复制到剪贴板', 'success');
  } catch (err) {
    // 降级方案：使用传统的复制方法
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showNotification('链接已复制到剪贴板', 'success');
  }
};

// 生命周期
onMounted(async () => {
  await refreshStatus();
  loadPreview();
});

onUnmounted(() => {
  if (previewObjectUrl.value) {
    URL.revokeObjectURL(previewObjectUrl.value);
  }
});
</script>

<style scoped>
.gallery-page {
  padding: 24px;
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  border-radius: 24px;
  padding-bottom: 0 !important;
}
.v-card:last-child {
  margin-bottom: 0 !important;
}
.theme-light .gallery-page {
  background: rgba(255,255,255,0.92) !important;
  border: 2px solid #42a5f5;
  box-shadow: 0 8px 32px 0 #90caf9cc, 0 2px 12px 0 #1976d244;
}
[data-theme="dark"] .gallery-page,
[data-theme="purple"] .gallery-page,
[data-theme="transparent"] .gallery-page {
  background: rgba(40,50,70,0.75) !important;
  border: 2px solid #00eaff77;
  box-shadow: 0 0 32px 0 #00eaff33;
}

.glass-card, .footer-actions {
  background: #ffffff !important;
  border: 1px solid #e6e8eb !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
  border-radius: 12px !important;
}
[data-theme="dark"] .glass-card,
[data-theme="dark"] .footer-actions,
[data-theme="purple"] .glass-card,
[data-theme="purple"] .footer-actions,
[data-theme="transparent"] .glass-card,
[data-theme="transparent"] .footer-actions {
  background: #20242c !important;
  border-color: #2a2f3a !important;
}

/* 主要内容区域布局 */
.main-content {
  align-items: stretch;
}

/* 图片预览区域样式 */
.preview-card {
  height: 600px !important;
  min-height: 600px !important;
  display: flex !important;
  flex-direction: column !important;
}
.preview-card > .v-card-text {
  flex: 1;
  min-height: 0;
  display: flex;
  padding-top: 16px !important;
  padding-bottom: 16px !important;
}
.preview-container {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  border-radius: 8px;
  background: transparent !important;
}
.preview-image-container {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent !important;
}
.preview-image {
  display: block;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  width: auto;
  height: auto;
  border-radius: 8px;
  background: transparent !important;
  box-shadow: none;
}
.preview-loading,
.preview-error,
.preview-placeholder {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* 状态卡片垂直排列样式 */
.status-cards-vertical.v-row {
  height: 100%;
  display: grid; /* 改用网格，避免 Vuetify Flex 冲突 */
  grid-template-rows: 189px 189px 190px; /* 三行高度总计600px */
  row-gap: 16px;
}

.status-cards-vertical > .v-col {
  width: 100%;
  display: flex;
}

/* Grid 行高已经固定，无需对子列逐个设高 */

.status-cards-vertical .v-card.glass-card {
  width: 100%;
  height: 100% !important;
  min-height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
  margin-bottom: 0 !important;
}
/* 状态卡片内容样式 */
.status-cards-vertical .v-card.glass-card .v-card-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.status-cards-vertical .v-card.glass-card .v-card-title {
  min-height: 44px;
  padding-bottom: 8px;
}
.status-cards-vertical .v-card.glass-card .v-card-text > *:last-child { 
  margin-bottom: 0; 
}
.status-cards-vertical .status-item { 
  margin-bottom: 8px; 
}

.section-title {
  color: #2b2f36;
  font-weight: 700;
  padding: 12px 0;
  letter-spacing: 0.2px;
}
[data-theme="dark"] .section-title,
[data-theme="purple"] .section-title,
[data-theme="transparent"] .section-title {
  color: #e6e8eb;
}

/* 复用 Config 标题栏按钮样式（柔和、素雅） */
.section-title .title-actions { display: flex; align-items: center; gap: 8px; }
.section-title .title-actions .v-btn {
  border-radius: 8px !important;
  padding: 4px 10px !important;
  min-height: 28px !important;
  box-shadow: none !important;
  border: 1px solid #e6e8eb !important;
  background: #f7f8fa !important;
  color: #374151 !important;
}
.section-title .title-actions .v-btn:hover { filter: brightness(0.98); }
[data-theme="dark"] .section-title .title-actions .v-btn,
[data-theme="purple"] .section-title .title-actions .v-btn,
[data-theme="transparent"] .section-title .title-actions .v-btn {
  border-color: #2a2f3a !important;
  background: #1f2430 !important;
  color: #e5e7eb !important;
}
.section-title .title-actions .btn-gradient-status { background: #e0f2fe !important; border-color: #bae6fd !important; color: #075985 !important; }
.section-title .title-actions .btn-gradient-save { background: #ecfdf5 !important; border-color: #d1fae5 !important; color: #065f46 !important; }
.section-title .title-actions .btn-gradient-close { background: #f3f4f6 !important; border-color: #e5e7eb !important; color: #374151 !important; }
[data-theme="dark"] .section-title .title-actions .btn-gradient-status,
[data-theme="purple"] .section-title .title-actions .btn-gradient-status,
[data-theme="transparent"] .section-title .title-actions .btn-gradient-status {
  background: #152433 !important;
  border-color: #1f2f40 !important;
  color: #93c5fd !important;
}

[data-theme="dark"] .section-title .title-actions .btn-gradient-save,
[data-theme="purple"] .section-title .title-actions .btn-gradient-save,
[data-theme="transparent"] .section-title .title-actions .btn-gradient-save {
  background: #1f2a24 !important;
  border-color: #24362c !important;
  color: #a7f3d0 !important;
}

[data-theme="dark"] .section-title .title-actions .btn-gradient-close,
[data-theme="purple"] .section-title .title-actions .btn-gradient-close,
[data-theme="transparent"] .section-title .title-actions .btn-gradient-close {
  background: #242a36 !important;
  border-color: #2f3643 !important;
  color: #e5e7eb !important;
}

/* 统一卡片风格为简洁卡片（与 Config 保持一致） */
.glass-card {
  margin-bottom: 8px;
  padding: 16px;
  min-height: 180px;
}

/* 删除所有 status-card、server-status、image-stats、dir-status、quick-actions、api-card、preview-card、api-bg-*、api-endpoint 的背景色、渐变色等自定义样式，只保留必要的布局和字体色 */

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.status-item .label {
  font-weight: 500;
  color: #6b7280;
}
.status-item .value {
  font-weight: 600;
  color: #374151;
}
.api-runtime-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.api-health-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  width: 100%;
}
.api-health-item {
  min-width: 0;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 5px 7px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}
.api-health-name {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #374151;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}
[data-theme="dark"] .api-health-item,
[data-theme="purple"] .api-health-item,
[data-theme="transparent"] .api-health-item {
  border-color: #2f3643;
  background: #1f2430;
}
[data-theme="dark"] .api-health-name,
[data-theme="purple"] .api-health-name,
[data-theme="transparent"] .api-health-name {
  color: #e5e7eb;
}
.source-monitor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  width: 100%;
}
.source-monitor-item {
  min-width: 0;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 4px 7px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}
.source-monitor-name {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #374151;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}
.source-complete-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
[data-theme="dark"] .source-monitor-item,
[data-theme="purple"] .source-monitor-item,
[data-theme="transparent"] .source-monitor-item {
  border-color: #2f3643;
  background: #1f2430;
}
[data-theme="dark"] .source-monitor-name,
[data-theme="purple"] .source-monitor-name,
[data-theme="transparent"] .source-monitor-name {
  color: #e5e7eb;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  min-height: 96px;
  align-items: center;
}
.stat-item {
  text-align: center;
  padding: 0;
  margin: 0;
}
.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #2b2f36;
}
[data-theme="dark"] .stat-number,
[data-theme="purple"] .stat-number,
[data-theme="transparent"] .stat-number {
  color: #e6e8eb;
}
.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.action-btn {
  width: 100%;
}

/* 恢复最初的API接口样式 */
.api-endpoint-card {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.api-endpoint-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
  flex: 1;
}

.api-endpoint-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.api-endpoint-info {
  flex: 1;
  min-width: 0;
}

.api-endpoint-title {
  font-size: 16px;
  font-weight: 600;
  color: #2b2f36;
  margin: 0 0 4px 0;
  line-height: 1.4;
}

[data-theme="dark"] .api-endpoint-title,
[data-theme="purple"] .api-endpoint-title,
[data-theme="transparent"] .api-endpoint-title {
  color: #e6e8eb;
}

.api-endpoint-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
  line-height: 1.4;
}

[data-theme="dark"] .api-endpoint-desc,
[data-theme="purple"] .api-endpoint-desc,
[data-theme="transparent"] .api-endpoint-desc {
  color: #9ca3af;
}

.api-url-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
}

.api-url {
  flex: 1;
  font-family: 'Courier New', monospace;
  background: none;
  padding: 8px 12px;
  border-radius: 4px;
  color: #374151;
  font-size: 14px;
  margin: 10px 0 8px 0;
  word-break: break-all;
  user-select: all;
}

[data-theme="dark"] .api-url,
[data-theme="purple"] .api-url,
[data-theme="transparent"] .api-url {
  color: #e5e7eb;
}

.api-copy-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  background: #f3f4f6;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.api-copy-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

[data-theme="dark"] .api-copy-btn,
[data-theme="purple"] .api-copy-btn,
[data-theme="transparent"] .api-copy-btn {
  background: #1f2937;
  color: #9ca3af;
}

[data-theme="dark"] .api-copy-btn:hover,
[data-theme="purple"] .api-copy-btn:hover,
[data-theme="transparent"] .api-copy-btn:hover {
  background: #374151;
  color: #d1d5db;
}

/* 统一顶部按钮样式（柔和） */
.btn-soft {
  background: #f7f8fa !important;
  color: #374151 !important;
  border: 1px solid #e6e8eb !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
.btn-soft:hover { filter: brightness(0.98); }
[data-theme="dark"] .btn-soft,
[data-theme="purple"] .btn-soft,
[data-theme="transparent"] .btn-soft {
  background: #1f2430 !important;
  color: #e5e7eb !important;
  border-color: #2a2f3a !important;
}
.endpoint-desc {
  font-size: 13px;
  color: #888;
}
.footer-actions {
  background: transparent;
  box-shadow: none;
  border-radius: 12px;
  margin-top: 16px;
  padding: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }
  .action-buttons {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .action-btn {
    width: auto;
    flex: 1;
  }
  .footer-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  /* API接口卡片移动端间距 */
  .api-row {
    margin-top: 32px !important;
  }
  
  /* API接口移动端样式 */
  .api-endpoint-card {
    padding: 14px;
  }
  
  .api-endpoint-header {
    margin-bottom: 6px;
    gap: 10px;
  }
  
  .api-endpoint-icon {
    width: 36px;
    height: 36px;
  }
  
  .api-endpoint-title {
    font-size: 15px;
  }
  
  .api-endpoint-desc {
    font-size: 12px;
  }
  
  .api-url {
    font-size: 12px;
    padding: 6px 10px;
  }
  
  .api-copy-btn {
    width: 28px;
    height: 28px;
  }
}

.btn-gradient-start {
  background: linear-gradient(90deg, #00e676 0%, #00bcd4 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 12px 0 #00e67655;
  border-radius: 10px;
  font-weight: 500;
  min-width: 120px;
}
.btn-gradient-start:hover {
  background: linear-gradient(90deg, #00bcd4 0%, #00e676 100%) !important;
}

.btn-gradient-stop {
  background: linear-gradient(90deg, #e040fb 0%, #ff4081 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 12px 0 #e040fb55;
  border-radius: 10px;
  font-weight: 500;
  min-width: 120px;
}
.btn-gradient-stop:hover {
  background: linear-gradient(90deg, #ff4081 0%, #e040fb 100%) !important;
}

/* 图片预览标题容器样式 */
.preview-title-container {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-title-left {
  display: flex;
  align-items: center;
}

.preview-title-right {
  margin-left: auto;
}

/* 全新的预览模式选择器样式 */
.preview-mode-selector {
  display: flex;
  background: #ffffff;
  border-radius: 14px;
  padding: 3px;
  border: 1px solid #e5e7eb;
  gap: 1px;
}

[data-theme="dark"] .preview-mode-selector,
[data-theme="purple"] .preview-mode-selector,
[data-theme="transparent"] .preview-mode-selector {
  background: #1f2937;
  border-color: #374151;
}

.mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  min-width: 60px;
  height: 30px;
  overflow: hidden;
}

.mode-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 12px;
}

.mode-btn-active::before {
  opacity: 1;
}

.mode-btn:hover::before {
  opacity: 0.1;
}

.mode-btn-active:hover::before {
  opacity: 1;
}

.mode-icon,
.mode-text {
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.mode-btn:hover .mode-icon,
.mode-btn:hover .mode-text {
  color: #4f46e5;
  transform: scale(1.05);
}

.mode-btn-active .mode-icon,
.mode-btn-active .mode-text {
  color: #ffffff;
  font-weight: 600;
}

.mode-btn-active:hover .mode-icon,
.mode-btn-active:hover .mode-text {
  color: #ffffff;
  transform: scale(1.05);
}

[data-theme="dark"] .mode-btn,
[data-theme="purple"] .mode-btn,
[data-theme="transparent"] .mode-btn {
  color: #9ca3af;
}

[data-theme="dark"] .mode-btn:hover .mode-icon,
[data-theme="dark"] .mode-btn:hover .mode-text,
[data-theme="purple"] .mode-btn:hover .mode-icon,
[data-theme="purple"] .mode-btn:hover .mode-text,
[data-theme="transparent"] .mode-btn:hover .mode-icon,
[data-theme="transparent"] .mode-btn:hover .mode-text {
  color: #d1d5db;
}

[data-theme="dark"] .mode-btn-active .mode-icon,
[data-theme="dark"] .mode-btn-active .mode-text,
[data-theme="purple"] .mode-btn-active .mode-icon,
[data-theme="purple"] .mode-btn-active .mode-text,
[data-theme="transparent"] .mode-btn-active .mode-icon,
[data-theme="transparent"] .mode-btn-active .mode-text {
  color: #ffffff;
}

/* 添加微妙的脉冲动画 */
.mode-btn-active::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    width: 40px;
    height: 40px;
    opacity: 0;
  }
}

/* 分隔符样式 */
.mode-separator {
  width: 1px;
  height: 20px;
  background: #e5e7eb;
  margin: 0 3px;
  align-self: center;
}

[data-theme="dark"] .mode-separator,
[data-theme="purple"] .mode-separator,
[data-theme="transparent"] .mode-separator {
  background: #374151;
}

/* 刷新按钮特殊样式 */
.mode-btn-refresh {
  background: #f3f4f6 !important;
  color: #6b7280 !important;
}

.mode-btn-refresh:hover {
  background: #e5e7eb !important;
  color: #374151 !important;
}

.mode-btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

[data-theme="dark"] .mode-btn-refresh,
[data-theme="purple"] .mode-btn-refresh,
[data-theme="transparent"] .mode-btn-refresh {
  background: #374151 !important;
  color: #d1d5db !important;
}

[data-theme="dark"] .mode-btn-refresh:hover,
[data-theme="purple"] .mode-btn-refresh:hover,
[data-theme="transparent"] .mode-btn-refresh:hover {
  background: #4b5563 !important;
  color: #f3f4f6 !important;
}

/* 旋转动画 */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 服务状态刷新按钮样式 - 参考图片预览按钮 */
.status-refresh-btn {
  min-width: 30px !important;
  width: 30px !important;
  height: 30px !important;
  padding: 6px !important;
  gap: 0 !important;
  background: #f3f4f6 !important;
  color: #6b7280 !important;
}

.status-refresh-btn:hover {
  background: #e5e7eb !important;
  color: #374151 !important;
}

.status-refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

[data-theme="dark"] .status-refresh-btn,
[data-theme="purple"] .status-refresh-btn,
[data-theme="transparent"] .status-refresh-btn {
  background: #2a2f3a !important;
  color: #6b7280 !important;
}

[data-theme="dark"] .status-refresh-btn:hover,
[data-theme="purple"] .status-refresh-btn:hover,
[data-theme="transparent"] .status-refresh-btn:hover {
  background: #374151 !important;
  color: #9ca3af !important;
}

[data-theme="dark"] .status-refresh-btn .mode-icon,
[data-theme="purple"] .status-refresh-btn .mode-icon,
[data-theme="transparent"] .status-refresh-btn .mode-icon {
  color: #6b7280 !important;
}

[data-theme="dark"] .status-refresh-btn:hover .mode-icon,
[data-theme="purple"] .status-refresh-btn:hover .mode-icon,
[data-theme="transparent"] .status-refresh-btn:hover .mode-icon {
  color: #9ca3af !important;
}

/* v-alert 样式 */
.v-alert {
  border-radius: 12px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

.v-alert:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15) !important;
}

[data-theme="dark"] .v-alert,
[data-theme="purple"] .v-alert,
[data-theme="transparent"] .v-alert {
  box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

[data-theme="dark"] .v-alert:hover,
[data-theme="purple"] .v-alert:hover,
[data-theme="transparent"] .v-alert:hover {
  box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
}

/* 系统深色模式兜底 */
@media (prefers-color-scheme: dark) {
  .api-copy-btn {
    background: #1f2937;
    color: #9ca3af;
  }
  .api-copy-btn:hover {
    background: #374151;
    color: #d1d5db;
  }
  .mode-btn {
    color: #9ca3af;
  }
  .mode-btn:hover .mode-icon,
  .mode-btn:hover .mode-text {
    color: #d1d5db;
  }
  .mode-btn-active .mode-icon,
  .mode-btn-active .mode-text {
    color: #ffffff;
  }
  .mode-btn-refresh {
    background: #374151 !important;
    color: #d1d5db !important;
  }
  .mode-btn-refresh:hover {
    background: #4b5563 !important;
    color: #f3f4f6 !important;
  }
  .status-refresh-btn {
    background: #2a2f3a !important;
    color: #6b7280 !important;
  }
  .status-refresh-btn:hover {
    background: #374151 !important;
    color: #9ca3af !important;
  }
  .status-refresh-btn .mode-icon {
    color: #6b7280 !important;
  }
  .status-refresh-btn:hover .mode-icon {
    color: #9ca3af !important;
  }
  .mode-separator {
    background: #374151;
  }
  .section-title .title-actions .btn-gradient-status {
    background: #152433 !important;
    border-color: #1f2f40 !important;
    color: #93c5fd !important;
  }
  .section-title .title-actions .btn-gradient-reset {
    background: #2a2224 !important;
    border-color: #3a2a2d !important;
    color: #fca5a5 !important;
  }
  .section-title .title-actions .btn-gradient-save {
    background: #1f2a24 !important;
    border-color: #24362c !important;
    color: #a7f3d0 !important;
  }
  .section-title .title-actions .btn-gradient-close {
    background: #242a36 !important;
    border-color: #2f3643 !important;
    color: #e5e7eb !important;
  }
  .gallery-page {
    background: rgba(40,50,70,0.75) !important;
    border: 2px solid #00eaff77;
    box-shadow: 0 0 32px 0 #00eaff33;
  }
  .glass-card, .footer-actions {
    background: #20242c !important;
    border-color: #2a2f3a !important;
  }
  .section-title {
    color: #e6e8eb;
  }
  .section-title .title-actions .v-btn {
    border-color: #2a2f3a !important;
    background: #1f2430 !important;
    color: #e5e7eb !important;
  }
  .port-error-text {
    color: #fca5a5;
    background: #2a2224;
    border-color: #3a2a2d;
  }
  .stat-number {
    color: #e6e8eb;
  }
  .api-endpoint-title {
    color: #e6e8eb;
  }
  .api-endpoint-desc {
    color: #9ca3af;
  }
  .api-url {
    color: #e5e7eb;
  }
  .btn-soft {
    background: #1f2430 !important;
    color: #e5e7eb !important;
    border-color: #2a2f3a !important;
  }
  .v-alert {
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
  }
  .v-alert:hover {
    box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  /* 主标题栏按钮 - 移动端只显示图标 */
  .title-actions .v-btn {
    min-width: 36px !important;
    width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .title-actions .btn-text {
    display: none;
  }
  
  .title-actions .btn-icon {
    margin: 0 !important;
    font-size: 18px !important;
  }
  
  .title-actions .v-btn .v-btn__content {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
  }
  
  /* 图片预览标题容器 - 移动端换行显示 */
  .preview-title-container {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .preview-title-right {
    margin-left: 0;
    width: 100%;
  }
  
  .preview-mode-selector {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    padding: 3px;
    gap: 3px;
    width: 100%;
  }
  
  .mode-btn {
    width: 100%;
    min-width: 0;
    padding: 6px 4px;
    height: 28px;
    font-size: 12px;
  }
  
  .mode-btn .mode-text {
    display: inline;
  }
  
  .mode-btn .mode-icon {
    font-size: 14px !important;
    margin-right: 4px !important;
  }
  
  .mode-separator {
    display: none;
  }
  
  /* 服务状态刷新按钮 - 移动端优化 */
  .status-refresh-btn {
    min-width: 24px !important;
    width: 24px !important;
    height: 24px !important;
    padding: 4px !important;
  }
  
  .status-refresh-btn .mode-icon {
    font-size: 12px !important;
  }
  
  /* 图片预览卡片 - 移动端动态高度 */
  .preview-card {
    height: auto !important;
    min-height: 200px !important;
  }
  
  .preview-card > .v-card-text {
    padding: 8px !important;
  }
  
  /* 图片预览容器 - 移动端自适应高度 */
  .preview-container {
    min-height: 150px !important;
    height: auto !important;
  }
  
  .preview-loading,
  .preview-error,
  .preview-placeholder {
    min-height: 150px !important;
    height: auto !important;
  }
  
  .preview-image-container {
    min-height: 150px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 4px !important;
  }
  
  .preview-image {
    max-width: 100% !important;
    max-height: 300px !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
  }
}

@media (max-width: 480px) {
  /* 超小屏幕进一步优化 */
  .preview-title-container {
    gap: 6px;
  }
  
  .preview-mode-selector {
    padding: 2px;
    gap: 2px;
  }
  
  .mode-btn {
    width: 100%;
    min-width: 0;
    padding: 4px 2px;
    height: 26px;
    font-size: 11px;
  }
  
  .mode-btn .mode-text {
    display: inline;
  }
  
  .mode-btn .mode-icon {
    font-size: 12px !important;
    margin-right: 3px !important;
  }
  
  .title-actions .v-btn {
    min-width: 32px !important;
    width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
  }
  
  .title-actions .btn-icon {
    font-size: 16px !important;
  }
  
  /* 超小屏幕图片预览卡片动态高度 */
  .preview-card {
    height: auto !important;
    min-height: 180px !important;
  }
  
  .preview-card > .v-card-text {
    padding: 6px !important;
  }
  
  /* 超小屏幕图片预览容器自适应高度 */
  .preview-container {
    min-height: 120px !important;
    height: auto !important;
  }
  
  .preview-loading,
  .preview-error,
  .preview-placeholder {
    min-height: 120px !important;
    height: auto !important;
  }
  
  .preview-image-container {
    min-height: 120px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 4px !important;
  }
  
  .preview-image {
    max-width: 100% !important;
    max-height: 250px !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
  }
  
  /* 超小屏幕API接口卡片间距 */
  .api-row {
    margin-top: 28px !important;
  }
  
  /* 超小屏幕图片统计布局 */
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 4px;
  }
  
  /* 超小屏幕API接口样式 */
  .api-endpoint-card {
    padding: 12px;
  }
  
  .api-endpoint-header {
    margin-bottom: 6px;
    gap: 8px;
  }
  
  .api-endpoint-icon {
    width: 32px;
    height: 32px;
  }
  
  .api-endpoint-title {
    font-size: 14px;
  }
  
  .api-endpoint-desc {
    font-size: 11px;
  }
  
  .api-url {
    font-size: 11px;
    padding: 6px 8px;
  }
  
  .api-copy-btn {
    width: 24px;
    height: 24px;
  }
}
</style> 