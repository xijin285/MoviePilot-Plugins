<template>
  <div class="qk-page">
    <!-- 顶栏 -->
    <div class="qk-topbar">
      <div class="qk-topbar__left">
        <div class="qk-topbar__icon">
          <v-icon icon="mdi-cloud-outline" size="24" />
        </div>
        <div>
          <div class="qk-topbar__title">夸克网盘</div>
          <div class="qk-topbar__sub">管理夸克网盘文件同步与访问</div>
        </div>
      </div>
      <div class="qk-topbar__right">
        <v-btn-group variant="tonal" density="compact" class="elevation-0">
          <v-btn color="primary" @click="refreshStatus" size="small" min-width="40" class="px-0 px-sm-3" :loading="loading">
            <v-icon icon="mdi-refresh" size="18" class="mr-sm-1"></v-icon>
            <span class="btn-text d-none d-sm-inline">刷新</span>
          </v-btn>
          <v-btn color="primary" @click="emit('switch')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-cog" size="18" class="mr-sm-1"></v-icon>
            <span class="btn-text d-none d-sm-inline">配置</span>
          </v-btn>
          <v-btn color="primary" @click="emit('close')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-close" size="18"></v-icon>
            <span class="btn-text d-none d-sm-inline">关闭</span>
          </v-btn>
        </v-btn-group>
      </div>
    </div>

    <v-row class="qk-panel-row">
      <!-- 左侧：状态信息 -->
      <v-col cols="12" md="7" class="qk-panel-col">
        <div class="qk-left-col">
          <!-- 统计卡片 -->
          <div class="qk-card qk-card--status">
            <div class="qk-card__header">
              <span class="qk-card__title d-flex align-center">
                <v-icon icon="mdi-connection" size="18" color="#10b981" class="mr-1" />
                连接状态
              </span>
            </div>
            <div class="qk-results qk-results--summary">
              <div class="qk-stat-card" :class="status.logged_in ? 'qk-stat-card--success' : 'qk-stat-card--warning'">
                <div class="qk-stat-card__label">登录状态</div>
                <div class="qk-stat-card__value">{{ status.logged_in ? '在线' : '离线' }}</div>
              </div>
              <div class="qk-stat-card" :class="status.enabled ? 'qk-stat-card--primary' : 'qk-stat-card--muted'">
                <div class="qk-stat-card__label">插件状态</div>
                <div class="qk-stat-card__value">{{ status.enabled ? '启用' : '禁用' }}</div>
              </div>
              <div class="qk-stat-card qk-stat-card--info">
                <div class="qk-stat-card__label">排序字段</div>
                <div class="qk-stat-card__value">{{ sortFieldMap[status.sort_field] || status.sort_field || '文件名' }}</div>
              </div>
              <div class="qk-stat-card qk-stat-card--primary">
                <div class="qk-stat-card__label">分页大小</div>
                <div class="qk-stat-card__value">{{ status.page_size || 50 }}</div>
              </div>
            </div>
            <div class="qk-status-note">
              <v-icon icon="mdi-information-outline" size="16" class="qk-status-note__icon" />
              <div class="qk-status-note__content">
                <div class="qk-status-note__title">状态说明</div>
                <div class="qk-status-note__text">页面会自动拉取最新登录状态与空间信息，二维码失效后也会自动刷新。</div>
              </div>
            </div>
          </div>

          <!-- 空间统计卡片 -->
          <div class="qk-card qk-card--space qk-desktop-only-space">
            <div class="qk-card__header">
              <span class="qk-card__title d-flex align-center">
                <v-icon icon="mdi-database-outline" size="18" color="#0ea5e9" class="mr-1" />
                空间统计
              </span>
            </div>
            <template v-if="status.total_space">
              <div class="qk-space-bar">
                <div class="qk-space-text">
                  <span>已用 {{ formatSize(status.used_space) }}</span>
                  <span>/ {{ formatSize(status.total_space) }}</span>
                </div>
                <div class="qk-progress-bar">
                  <div class="qk-progress-fill" :style="{ width: spacePercent + '%' }"></div>
                </div>
                <div class="qk-space-percent">{{ spacePercent }}%</div>
              </div>
              <div class="qk-info-grid">
                <div class="qk-info-item">
                  <div class="qk-info-item__label">总空间</div>
                  <div class="qk-info-item__value">{{ formatSize(status.total_space) || '-' }}</div>
                </div>
                <div class="qk-info-item">
                  <div class="qk-info-item__label">已用空间</div>
                  <div class="qk-info-item__value">{{ formatSize(status.used_space) || '-' }}</div>
                </div>
                <div class="qk-info-item">
                  <div class="qk-info-item__label">剩余空间</div>
                  <div class="qk-info-item__value">{{ formatSize(status.free_space) || '-' }}</div>
                </div>
                <div class="qk-info-item">
                  <div class="qk-info-item__label">排序方向</div>
                  <div class="qk-info-item__value">{{ status.sort_order === 'asc' ? '升序' : '降序' }}</div>
                </div>
              </div>
            </template>
            <div v-else class="qk-empty-state">
              <div class="qk-empty-state__icon">
                <v-icon icon="mdi-database-off-outline" size="40" />
              </div>
              <div class="qk-empty-state__title">暂无空间统计数据</div>
              <div class="qk-empty-state__sub">完成扫码登录后，将自动展示总空间、已用空间、剩余空间。</div>
              <div class="qk-empty-state__steps">
                <div class="qk-empty-step">
                  <div class="qk-empty-step__num">1</div>
                  <div>
                    <div class="qk-empty-step__label">扫码登录</div>
                    <div class="qk-empty-step__desc">使用右侧二维码完成授权登录</div>
                  </div>
                </div>
                <v-icon icon="mdi-chevron-right" size="18" color="rgba(var(--v-theme-on-surface), 0.3)" class="qk-empty-step__arrow" />
                <div class="qk-empty-step">
                  <div class="qk-empty-step__num">2</div>
                  <div>
                    <div class="qk-empty-step__label">自动同步</div>
                    <div class="qk-empty-step__desc">系统会自动拉取空间与用户信息</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-col>

      <!-- 右侧：扫码登录 + 用户信息 -->
      <v-col cols="12" md="5" class="qk-panel-col">
        <div class="qk-right-col">
          <!-- 扫码登录卡片 -->
          <div class="qk-card qk-card--qrcode">
            <div class="qk-card__header">
              <span class="qk-card__title d-flex align-center">
                <v-icon icon="mdi-qrcode-scan" size="18" color="#10b981" class="mr-1"></v-icon>
                扫码登录
              </span>
              <v-chip :color="status.logged_in ? 'success' : 'warning'" size="x-small" variant="tonal">
                {{ status.logged_in ? '已登录' : '未登录' }}
              </v-chip>
            </div>

            <div class="qk-qrcode-box">
              <template v-if="status.logged_in">
                <div class="qk-qrcode-placeholder qk-qrcode-placeholder--success">
                  <v-icon icon="mdi-check-decagram" size="64" color="success"></v-icon>
                  <div class="text-success mt-2">当前已登录</div>
                  <div class="text-medium-emphasis mt-1">如需重新扫码，请先退出登录</div>
                </div>
              </template>
              <template v-else-if="qrCodeSrc">
                <img :src="qrCodeSrc" alt="夸克网盘二维码" :class="['qk-qrcode-image', { 'qk-qrcode-image--dark': isDarkMode }]" />
              </template>
              <template v-else>
                <div class="qk-qrcode-placeholder">
                  <v-icon icon="mdi-qrcode" size="72" color="grey"></v-icon>
                  <div class="text-medium-emphasis mt-2">{{ qrLoading || qrRendering ? '正在准备二维码...' : '二维码加载中...' }}</div>
                </div>
              </template>
            </div>

            <div class="qk-qrcode-meta" v-if="shouldShowQrMeta && !qrRendering">
              <div class="qk-qrcode-meta__item">
                <span class="qk-qrcode-meta__label">登录方式</span>
                <span class="qk-qrcode-meta__value">夸克扫码</span>
              </div>
              <div class="qk-qrcode-meta__item">
                <span class="qk-qrcode-meta__label">二维码有效期</span>
                <span class="qk-qrcode-meta__value" :class="qrCountdown <= 30 ? 'qk-qrcode-meta__value--warning' : ''">
                  {{ countdownText }}
                </span>
              </div>
            </div>

          </div>

          <!-- 用户信息卡片 -->
          <div class="qk-card qk-card--user">
            <div class="qk-card__header">
              <span class="qk-card__title d-flex align-center">
                <v-icon icon="mdi-account-circle-outline" size="18" color="#8b5cf6" class="mr-1" />
                用户信息
                <v-btn
                  variant="text"
                  density="comfortable"
                  size="x-small"
                  class="qk-privacy-btn ml-1"
                  :icon="privacyMode ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                  @click="privacyMode = !privacyMode"
                />
              </span>
              <v-btn v-if="status.logged_in" color="error" variant="tonal" prepend-icon="mdi-logout" @click="logout" :disabled="saving" size="small">
                退出
              </v-btn>
            </div>
            <div class="qk-info-grid">
              <div class="qk-info-item">
                <div class="qk-info-item__label">用户名</div>
                <div class="qk-info-item__value">{{ maskPrivacyValue(status.user_name) }}</div>
              </div>
              <div class="qk-info-item">
                <div class="qk-info-item__label">会员类型</div>
                <div class="qk-info-item__value">{{ maskPrivacyValue(status.vip_level || '-') }}</div>
              </div>
              <div class="qk-info-item">
                <div class="qk-info-item__label">会员到期</div>
                <div class="qk-info-item__value" :class="status.svip_exp_at ? 'qk-info-item__value--mono' : ''">{{ maskPrivacyValue(status.svip_exp_at || '-') }}</div>
              </div>
              <div class="qk-info-item">
                <div class="qk-info-item__label">Cookie 状态</div>
                <div class="qk-info-item__value">{{ status.logged_in ? '已保存' : '未保存' }}</div>
              </div>
            </div>
          </div>

          <div class="qk-card qk-card--space qk-mobile-only-space">
            <div class="qk-card__header">
              <span class="qk-card__title d-flex align-center">
                <v-icon icon="mdi-database-outline" size="18" color="#0ea5e9" class="mr-1" />
                空间统计
              </span>
            </div>
            <template v-if="status.total_space">
              <div class="qk-space-bar">
                <div class="qk-space-text">
                  <span>已用 {{ formatSize(status.used_space) }}</span>
                  <span>/ {{ formatSize(status.total_space) }}</span>
                </div>
                <div class="qk-progress-bar">
                  <div class="qk-progress-fill" :style="{ width: spacePercent + '%' }"></div>
                </div>
                <div class="qk-space-percent">{{ spacePercent }}%</div>
              </div>
              <div class="qk-info-grid">
                <div class="qk-info-item">
                  <div class="qk-info-item__label">总空间</div>
                  <div class="qk-info-item__value">{{ formatSize(status.total_space) || '-' }}</div>
                </div>
                <div class="qk-info-item">
                  <div class="qk-info-item__label">已用空间</div>
                  <div class="qk-info-item__value">{{ formatSize(status.used_space) || '-' }}</div>
                </div>
                <div class="qk-info-item">
                  <div class="qk-info-item__label">剩余空间</div>
                  <div class="qk-info-item__value">{{ formatSize(status.free_space) || '-' }}</div>
                </div>
                <div class="qk-info-item">
                  <div class="qk-info-item__label">排序方向</div>
                  <div class="qk-info-item__value">{{ status.sort_order === 'asc' ? '升序' : '降序' }}</div>
                </div>
              </div>
            </template>
            <div v-else class="qk-empty-state">
              <div class="qk-empty-state__icon">
                <v-icon icon="mdi-database-off-outline" size="40" />
              </div>
              <div class="qk-empty-state__title">暂无空间统计数据</div>
              <div class="qk-empty-state__sub">完成扫码登录后，将自动展示总空间、已用空间、剩余空间。</div>
              <div class="qk-empty-state__steps">
                <div class="qk-empty-step">
                  <div class="qk-empty-step__num">1</div>
                  <div>
                    <div class="qk-empty-step__label">扫码登录</div>
                    <div class="qk-empty-step__desc">使用右侧二维码完成授权登录</div>
                  </div>
                </div>
                <v-icon icon="mdi-chevron-right" size="18" color="rgba(var(--v-theme-on-surface), 0.3)" class="qk-empty-step__arrow" />
                <div class="qk-empty-step">
                  <div class="qk-empty-step__num">2</div>
                  <div>
                    <div class="qk-empty-step__label">自动同步</div>
                    <div class="qk-empty-step__desc">系统会自动拉取空间与用户信息</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- 消息提示 -->
    <v-snackbar v-model="message.show" :color="message.type" :timeout="3000" location="top">
      {{ message.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import QRCode from 'qrcode'

const PRIVACY_MODE_STORAGE_KEY = 'quarkdisk-page-privacy-mode'

const sortFieldMap = {
  file_name: '文件名',
  updated_at: '更新时间',
  size: '文件大小',
  created_at: '创建时间',
}

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'switch'])

const status = reactive({
  enabled: false,
  cookie: '',
  page_size: 50,
  sort_field: 'file_name',
  sort_order: 'asc',
  permanently_delete: false,
  logged_in: false,
  // 用户信息
  user_name: '',
  user_id: '',
  svip_exp_at: '',
  vip_level: '',
  // 空间统计
  total_space: 0,
  used_space: 0,
  free_space: 0,
  // 二维码
  qr_expires_in: 0,
  ...props.initialConfig,
})

const loading = ref(false)
const saving = ref(false)
const qrLoading = ref(false)
const qrRendering = ref(false)
const polling = ref(false)
const qrCodeImage = ref('')
const qrUrl = ref('')
const qrCountdown = ref(0)
const privacyMode = ref(false)
const isDarkMode = ref(false)
const message = reactive({ show: false, type: 'info', text: '' })
let qrFetchRequestSeq = 0
let qrRenderRequestSeq = 0
let pollSessionSeq = 0
let pollRequestSeq = 0
let statusRefreshRequestSeq = 0

const hasPendingQr = computed(() => Boolean(qrUrl.value || qrCodeImage.value))
const shouldShowQrMeta = computed(() => !status.logged_in && (hasPendingQr.value || qrLoading.value || qrRendering.value || qrCountdown.value > 0))
const qrCodeSrc = computed(() => {
  if (qrCodeImage.value) {
    return qrCodeImage.value
  }
  return ''
})

const spacePercent = computed(() => {
  if (!status.total_space || status.total_space === 0) return 0
  return Math.round((status.used_space / status.total_space) * 100)
})

const countdownText = computed(() => {
  if (!hasPendingQr.value && qrCountdown.value <= 0) {
    return '-'
  }
  if (qrCountdown.value <= 0) {
    return '已过期'
  }
  const minutes = Math.floor(qrCountdown.value / 60)
  const seconds = qrCountdown.value % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})

function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function maskPrivacyValue(value) {
  const text = value == null || value === '' ? '-' : String(value)
  if (!privacyMode.value || text === '-') {
    return text
  }

  if (text.length <= 2) {
    return '*'.repeat(text.length)
  }
  if (text.length <= 4) {
    return `${text.slice(0, 1)}${'*'.repeat(text.length - 2)}${text.slice(-1)}`
  }

  const keep = Math.min(2, Math.floor(text.length / 4))
  const maskedLength = Math.max(text.length - keep * 2, 1)
  return `${text.slice(0, keep)}${'*'.repeat(maskedLength)}${text.slice(-keep)}`
}

async function buildQrCodeImage(qrTextOverride = '') {
  const qrText = qrTextOverride || qrUrl.value
  if (!qrText) {
    qrCodeImage.value = ''
    qrRendering.value = false
    return
  }
  const renderSeq = ++qrRenderRequestSeq
  qrRendering.value = true
  try {
    const renderedImage = await QRCode.toDataURL(qrText, {
      width: 180,
      margin: 2,
      errorCorrectionLevel: 'M',
      color: {
        dark: '#111111',
        light: isDarkMode.value ? '#d1d5db' : '#ffffff',
      },
    })
    if (renderSeq !== qrRenderRequestSeq) {
      return
    }
    qrCodeImage.value = renderedImage
  } catch (error) {
    if (renderSeq === qrRenderRequestSeq) {
      qrCodeImage.value = ''
    }
    console.error('生成二维码失败', error)
  } finally {
    if (renderSeq === qrRenderRequestSeq) {
      qrRendering.value = false
    }
  }
}

function resetQrDisplayState() {
  qrCodeImage.value = ''
  qrUrl.value = ''
  updateQrCountdown(0)
}

function detectDarkMode() {
  try {
    const root = document.documentElement
    const rootStyle = window.getComputedStyle(root)
    const colorScheme = rootStyle.getPropertyValue('color-scheme') || ''
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    isDarkMode.value = Boolean(
      root.classList.contains('v-theme--dark')
      || root.classList.contains('dark')
      || colorScheme.includes('dark')
      || prefersDark
    )
  } catch (_) {
    isDarkMode.value = false
  }
}

function pluginUrl(path) {
  return `/api/v1/plugin/QuarkDisk${path}`
}

async function request(path, options = {}) {
  const apiPath = `plugin/QuarkDisk${path}`
  if (options.method === 'POST') {
    if (props.api?.post) {
      return props.api.post(apiPath, options.body ? JSON.parse(options.body) : {}, options)
    }
  } else if (props.api?.get) {
    return props.api.get(apiPath, options)
  }

  const response = await fetch(pluginUrl(path), {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  return response.json()
}

const setMessage = (type, text) => {
  message.type = type
  message.text = text
  message.show = true
}

function updateQrCountdown(expiresIn = 0) {
  qrCountdown.value = Math.max(Number(expiresIn || 0), 0)
}

async function syncQrStateFromConfig(data = {}) {
  if (status.logged_in) {
    resetQrDisplayState()
    return
  }

  qrUrl.value = data.qr_url || ''
  updateQrCountdown(data.qr_expires_in || data.expires_in || 0)

  if (qrUrl.value) {
    await buildQrCodeImage()
  } else {
    qrCodeImage.value = ''
  }

  if (qrCountdown.value > 0) {
    startQrCountdown()
  } else {
    stopQrCountdown()
  }
}

async function refreshStatus(showToast = true) {
  const requestSeq = ++statusRefreshRequestSeq
  loading.value = true
  try {
    let data
    if (props.api?.get) {
      data = await props.api.get('plugin/QuarkDisk/config')
    } else {
      const response = await fetch(pluginUrl('/config'))
      data = await response.json()
    }
    if (requestSeq !== statusRefreshRequestSeq) {
      return
    }
    Object.assign(status, {
      enabled: Boolean(data.enabled),
      cookie: data.cookie || '',
      page_size: Number(data.page_size || 50),
      sort_field: data.sort_field || 'file_name',
      sort_order: data.sort_order || 'asc',
      permanently_delete: Boolean(data.permanently_delete),
      logged_in: Boolean(data.logged_in),
      // 用户信息
      user_name: data.user_name || '',
      user_id: data.user_id || '',
      svip_exp_at: data.svip_exp_at || '',
      vip_level: data.vip_level || '',
      // 空间统计
      total_space: Number(data.total_space || 0),
      used_space: Number(data.used_space || 0),
      free_space: Number(data.free_space || 0),
    })
    await syncQrStateFromConfig(data)
    if (requestSeq !== statusRefreshRequestSeq) {
      return
    }
    if (!status.logged_in && !qrLoading.value) {
      await fetchQrCode({ showSuccessMessage: false })
      if (requestSeq !== statusRefreshRequestSeq) {
        return
      }
    }
    if (showToast) {
      setMessage('success', '状态已刷新')
    }
  } catch (error) {
    if (requestSeq === statusRefreshRequestSeq) {
      setMessage('error', `获取状态失败：${error.message || error}`)
    }
  } finally {
    if (requestSeq === statusRefreshRequestSeq) {
      loading.value = false
    }
  }
}

function stopPolling() {
  pollSessionSeq += 1
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}
let pollTimer = null

function stopQrCountdown() {
  if (qrTimer) {
    clearInterval(qrTimer)
    qrTimer = null
  }
}
let qrTimer = null

function startQrCountdown() {
  stopQrCountdown()
  if (qrCountdown.value <= 0) {
    if (!status.logged_in && !qrLoading.value) {
      fetchQrCode({ showSuccessMessage: false })
    }
    return
  }
  qrTimer = setInterval(() => {
    if (qrCountdown.value > 0) {
      qrCountdown.value -= 1
      return
    }
    stopQrCountdown()
    if (!status.logged_in && !qrLoading.value) {
      fetchQrCode({ showSuccessMessage: false })
    }
  }, 1000)
}

const POLL_INTERVAL = 3

async function fetchQrCode(options = {}) {
  const { showSuccessMessage = true } = options
  const requestSeq = ++qrFetchRequestSeq
  qrLoading.value = true
  try {
    stopPolling()
    stopQrCountdown()
    resetQrDisplayState()
    const result = await request('/login/qrcode')
    if (requestSeq !== qrFetchRequestSeq) {
      return
    }
    if (!result.success) {
      throw new Error(result.message || '获取二维码失败')
    }
    const nextQrUrl = result.qr_url || ''

    qrUrl.value = nextQrUrl
    qrCodeImage.value = ''
    updateQrCountdown(result.expires_in || 300)
    await buildQrCodeImage(nextQrUrl)
    if (requestSeq !== qrFetchRequestSeq) {
      return
    }
    startQrCountdown()
    if (showSuccessMessage) {
      setMessage('success', '二维码已生成，请使用夸克 App 扫码')
    }
    startPolling()
  } catch (error) {
    if (requestSeq === qrFetchRequestSeq) {
      qrRendering.value = false
      setMessage('error', `获取二维码失败：${error.message || error}`)
    }
  } finally {
    if (requestSeq === qrFetchRequestSeq) {
      qrLoading.value = false
    }
  }
}

async function pollLoginOnce() {
  if (!hasPendingQr.value || polling.value) {
    return
  }
  const currentPollSessionSeq = pollSessionSeq
  const currentPollRequestSeq = ++pollRequestSeq
  polling.value = true
  try {
    const result = await request('/login/poll')
    if (currentPollSessionSeq !== pollSessionSeq || currentPollRequestSeq !== pollRequestSeq) {
      return
    }
    if (result.success) {
      stopPolling()
      polling.value = false
      // 登录成功后自动启用插件
      status.enabled = true
      await request('/config', {
        method: 'POST',
        body: JSON.stringify({ enabled: true }),
      })
      await refreshStatus(false)
      resetQrDisplayState()
      stopQrCountdown()
      setMessage('success', result.message || '登录成功，插件已自动启用')
      return
    }
    if (!result.waiting) {
      setMessage('error', result.message || '登录失败')
    }
  } catch (error) {
    if (currentPollSessionSeq === pollSessionSeq && currentPollRequestSeq === pollRequestSeq) {
      setMessage('error', `轮询失败：${error.message || error}`)
      stopPolling()
    }
  } finally {
    if (currentPollSessionSeq === pollSessionSeq && currentPollRequestSeq === pollRequestSeq) {
      polling.value = false
    }
  }
}

function startPolling() {
  stopPolling()
  pollSessionSeq += 1
  const interval = POLL_INTERVAL * 1000
  pollTimer = setInterval(() => {
    pollLoginOnce()
  }, interval)
}

async function logout() {
  saving.value = true
  try {
    const result = await request('/login/logout', { method: 'POST' })
    if (!result.success) {
      throw new Error(result.message || '退出失败')
    }
    stopPolling()
    resetQrDisplayState()
    stopQrCountdown()
    await refreshStatus(false)
    setMessage('success', result.message || '已退出登录')
  } catch (error) {
    setMessage('error', `退出失败：${error.message || error}`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    privacyMode.value = localStorage.getItem(PRIVACY_MODE_STORAGE_KEY) === '1'
  } catch (_) {
    privacyMode.value = false
  }
  detectDarkMode()
  await refreshStatus(false)
})

onBeforeUnmount(() => {
  stopPolling()
  stopQrCountdown()
})

watch(privacyMode, value => {
  try {
    localStorage.setItem(PRIVACY_MODE_STORAGE_KEY, value ? '1' : '0')
  } catch (_) {
    // ignore storage failures
  }
})

watch(
  () => [status.logged_in, qrUrl.value].join('|'),
  () => {
    detectDarkMode()
  }
)

watch(isDarkMode, async (value, oldValue) => {
  if (value === oldValue || status.logged_in) {
    return
  }
  if (qrUrl.value) {
    await buildQrCodeImage()
  }
})
</script>

<style scoped>
.qk-page {
  --qk-panel-gap: 12px;
  --qk-panel-min-height: 548px;
  --qk-status-card-min-height: 168px;
  --qk-qrcode-card-min-height: 308px;
}

.qk-page {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
  color: rgba(var(--v-theme-on-surface), 0.85);
  min-height: 400px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
}

.qk-topbar,
.qk-card__header,
.qk-results,
.qk-action-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qk-topbar,
.qk-card__header {
  justify-content: space-between;
}

.qk-topbar__left,
.qk-topbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.qk-topbar__right {
  flex-shrink: 0;
}

.qk-topbar__right :deep(.v-btn-group) {
  flex-wrap: nowrap;
}

.qk-topbar__icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: rgba(var(--v-theme-primary), 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgb(var(--v-theme-primary));
  flex-shrink: 0;
}

.qk-topbar__title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

.qk-topbar__sub,
.qk-stat-card__label {
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.qk-topbar__sub,
.qk-stat-card__label {
  font-size: 11px;
}

.qk-panel-row {
  margin: -6px;
  align-items: stretch;
}

.qk-panel-col {
  display: flex;
  padding: 6px;
}

.qk-panel-col > div {
  width: 100%;
}

.qk-qrcode-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 0;
}

.qk-qrcode-meta__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.qk-qrcode-meta__label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.qk-qrcode-meta__value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.qk-qrcode-meta__value--warning {
  color: rgb(var(--v-theme-warning));
}

.qk-card {
  background: rgba(var(--v-theme-on-surface), 0.03);
  backdrop-filter: blur(20px) saturate(150%);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qk-card__title {
  font-size: 13px;
  font-weight: 600;
}

.qk-privacy-btn {
  min-width: 24px;
  width: 24px;
  height: 24px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.qk-left-col {
  display: flex;
  flex-direction: column;
  gap: var(--qk-panel-gap);
  height: 100%;
  min-height: var(--qk-panel-min-height);
}

.qk-right-col {
  display: flex;
  flex-direction: column;
  gap: var(--qk-panel-gap);
  height: 100%;
  min-height: var(--qk-panel-min-height);
}

.qk-results--summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.qk-stat-card {
  flex: 1;
  min-width: 0;
  border-radius: 14px;
  padding: 8px 10px 7px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 2px 12px rgba(var(--v-theme-on-surface), 0.1);
}

.qk-stat-card__value {
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -1px;
  line-height: 1;
  text-align: center;
}

.qk-stat-card__label {
  text-align: center;
}

.qk-stat-card--primary {
  background: rgba(139, 92, 246, 0.12);
  border: 0.5px solid rgba(139, 92, 246, 0.3);
}
.qk-stat-card--primary .qk-stat-card__value { color: #8b5cf6; }

.qk-stat-card--success {
  background: rgba(16, 185, 129, 0.12);
  border: 0.5px solid rgba(16, 185, 129, 0.3);
}
.qk-stat-card--success .qk-stat-card__value { color: #10b981; }

.qk-stat-card--warning {
  background: rgba(245, 158, 11, 0.12);
  border: 0.5px solid rgba(245, 158, 11, 0.3);
}
.qk-stat-card--warning .qk-stat-card__value { color: #f59e0b; }

.qk-stat-card--info {
  background: rgba(59, 130, 246, 0.12);
  border: 0.5px solid rgba(59, 130, 246, 0.3);
}
.qk-stat-card--info .qk-stat-card__value { color: #3b82f6; }

.qk-stat-card--muted {
  background: rgba(var(--v-theme-on-surface), 0.06);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.12);
}
.qk-stat-card--muted .qk-stat-card__value { color: rgba(var(--v-theme-on-surface), 0.55); }

.qk-status-note {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(var(--v-theme-info), 0.08);
  border: 1px dashed rgba(var(--v-theme-info), 0.22);
}

.qk-status-note__icon {
  margin-top: 1px;
  color: rgb(var(--v-theme-info));
  flex-shrink: 0;
}

.qk-status-note__content {
  min-width: 0;
}

.qk-status-note__title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.75);
  margin-bottom: 2px;
}

.qk-status-note__text {
  font-size: 11px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.qk-qrcode-box {
  flex: 1 1 auto;
  min-height: 150px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
}

.qk-qrcode-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
}

.qk-qrcode-placeholder--success {
  min-height: 100%;
}

.qk-qrcode-image {
  width: 144px;
  height: 144px;
  object-fit: contain;
  border-radius: 8px;
  background: #fff;
  padding: 6px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.qk-qrcode-image--dark {
  background: #d1d5db;
  border-color: rgba(209, 213, 219, 0.55);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
}

.qk-card--qrcode {
  flex: 0 0 auto;
  min-height: var(--qk-qrcode-card-min-height);
  padding-bottom: 16px;
}

.qk-card--status {
  flex: 0 0 auto;
  min-height: var(--qk-status-card-min-height);
}

.qk-card--space {
  flex: 1 1 0;
  min-height: 0;
}

.qk-mobile-only-space {
  display: none;
}

.qk-card--user {
  flex: 1 1 0;
  min-height: 0;
}

.qk-card--space .qk-info-grid,
.qk-card--user .qk-info-grid {
  align-content: start;
}

.qk-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.qk-info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: rgba(var(--v-theme-on-surface), 0.025);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 10px;
}

.qk-info-item__label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.qk-info-item__value {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qk-info-item__value--mono {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 12px;
}

.qk-space-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.025);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 10px;
}

.qk-space-text {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.65);
}

.qk-progress-bar {
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.qk-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #3b82f6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.qk-space-percent {
  font-size: 14px;
  font-weight: 700;
  color: #3b82f6;
  text-align: right;
}

.qk-empty-state {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 19px 15px 24px;
  text-align: center;
  gap: 10px;
  background: rgba(var(--v-theme-info), 0.08);
  border: 1px dashed rgba(var(--v-theme-info), 0.24);
  border-radius: 14px;
}

.qk-empty-state__icon {
  width: 62px;
  height: 62px;
  border-radius: 18px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.3);
  margin-bottom: 3px;
}

.qk-empty-state__title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  letter-spacing: -0.2px;
}

.qk-empty-state__sub {
  font-size: 12px;
  line-height: 1.55;
  color: rgba(var(--v-theme-on-surface), 0.45);
}

.qk-empty-state__steps {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 6px;
}

.qk-empty-step {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  padding: 8px 13px;
  text-align: left;
  max-width: 170px;
}

.qk-empty-step__num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.qk-empty-step__label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.75);
  margin-bottom: 3px;
}

.qk-empty-step__desc {
  font-size: 11px;
  line-height: 1.45;
  color: rgba(var(--v-theme-on-surface), 0.45);
}

.qk-empty-step__arrow {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .qk-page {
    padding: 14px;
  }

  .qk-topbar {
    flex-direction: row;
    align-items: flex-start;
    gap: 10px;
  }

  .qk-panel-col {
    display: block;
  }

  .qk-topbar__left {
    min-width: 0;
    flex: 1;
  }

  .qk-topbar__right {
    justify-content: flex-end;
  }

  .qk-topbar__right :deep(.v-btn-group) {
    gap: 0;
  }

  .qk-topbar__right :deep(.v-btn) {
    min-width: 36px !important;
    padding-inline: 0 !important;
  }

  .qk-results--summary {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: space-between;
    flex-wrap: nowrap;
    gap: 0;
    padding: 8px 6px;
    background: rgba(var(--v-theme-on-surface), 0.03);
    border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
    border-radius: 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 2px 10px rgba(0,0,0,0.05);
    overflow-x: auto;
  }

  .qk-stat-card {
    flex: 1 1 20%;
    min-width: 0;
    padding: 6px 4px;
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 0;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
  }

  .qk-stat-card__label {
    font-size: 10px;
    white-space: nowrap;
  }

  .qk-stat-card__value {
    font-size: 18px;
    letter-spacing: -0.4px;
    text-align: center;
  }

  .qk-info-grid {
    grid-template-columns: 1fr;
  }

  .qk-qrcode-box {
    min-height: 180px;
  }

  .qk-desktop-only-space {
    display: none;
  }

  .qk-mobile-only-space {
    display: flex;
  }

  .qk-card--space .qk-empty-state__steps {
    display: none;
  }

  .qk-card--qrcode {
    min-height: auto !important;
  }

  .qk-card--status,
  .qk-card--space,
  .qk-card--user,
  .qk-left-col,
  .qk-right-col {
    min-height: auto;
    height: auto;
  }
}
</style>
