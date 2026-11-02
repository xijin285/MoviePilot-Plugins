<template>
  <div class="app-page">
    <!-- 顶部标题栏 -->
    <div class="page-header d-flex align-center flex-wrap ga-3 mb-4">
      <v-icon color="primary" size="28">mdi-image-multiple-outline</v-icon>
      <span class="text-h5 font-weight-bold">随机图库仪表盘</span>
      <v-chip :color="status.enable ? 'success' : 'grey'" size="small" variant="tonal">
        {{ status.enable ? 'API 可用' : 'API 已禁用' }}
      </v-chip>
      <v-spacer />
      <v-btn size="small" variant="tonal" color="primary" :loading="refreshing" @click="refreshAll">
        <v-icon size="16" class="mr-1">mdi-refresh</v-icon>
        刷新
      </v-btn>
    </div>

    <!-- 统计卡片行 -->
    <v-row dense class="mb-1">
      <v-col cols="6" md="3" v-for="card in statCards" :key="card.label">
        <v-card class="stat-card" elevation="2">
          <div class="stat-card-icon" :style="{ background: card.bg }">
            <v-icon :color="card.color" size="26">{{ card.icon }}</v-icon>
          </div>
          <div class="stat-card-body">
            <div class="stat-card-number">{{ card.value }}</div>
            <div class="stat-card-label">{{ card.label }}</div>
            <div class="stat-card-sub" v-if="card.sub">{{ card.sub }}</div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row align="stretch">
      <!-- 左侧：图片预览 -->
      <v-col cols="12" md="7">
        <v-card class="glass-card fill-height" elevation="4">
          <v-card-title class="d-flex align-center flex-wrap ga-2">
            <v-icon color="primary" size="22" class="mr-1">mdi-image-search</v-icon>
            <span>图片预览</span>
            <v-spacer />
            <div class="mode-selector">
              <button
                v-for="t in previewTypes"
                :key="t.key"
                :class="['mode-btn', previewType === t.key ? 'mode-btn-active' : '']"
                @click="switchPreviewType(t.key)"
              >
                <v-icon size="15" class="mode-icon">{{ t.icon }}</v-icon>
                <span class="mode-text">{{ t.label }}</span>
              </button>
              <div class="mode-separator"></div>
              <button class="mode-btn" @click="loadPreview" :disabled="previewLoading">
                <v-icon size="15" class="mode-icon" :class="{ rotating: previewLoading }">mdi-refresh</v-icon>
                <span class="mode-text">换一张</span>
              </button>
              <button class="mode-btn" @click="savePreviewToLocal" :disabled="!previewImageUrl || savingToLocal">
                <v-icon size="15" class="mode-icon">mdi-folder-download</v-icon>
                <span class="mode-text">收藏</span>
              </button>
            </div>
          </v-card-title>
          <v-card-text>
            <div class="preview-container">
              <div v-if="previewLoading && !previewImageUrl" class="preview-center">
                <v-progress-circular indeterminate color="primary" size="56" />
                <div class="mt-3 text-medium-emphasis">正在加载图片...</div>
              </div>
              <div v-else-if="previewError" class="preview-center">
                <v-icon color="error" size="56">mdi-image-broken</v-icon>
                <div class="mt-3 text-error">{{ previewError }}</div>
                <v-btn color="primary" variant="tonal" class="mt-3" @click="loadPreview">重试</v-btn>
              </div>
              <div v-else-if="previewImageUrl" class="preview-image-wrap">
                <img
                  :src="previewImageUrl"
                  class="preview-image"
                  alt="随机图片预览"
                  @error="handlePreviewError"
                />
              </div>
              <div v-else class="preview-center">
                <v-icon color="grey" size="56">mdi-image</v-icon>
                <div class="mt-3 text-medium-emphasis">暂无预览</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 右侧：运行状态 + 下载任务 -->
      <v-col cols="12" md="5">
        <v-card class="glass-card mb-4" elevation="4">
          <v-card-title class="d-flex align-center">
            <v-icon color="info" size="22" class="mr-1">mdi-heart-pulse</v-icon>
            <span>运行状态</span>
            <v-spacer />
            <v-btn
              size="x-small"
              variant="text"
              color="info"
              :loading="pinging"
              @click="runPing"
            >
              <v-icon size="14" class="mr-1">mdi-speedometer</v-icon>
              测速
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div class="source-grid">
              <div v-for="s in sourceMonitorItems" :key="s.key" class="source-item">
                <div class="source-name">
                  <v-icon size="15" :color="s.configured ? 'success' : 'grey'">{{ s.icon }}</v-icon>
                  <span>{{ s.label }}</span>
                </div>
                <span class="source-count">{{ s.count }}</span>
                <v-chip :color="s.configured ? 'success' : 'grey'" size="x-small" variant="tonal">
                  {{ s.configured ? '已配置' : '未配置' }}
                </v-chip>
              </div>
            </div>
            <template v-if="pingResults">
              <v-divider class="my-3" />
              <div class="d-flex flex-wrap ga-2">
                <v-chip
                  v-for="(r, key) in pingResults"
                  :key="key"
                  size="small"
                  :color="!r.configured ? 'grey' : r.ok ? 'success' : 'error'"
                  variant="tonal"
                >
                  <v-icon size="13" class="mr-1">
                    {{ !r.configured ? 'mdi-minus' : r.ok ? 'mdi-check' : 'mdi-close' }}
                  </v-icon>
                  {{ r.label }}
                  <span v-if="r.configured && r.ok" class="ml-1 font-weight-bold">{{ r.ms }}ms</span>
                  <span v-else-if="r.configured" class="ml-1">失败</span>
                  <span v-else class="ml-1">未配置</span>
                </v-chip>
              </div>
            </template>
          </v-card-text>
        </v-card>

        <v-card class="glass-card" elevation="4">
          <v-card-title class="d-flex align-center">
            <v-icon color="warning" size="22" class="mr-1">mdi-cloud-download</v-icon>
            <span>网络图片下载</span>
          </v-card-title>
          <v-card-text>
            <div class="d-flex align-center flex-wrap ga-2 mb-3">
              <v-text-field
                v-model="downloadCount"
                type="number"
                min="1"
                max="500"
                density="compact"
                hide-details
                label="数量"
                style="max-width: 96px"
              />
              <v-select
                v-model="downloadSource"
                :items="downloadSources"
                density="compact"
                hide-details
                label="来源"
                style="max-width: 130px"
              />
              <v-btn
                color="primary"
                variant="tonal"
                :disabled="downloadStatus.running"
                @click="startDownload"
              >
                <v-icon size="16" class="mr-1">mdi-play</v-icon>
                立即下载
              </v-btn>
            </div>
            <template v-if="downloadStatus.running || downloadStatus.total">
              <div class="text-caption text-medium-emphasis mb-1">
                {{ downloadStatus.message || '下载任务' }}
                <span v-if="downloadStatus.total">
                  （{{ downloadStatus.done }}/{{ downloadStatus.total }}）
                </span>
              </div>
              <v-progress-linear
                :model-value="downloadProgress"
                color="primary"
                height="8"
                rounded
                class="mb-2"
              />
              <div class="text-caption d-flex ga-3">
                <span class="text-success">成功 {{ downloadStatus.success || 0 }}</span>
                <span class="text-info">横屏 {{ downloadStatus.pc_saved || 0 }}</span>
                <span class="text-info">竖屏 {{ downloadStatus.mobile_saved || 0 }}</span>
                <span class="text-warning">跳过 {{ downloadStatus.skipped || 0 }}</span>
                <span class="text-error">失败 {{ downloadStatus.failed || 0 }}</span>
              </div>
            </template>
            <div v-else class="text-caption text-medium-emphasis">
              从配置的网络图源批量下载图片，自动按横竖屏分类保存到本地目录。
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 访问统计 -->
    <v-card class="glass-card mt-4" elevation="4">
      <v-card-title class="d-flex align-center">
        <v-icon color="warning" size="22" class="mr-1">mdi-chart-areaspline</v-icon>
        <span>访问统计</span>
        <span class="text-caption text-medium-emphasis ml-2">近 7 天 API 调用趋势与最近访问记录</span>
        <v-spacer />
        <v-btn size="small" variant="text" :loading="visitsLoading" @click="loadVisits">
          <v-icon size="16" class="mr-1">mdi-refresh</v-icon>
          刷新
        </v-btn>
      </v-card-title>
      <v-card-text>
        <!-- 7 天趋势 -->
        <div class="trend-row">
          <div
            v-for="day in visitDaily"
            :key="day.date"
            class="trend-col"
            :title="`${day.label}：${day.count} 次`"
          >
            <span class="trend-count">{{ day.count }}</span>
            <div class="trend-bar-wrap">
              <div
                class="trend-bar"
                :class="{ 'trend-bar-empty': day.count === 0 }"
                :style="{ height: trendBarHeight(day.count) }"
              ></div>
            </div>
            <span class="trend-label">{{ day.label }}</span>
          </div>
        </div>

        <v-divider v-if="visitRecent.length" class="my-3" />

        <!-- 最近调用记录 -->
        <div v-if="visitRecent.length" class="visit-table">
          <div class="visit-row visit-row-head">
            <span>时间</span><span>接口</span><span>类型</span><span>来源</span><span>耗时</span><span>结果</span>
          </div>
          <div v-for="(v, idx) in visitRecent.slice(0, 12)" :key="idx" class="visit-row">
            <span class="visit-time">{{ v.time }}</span>
            <span>{{ endpointLabel(v.endpoint) }}</span>
            <span>{{ typeLabel(v.type) }}</span>
            <span>{{ sourceLabel(v.source) }}</span>
            <span>{{ v.elapsed_ms }}ms</span>
            <span>
              <v-icon size="14" :color="v.ok ? 'success' : 'error'">
                {{ v.ok ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </v-icon>
            </span>
          </div>
        </div>
        <div v-else class="text-caption text-medium-emphasis text-center py-2">
          暂无调用记录，等待 API 被访问后展示
        </div>
      </v-card-text>
    </v-card>

    <!-- API 接口信息 -->
    <v-card class="glass-card mt-4" elevation="4">
      <v-card-title class="d-flex align-center flex-wrap ga-2">
        <v-icon color="success" size="22" class="mr-1">mdi-api</v-icon>
        <span>API 接口</span>
        <v-chip
          v-for="ep in apiHealthItems"
          :key="ep.key"
          :color="ep.available ? 'success' : 'grey'"
          size="x-small"
          variant="tonal"
        >
          <v-icon size="12" class="mr-1">{{ ep.icon }}</v-icon>
          {{ ep.label }}
        </v-chip>
        <v-spacer />
        <v-btn
          size="small"
          variant="text"
          :append-icon="showExamples ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          @click="showExamples = !showExamples"
        >
          使用示例
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="6" v-for="ep in apiEndpoints" :key="ep.url">
            <div class="api-endpoint-row">
              <v-icon :color="ep.color" size="20" class="mr-2">{{ ep.icon }}</v-icon>
              <div class="api-endpoint-info">
                <div class="api-endpoint-title">{{ ep.title }}</div>
                <div class="api-url">{{ ep.url }}</div>
              </div>
              <v-btn icon size="small" variant="text" @click="copyToClipboard(ep.url)">
                <v-icon size="16">mdi-content-copy</v-icon>
                <v-tooltip activator="parent" location="top">复制链接</v-tooltip>
              </v-btn>
            </div>
          </v-col>
        </v-row>

        <!-- 使用示例 -->
        <v-expand-transition>
          <div v-if="showExamples" class="examples-wrap">
            <v-divider class="my-2" />
            <div v-for="ex in usageExamples" :key="ex.title" class="example-item">
              <div class="d-flex align-center mb-1">
                <v-icon size="15" color="primary" class="mr-1">{{ ex.icon }}</v-icon>
                <span class="text-caption font-weight-bold">{{ ex.title }}</span>
                <v-spacer />
                <v-btn icon size="x-small" variant="text" @click="copyToClipboard(ex.code)">
                  <v-icon size="14">mdi-content-copy</v-icon>
                </v-btn>
              </div>
              <pre class="example-code">{{ ex.code }}</pre>
            </div>
          </div>
        </v-expand-transition>
      </v-card-text>
    </v-card>

    <!-- 悬浮通知 -->
    <v-snackbar v-model="snackbar.visible" :color="snackbar.color" timeout="2500" location="top">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'RandomPic' },
  navKey: { type: String, default: 'main' },
});

const pluginId = computed(() => props.pluginId || 'RandomPic');

// ============ 状态数据 ============
const refreshing = ref(false);
const status = reactive({
  enable: false,
  api_endpoints: { auto: false, pc: false, mobile: false, stats: false },
  pc_path: '',
  pc_path_custom: false,
  mobile_path: '',
  mobile_path_custom: false,
  pc_count: 0,
  mobile_count: 0,
  total_count: 0,
  today_visits: 0,
  network_image_url_pc: '',
  network_image_url_mobile: '',
  network_image_url: '',
  detail: { local: { pc: 0, mobile: 0 }, network: { pc: 0, mobile: 0 } },
});

const statCards = computed(() => {
  const localPc = status.detail?.local?.pc ?? 0;
  const localMobile = status.detail?.local?.mobile ?? 0;
  return [
    {
      label: '图片总数', value: status.total_count || 0,
      icon: 'mdi-image-multiple', color: 'primary', bg: 'rgba(102,126,234,0.12)',
      sub: `本地 ${localPc + localMobile} 张`,
    },
    {
      label: '横屏图片', value: status.pc_count || 0,
      icon: 'mdi-monitor', color: 'info', bg: 'rgba(79,172,254,0.12)',
      sub: `本地 ${localPc} 张`,
    },
    {
      label: '竖屏图片', value: status.mobile_count || 0,
      icon: 'mdi-cellphone', color: 'success', bg: 'rgba(67,233,123,0.12)',
      sub: `本地 ${localMobile} 张`,
    },
    {
      label: '今日访问', value: status.today_visits || 0,
      icon: 'mdi-chart-line', color: 'warning', bg: 'rgba(250,112,154,0.12)',
      sub: 'API 调用次数',
    },
  ];
});

const apiHealthItems = computed(() => [
  { key: 'auto', label: '自动', icon: 'mdi-auto-fix', available: Boolean(status.api_endpoints?.auto) },
  { key: 'pc', label: '横屏', icon: 'mdi-monitor', available: Boolean(status.api_endpoints?.pc) },
  { key: 'mobile', label: '竖屏', icon: 'mdi-cellphone', available: Boolean(status.api_endpoints?.mobile) },
  { key: 'stats', label: '统计', icon: 'mdi-chart-box-outline', available: Boolean(status.api_endpoints?.stats) },
]);

const sourceMonitorItems = computed(() => {
  const commonNetwork = Boolean(status.network_image_url);
  const networkPc = status.detail?.network?.pc ?? 0;
  const networkMobile = status.detail?.network?.mobile ?? 0;
  return [
    {
      key: 'local-pc', label: '本地横屏', icon: 'mdi-folder-image',
      configured: Boolean(status.pc_path), count: `${status.detail?.local?.pc ?? 0} 张`,
    },
    {
      key: 'local-mobile', label: '本地竖屏', icon: 'mdi-folder-image',
      configured: Boolean(status.mobile_path), count: `${status.detail?.local?.mobile ?? 0} 张`,
    },
    {
      key: 'network-pc', label: '网络横屏', icon: 'mdi-cloud-outline',
      configured: Boolean(status.network_image_url_pc || commonNetwork),
      count: typeof networkPc === 'number' ? `${networkPc} 张` : '未知',
    },
    {
      key: 'network-mobile', label: '网络竖屏', icon: 'mdi-cloud-outline',
      configured: Boolean(status.network_image_url_mobile || commonNetwork),
      count: typeof networkMobile === 'number' ? `${networkMobile} 张` : '未知',
    },
  ];
});

// ============ 图片预览 ============
const previewTypes = [
  { key: 'auto', label: '自动', icon: 'mdi-auto-fix' },
  { key: 'pc', label: '横屏', icon: 'mdi-monitor' },
  { key: 'mobile', label: '竖屏', icon: 'mdi-cellphone' },
];
const previewType = ref('auto');
const previewImageUrl = ref('');
const previewObjectUrl = ref('');
const previewLoading = ref(false);
const previewError = ref('');
const savingToLocal = ref(false);

const switchPreviewType = (type) => {
  previewType.value = type;
  loadPreview();
};

const loadPreview = async () => {
  if (!status.enable) {
    previewError.value = '插件未启用，请先在插件配置中启用';
    return;
  }
  previewLoading.value = true;
  previewError.value = '';
  try {
    const params = previewType.value === 'auto' ? {} : { type: previewType.value };
    const image = await props.api.get(`plugin/${pluginId.value}/preview`, {
      params: { ...params, t: Date.now() },
      responseType: 'blob',
    });
    if (previewObjectUrl.value) URL.revokeObjectURL(previewObjectUrl.value);
    previewObjectUrl.value = URL.createObjectURL(image);
    previewImageUrl.value = previewObjectUrl.value;
  } catch (error) {
    previewError.value = error?.response?.data?.detail || '加载预览失败';
  } finally {
    previewLoading.value = false;
  }
};

const handlePreviewError = () => {
  previewError.value = '图片加载失败';
};

const savePreviewToLocal = async () => {
  if (!previewObjectUrl.value) return;
  savingToLocal.value = true;
  try {
    const blob = await fetch(previewObjectUrl.value).then((res) => res.blob());
    const formData = new FormData();
    formData.append('file', blob, 'preview-image.jpg');
    const result = await props.api.post(`plugin/${pluginId.value}/preview/save`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    showSnackbar(result?.msg || '已保存到本地目录', result?.success === false ? 'error' : 'success');
  } catch (error) {
    showSnackbar('保存到本地目录失败', 'error');
  } finally {
    savingToLocal.value = false;
  }
};

// ============ 下载任务 ============
const downloadCount = ref(20);
const downloadSource = ref('both');
const downloadSources = [
  { title: '横屏+竖屏', value: 'both' },
  { title: '仅横屏', value: 'pc' },
  { title: '仅竖屏', value: 'mobile' },
];
const downloadStatus = reactive({
  running: false, total: 0, done: 0, success: 0,
  failed: 0, skipped: 0, pc_saved: 0, mobile_saved: 0, message: '',
});
let downloadTimer = null;
let visitsTimer = null;

const downloadProgress = computed(() => {
  if (!downloadStatus.total) return 0;
  return Math.round((downloadStatus.done / downloadStatus.total) * 100);
});

const startDownload = async () => {
  const count = parseInt(downloadCount.value, 10);
  if (!count || count < 1 || count > 500) {
    showSnackbar('下载数量需在 1-500 之间', 'error');
    return;
  }
  try {
    const result = await props.api.post(`plugin/${pluginId.value}/download`, {
      count, source: downloadSource.value,
    });
    if (result?.success === false) {
      showSnackbar(result?.msg || '启动下载失败', 'error');
      return;
    }
    showSnackbar(result?.msg || '下载任务已启动', 'success');
    pollDownloadStatus();
  } catch (error) {
    showSnackbar('启动下载失败', 'error');
  }
};

const pollDownloadStatus = async () => {
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/download/status`);
    Object.assign(downloadStatus, data || {});
    if (downloadStatus.running) {
      downloadTimer = setTimeout(pollDownloadStatus, 1500);
    } else if (downloadStatus.total && downloadStatus.message === '下载任务已完成') {
      showSnackbar('下载任务已完成', 'success');
      refreshStatus();
    }
  } catch (error) {
    /* 静默重试 */
  }
};

// ============ 图源测速 ============
const pinging = ref(false);
const pingResults = ref(null);

const runPing = async () => {
  pinging.value = true;
  try {
    const result = await props.api.get(`plugin/${pluginId.value}/ping`);
    pingResults.value = result?.data || result || null;
  } catch (error) {
    showSnackbar('图源测速失败', 'error');
  } finally {
    pinging.value = false;
  }
};

// ============ 访问统计 ============
const visitsLoading = ref(false);
const visitDaily = ref([]);
const visitRecent = ref([]);

const trendBarHeight = (count) => {
  const max = Math.max(...visitDaily.value.map((d) => d.count), 1);
  if (!count) return '4px';
  return `${Math.max(8, Math.round((count / max) * 64))}px`;
};

const endpointLabel = (endpoint) =>
  ({ random: '随机图', preview: '预览' }[endpoint] || endpoint || '-');
const typeLabel = (type) =>
  ({ auto: '自动', pc: '横屏', mobile: '竖屏' }[type] || type || '-');
const sourceLabel = (source) =>
  ({ local: '本地', network: '网络', error: '错误' }[source] || source || '-');

const loadVisits = async () => {
  visitsLoading.value = true;
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/visits`);
    visitDaily.value = data?.daily || [];
    visitRecent.value = data?.recent || [];
  } catch (error) {
    /* 静默处理 */
  } finally {
    visitsLoading.value = false;
  }
};

// ============ API 接口 ============
const showExamples = ref(false);

const getApiUrl = (endpoint) =>
  `${window.location.origin}/api/v1/plugin/${pluginId.value}${endpoint}`;

const usageExamples = computed(() => {
  const randomUrl = getApiUrl('/random');
  return [
    {
      title: 'cURL 测试',
      icon: 'mdi-console',
      code: `curl -L -o random.jpg "${randomUrl}"`,
    },
    {
      title: 'HTML 网页引用',
      icon: 'mdi-language-html5',
      code: `<img src="${randomUrl}" alt="随机图片" width="1920" />`,
    },
    {
      title: 'Markdown 引用',
      icon: 'mdi-language-markdown-outline',
      code: `![随机图片](${randomUrl})`,
    },
    {
      title: 'Windows 壁纸脚本 (PowerShell)',
      icon: 'mdi-microsoft-windows',
      code:
`$img = "$env:TEMP\\wallpaper.jpg"
Invoke-WebRequest -Uri "${randomUrl}" -OutFile $img
Add-Type -TypeDefinition @"
using System.Runtime.InteropServices;
public class Wallpaper {
  [DllImport("user32.dll", CharSet=CharSet.Auto)]
  public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
"@
[Wallpaper]::SystemParametersInfo(20, 0, $img, 3)`,
    },
  ];
});

const apiEndpoints = computed(() => [
  { title: '自动识别设备', desc: '', icon: 'mdi-web', color: 'primary', url: getApiUrl('/random') },
  { title: '指定横屏图片', desc: '', icon: 'mdi-monitor', color: 'success', url: getApiUrl('/random?type=pc') },
  { title: '指定竖屏图片', desc: '', icon: 'mdi-cellphone', color: 'warning', url: getApiUrl('/random?type=mobile') },
  { title: '统计数据', desc: '', icon: 'mdi-chart-bar', color: 'info', url: getApiUrl('/stats') },
]);

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
  } catch (err) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
  }
  showSnackbar('链接已复制到剪贴板', 'success');
};

// ============ 通知与刷新 ============
const snackbar = reactive({ visible: false, text: '', color: 'success' });
const showSnackbar = (text, color = 'success') => {
  snackbar.text = text;
  snackbar.color = color;
  snackbar.visible = true;
};

const refreshStatus = async () => {
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/status`);
    if (data) Object.assign(status, data);
  } catch (error) {
    showSnackbar('获取状态失败', 'error');
  }
};

const refreshAll = async () => {
  refreshing.value = true;
  try {
    await refreshStatus();
    loadPreview();
    loadVisits();
  } finally {
    refreshing.value = false;
  }
};

onMounted(async () => {
  await refreshStatus();
  loadPreview();
  loadVisits();
  pollDownloadStatus();
  // 访问统计每 30 秒自动刷新
  visitsTimer = setInterval(loadVisits, 30000);
});

onUnmounted(() => {
  if (downloadTimer) clearTimeout(downloadTimer);
  if (visitsTimer) clearInterval(visitsTimer);
  if (previewObjectUrl.value) URL.revokeObjectURL(previewObjectUrl.value);
});
</script>

<style scoped>
.app-page {
  padding: 4px;
}

/* 统计卡片 */
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
}
.stat-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-card-number {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-card-label {
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}
.stat-card-sub {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
  opacity: 0.7;
}

.glass-card {
  border-radius: 12px;
}

/* 预览 */
.preview-container {
  height: 420px;
  display: flex;
}
.preview-image-wrap,
.preview-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}
.preview-center {
  flex-direction: column;
}
.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

/* 模式按钮组 */
.mode-selector {
  display: flex;
  align-items: center;
  gap: 2px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  padding: 3px;
}
.mode-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.mode-btn:hover:not(:disabled) {
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}
.mode-btn-active {
  background: rgba(var(--v-theme-primary), 0.9);
  color: #fff;
}
.mode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.mode-separator {
  width: 1px;
  height: 18px;
  background: rgba(var(--v-border-color), var(--v-border-opacity));
  margin: 0 3px;
}
.rotating {
  animation: rotate 1s linear infinite;
}
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 源监控 */
.source-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.source-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 8px;
  min-width: 0;
}
.source-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.source-count {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
  white-space: nowrap;
}

/* API 接口 */
.api-endpoint-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 10px;
  min-width: 0;
}
.api-endpoint-info {
  flex: 1;
  min-width: 0;
}
.api-endpoint-title {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 2px;
}
.api-url {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
  word-break: break-all;
  user-select: all;
}

/* 访问趋势 */
.trend-row {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  padding: 4px 2px 0;
}
.trend-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}
.trend-count {
  font-size: 11px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface-variant));
}
.trend-bar-wrap {
  width: 100%;
  max-width: 56px;
  height: 68px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.trend-bar {
  width: 70%;
  min-height: 4px;
  border-radius: 4px 4px 2px 2px;
  background: linear-gradient(180deg, rgba(var(--v-theme-primary), 0.85), rgba(var(--v-theme-primary), 0.45));
  transition: height 0.4s ease;
}
.trend-bar-empty {
  background: rgba(var(--v-border-color), var(--v-border-opacity));
}
.trend-label {
  font-size: 10px;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* 最近调用记录 */
.visit-table {
  font-size: 12px;
}
.visit-row {
  display: grid;
  grid-template-columns: 72px 64px 56px 56px 64px 40px;
  gap: 8px;
  align-items: center;
  padding: 5px 8px;
  border-radius: 6px;
}
.visit-row:not(.visit-row-head):hover {
  background: rgba(var(--v-theme-primary), 0.05);
}
.visit-row-head {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 11px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 0;
}
.visit-time {
  font-family: 'Courier New', monospace;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* 使用示例 */
.examples-wrap {
  margin-top: 8px;
}
.example-item {
  margin-bottom: 10px;
}
.example-code {
  margin: 0;
  padding: 8px 10px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface-variant), 0.06);
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  user-select: all;
}

@media (max-width: 768px) {
  .preview-container {
    height: 260px;
  }
  .source-grid {
    grid-template-columns: 1fr;
  }
  .visit-row {
    grid-template-columns: 64px 52px 48px 48px 56px 32px;
    gap: 4px;
    font-size: 11px;
  }
}
</style>
