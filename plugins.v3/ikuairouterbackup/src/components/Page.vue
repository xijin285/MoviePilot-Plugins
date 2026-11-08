<template>
  <div class="ikuai-page">
    <!-- 顶栏 -->
    <div class="ikuai-topbar">
      <div class="ikuai-topbar__left">
        <div class="ikuai-topbar__icon">
          <v-icon icon="mdi-router-network" size="24" />
        </div>
        <div class="ikuai-topbar__meta">
          <div class="ikuai-topbar__title">爱快路由时光机</div>
          <div class="ikuai-topbar__sub">
            {{ status.hostname ? `${status.hostname} ${status.version || ''}` : '配置备份 · 实时监控 · 负载告警' }}
          </div>
        </div>
      </div>
      <div class="ikuai-topbar__right">
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-refresh" :loading="loading" @click="loadAll">
          <span class="d-none d-sm-inline">刷新</span>
        </v-btn>
        <v-btn variant="tonal" color="success" size="small" prepend-icon="mdi-cloud-upload-outline" :loading="backingUp" @click="runBackupNow">
          <span class="d-none d-sm-inline">立即备份</span>
        </v-btn>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-cog-outline" @click="emit('switch')">
          <span class="d-none d-sm-inline">插件配置</span>
        </v-btn>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-close" @click="emit('close')">
          <span class="d-none d-sm-inline">关闭</span>
        </v-btn>
      </div>
    </div>

    <!-- 悬浮通知 -->
    <transition name="toast-fade">
      <div v-if="toast.show" class="ikuai-toast" :class="toast.type === 'error' ? 'ikuai-toast--error' : 'ikuai-toast--success'">
        <v-icon size="16">{{ toast.type === 'error' ? 'mdi-alert-circle' : 'mdi-check-circle' }}</v-icon>
        <span>{{ toast.text }}</span>
      </div>
    </transition>

    <!-- 实时状态 -->
    <div class="ikuai-stats">
      <div class="ikuai-stat" style="--accent: #3b82f6">
        <div class="ikuai-stat__icon"><v-icon icon="mdi-cpu-64-bit" size="18" /></div>
        <div class="ikuai-stat__value">{{ status.cpu != null ? status.cpu + '%' : '—' }}</div>
        <div class="ikuai-stat__label">CPU 使用率</div>
      </div>
      <div class="ikuai-stat" style="--accent: #8b5cf6">
        <div class="ikuai-stat__icon"><v-icon icon="mdi-memory" size="18" /></div>
        <div class="ikuai-stat__value">{{ status.mem != null ? status.mem + '%' : '—' }}</div>
        <div class="ikuai-stat__label">内存使用率</div>
      </div>
      <div class="ikuai-stat" style="--accent: #22c55e">
        <div class="ikuai-stat__icon"><v-icon icon="mdi-arrow-up-bold" size="18" /></div>
        <div class="ikuai-stat__value">{{ status.up_speed || '—' }}</div>
        <div class="ikuai-stat__label">WAN 上行</div>
      </div>
      <div class="ikuai-stat" style="--accent: #f59e0b">
        <div class="ikuai-stat__icon"><v-icon icon="mdi-arrow-down-bold" size="18" /></div>
        <div class="ikuai-stat__value">{{ status.down_speed || '—' }}</div>
        <div class="ikuai-stat__label">WAN 下行</div>
      </div>
      <div class="ikuai-stat" style="--accent: #06b6d4">
        <div class="ikuai-stat__icon"><v-icon icon="mdi-devices" size="18" /></div>
        <div class="ikuai-stat__value">{{ status.online_devices != null ? status.online_devices : '—' }}</div>
        <div class="ikuai-stat__label">在线设备</div>
      </div>
      <div class="ikuai-stat" style="--accent: #6366f1">
        <div class="ikuai-stat__icon"><v-icon icon="mdi-clock-outline" size="18" /></div>
        <div class="ikuai-stat__value">{{ fmtUptime(status.uptime) || '—' }}</div>
        <div class="ikuai-stat__label">运行时间</div>
      </div>
    </div>

    <!-- 活动 + 提示 -->
    <v-alert v-if="status.error" type="warning" variant="tonal" density="compact" class="mb-3">
      {{ status.error }}（请检查插件配置或路由器连接）
    </v-alert>

    <!-- 备份状态 -->
    <div class="ikuai-card">
      <div class="ikuai-card__header">
        <span class="ikuai-card__title d-flex align-center">
          <v-icon icon="mdi-content-save-check" size="18" color="#22c55e" class="mr-1" />
          备份管理
        </span>
        <span class="d-flex align-center flex-wrap ga-2">
          <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-cloud-upload-outline"
            :loading="backingUp" :disabled="busy" @click="runBackupNow">
            立即备份
          </v-btn>
          <v-btn variant="tonal" color="error" size="small" prepend-icon="mdi-backup-restore" @click="openRestoreDialog">
            恢复备份
          </v-btn>
        </span>
      </div>
      <div v-if="backupHistory.length" class="ikuai-logs">
        <div v-for="(log, index) in backupHistory.slice(0, 6)" :key="index" class="ikuai-log">
          <span class="ikuai-log__dot" :style="{ background: log.success ? '#22c55e' : '#ef4444' }" />
          <div class="ikuai-log__body">
            <div class="ikuai-log__title">{{ log.filename || log.message || '备份任务' }}</div>
            <div class="ikuai-log__msg">
              {{ log.message || '' }}
              <span v-if="targetsText(log)" class="ikuai-log__targets">落点：{{ targetsText(log) }}</span>
              <span v-if="failedText(log)" class="ikuai-log__targets ikuai-log__targets--fail">未成功：{{ failedText(log) }}</span>
            </div>
          </div>
          <div class="ikuai-log__meta">
            <span class="ikuai-log__result" :style="{ color: log.success ? '#22c55e' : '#ef4444' }">
              {{ log.success ? '成功' : '失败' }}
            </span>
            <span class="ikuai-log__time">{{ log.time || '' }}</span>
          </div>
        </div>
      </div>
      <div v-else class="ikuai-empty">暂无备份记录，可点击右上角「立即备份」或在「插件配置」中设置定时备份</div>
    </div>

    <!-- 备份文件 / 恢复备份 对话框 -->
    <v-dialog v-model="restoreDialog.show" max-width="640" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-file-cog-outline" size="20" color="primary" class="mr-2" />
          备份文件
          <v-chip size="x-small" variant="tonal" class="ml-2">{{ restoreDialog.backups.length }} 个</v-chip>
          <v-spacer />
          <v-btn size="x-small" variant="text" prepend-icon="mdi-refresh" :loading="restoreDialog.loading"
            @click="openRestoreDialog">刷新</v-btn>
        </v-card-title>
        <v-card-text>
          <v-alert type="warning" variant="tonal" density="compact" class="mb-3">
            恢复会用备份文件覆盖路由器当前全部配置，操作前会自动创建恢复点。下载 / 删除只影响备份文件本身，不影响路由器。
          </v-alert>
          <v-alert v-if="!restoreDialog.enableRestore" type="info" variant="tonal" density="compact" class="mb-3">
            恢复功能未启用（插件配置 → 恢复设置）。当前仍可下载或删除备份文件。
          </v-alert>
          <div v-if="restoreDialog.backups.length" class="restore-list">
            <div v-for="(b, idx) in restoreDialog.backups" :key="idx" class="restore-row">
              <v-icon size="16" color="primary">mdi-file-cog-outline</v-icon>
              <span class="restore-name" :title="b.filename">{{ b.filename }}</span>
              <v-chip size="x-small" variant="outlined" class="mx-1" :color="sourceChipColor(b.source)">{{ b.source || '本地备份' }}</v-chip>
              <span class="restore-time">{{ b.time ? fmtTime(b.time) : '' }}</span>
              <v-btn size="x-small" variant="tonal" color="error" :disabled="!restoreDialog.enableRestore"
                :loading="restoreDialog.restoring === b.filename" @click="askRestore(b)">恢复</v-btn>
              <v-btn size="x-small" variant="text" icon="mdi-download" title="下载到浏览器"
                :loading="downloading === b.filename" @click="downloadBackup(b)" />
              <v-btn size="x-small" variant="text" icon="mdi-trash-can-outline" color="error" title="删除备份"
                @click="askDelete(b)" />
            </div>
          </div>
          <div v-else class="text-caption text-medium-emphasis text-center py-2">
            {{ restoreDialog.loading ? '加载中...' : '暂无可用的备份文件，请先执行备份' }}
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="restoreDialog.show = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除备份确认 -->
    <v-dialog v-model="deleteConfirm.show" max-width="420" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-trash-can-outline" size="20" color="error" class="mr-2" />
          删除备份文件？
        </v-card-title>
        <v-card-text>
          将从 <b>{{ deleteConfirm.backup?.source || '本地备份' }}</b> 中永久删除
          <b>{{ deleteConfirm.backup?.filename }}</b>，删除后不可恢复。
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteConfirm.show = false">取消</v-btn>
          <v-btn color="error" variant="tonal" :loading="deleteConfirm.loading" @click="doDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 恢复二次确认 -->
    <v-dialog v-model="restoreConfirm.show" max-width="420" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-alert-octagon-outline" size="20" color="error" class="mr-2" />
          确认恢复？
        </v-card-title>
        <v-card-text>
          将使用 <b>{{ restoreConfirm.backup?.filename }}</b>（{{ restoreConfirm.backup?.source || '本地备份' }}）
          覆盖路由器当前配置，恢复期间路由器可能短暂离线。确定继续吗？
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="restoreConfirm.show = false">取消</v-btn>
          <v-btn color="error" variant="tonal" :loading="restoreDialog.restoring === restoreConfirm.backup?.filename"
            @click="doRestore">确认恢复</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 告警记录 -->
    <div class="ikuai-card">
      <div class="ikuai-card__header">
        <span class="ikuai-card__title d-flex align-center">
          <v-icon icon="mdi-bell-alert-outline" size="18" color="#f59e0b" class="mr-1" />
          告警记录
          <v-chip size="x-small" variant="tonal" class="ml-2" :color="alerts.enabled ? 'success' : 'grey'">
            {{ alerts.enabled ? '监控中' : '未启用' }}
          </v-chip>
          <v-chip v-if="alerts.active" size="x-small" variant="tonal" color="error" class="ml-1">告警中</v-chip>
        </span>
        <span class="d-flex align-center ga-2">
          <span v-if="alerts.enabled" class="text-caption text-medium-emphasis">
            CPU ≥ {{ alerts.cpu_threshold }}% / 内存 ≥ {{ alerts.mem_threshold }}%
          </span>
          <v-btn size="small" variant="text" prepend-icon="mdi-refresh" :loading="alertsLoading" @click="loadAlerts">刷新</v-btn>
          <v-btn v-if="alerts.items.length" size="small" variant="text" color="error" @click="clearAlerts">清空</v-btn>
        </span>
      </div>
      <div v-if="alerts.items.length" class="alert-list">
        <div v-for="(a, idx) in alerts.items.slice(0, 8)" :key="a.id || idx" class="alert-row">
          <span class="alert-dot" :style="{ background: a.end ? 'rgba(34,197,94,0.9)' : 'rgba(239,68,68,0.9)' }" />
          <span class="alert-kind">{{ a.kind }}</span>
          <span class="alert-detail">
            CPU {{ a.peak_cpu }}% / 内存 {{ a.peak_mem }}%
            <span class="alert-threshold">阈值 {{ a.cpu_limit }}% / {{ a.mem_limit }}%</span>
          </span>
          <span class="alert-time">
            {{ fmtAlertTime(a.start) }}
            <span class="alert-sep">→</span>
            <span :style="{ color: a.end ? '#22c55e' : '#ef4444' }">
              {{ a.end ? fmtAlertTime(a.end) : '持续中' }}
            </span>
            <span v-if="a.end && a.duration" class="alert-dur">（{{ fmtDuration(a.duration) }}）</span>
          </span>
        </div>
      </div>
      <div v-else class="ikuai-empty">
        {{ alerts.enabled ? '暂无告警记录，负载正常时会保持安静' : '负载告警未启用，可在「插件配置 → 监控与告警」中打开' }}
      </div>
    </div>

    <!-- 说明 -->
    <div class="ikuai-card">
      <div class="ikuai-card__header">
        <span class="ikuai-card__title d-flex align-center">
          <v-icon icon="mdi-information-outline" size="18" color="#6366f1" class="mr-1" />
          完整监控
        </span>
      </div>
      <div class="ikuai-guide">
        <p>
          <v-icon icon="mdi-view-dashboard-outline" size="15" color="primary" class="mr-1" />
          实时监控（性能负载 / 终端排行 / 协议排行 / 在线终端等 14 视图）/ 线路监控 / 系统日志，请到左侧导航「<strong>爱快路由</strong>」页面查看。
        </p>
        <p>
          <v-icon icon="mdi-cog-outline" size="15" color="primary" class="mr-1" />
          定时备份 / 存储备份 / WebDAV / 负载告警等设置，点击右上角「<strong>插件配置</strong>」。
        </p>
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

const PLUGIN_ID = 'IkuaiRouterBackup'
const REFRESH_MS = 30000

const status = reactive({ cpu: null, mem: null, up_speed: '', down_speed: '', online_devices: null, uptime: 0, error: '' })
const interfaces = ref([])
const backupHistory = ref([])
const backupActivity = ref('空闲')
const restoreActivity = ref('空闲')

// 备份历史落点（本地 / 网盘 / WebDAV）
const targetsText = (log) => {
  const labels = []
  for (const t of log?.targets || []) {
    const kind = String(t?.kind || '')
    let label
    if (kind === 'local') label = '本地磁盘'
    else if (kind === 'webdav') label = 'WebDAV'
    else if (kind === 'cloud') label = `网盘·${t?.label || ''}`
    else label = String(t?.label || kind)
    if (label && !labels.includes(label)) labels.push(label)
  }
  return labels.join(' + ')
}
const failedText = (log) => (log?.failed || []).filter(Boolean).join('、')
const loading = ref(false)
const backingUp = ref(false)
const toast = reactive({ show: false, type: 'success', text: '' })
let timer = null
let toastTimer = null

const showToast = (text, type = 'success') => {
  toast.text = text
  toast.type = type
  toast.show = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.show = false), 3500)
}

async function runBackupNow() {
  backingUp.value = true
  try {
    const apiPath = `plugin/${PLUGIN_ID}/backup`
    const result = props.api?.post
      ? await props.api.post(apiPath, {})
      : await (await fetch(`/api/v1/${apiPath}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })).json()
    if (result?.success) {
      showToast(result.message || '备份任务已启动')
      setTimeout(loadAll, 3000)
    } else {
      showToast(result?.message || '启动备份任务失败', 'error')
    }
  } catch (error) {
    showToast('启动备份任务失败', 'error')
  } finally {
    backingUp.value = false
  }
}

const fmtSpeed = (bps) => {
  const v = Number(bps) || 0
  if (v >= 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024).toFixed(2) + ' GB/s'
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(1) + ' MB/s'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' KB/s'
  return v + ' B/s'
}

const fmtUptime = (sec) => {
  const s = Number(sec) || 0
  if (!s) return ''
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (d > 0) return `${d}天${h}时`
  if (h > 0) return `${h}时${m}分`
  return `${m}分`
}

const busy = computed(() => {
  const b = String(backupActivity.value || '')
  const r = String(restoreActivity.value || '')
  return (b && b !== '空闲') || (r && r !== '空闲')
})

// ============ 恢复备份 ============
const restoreDialog = reactive({ show: false, loading: false, restoring: '', enableRestore: false, backups: [] })
const restoreConfirm = reactive({ show: false, backup: null })

const sourceChipColor = (source) => {
  if (!source) return 'primary'
  if (source.includes('网盘')) return 'info'
  if (source.includes('WebDAV')) return 'purple'
  return 'primary'
}

const fmtTime = (ts) => {
  if (!ts) return '-'
  try {
    return new Date(Number(ts) * 1000).toLocaleString()
  } catch (error) {
    return '-'
  }
}

const openRestoreDialog = async () => {
  restoreDialog.show = true
  restoreDialog.loading = true
  restoreDialog.restoring = ''
  try {
    const data = await request('/available_backups')
    restoreDialog.enableRestore = !!data?.enable_restore
    restoreDialog.backups = data?.backups || []
  } catch (error) {
    restoreDialog.enableRestore = false
    restoreDialog.backups = []
  } finally {
    restoreDialog.loading = false
  }
}

const askRestore = (backup) => {
  restoreConfirm.backup = backup
  restoreConfirm.show = true
}

// ============ 备份文件下载 / 删除 ============
const downloading = ref('')
const deleteConfirm = reactive({ show: false, loading: false, backup: null })

const backupParams = (b) => ({
  filename: b.filename,
  source: b.source || '本地备份',
  storage: b.storage || '',
  remote_dir: b.remote_dir || '',
})

async function downloadBackup(b) {
  downloading.value = b.filename
  try {
    const apiPath = `plugin/${PLUGIN_ID}/download_backup`
    const params = backupParams(b)
    let data
    if (props.api?.get) {
      data = await props.api.get(apiPath, { params })
    } else {
      const qs = new URLSearchParams(params).toString()
      data = await (await fetch(`/api/v1/${apiPath}?${qs}`)).json()
    }
    if (!data?.ok) throw new Error(data?.error || '读取备份文件失败')
    const bin = atob(data.content || '')
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i)
    const blob = new Blob([bytes], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = data.filename || b.filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    showToast(`已下载 ${a.download}（${((data.size || 0) / 1024).toFixed(1)} KB）`)
  } catch (error) {
    showToast(error?.message || '下载备份失败', 'error')
  } finally {
    downloading.value = ''
  }
}

const askDelete = (b) => {
  deleteConfirm.backup = b
  deleteConfirm.show = true
}

async function doDelete() {
  const b = deleteConfirm.backup
  if (!b) return
  deleteConfirm.loading = true
  try {
    const apiPath = `plugin/${PLUGIN_ID}/delete_backup`
    const body = backupParams(b)
    const result = props.api?.post
      ? await props.api.post(apiPath, body)
      : await (await fetch(`/api/v1/${apiPath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })).json()
    if (result?.ok) {
      showToast(result?.msg || '已删除备份文件')
      deleteConfirm.show = false
      await openRestoreDialog()
    } else {
      showToast(result?.msg || result?.error || '删除失败', 'error')
    }
  } catch (error) {
    showToast('删除备份失败', 'error')
  } finally {
    deleteConfirm.loading = false
  }
}

const doRestore = async () => {
  const b = restoreConfirm.backup
  if (!b) return
  restoreDialog.restoring = b.filename
  try {
    const apiPath = `plugin/${PLUGIN_ID}/restore`
    const body = {
      filename: b.filename,
      source: b.source || '本地备份',
      storage: b.storage || '',
      remote_dir: b.remote_dir || '',
    }
    const result = props.api?.post
      ? await props.api.post(apiPath, body)
      : await (await fetch(`/api/v1/${apiPath}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json()
    if (result?.success === false) {
      showToast(result?.message || '启动恢复失败', 'error')
    } else {
      showToast('恢复任务已启动，恢复完成后路由器将应用备份配置')
      restoreConfirm.show = false
      restoreDialog.show = false
      setTimeout(loadHistories, 3000)
    }
  } catch (error) {
    showToast('启动恢复失败', 'error')
  } finally {
    restoreDialog.restoring = ''
  }
}

async function request(path, method = 'GET', body = null) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`
  if (method === 'POST') {
    if (props.api?.post) {
      return await props.api.post(apiPath, body || {})
    }
    const response = await fetch(`/api/v1/${apiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    })
    return await response.json()
  }
  if (props.api?.get) {
    return await props.api.get(apiPath, {})
  }
  const response = await fetch(`/api/v1/${apiPath}`)
  return await response.json()
}

async function loadStatus() {
  try {
    const data = await request('/status')
    if (data && typeof data === 'object') {
      status.cpu = data.cpu_usage != null ? Number(data.cpu_usage) : null
      status.mem = data.mem_usage != null ? Number(data.mem_usage) : null
      status.up_speed = fmtSpeed(data.upload_speed)
      status.down_speed = fmtSpeed(data.download_speed)
      status.uptime = data.uptime || 0
      status.hostname = data.hostname || ''
      status.version = data.version || ''
      status.error = data.ok === false ? (data.error || '获取状态失败') : ''
      interfaces.value = Array.isArray(data.interfaces) ? data.interfaces : []
    }
  } catch (error) {
    status.error = '获取路由器状态失败'
  }
  try {
    const data = await request('/devices')
    if (data && typeof data === 'object') {
      status.online_devices = data.ok && Array.isArray(data.devices) ? data.devices.length : null
    }
  } catch (error) {
    // 设备数获取失败不影响其他状态
  }
}

async function loadHistories() {
  try {
    const data = await request('/histories')
    if (data && typeof data === 'object') {
      backupHistory.value = Array.isArray(data.backup_history) ? data.backup_history : []
      backupActivity.value = data.backup_activity || '空闲'
      restoreActivity.value = data.restore_activity || '空闲'
    }
  } catch (error) {
    // 静默失败，保留上一次结果
  }
}

async function loadAll() {
  loading.value = true
  try {
    await Promise.all([loadStatus(), loadHistories(), loadAlerts()])
  } finally {
    loading.value = false
  }
}

// ============ 告警记录 ============
const alerts = reactive({ items: [], total: 0, active: null, enabled: false, cpu_threshold: 90, mem_threshold: 90 })
const alertsLoading = ref(false)

const fmtAlertTime = (ts) => {
  const n = Number(ts) || 0
  if (!n) return '-'
  const d = new Date(n * 1000)
  const p = (x) => String(x).padStart(2, '0')
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const fmtDuration = (sec) => {
  const s = Number(sec) || 0
  if (s >= 3600) return `${Math.floor(s / 3600)} 小时 ${Math.floor((s % 3600) / 60)} 分`
  if (s >= 60) return `${Math.floor(s / 60)} 分钟`
  return `${s} 秒`
}

async function loadAlerts() {
  alertsLoading.value = true
  try {
    const data = await request('/alert_history')
    if (data && typeof data === 'object' && data.ok !== false) {
      alerts.items = Array.isArray(data.items) ? data.items : []
      alerts.total = data.total || 0
      alerts.active = data.active || null
      alerts.enabled = !!data.enabled
      alerts.cpu_threshold = data.cpu_threshold ?? 90
      alerts.mem_threshold = data.mem_threshold ?? 90
    }
  } catch (error) {
    // 静默
  } finally {
    alertsLoading.value = false
  }
}

async function clearAlerts() {
  try {
    const res = await request('/alert_history', 'POST', {})
    if (res?.ok) {
      showToast(res.msg || '告警记录已清空')
      loadAlerts()
    } else {
      showToast(res?.error || '清空失败', 'error')
    }
  } catch (error) {
    showToast('清空失败', 'error')
  }
}

onMounted(() => {
  loadAll()
  timer = setInterval(() => {
    loadStatus()
    loadAlerts()
  }, REFRESH_MS)
})

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>

<style scoped>
.ikuai-page {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.ikuai-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 8px;
}

.ikuai-topbar__left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.ikuai-topbar__meta { min-width: 0; flex: 1; }
.ikuai-topbar__right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.ikuai-topbar__icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: rgba(79, 140, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4f8cff;
  flex-shrink: 0;
}

.ikuai-topbar__title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.ikuai-topbar__sub {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 2px;
}

.ikuai-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
}

.ikuai-stat {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ikuai-stat__icon {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  color: var(--accent);
  margin-bottom: 2px;
}

.ikuai-stat__value {
  font-size: 20px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.ikuai-stat__label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.ikuai-card {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ikuai-card__header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }

.ikuai-card__title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.ikuai-logs {
  display: flex;
  flex-direction: column;
  max-height: 260px;
  overflow-y: auto;
}

.ikuai-log {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 2px;
  border-bottom: 0.5px solid rgba(var(--v-theme-on-surface), 0.06);
}

.ikuai-log:last-child { border-bottom: none; }

.ikuai-log__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.ikuai-log__body { flex: 1; min-width: 0; }

.ikuai-log__title {
  font-size: 12.5px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.82);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ikuai-log__msg {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 2px;
}

.ikuai-log__targets {
  display: inline-block;
  margin-left: 8px;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 10px;
  color: rgba(var(--v-theme-primary), 0.9);
  background: rgba(var(--v-theme-primary), 0.08);
  border: 1px solid rgba(var(--v-theme-primary), 0.18);
}
.ikuai-log__targets--fail {
  color: rgba(var(--v-theme-error), 0.9);
  background: rgba(var(--v-theme-error), 0.08);
  border-color: rgba(var(--v-theme-error), 0.2);
  margin-left: 4px;
}

.ikuai-log__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.ikuai-log__result {
  font-size: 11px;
  font-weight: 600;
}

.ikuai-log__time {
  font-size: 10.5px;
  font-family: 'SF Mono', Menlo, monospace;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.ikuai-empty {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  padding: 6px 0;
}

/* 告警记录 */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.alert-row {
  display: grid;
  grid-template-columns: 8px 70px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 6px 4px;
  border-bottom: 1px dashed rgba(var(--v-theme-on-surface), 0.07);
  font-size: 12px;
}
.alert-row:last-child {
  border-bottom: none;
}
.alert-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: block;
}
.alert-kind {
  font-weight: 600;
  font-size: 11.5px;
}
.alert-detail {
  color: rgba(var(--v-theme-on-surface), 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.alert-threshold {
  color: rgba(var(--v-theme-on-surface), 0.35);
  font-size: 10.5px;
  margin-left: 6px;
}
.alert-time {
  font-family: 'SF Mono', Menlo, monospace;
  font-size: 10.5px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  white-space: nowrap;
}
.alert-sep {
  margin: 0 4px;
  opacity: 0.5;
}
.alert-dur {
  opacity: 0.7;
}

/* 恢复列表 */
.restore-list {
  max-height: 320px;
  overflow-y: auto;
}
.restore-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 12px;
}
.restore-row:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}
.restore-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.restore-time {
  color: rgba(var(--v-theme-on-surface), 0.55);
  font-family: 'SF Mono', Menlo, monospace;
  white-space: nowrap;
}

.ikuai-guide { display: flex; flex-direction: column; gap: 7px; }

.ikuai-guide p {
  margin: 0;
  font-size: 12px;
  line-height: 1.65;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.ikuai-guide strong {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.78);
}

.ikuai-toast {
  position: fixed;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3000;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}

.ikuai-toast--success { background: rgba(34, 197, 94, 0.92); }
.ikuai-toast--error { background: rgba(239, 68, 68, 0.92); }

.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-8px); }

@media (max-width: 600px) {
  .ikuai-page { padding: 12px; }
  .ikuai-topbar__sub { display: none; }
}
</style>
