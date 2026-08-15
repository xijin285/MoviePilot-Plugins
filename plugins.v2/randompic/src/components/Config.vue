<template>
  <div class="plugin-config">
    <v-card flat class="rounded border">
      <v-card-text>
        <div class="config-wrapper">
          <div class="title-bar">
            <div class="title-left">
              <v-icon size="28" color="primary" class="mr-2">mdi-cog</v-icon>
              <div class="title-texts">
                <div class="title-main">图库配置</div>
                <div class="title-sub">配置您的随机图片服务</div>
              </div>
            </div>
            <div class="title-right">
              <div class="title-actions">
                <v-btn class="btn-gradient-status" @click="$emit('switch')" :disabled="saving" size="small">
                  <v-icon class="btn-icon">mdi-view-dashboard</v-icon>
                  <span class="btn-text">状态页</span>
                </v-btn>
                <v-btn class="btn-gradient-reset" @click="resetConfig" :disabled="saving" size="small">
                  <v-icon class="btn-icon">mdi-restore</v-icon>
                  <span class="btn-text">重置</span>
                </v-btn>
                <v-btn class="btn-gradient-save" :disabled="!isConfigValid() || saving" @click="saveConfig" :loading="saving" size="small">
                  <v-icon class="btn-icon">mdi-content-save</v-icon>
                  <span class="btn-text">保存配置</span>
                </v-btn>
                <v-btn class="btn-gradient-close" @click="$emit('close')" :disabled="saving" size="small">
                  <v-icon class="btn-icon">mdi-close</v-icon>
                  <span class="btn-text">关闭</span>
                </v-btn>
              </div>
            </div>
          </div>
          <div class="config-body">

        <!-- 基本设置 -->
        <div class="mp-card config-section basic-settings">
          <div class="card-overlay"></div>
          <div class="section-title">
            <v-icon class="mr-2" color="primary">mdi-tune</v-icon>
            基本设置
          </div>
          <div class="card-inner">
            <v-card-text>
              <v-row dense>
                <v-col cols="12">
                  <div class="config-switch-row">
                    <v-icon size="18" class="switch-icon" :color="config.enable ? 'success' : 'grey'">mdi-power</v-icon>
                    <span class="switch-label">启用插件</span>
                    <label class="switch">
                      <input type="checkbox" v-model="config.enable" />
                      <div class="slider">
                        <div class="circle">
                          <svg class="cross" viewBox="0 0 365.696 365.696" height="6" width="6" xmlns="http://www.w3.org/2000/svg">
                            <path fill="currentColor" d="M243.188 182.86 356.32 69.726c12.5-12.5 12.5-32.766 0-45.247L341.238 9.398c-12.504-12.503-32.77-12.503-45.25 0L182.86 122.528 69.727 9.374c-12.5-12.5-32.766-12.5-45.247 0L9.375 24.457c-12.5 12.504-12.5 32.77 0 45.25l113.152 113.152L9.398 295.99c-12.503 12.503-12.503 32.769 0 45.25L24.48 356.32c12.5 12.5 32.766 12.5 45.247 0l113.132-113.132L295.99 356.32c12.503 12.5 32.769 12.5 45.25 0l15.081-15.082c12.5-12.504 12.5-32.77 0-45.25zm0 0"></path>
                          </svg>
                          <svg class="checkmark" viewBox="0 0 24 24" height="10" width="10" xmlns="http://www.w3.org/2000/svg">
                            <path fill="currentColor" d="M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z"></path>
                          </svg>
                        </div>
                      </div>
                    </label>
                    <span class="service-mode-hint">API 由当前插件直接提供</span>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </div>
        </div>

        <!-- 本地目录配置 -->
        <div class="mp-card config-section local-directory-settings">
          <div class="card-overlay"></div>
          <div class="section-title">
            <v-icon class="mr-2" color="info">mdi-folder-multiple-image</v-icon>
            本地目录配置
          </div>
          <div class="card-inner">
            <v-card-text>
              <!-- 横屏本地目录 -->
              <v-row dense class="mb-4">
                <v-col cols="12">
                  <div class="directory-card pc-directory">
                    <div class="directory-header">
                      <v-icon color="primary" size="24" class="mr-2">mdi-monitor</v-icon>
                      <span class="directory-title">横屏本地图片目录</span>
                      <v-chip color="primary" size="small" class="ml-2">PC/横屏</v-chip>
                    </div>
                    <v-text-field
                      v-model="config.pc_path"
                      label="横屏图片路径"
                      :placeholder="defaultPcPath || '/path/pc/images'"
                      prepend-inner-icon="mdi-folder"
                      hint="留空时使用默认目录"
                      persistent-hint
                      dense
                    />
                  </div>
                </v-col>
              </v-row>
              <!-- 竖屏本地目录 -->
              <v-row dense>
                <v-col cols="12">
                  <div class="directory-card mobile-directory">
                    <div class="directory-header">
                      <v-icon color="success" size="24" class="mr-2">mdi-cellphone</v-icon>
                      <span class="directory-title">竖屏本地图片目录</span>
                      <v-chip color="success" size="small" class="ml-2">Mobile/竖屏</v-chip>
                    </div>
                    <v-text-field
                      v-model="config.mobile_path"
                      label="竖屏图片路径"
                      :placeholder="defaultMobilePath || '/path/mobile/images'"
                      prepend-inner-icon="mdi-folder"
                      hint="留空时使用默认目录"
                      persistent-hint
                      dense
                    />
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </div>
        </div>

        <!-- 网络目录配置 -->
        <div class="mp-card config-section network-directory-settings">
          <div class="card-overlay"></div>
          <div class="section-title">
            <v-icon class="mr-2" color="primary">mdi-link-variant</v-icon>
            网络目录配置
          </div>
          <div class="card-inner">
            <v-card-text>
              <!-- 横屏网络图片地址 -->
              <v-row dense class="mb-4">
                <v-col cols="12">
                  <div class="directory-card pc-directory">
                    <div class="directory-header">
                      <v-icon color="primary" size="24" class="mr-2">mdi-monitor</v-icon>
                      <span class="directory-title">横屏网络图片地址</span>
                      <v-chip color="primary" size="small" class="ml-2">PC/横屏</v-chip>
                    </div>
                    <v-text-field
                      v-model="config.network_image_url_pc"
                      label="横屏网络图片地址"
                      placeholder="https://example.com/your-pc-image.jpg，支持多个逗号分隔"
                      prepend-inner-icon="mdi-link"
                      hint="支持图片直链、API、json/txt等，多个用英文逗号分隔，优先级高于本地横屏目录"
                      persistent-hint
                      dense
                    />
                  </div>
                </v-col>
              </v-row>
              <!-- 竖屏网络图片地址 -->
              <v-row dense>
                <v-col cols="12">
                  <div class="directory-card mobile-directory">
                    <div class="directory-header">
                      <v-icon color="success" size="24" class="mr-2">mdi-cellphone-link</v-icon>
                      <span class="directory-title">竖屏网络图片地址</span>
                      <v-chip color="success" size="small" class="ml-2">Mobile/竖屏</v-chip>
                    </div>
                    <v-text-field
                      v-model="config.network_image_url_mobile"
                      label="竖屏网络图片地址"
                      placeholder="https://example.com/your-mobile-image.jpg，支持多个逗号分隔"
                      prepend-inner-icon="mdi-link"
                      hint="支持图片直链、API、json/txt等，多个用英文逗号分隔，优先级高于本地竖屏目录"
                      persistent-hint
                      dense
                    />
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </div>
        </div>
          </div>
        </div>

        <!-- 下载管理 -->
        <div class="mp-card config-section download-manage-settings">
          <div class="card-overlay"></div>
          <div class="section-title">
            <v-icon class="mr-2" color="warning">mdi-download-multiple</v-icon>
            下载管理
          </div>
          <div class="card-inner">
            <v-card-text>
              <v-row dense>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model.number="config.download_count"
                    label="候选图片数量"
                    type="number"
                    min="1"
                    max="100"
                    prepend-inner-icon="mdi-counter"
                    hint="预览时从网络源获取的候选图片数量（1-100）"
                    persistent-hint
                    dense
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="downloadSource"
                    :items="downloadSourceOptions"
                    label="下载源"
                    prepend-inner-icon="mdi-source-branch"
                    hint="Auto 同时使用横屏+竖屏网络源；PC/Mobile 仅使用对应网络源"
                    persistent-hint
                    dense
                    class="source-select"
                  />
                </v-col>
              </v-row>
              <v-row dense class="mt-1">
                <v-col cols="12">
                  <v-btn
                    color="warning"
                    variant="tonal"
                    :loading="candidateLoading"
                    :disabled="!config.enable || candidateLoading"
                    @click="loadCandidates"
                  >
                    <v-icon start size="18">mdi-image-search</v-icon>
                    预览候选图片
                  </v-btn>
                  <span class="download-status-text ml-3" :class="downloadStatusColor">
                    {{ downloadStatusText }}
                  </span>
                </v-col>
              </v-row>
              <v-row v-if="downloadProgressText" dense class="mt-1">
                <v-col cols="12">
                  <div class="download-progress-text">{{ downloadProgressText }}</div>
                </v-col>
              </v-row>
            </v-card-text>
          </div>
        </div>

        <!-- 候选图片选择对话框 -->
        <v-dialog v-model="candidateDialog" max-width="880" persistent>
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon color="warning" class="mr-2">mdi-image-multiple</v-icon>
              选择要下载的图片（已选 {{ selectedCount }}/{{ candidateItems.length }}）
              <v-spacer></v-spacer>
              <v-btn icon size="small" @click="candidateDialog = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <div v-if="candidateItems.length === 0" class="text-center py-6 text-grey">
                未获取到候选图片，请检查网络源配置
              </div>
              <div v-else class="candidate-grid">
                <div
                  v-for="(item, index) in candidateItems"
                  :key="item.url"
                  class="candidate-item"
                  :class="{ 'candidate-selected': item.selected }"
                  @click="toggleCandidate(index)"
                >
                  <img
                    :src="item.url"
                    :alt="'候选图片 ' + (index + 1)"
                    loading="lazy"
                    @error="handleImageError(index)"
                  />
                  <div class="candidate-check">
                    <v-icon v-if="item.selected" color="success" size="18">mdi-check-circle</v-icon>
                    <v-icon v-else color="white" size="18">mdi-checkbox-blank-circle-outline</v-icon>
                  </div>
                </div>
              </div>
            </v-card-text>
            <v-card-actions>
              <v-btn size="small" variant="tonal" @click="toggleAllCandidates">
                <v-icon start size="16">mdi-select-all</v-icon>
                {{ allSelected ? '取消全选' : '全选' }}
              </v-btn>
              <v-btn size="small" variant="tonal" @click="invertCandidates" class="ml-1">
                <v-icon start size="16">mdi-select-inverse</v-icon>
                反选
              </v-btn>
              <v-spacer></v-spacer>
              <v-btn size="small" variant="tonal" @click="candidateDialog = false">取消</v-btn>
              <v-btn
                color="warning"
                size="small"
                :disabled="selectedCount === 0 || downloadRunning"
                :loading="downloadRunning"
                @click="confirmDownload"
              >
                <v-icon start size="16">mdi-download</v-icon>
                确认下载（{{ selectedCount }}）
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- 通知 -->
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>
        <v-alert v-if="errorMessage" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ errorMessage }}</v-alert>
      </v-card-text>
      
      
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  api: { type: Object, required: true },
  initialConfig: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['close', 'switch', 'save', 'config-updated-on-server']);

// 响应式数据
const config = reactive({
  enable: false,
  pc_path: "",
  mobile_path: "",
  network_image_url_pc: "",
  network_image_url_mobile: "",
  network_image_url: "", // 兼容老配置
  download_count: 20,
});

// 默认本地目录（来自后端，用于空值占位提示）
const defaultPcPath = ref("");
const defaultMobilePath = ref("");

const saving = ref(false);

const successMessage = ref(null);
const errorMessage = ref(null);

// 下载管理
const downloadSource = ref('both');
const downloadSourceOptions = [
  { title: '横屏+竖屏（Auto）', value: 'both' },
  { title: '仅横屏源（PC）', value: 'pc' },
  { title: '仅竖屏源（Mobile）', value: 'mobile' },
];
const downloadRunning = ref(false);
const downloadStatus = ref(null);
let downloadPollTimer = null;

// 候选图片预览选择
const candidateDialog = ref(false);
const candidateLoading = ref(false);
const candidateItems = ref([]);

const selectedCount = computed(() => candidateItems.value.filter((item) => item.selected).length);
const allSelected = computed(
  () => candidateItems.value.length > 0 && selectedCount.value === candidateItems.value.length,
);

const downloadStatusText = computed(() => {
  if (downloadRunning.value) return '下载中...';
  if (!downloadStatus.value) return '尚未开始';
  const s = downloadStatus.value;
  if (s.running) return `下载中 ${s.done}/${s.total}`;
  return s.total > 0 ? '下载完成' : '无下载记录';
});

const downloadStatusColor = computed(() => {
  if (downloadRunning.value || downloadStatus.value?.running) return 'text-warning';
  if (downloadStatus.value?.total > 0) return 'text-success';
  return 'text-grey';
});

const downloadProgressText = computed(() => {
  const s = downloadStatus.value;
  if (!s || s.total === 0) return '';
  const pct = s.total > 0 ? Math.round((s.done / s.total) * 100) : 0;
  return `进度 ${pct}% | 完成 ${s.done}/${s.total} | 成功 ${s.success} | 横屏 ${s.pc_saved || 0} | 竖屏 ${s.mobile_saved || 0} | 失败 ${s.failed} | 跳过 ${s.skipped}`;
});

const loadCandidates = async () => {
  if (!config.enable) {
    showNotification('请先启用插件', 'error');
    return;
  }
  candidateLoading.value = true;
  try {
    const result = await props.api.get('plugin/RandomPic/download/candidates', {
      params: {
        source: downloadSource.value,
        count: Number(config.download_count) || 30,
      },
    });
    const urls = result?.data?.urls || [];
    candidateItems.value = urls.map((url) => ({ url, selected: true }));
    candidateDialog.value = true;
    if (urls.length === 0) {
      showNotification('未获取到候选图片，请检查网络源配置', 'error');
    }
  } catch (error) {
    showNotification('获取候选图片失败', 'error');
  } finally {
    candidateLoading.value = false;
  }
};

const toggleCandidate = (index) => {
  const item = candidateItems.value[index];
  if (item) {
    item.selected = !item.selected;
  }
};

const toggleAllCandidates = () => {
  const next = !allSelected.value;
  candidateItems.value.forEach((item) => {
    item.selected = next;
  });
};

const invertCandidates = () => {
  candidateItems.value.forEach((item) => {
    item.selected = !item.selected;
  });
};

const handleImageError = (index) => {
  const item = candidateItems.value[index];
  if (item) {
    item.url = '';
  }
};

const confirmDownload = async () => {
  const urls = candidateItems.value.filter((item) => item.selected && item.url).map((item) => item.url);
  if (urls.length === 0) {
    showNotification('未选择可用的图片地址', 'error');
    return;
  }
  downloadRunning.value = true;
  try {
    const result = await props.api.post('plugin/RandomPic/download', { urls });
    if (result && result.msg) {
      showNotification(result.msg, 'success');
    }
    candidateDialog.value = false;
    pollDownloadStatus();
  } catch (error) {
    downloadRunning.value = false;
    showNotification('启动下载失败', 'error');
  }
};

const pollDownloadStatus = async () => {
  stopPollDownloadStatus();
  downloadPollTimer = setInterval(async () => {
    try {
      const status = await props.api.get('plugin/RandomPic/download/status');
      downloadStatus.value = status || null;
      if (!status || !status.running) {
        downloadRunning.value = false;
        stopPollDownloadStatus();
      }
    } catch (error) {
      downloadRunning.value = false;
      stopPollDownloadStatus();
    }
  }, 2000);
};

const stopPollDownloadStatus = () => {
  if (downloadPollTimer) {
    clearInterval(downloadPollTimer);
    downloadPollTimer = null;
  }
};

const isConfigValid = () => {
  if (!config.enable) return true;
  const hasPc = (config.pc_path || defaultPcPath.value) || config.network_image_url_pc;
  const hasMobile = (config.mobile_path || defaultMobilePath.value) || config.network_image_url_mobile;
  return Boolean(hasPc && hasMobile);
};

// 方法
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

const resetConfig = () => {
  Object.assign(config, {
    enable: false,
    pc_path: "",
    mobile_path: "",
    network_image_url_pc: "",
    network_image_url_mobile: "",
    network_image_url: "",
    download_count: 20,
  });
  showNotification('配置已重置', 'success');
};

const saveConfig = async () => {
  if (!isConfigValid()) {
    showNotification('请完善配置信息', 'error');
    return;
  }

  saving.value = true;
  try {
    const payload = {
      enable: config.enable,
      pc_path: config.pc_path,
      mobile_path: config.mobile_path,
      network_image_url_pc: config.network_image_url_pc,
      network_image_url_mobile: config.network_image_url_mobile,
      network_image_url: config.network_image_url,
      download_count: config.download_count,
    };
    await props.api.post('plugin/RandomPic/config', payload);
    showNotification('配置保存成功', 'success');
    emit('save', JSON.parse(JSON.stringify(payload)));
    emit('config-updated-on-server', payload);
  } catch (error) {
    showNotification('配置保存失败', 'error');
  } finally {
    saving.value = false;
  }
};

// 生命周期
onMounted(() => {
  if (props.initialConfig) {
    Object.assign(config, props.initialConfig);
    defaultPcPath.value = props.initialConfig.default_pc_path || "";
    defaultMobilePath.value = props.initialConfig.default_mobile_path || "";
  }
  if (config.enable) {
    pollDownloadStatus();
  }
});

onUnmounted(() => {
  stopPollDownloadStatus();
});
</script>

<style scoped>
.plugin-page, .config-page {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  border-radius: 24px;
  padding: 0;
}
.theme-light .plugin-page, .theme-light .config-page {
  background: rgba(255,255,255,0.92) !important;
  border: 2px solid #42a5f5;
  box-shadow: 0 8px 32px 0 #90caf9cc, 0 2px 12px 0 #1976d244;
}
[data-theme="dark"] .plugin-page,
[data-theme="dark"] .config-page,
[data-theme="purple"] .plugin-page,
[data-theme="purple"] .config-page,
[data-theme="transparent"] .plugin-page,
[data-theme="transparent"] .config-page {
  background: rgba(40,50,70,0.75) !important;
  border: 2px solid #00eaff77;
  box-shadow: 0 0 32px 0 #00eaff33;
}

.config-page {
  background: transparent;
}

.config-header {
  margin-bottom: 24px;
}

.title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border: none;
  border-radius: 0;
  background: transparent;
}
[data-theme="dark"] .title-bar,
[data-theme="purple"] .title-bar,
[data-theme="transparent"] .title-bar {
  background: transparent;
  border-color: transparent;
}
.title-left {
  display: flex;
  align-items: center;
}
.title-texts {
  display: flex;
  flex-direction: column;
}
.title-main {
  font-weight: 700;
  font-size: 18px;
  color: #2b2f36;
}
[data-theme="dark"] .title-main,
[data-theme="purple"] .title-main,
[data-theme="transparent"] .title-main {
  color: #e6e8eb;
}
.title-sub,
.config-subtitle,
.subtitle {
  font-size: 12px;
  line-height: 1.4;
  color: #6b7280;
  margin-top: 2px;
}
[data-theme="dark"] .title-sub,
[data-theme="dark"] .config-subtitle,
[data-theme="dark"] .subtitle,
[data-theme="purple"] .title-sub,
[data-theme="purple"] .config-subtitle,
[data-theme="purple"] .subtitle,
[data-theme="transparent"] .title-sub,
[data-theme="transparent"] .config-subtitle,
[data-theme="transparent"] .subtitle {
  color: #9aa3b2;
}
.title-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-actions { display: flex; align-items: center; gap: 8px; }
.title-actions .v-btn {
  border-radius: 8px !important;
  padding: 4px 10px !important;
  min-height: 28px !important;
  box-shadow: none !important;
  border: 1px solid #e6e8eb !important;
  background: #f7f8fa !important;
  color: #374151 !important;
}
.title-actions .v-btn:hover { filter: brightness(0.98); }
[data-theme="dark"] .title-actions .v-btn,
[data-theme="purple"] .title-actions .v-btn,
[data-theme="transparent"] .title-actions .v-btn {
  border-color: #2a2f3a !important;
  background: #1f2430 !important;
  color: #e5e7eb !important;
}

/* 更柔和的语义配色（仅标题栏按钮） */
.title-actions .btn-gradient-status { background: #e0f2fe !important; border-color: #bae6fd !important; color: #075985 !important; }
.title-actions .btn-gradient-reset { background: #fef2f2 !important; border-color: #fde2e2 !important; color: #991b1b !important; }
.title-actions .btn-gradient-save { background: #ecfdf5 !important; border-color: #d1fae5 !important; color: #065f46 !important; }
.title-actions .btn-gradient-close { background: #f3f4f6 !important; border-color: #e5e7eb !important; color: #374151 !important; }
[data-theme="dark"] .title-actions .btn-gradient-status,
[data-theme="purple"] .title-actions .btn-gradient-status,
[data-theme="transparent"] .title-actions .btn-gradient-status {
  background: #152433 !important;
  border-color: #1f2f40 !important;
  color: #93c5fd !important;
}

[data-theme="dark"] .title-actions .btn-gradient-reset,
[data-theme="purple"] .title-actions .btn-gradient-reset,
[data-theme="transparent"] .title-actions .btn-gradient-reset {
  background: #2a2224 !important;
  border-color: #3a2a2d !important;
  color: #fca5a5 !important;
}

[data-theme="dark"] .title-actions .btn-gradient-save,
[data-theme="purple"] .title-actions .btn-gradient-save,
[data-theme="transparent"] .title-actions .btn-gradient-save {
  background: #1f2a24 !important;
  border-color: #24362c !important;
  color: #a7f3d0 !important;
}

[data-theme="dark"] .title-actions .btn-gradient-close,
[data-theme="purple"] .title-actions .btn-gradient-close,
[data-theme="transparent"] .title-actions .btn-gradient-close {
  background: #242a36 !important;
  border-color: #2f3643 !important;
  color: #e5e7eb !important;
}
.url-preview {
  display: flex;
  align-items: center;
}
.url-preview .mono {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #374151;
}
[data-theme="dark"] .url-preview .mono,
[data-theme="purple"] .url-preview .mono,
[data-theme="transparent"] .url-preview .mono {
  color: #e5e7eb;
}

.mp-card {
  --bg: #fafbfc;
  --contrast: #ffffff;
  --border: #e6e8eb;
  position: relative;
  padding: 8px;
  background-color: transparent;
  border-radius: 12px;
  border: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  overflow: hidden;
}

[data-theme="dark"] .mp-card,
[data-theme="purple"] .mp-card,
[data-theme="transparent"] .mp-card {
  --bg: #20242c;
  --contrast: #1a1f27;
  --border: #2a2f3a;
}

.mp-card .card-overlay {
  display: none;
}

.mp-card .card-inner {
  background-color: var(--contrast);
  border-radius: 10px;
  padding: 12px;
}

/* 强制使基本设置呈现卡片视觉，覆盖先前将 .basic-settings 透明化的规则 */
.mp-card.basic-settings {
  background-color: var(--bg) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
  padding: 8px !important;
  border-radius: 12px !important;
}

/* 统一本地目录配置、网络目录配置与基本设置的卡片视觉 */
.mp-card.local-directory-settings,
.mp-card.network-directory-settings {
  background-color: var(--bg) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
  padding: 8px !important;
  border-radius: 12px !important;
}

.gallery-visual {
  position: relative;
  text-align: center;
  padding: 20px 0;
  background: var(--header-bg, #f7f8fa);
  border-radius: 12px;
  border: 1px solid #e6e8eb;
  overflow: hidden;
}
[data-theme="dark"] .gallery-visual,
[data-theme="purple"] .gallery-visual,
[data-theme="transparent"] .gallery-visual {
  --header-bg: #1e232b;
  border-color: #2a2f3a;
}

.floating-images {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.floating-image {
  display: none;
}

.floating-image.img-1 {
  top: 20%;
  left: 15%;
  width: 80px;
  height: 80px;
}

.floating-image.img-2 {
  top: 60%;
  right: 20%;
  width: 60px;
  height: 60px;
}

.floating-image.img-3 {
  top: 30%;
  right: 10%;
  width: 40px;
  height: 40px;
}

.config-title {
  color: #2b2f36;
  margin-bottom: 4px;
  position: relative;
  z-index: 1;
}
[data-theme="dark"] .config-title,
[data-theme="purple"] .config-title,
[data-theme="transparent"] .config-title {
  color: #e6e8eb;
}

.config-subtitle { position: relative; z-index: 1; }

.config-section,
.glass-card {
  margin-bottom: 8px !important;
}

/* 玻璃拟态样式 */
.glass-card {
  background: rgba(40, 50, 70, 0.75);
  border-radius: 18px;
  box-shadow: 0 4px 32px 0 #00eaff22, 0 1.5px 8px 0 #0006;
  backdrop-filter: blur(8px);
  border: 1.5px solid #00eaff33;
  margin-bottom: 2px !important;
  padding: 24px 32px 16px 32px;
}
.section-title {
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  color: #2b2f36;
  margin-bottom: 6px;
  letter-spacing: 0.2px;
}
[data-theme="dark"] .section-title,
[data-theme="purple"] .section-title,
[data-theme="transparent"] .section-title {
  color: #e6e8eb;
}

.config-switch {
  margin-bottom: 8px;
}

/* Custom switch styles for enable toggle */
.config-switch-row { display: flex; align-items: center; gap: 10px; transform: translateY(-2px); }
.service-mode-hint {
  margin-left: auto;
  color: #6b7280;
  font-size: 12px;
}
[data-theme="dark"] .service-mode-hint,
[data-theme="purple"] .service-mode-hint,
[data-theme="transparent"] .service-mode-hint {
  color: #9ca3af;
}
.config-switch-row .switch-label { font-size: 14px; color: #374151; }
[data-theme="dark"] .config-switch-row .switch-label,
[data-theme="purple"] .config-switch-row .switch-label,
[data-theme="transparent"] .config-switch-row .switch-label {
  color: #e5e7eb;
}
.config-switch-row .switch-icon { opacity: 0.95; transition: color .2s ease; }

.switch {
  --switch-width: 46px;
  --switch-height: 24px;
  --switch-bg: rgb(131, 131, 131);
  --switch-checked-bg: rgb(0, 218, 80);
  --circle-diameter: 18px;
  --circle-bg: #fff;
  --circle-shadow: 1px 1px 2px rgba(146, 146, 146, 0.45);
  --circle-checked-shadow: -1px 1px 2px rgba(163, 163, 163, 0.45);
  --switch-transition: all .2s cubic-bezier(0.27, 0.2, 0.25, 1.51);
  --circle-transition: var(--switch-transition);
  --icon-transition: all .2s cubic-bezier(0.27, 0.2, 0.25, 1.51);
  --icon-cross-color: var(--switch-bg);
  --icon-cross-size: 6px;
  --icon-checkmark-color: var(--switch-checked-bg);
  --icon-checkmark-size: 10px;
  --effect-width: calc(var(--circle-diameter) / 2);
  --effect-height: calc(var(--effect-width) / 2 - 1px);
  --effect-bg: var(--circle-bg);
  --effect-border-radius: 1px;
  --effect-transition: all .2s ease-in-out;
  display: inline-block;
}
.switch input { display: none; }
.switch svg { transition: var(--icon-transition); position: absolute; height: auto; }
.switch .checkmark { width: var(--icon-checkmark-size); color: var(--icon-checkmark-color); transform: scale(0); }
.switch .cross { width: var(--icon-cross-size); color: var(--icon-cross-color); }
.slider {
  box-sizing: border-box;
  width: var(--switch-width);
  height: var(--switch-height);
  background: var(--switch-bg);
  border-radius: 999px;
  display: flex;
  align-items: center;
  position: relative;
  transition: var(--switch-transition);
  cursor: pointer;
}
.circle {
  width: var(--circle-diameter);
  height: var(--circle-diameter);
  background: var(--circle-bg);
  border-radius: inherit;
  box-shadow: var(--circle-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--circle-transition);
  z-index: 1;
  position: absolute;
  left: calc((var(--switch-height) - var(--circle-diameter)) / 2);
}
.slider::before {
  content: "";
  position: absolute;
  width: var(--effect-width);
  height: var(--effect-height);
  left: calc((var(--switch-height) - var(--circle-diameter)) / 2 + (var(--effect-width) / 2));
  background: var(--effect-bg);
  border-radius: var(--effect-border-radius);
  transition: var(--effect-transition);
}
.switch input:checked + .slider { background: var(--switch-checked-bg); }
.switch input:checked + .slider .checkmark { transform: scale(1); }
.switch input:checked + .slider .cross { transform: scale(0); }
.switch input:checked + .slider::before {
  left: calc(100% - var(--effect-width) - (var(--effect-width) / 2) - ((var(--switch-height) - var(--circle-diameter)) / 2));
}
.switch input:checked + .slider .circle {
  left: calc(100% - var(--circle-diameter) - ((var(--switch-height) - var(--circle-diameter)) / 2));
  box-shadow: var(--circle-checked-shadow);
}

.directory-card {
  padding: 8px 0 0 0;
  border-radius: 6px;
  border: none;
  background: transparent;
  box-shadow: none;
}

.directory-card:hover { box-shadow: none; }

.pc-directory {
  background: transparent;
  border: none;
}

.mobile-directory {
  background: transparent;
  border: none;
}

.directory-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.directory-title {
  font-weight: 600;
}

/* 下载源下拉：图标与文字分开一点 */
.source-select :deep(.v-field__prepend-inner) {
  padding-inline-end: 8px;
}
.source-select :deep(.v-field__input) {
  padding-inline-start: 4px;
}
/* 下拉面板选项内图标与文字的间距 */
.source-select :deep(.v-list-item__content) {
  margin-inline-start: 4px;
}

.candidate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  max-height: 480px;
  overflow-y: auto;
}
.candidate-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #e6e8eb;
  cursor: pointer;
  background: #f3f4f6;
}
.candidate-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.candidate-item.candidate-selected {
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
}
.candidate-check {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 50%;
  padding: 1px;
  line-height: 1;
}
[data-theme="dark"] .candidate-item,
[data-theme="purple"] .candidate-item,
[data-theme="transparent"] .candidate-item {
  border-color: #2f3643;
}
.download-status-text {
  font-size: 13px;
  font-weight: 600;
}
.download-progress-text {
  font-size: 12px;
  color: #6b7280;
  background: rgba(127, 127, 127, 0.08);
  border-radius: 8px;
  padding: 8px 12px;
  font-family: 'Courier New', monospace;
}
[data-theme="dark"] .download-progress-text,
[data-theme="purple"] .download-progress-text,
[data-theme="transparent"] .download-progress-text {
  color: #9ca3af;
}
.directory-info {
  display: flex;
  align-items: center;
  margin-top: 8px;
}

.info-text {
  font-size: 12px;
  color: #666;
}

.status-preview-card {
  padding: 16px;
  border-radius: 8px;
  background: transparent;
  border: none;
  box-shadow: none;
}

.status-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}
[data-theme="dark"] .status-header,
[data-theme="purple"] .status-header,
[data-theme="transparent"] .status-header {
  color: #d1d5db;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-item .label {
  font-weight: 500;
  color: #6b7280;
}

.status-item .value {
  font-weight: 600;
  color: #374151;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
[data-theme="dark"] .status-item .value,
[data-theme="purple"] .status-item .value,
[data-theme="transparent"] .status-item .value {
  color: #e5e7eb;
}

.action-btns {
  display: flex;
  justify-content: flex-end;
  gap: 18px;
  margin-top: 24px;
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 12px;
  padding: 0;
}
.glow-btn {
  border-radius: 10px;
  font-weight: 500;
  min-width: 120px;
  background: linear-gradient(90deg, #00eaff 0%, #3f51b5 100%);
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #00eaff55;
  transition: box-shadow 0.3s, background 0.3s;
}
.glow-btn:hover {
  box-shadow: 0 4px 32px 0 #00eaffcc;
  background: linear-gradient(90deg, #3f51b5 0%, #00eaff 100%);
}

.v-alert {
  background: transparent !important;
  box-shadow: none !important;
}

.glass-card.config-section,
.basic-settings,
.directory-settings {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.config-section.usage-info {
  margin-top: 2px !important;
}

.gallery-visual,
.floating-image,
.config-header,
.back-btn-wrapper,
.config-title,
.config-subtitle,
.directory-header,
.directory-info,
.info-text,
.section-title,
.v-card-title,
.v-card-text,
.action-btns,
.preview-url,
.preview-container,
.preview-placeholder,
.preview-loading,
.preview-error,
.preview-image-container {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

/* 彻底去除底部左下角角块，全局兜底 */
.plugin-page > *,
.plugin-page *::before,
.plugin-page *::after,
.plugin-page::before,
.plugin-page::after {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

@media (max-width: 768px) {
  .config-switch-row {
    flex-wrap: wrap;
  }
  .service-mode-hint {
    width: 100%;
    margin-left: 28px;
  }
  .action-btns {
    flex-direction: column;
    gap: 10px;
  }
  .glow-btn {
    width: 100%;
    min-width: 0;
    margin: 0;
  }
  
  .floating-image {
    display: none;
  }
  
  .config-title {
    font-size: 24px;
  }
  
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
}

@media (max-width: 480px) {
  /* 超小屏幕进一步优化 */
  .title-actions .v-btn {
    min-width: 32px !important;
    width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
  }
  
  .title-actions .btn-icon {
    font-size: 16px !important;
  }
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
  .plugin-page, .config-page {
    background: rgba(40,50,70,0.75) !important;
    border: 2px solid #00eaff77;
    box-shadow: 0 0 32px 0 #00eaff33;
  }
  .title-bar {
    background: transparent;
    border-color: transparent;
  }
  .title-main {
    color: #e6e8eb;
  }
  .title-sub,
  .config-subtitle,
  .subtitle {
    color: #9aa3b2;
  }
  .title-actions .v-btn {
    border-color: #2a2f3a !important;
    background: #1f2430 !important;
    color: #e5e7eb !important;
  }
  .title-actions .btn-gradient-status {
    background: #152433 !important;
    border-color: #1f2f40 !important;
    color: #93c5fd !important;
  }
  .title-actions .btn-gradient-reset {
    background: #2a2224 !important;
    border-color: #3a2a2d !important;
    color: #fca5a5 !important;
  }
  .title-actions .btn-gradient-save {
    background: #1f2a24 !important;
    border-color: #24362c !important;
    color: #a7f3d0 !important;
  }
  .title-actions .btn-gradient-close {
    background: #242a36 !important;
    border-color: #2f3643 !important;
    color: #e5e7eb !important;
  }
  .url-preview .mono {
    color: #e5e7eb;
  }
  .mp-card {
    --bg: #20242c;
    --contrast: #1a1f27;
    --border: #2a2f3a;
  }
  .gallery-visual {
    --header-bg: #1e232b;
    border-color: #2a2f3a;
  }
  .config-title {
    color: #e6e8eb;
  }
  .section-title {
    color: #e6e8eb;
  }
  .config-switch-row .switch-label {
    color: #e5e7eb;
  }
  .status-header {
    color: #d1d5db;
  }
  .status-item .value {
    color: #e5e7eb;
  }
  .v-alert {
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
  }
  .v-alert:hover {
    box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
  }
}

.btn-gradient-status {
  background: #4f46e5 !important;
  color: #fff !important;
  box-shadow: none !important;
}
.btn-gradient-status:hover { filter: brightness(0.95); }

.btn-gradient-reset {
  background: #ef4444 !important;
  color: #fff !important;
  box-shadow: none !important;
}
.btn-gradient-reset:hover { filter: brightness(0.95); }

.btn-gradient-save {
  background: #10b981 !important;
  color: #fff !important;
  box-shadow: none !important;
}
.btn-gradient-save:hover { filter: brightness(0.95); }

.btn-gradient-close {
  background: #6b7280 !important;
  color: #fff !important;
  box-shadow: none !important;
}
.btn-gradient-close:hover { filter: brightness(0.95); }
</style> 