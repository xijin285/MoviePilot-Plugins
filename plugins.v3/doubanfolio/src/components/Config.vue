<template>
  <div class="dbfcfg-page">
    <!-- 顶栏 -->
    <div class="dbfcfg-topbar">
      <div class="dbfcfg-topbar__left">
        <div class="dbfcfg-topbar__icon">
          <v-icon icon="mdi-movie-open-outline" size="24" />
        </div>
        <div class="dbfcfg-topbar__meta">
          <div class="dbfcfg-topbar__title">豆瓣档案 · 配置</div>
          <div class="dbfcfg-topbar__sub">扫码登录与同步参数设置</div>
        </div>
      </div>
      <div class="dbfcfg-topbar__right">
        <v-btn-group variant="tonal" density="compact" class="elevation-0">
          <v-btn color="primary" @click="emit('switch')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-view-dashboard" size="18" class="mr-sm-1" />
            <span class="d-none d-sm-inline">状态页</span>
          </v-btn>
          <v-btn color="primary" :loading="saving" @click="saveConfig()" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-content-save" size="18" class="mr-sm-1" />
            <span class="d-none d-sm-inline">保存</span>
          </v-btn>
          <v-btn color="primary" @click="emit('close')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-close" size="18" />
            <span class="d-none d-sm-inline">关闭</span>
          </v-btn>
        </v-btn-group>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="dbfcfg-slide">
      <div v-if="message.show" class="dbfcfg-toast" :class="`dbfcfg-toast--${message.type}`">
        <v-icon :icon="message.type === 'success' ? 'mdi-check-circle' : message.type === 'error' ? 'mdi-alert-circle' : 'mdi-information'" size="18" />
        <span>{{ message.text }}</span>
        <button class="dbfcfg-toast__close" @click="message.show = false">
          <v-icon icon="mdi-close" size="16" />
        </button>
      </div>
    </Transition>

    <!-- 豆瓣账号 -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-account-circle-outline" size="18" color="#2e963d" class="mr-1" />
          豆瓣账号
        </span>
        <v-chip v-if="status.logged_in" size="x-small" variant="tonal" color="success" prepend-icon="mdi-check-decagram">
          已登录
        </v-chip>
        <v-chip v-else size="x-small" variant="tonal" color="warning" prepend-icon="mdi-alert-circle-outline">
          未登录
        </v-chip>
      </div>

      <!-- 已登录 -->
      <div v-if="status.logged_in" class="dbfcfg-account">
        <div class="dbfcfg-account__avatar">
          <img
            v-if="status.avatar"
            :src="status.avatar"
            alt=""
            class="dbfcfg-account__img"
            referrerpolicy="no-referrer"
          />
          <v-icon v-else icon="mdi-account" size="26" />
        </div>
        <div class="dbfcfg-account__info">
          <div class="dbfcfg-account__name">{{ status.nickname || '豆瓣账号' }}</div>
          <div class="dbfcfg-account__desc">
            Cookie 已保存，可正常同步观影记录
            <span v-if="cookiePreview" class="dbfcfg-account__cookie">{{ cookiePreview }}</span>
          </div>
        </div>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-qrcode-scan" @click="relogin">
          重新扫码
        </v-btn>
      </div>

      <!-- 未登录：扫码 -->
      <div v-else class="dbfcfg-qr">
        <div class="dbfcfg-qr__box">
          <template v-if="qr.img">
            <img :src="qr.img" alt="豆瓣登录二维码" class="dbfcfg-qr__image" />
            <div v-if="qr.status === 'scanned'" class="dbfcfg-qr__mask">
              <v-icon icon="mdi-cellphone-check" size="34" color="#22c55e" />
              <span>已扫码，请在手机确认</span>
            </div>
            <div v-else-if="qr.status === 'expired'" class="dbfcfg-qr__mask">
              <v-icon icon="mdi-qrcode-remove" size="34" color="#f59e0b" />
              <span>二维码已过期</span>
            </div>
          </template>
          <div v-else class="dbfcfg-qr__placeholder">
            <v-progress-circular v-if="qrLoading" indeterminate size="28" color="primary" />
            <v-icon v-else icon="mdi-qrcode" size="56" color="grey" />
            <span class="mt-2">{{ qrLoading ? '正在获取二维码...' : '二维码未加载' }}</span>
          </div>
        </div>

        <div class="dbfcfg-qr__side">
          <div class="dbfcfg-qr__title">
            <v-icon :icon="qrIcon" size="18" :color="qrColor" class="mr-1" />
            {{ qrTitle }}
          </div>
          <div class="dbfcfg-qr__text">{{ qrTip }}</div>
          <div v-if="qr.error" class="dbfcfg-qr__error">{{ qr.error }}</div>
          <div class="dbfcfg-qr__actions">
            <v-btn
              size="small"
              variant="tonal"
              color="primary"
              prepend-icon="mdi-refresh"
              :loading="qrLoading"
              @click="startQr()"
            >
              刷新二维码
            </v-btn>
            <span v-if="countdownText" class="dbfcfg-qr__countdown" :class="{ 'dbfcfg-qr__countdown--warn': qr.expire_in <= 30 }">
              <v-icon icon="mdi-timer-outline" size="14" class="mr-1" />{{ countdownText }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 基础设置 -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-toggle-switch-outline" size="18" color="#8b5cf6" class="mr-1" />
          基础设置
        </span>
      </div>
      <div class="dbfcfg-switch-grid">
        <div class="dbfcfg-switch-item" :class="{ 'dbfcfg-switch-item--active': config.enabled }" style="--accent: #8b5cf6">
          <div class="dbfcfg-switch-item__main">
            <v-icon icon="mdi-power-plug" size="18" />
            <span>启用插件</span>
          </div>
          <v-switch v-model="config.enabled" color="#8b5cf6" density="compact" hide-details inset />
        </div>
        <div class="dbfcfg-switch-item" :class="{ 'dbfcfg-switch-item--active': config.private }" style="--accent: #22c55e">
          <div class="dbfcfg-switch-item__main">
            <v-icon icon="mdi-eye-off-outline" size="18" />
            <span>仅自己可见</span>
          </div>
          <v-switch v-model="config.private" color="#22c55e" density="compact" hide-details inset />
        </div>
        <div class="dbfcfg-switch-item" :class="{ 'dbfcfg-switch-item--active': config.first }" style="--accent: #3b82f6">
          <div class="dbfcfg-switch-item__main">
            <v-icon icon="mdi-playlist-check" size="18" />
            <span>首集同步</span>
          </div>
          <v-switch v-model="config.first" color="#3b82f6" density="compact" hide-details inset />
        </div>
        <div class="dbfcfg-switch-item" :class="{ 'dbfcfg-switch-item--active': config.notify }" style="--accent: #f59e0b">
          <div class="dbfcfg-switch-item__main">
            <v-icon icon="mdi-bell-outline" size="18" />
            <span>发送通知</span>
          </div>
          <v-switch v-model="config.notify" color="#f59e0b" density="compact" hide-details inset />
        </div>
      </div>
      <div class="dbfcfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        首集同步会在播放第一集时把剧集整体标记为「在看」；通知用于 Cookie 失效提醒。
      </div>
    </div>

    <!-- 想看自动订阅 -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-auto-fix" size="18" color="#2e963d" class="mr-1" />
          想看自动订阅
        </span>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-play-circle-outline" :loading="autoChecking" @click="runAutoCheck">
          立即检查
        </v-btn>
      </div>
      <div class="dbfcfg-switch-grid">
        <div class="dbfcfg-switch-item" :class="{ 'dbfcfg-switch-item--active': config.auto_subscribe }" style="--accent: #2e963d">
          <div class="dbfcfg-switch-item__main">
            <v-icon icon="mdi-movie-plus-outline" size="18" />
            <span>自动订阅想看</span>
          </div>
          <v-switch v-model="config.auto_subscribe" color="#2e963d" density="compact" hide-details inset />
        </div>
        <div class="dbfcfg-switch-item" :class="{ 'dbfcfg-switch-item--active': config.auto_subscribe_existing }" style="--accent: #f59e0b">
          <div class="dbfcfg-switch-item__main">
            <v-icon icon="mdi-playlist-plus-outline" size="18" />
            <span>已有想看也订阅</span>
          </div>
          <v-switch v-model="config.auto_subscribe_existing" color="#f59e0b" density="compact" hide-details inset />
        </div>
      </div>
      <div class="dbfcfg-form-grid">
        <div class="dbfcfg-form-item">
          <v-text-field v-model.number="config.auto_subscribe_interval" label="检查间隔（分钟）" type="number" min="1" max="59" density="compact" variant="outlined" hide-details="auto" class="dbfcfg-input" />
          <div class="dbfcfg-hint">每 N 分钟检查豆瓣新增「想看」并自动加入 MoviePilot 订阅；保存后若未生效请重载插件</div>
        </div>
      </div>
      <div class="dbfcfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        首次开启只建立基线，不会批量订阅已有想看；只有勾选「已有想看也订阅」时才会处理现有条目。自动订阅结果会写入「同步」页签。
      </div>
    </div>

    <!-- 同步范围 -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-account-filter-outline" size="18" color="#2e963d" class="mr-1" />
          同步范围
        </span>
      </div>
      <div class="dbfcfg-form-grid">
        <div class="dbfcfg-form-item">
          <v-text-field v-model="config.user" label="只同步这些用户" density="compact" variant="outlined" hide-details="auto" placeholder="用英文逗号分隔，留空为全部" class="dbfcfg-input" />
          <div class="dbfcfg-hint">按媒体服务器用户名过滤，多个用 , 分隔</div>
        </div>
        <div class="dbfcfg-form-item">
          <v-text-field v-model="config.exclude" label="排除的剧名" density="compact" variant="outlined" hide-details="auto" placeholder="用英文逗号分隔" class="dbfcfg-input" />
          <div class="dbfcfg-hint">命中关键词的条目不会同步到豆瓣</div>
        </div>
      </div>
    </div>

    <!-- 展示数量 -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-format-list-numbered" size="18" color="#6366f1" class="mr-1" />
          展示数量
        </span>
      </div>
      <div class="dbfcfg-form-grid dbfcfg-form-grid--four">
        <div class="dbfcfg-form-item">
          <v-text-field v-model.number="config.pc_month" label="大屏月数" type="number" min="1" density="compact" variant="outlined" hide-details="auto" class="dbfcfg-input" />
          <div class="dbfcfg-hint">大屏仪表盘展示最近几个月</div>
        </div>
        <div class="dbfcfg-form-item">
          <v-text-field v-model.number="config.pc_num" label="大屏条数" type="number" min="1" density="compact" variant="outlined" hide-details="auto" class="dbfcfg-input" />
          <div class="dbfcfg-hint">大屏每次最多显示的条目数</div>
        </div>
        <div class="dbfcfg-form-item">
          <v-text-field v-model.number="config.mobile_month" label="小屏月数" type="number" min="1" density="compact" variant="outlined" hide-details="auto" class="dbfcfg-input" />
          <div class="dbfcfg-hint">手机端展示最近几个月</div>
        </div>
        <div class="dbfcfg-form-item">
          <v-text-field v-model.number="config.mobile_num" label="小屏条数" type="number" min="1" density="compact" variant="outlined" hide-details="auto" class="dbfcfg-input" />
          <div class="dbfcfg-hint">手机端每次最多显示的条目数</div>
        </div>
      </div>
    </div>

    <!-- 手动 Cookie -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-cookie-outline" size="18" color="#f59e0b" class="mr-1" />
          手动填写 Cookie
        </span>
        <v-btn
          variant="text"
          density="compact"
          size="small"
          :icon="showCookie ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
          @click="showCookie = !showCookie"
        />
      </div>
      <v-text-field
        v-if="!showCookie"
        v-model="config.cookie"
        type="password"
        density="compact"
        variant="outlined"
        hide-details
        autocomplete="off"
        placeholder="扫码登录后自动填充，一般无需手动填写"
        class="dbfcfg-input"
      />
      <v-textarea
        v-else
        v-model="config.cookie"
        density="compact"
        variant="outlined"
        hide-details
        rows="2"
        auto-grow
        autocomplete="off"
        placeholder="扫码登录后自动填充，一般无需手动填写"
        class="dbfcfg-input"
      />
      <div class="dbfcfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        Cookie 由扫码登录自动维护，一般无需手动填写；也可粘贴从浏览器复制的豆瓣 Cookie。
      </div>
    </div>

    <!-- 使用说明 -->
    <div class="dbfcfg-card">
      <div class="dbfcfg-card__header">
        <span class="dbfcfg-card__title d-flex align-center">
          <v-icon icon="mdi-book-information-variant" size="18" color="#6366f1" class="mr-1" />
          使用说明
        </span>
      </div>
      <div class="dbfcfg-guide">
        <p><v-icon icon="mdi-numeric-1-circle-outline" size="15" color="primary" class="mr-1" /><strong>扫码登录：</strong>用豆瓣 APP 扫描上方二维码，在手机上确认后 Cookie 会自动填入并保存，无需手动复制。</p>
        <p><v-icon icon="mdi-numeric-2-circle-outline" size="15" color="primary" class="mr-1" /><strong>开启 Webhook：</strong>需要在媒体服务器中配置 webhook，播放事件才会触发同步。</p>
        <p><v-icon icon="mdi-numeric-3-circle-outline" size="15" color="primary" class="mr-1" /><strong>同步规则：</strong>播放开始标记为「在看」，播放完成标记为「看过」，剧集进度会累积到对应条目。</p>
        <p><v-icon icon="mdi-numeric-4-circle-outline" size="15" color="primary" class="mr-1" /><strong>Cookie 失效：</strong>插件每小时检测一次，失效时会按设置发送通知，重新扫码即可。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'switch'])

const PLUGIN_ID = 'DoubanFolio'
const POLL_INTERVAL = 2000

const config = reactive({
  enabled: false,
  private: true,
  first: true,
  user: '',
  exclude: '',
  cookie: '',
  pc_month: 3,
  pc_num: 50,
  mobile_month: 2,
  mobile_num: 15,
  notify: false,
  auto_subscribe: false,
  auto_subscribe_interval: 5,
  auto_subscribe_existing: false,
  ...props.initialConfig,
})

const status = reactive({ logged_in: false, nickname: '', avatar: '' })
const qr = reactive({ img: '', status: 'idle', error: '', expire_in: 0 })
const loading = ref(false)
const saving = ref(false)
const autoChecking = ref(false)
const qrLoading = ref(false)
const showCookie = ref(false)
const message = reactive({ show: false, type: 'info', text: '' })

let messageTimer = null
let pollTimer = null
let countdownTimer = null
let pollSeq = 0

const cookiePreview = computed(() => {
  const raw = String(config.cookie || '')
  if (!raw) return ''
  const hit = raw.match(/dbcl2="?(\d+):/i)
  return hit ? `UID ${hit[1]}` : ''
})

const countdownText = computed(() => {
  if (!qr.expire_in || qr.expire_in <= 0) return ''
  if (qr.status === 'login') return ''
  return `${Math.floor(qr.expire_in / 60)} 分 ${qr.expire_in % 60} 秒后过期`
})

const qrTitle = computed(() => {
  if (qr.status === 'scanned') return '已扫码，请在手机上确认'
  if (qr.status === 'expired') return '二维码已过期'
  if (qr.status === 'error') return '二维码状态异常'
  return '使用豆瓣 APP 扫码登录'
})

const qrTip = computed(() => {
  if (qr.status === 'scanned') return '确认后本页面会自动填入 Cookie，无需手动操作。'
  if (qr.status === 'expired') return '点击「刷新二维码」重新获取即可。'
  if (qr.status === 'error') return qr.error || '可点击刷新重试，或手动填写下方 Cookie。'
  return '打开豆瓣 APP → 右上角扫一扫 → 扫描左侧二维码 → 确认登录。'
})

const qrColor = computed(() => {
  if (qr.status === 'scanned') return '#22c55e'
  if (qr.status === 'expired' || qr.status === 'error') return '#f59e0b'
  return '#2e963d'
})

const qrIcon = computed(() => {
  if (qr.status === 'scanned') return 'mdi-cellphone-check'
  if (qr.status === 'expired') return 'mdi-qrcode-remove'
  if (qr.status === 'error') return 'mdi-alert-circle-outline'
  return 'mdi-qrcode-scan'
})

function clearMessageTimer() {
  if (messageTimer) {
    clearTimeout(messageTimer)
    messageTimer = null
  }
}

function pushMessage(text, type = 'info') {
  clearMessageTimer()
  message.text = text
  message.type = type
  message.show = true
  messageTimer = setTimeout(() => {
    message.show = false
    messageTimer = null
  }, type === 'error' ? 6000 : 3500)
}

async function request(path, options = {}) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`
  const method = (options.method || 'GET').toUpperCase()
  try {
    if (method === 'POST') {
      if (props.api?.post) {
        return await props.api.post(apiPath, options.body || {}, {})
      }
    } else if (props.api?.get) {
      return await props.api.get(apiPath, options.params || {})
    }
    const response = await fetch(`/api/v1/${apiPath}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: method === 'POST' ? JSON.stringify(options.body || {}) : undefined,
    })
    return await response.json()
  } catch (error) {
    throw new Error(error?.message || '请求失败')
  }
}

function applyConfig(data = {}) {
  if (!data || typeof data !== 'object') return
  if ('enabled' in data) config.enabled = Boolean(data.enabled)
  if ('private' in data) config.private = Boolean(data.private)
  if ('first' in data) config.first = Boolean(data.first)
  if ('user' in data) config.user = data.user || ''
  if ('exclude' in data) config.exclude = data.exclude || ''
  if ('cookie' in data) config.cookie = data.cookie || ''
  if ('pc_month' in data) config.pc_month = Number(data.pc_month || 3)
  if ('pc_num' in data) config.pc_num = Number(data.pc_num || 50)
  if ('mobile_month' in data) config.mobile_month = Number(data.mobile_month || 2)
  if ('mobile_num' in data) config.mobile_num = Number(data.mobile_num || 15)
  if ('notify' in data) config.notify = Boolean(data.notify)
  if ('auto_subscribe' in data) config.auto_subscribe = Boolean(data.auto_subscribe)
  if ('auto_subscribe_interval' in data) config.auto_subscribe_interval = Number(data.auto_subscribe_interval || 5)
  if ('auto_subscribe_existing' in data) config.auto_subscribe_existing = Boolean(data.auto_subscribe_existing)
  if ('logged_in' in data) status.logged_in = Boolean(data.logged_in)
  if ('nickname' in data) status.nickname = data.nickname || ''
  if ('avatar' in data) status.avatar = data.avatar || ''
}

async function loadConfig() {
  loading.value = true
  try {
    const data = await request('/config')
    applyConfig(data)
    if (status.logged_in) {
      stopPolling()
    } else {
      await startQr()
    }
  } catch (error) {
    pushMessage(`加载配置失败：${error.message}`, 'error')
  } finally {
    loading.value = false
  }
}

async function saveConfig(silent = false) {
  saving.value = true
  try {
    const result = await request('/config', {
      method: 'POST',
      body: {
        enabled: config.enabled,
        private: config.private,
        first: config.first,
        user: config.user,
        exclude: config.exclude,
        cookie: config.cookie,
        pc_month: Number(config.pc_month) || 3,
        pc_num: Number(config.pc_num) || 50,
        mobile_month: Number(config.mobile_month) || 2,
        mobile_num: Number(config.mobile_num) || 15,
        notify: config.notify,
        auto_subscribe: config.auto_subscribe,
        auto_subscribe_interval: Number(config.auto_subscribe_interval) || 5,
        auto_subscribe_existing: config.auto_subscribe_existing,
      },
    })
    if (result && result.success === false) {
      throw new Error(result.message || '保存失败')
    }
    if (result?.data) applyConfig(result.data)
    if (!silent) pushMessage('配置已保存', 'success')
    return true
  } catch (error) {
    pushMessage(`保存失败：${error.message}`, 'error')
    return false
  } finally {
    saving.value = false
  }
}

async function runAutoCheck() {
  if (!config.auto_subscribe) {
    pushMessage('请先开启「自动订阅想看」并保存', 'info')
    return
  }
  autoChecking.value = true
  try {
    const data = await request('/auto_subscribe/check', { method: 'POST', body: { force: true } })
    if (data?.success) pushMessage(data.message || '检查完成', 'success')
    else pushMessage(data?.message || '检查失败', 'error')
  } catch (error) {
    pushMessage(`检查失败：${error.message}`, 'error')
  } finally {
    autoChecking.value = false
  }
}

function stopPolling() {
  pollSeq += 1
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startCountdown() {
  stopCountdown()
  countdownTimer = setInterval(() => {
    if (status.logged_in) return
    if (qr.status !== 'pending' && qr.status !== 'scanned') return
    if (qr.expire_in > 0) {
      qr.expire_in -= 1
      if (qr.expire_in === 0) {
        qr.status = 'expired'
        stopPolling()
      }
    }
  }, 1000)
}

async function startQr() {
  if (qrLoading.value) return
  qrLoading.value = true
  stopPolling()
  try {
    const data = await request('/qr/start')
    qr.img = data?.img || ''
    qr.status = data?.status || 'pending'
    qr.error = data?.error || ''
    qr.expire_in = Number(data?.expire_in || 0)
    if (qr.status === 'login' && data?.cookie) {
      await handleLogin(data)
      return
    }
    if (qr.status === 'pending' || qr.status === 'scanned') {
      beginPolling()
      startCountdown()
    } else if (qr.error) {
      pushMessage(qr.error, 'error')
    }
  } catch (error) {
    qr.status = 'error'
    qr.error = error.message
    pushMessage(`获取二维码失败：${error.message}`, 'error')
  } finally {
    qrLoading.value = false
  }
}

function beginPolling() {
  stopPolling()
  const seq = ++pollSeq
  const tick = async () => {
    if (seq !== pollSeq) return
    try {
      const data = await request('/qr/poll')
      if (seq !== pollSeq) return
      if (data?.img) qr.img = data.img
      if (data?.error) qr.error = data.error
      if (data?.status) qr.status = data.status
      if (typeof data?.expire_in === 'number') qr.expire_in = data.expire_in
      if (qr.status === 'login') {
        await handleLogin(data || {})
        return
      }
      if (qr.status === 'expired' || qr.status === 'error') {
        stopPolling()
        return
      }
    } catch (error) {
      // 单次轮询失败不打断，交给下一轮
    }
    if (seq === pollSeq) {
      pollTimer = setTimeout(tick, POLL_INTERVAL)
    }
  }
  pollTimer = setTimeout(tick, 1200)
}

async function handleLogin(data) {
  stopPolling()
  stopCountdown()
  const cookie = data?.cookie || ''
  status.logged_in = true
  status.nickname = data?.nickname || ''
  status.avatar = data?.avatar || ''
  if (cookie) config.cookie = cookie
  qr.status = 'login'
  qr.error = ''
  await saveConfig(true)
  // 保存后重新拉取一次配置，带回头像等登录信息
  try {
    const fresh = await request('/config')
    applyConfig(fresh)
  } catch (error) {
    // 静默失败，保留本地状态
  }
  const who = status.nickname ? `：${status.nickname}` : ''
  pushMessage(`扫码登录成功${who}，Cookie 已保存`, 'success')
}

async function relogin() {
  status.logged_in = false
  status.nickname = ''
  status.avatar = ''
  config.cookie = ''
  qr.img = ''
  qr.status = 'idle'
  qr.error = ''
  qr.expire_in = 0
  await startQr()
}

onMounted(loadConfig)

onBeforeUnmount(() => {
  stopPolling()
  stopCountdown()
  clearMessageTimer()
})
</script>

<style scoped>
.dbfcfg-page {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 400px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: rgba(var(--v-theme-on-surface), 0.85);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
}

/* ===== 顶栏 ===== */
.dbfcfg-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 8px;
}

.dbfcfg-topbar__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.dbfcfg-topbar__meta { min-width: 0; flex: 1; }
.dbfcfg-topbar__right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.dbfcfg-topbar__icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: rgba(46, 150, 61, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2e963d;
  flex-shrink: 0;
}

.dbfcfg-topbar__title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfcfg-topbar__sub {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== Toast ===== */
.dbfcfg-toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.82rem;
  background: rgba(var(--v-theme-on-surface), 0.03);
  backdrop-filter: blur(20px) saturate(150%);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.dbfcfg-toast--success {
  background: rgba(34, 197, 94, 0.08);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.15);
}

.dbfcfg-toast--error {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.15);
}

.dbfcfg-toast--info {
  background: rgba(var(--v-theme-info), 0.08);
  color: rgb(var(--v-theme-info));
  border-color: rgba(var(--v-theme-info), 0.15);
}

.dbfcfg-toast__close {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
  display: flex;
  transition: opacity 0.2s ease;
}

.dbfcfg-toast__close:hover { opacity: 1; }

.dbfcfg-slide-enter-active,
.dbfcfg-slide-leave-active { transition: all 0.3s ease; }
.dbfcfg-slide-enter-from,
.dbfcfg-slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* ===== 卡片 ===== */
.dbfcfg-card {
  background: rgba(var(--v-theme-on-surface), 0.03);
  backdrop-filter: blur(20px) saturate(150%);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dbfcfg-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dbfcfg-card__title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* ===== 账号状态 ===== */
.dbfcfg-account {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.dbfcfg-account__avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: rgba(46, 150, 61, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2e963d;
  flex-shrink: 0;
  overflow: hidden;
}

.dbfcfg-account__img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.dbfcfg-account__info { flex: 1; min-width: 0; }

.dbfcfg-account__name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfcfg-account__desc {
  font-size: 11.5px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 3px;
}

.dbfcfg-account__cookie {
  margin-left: 8px;
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  font-family: 'SF Mono', Menlo, monospace;
  font-size: 10.5px;
}

/* ===== 二维码 ===== */
.dbfcfg-qr {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  align-items: center;
}

.dbfcfg-qr__box {
  position: relative;
  width: 172px;
  height: 172px;
  border-radius: 12px;
  background: #ffffff;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.dbfcfg-qr__image {
  width: 160px;
  height: 160px;
  object-fit: contain;
  display: block;
}

.dbfcfg-qr__mask {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.94);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11.5px;
  color: rgba(0, 0, 0, 0.7);
  font-weight: 500;
}

.dbfcfg-qr__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11.5px;
  color: rgba(0, 0, 0, 0.45);
  width: 100%;
  height: 100%;
}

.dbfcfg-qr__side {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dbfcfg-qr__title {
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfcfg-qr__text {
  font-size: 12px;
  line-height: 1.65;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dbfcfg-qr__error {
  font-size: 11.5px;
  color: #f59e0b;
  word-break: break-all;
}

.dbfcfg-qr__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.dbfcfg-qr__countdown {
  display: inline-flex;
  align-items: center;
  font-size: 11.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.dbfcfg-qr__countdown--warn { color: #f59e0b; }

/* ===== 开关网格 ===== */
.dbfcfg-switch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
}

.dbfcfg-switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 11px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.07);
  transition: all 0.2s ease;
}

.dbfcfg-switch-item--active {
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  border-color: color-mix(in srgb, var(--accent) 22%, transparent);
}

.dbfcfg-switch-item__main {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: rgba(var(--v-theme-on-surface), 0.75);
  min-width: 0;
}

.dbfcfg-switch-item--active .dbfcfg-switch-item__main { color: var(--accent); }

/* ===== 表单 ===== */
.dbfcfg-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.dbfcfg-form-grid--four {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.dbfcfg-form-item { display: flex; flex-direction: column; gap: 5px; }

.dbfcfg-hint {
  display: flex;
  align-items: center;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.45);
}

/* ===== 说明 ===== */
.dbfcfg-guide {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dbfcfg-guide p {
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dbfcfg-guide strong {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.78);
}

.dbfcfg-desc {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  padding-top: 4px;
  border-top: 0.5px solid rgba(var(--v-theme-on-surface), 0.07);
}

@media (max-width: 600px) {
  .dbfcfg-page { padding: 12px 12px; }
  .dbfcfg-qr { justify-content: center; }
  .dbfcfg-topbar__sub { display: none; }
}
</style>
