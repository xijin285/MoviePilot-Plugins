<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'switch'])

const config = reactive({
  enabled: false,
  permanently_delete: false,
  cookie: '',
  page_size: 50,
  sort_field: 'file_name',
  sort_order: 'asc',
  logged_in: false,
  ...props.initialConfig,
})

const loading = ref(false)
const saving = ref(false)
const showCookie = ref(false)
const message = reactive({ show: false, type: 'info', text: '' })
let messageTimer = null

const sortOrderOptions = ref([
  { title: '升序', value: 'asc' },
  { title: '降序', value: 'desc' },
])

const sortFieldOptions = ref([
  { title: '文件名', value: 'file_name' },
  { title: '更新时间', value: 'updated_at' },
  { title: '文件大小', value: 'size' },
  { title: '创建时间', value: 'created_at' },
])

function clearMessageTimer() {
  if (messageTimer) {
    clearTimeout(messageTimer)
    messageTimer = null
  }
}

function scheduleMessageClose(type = 'info') {
  clearMessageTimer()
  const timeout = type === 'error' ? 5000 : 3000
  messageTimer = setTimeout(() => {
    message.show = false
    messageTimer = null
  }, timeout)
}

function pushMessage(text, type = 'info') {
  message.text = text
  message.type = type
  message.show = true
  scheduleMessageClose(type)
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

function applyConfig(data = {}) {
  config.enabled = Boolean(data.enabled)
  config.permanently_delete = Boolean(data.permanently_delete)
  config.cookie = data.cookie || ''
  config.page_size = Number(data.page_size || 50)
  config.sort_field = data.sort_field || 'file_name'
  config.sort_order = data.sort_order || 'asc'
  config.logged_in = Boolean(data.logged_in)
}

async function loadConfig() {
  loading.value = true
  try {
    const data = await request('/config')
    applyConfig(data)
  } catch (error) {
    pushMessage(`加载配置失败：${error}`, 'error')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const result = await request('/config', {
      method: 'POST',
      body: JSON.stringify({ ...config }),
    })
    if (!result.success) {
      throw new Error(result.message || '保存失败')
    }
    applyConfig(result.data || {})
    pushMessage(result.message || '配置保存成功', 'success')
  } catch (error) {
    pushMessage(`保存配置失败：${error.message || error}`, 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})

onBeforeUnmount(() => {
  clearMessageTimer()
})
</script>

<template>
  <div class="qkcfg-page">
    <!-- 顶栏 -->
    <div class="qkcfg-topbar">
      <div class="qkcfg-topbar__left">
        <div class="qkcfg-topbar__icon">
          <v-icon icon="mdi-cloud-outline" size="24" />
        </div>
        <div class="qkcfg-topbar__meta">
          <div class="qkcfg-topbar__title">夸克网盘 · 配置</div>
          <div class="qkcfg-topbar__sub">插件参数、认证与文件操作管理</div>
        </div>
      </div>
      <div class="qkcfg-topbar__right">
        <v-btn-group variant="tonal" density="compact" class="elevation-0">
          <v-btn color="primary" @click="emit('switch')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-view-dashboard" size="18" class="mr-sm-1" />
            <span class="btn-text d-none d-sm-inline">状态页</span>
          </v-btn>
          <v-btn color="primary" :loading="saving" @click="saveConfig" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-content-save" size="18" class="mr-sm-1" />
            <span class="btn-text d-none d-sm-inline">保存</span>
          </v-btn>
          <v-btn color="primary" @click="emit('close')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-close" size="18" />
            <span class="btn-text d-none d-sm-inline">关闭</span>
          </v-btn>
        </v-btn-group>
      </div>
    </div>

    <!-- Toast 消息 -->
    <Transition name="qkcfg-slide">
      <div v-if="message.show" class="qkcfg-toast" :class="`qkcfg-toast--${message.type}`">
        <v-icon :icon="message.type === 'success' ? 'mdi-check-circle' : message.type === 'error' ? 'mdi-alert-circle' : 'mdi-information'" size="18" />
        <span>{{ message.text }}</span>
        <button class="qkcfg-toast__close" @click="message.show = false">
          <v-icon icon="mdi-close" size="16" />
        </button>
      </div>
    </Transition>

    <!-- 基础设置卡片 -->
    <div class="qkcfg-card">
      <div class="qkcfg-card__header">
        <span class="qkcfg-card__title d-flex align-center">
          <v-icon icon="mdi-toggle-switch-outline" size="18" color="#8b5cf6" class="mr-1" />
          基础设置
        </span>
      </div>

      <!-- 开关网格 -->
      <div class="qkcfg-switch-grid">
        <div
          class="qkcfg-switch-item"
          :class="{ 'qkcfg-switch-item--active': config.enabled }"
          style="--qkcfg-accent: #8b5cf6"
        >
          <div class="qkcfg-switch-item__main">
            <div class="qkcfg-switch-item__icon">
              <v-icon icon="mdi-power-plug" size="18" />
            </div>
            <div class="qkcfg-switch-item__text">
              <span class="qkcfg-switch-item__label">启用插件</span>
            </div>
          </div>
          <label class="qkcfg-switch" style="--switch-checked-bg: #8b5cf6;">
            <input v-model="config.enabled" type="checkbox" />
            <div class="qkcfg-switch__slider">
              <div class="qkcfg-switch__circle">
                <svg class="qkcfg-switch__cross" xml:space="preserve" style="enable-background:new 0 0 512 512" viewBox="0 0 365.696 365.696" y="0" x="0" height="6" width="6" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" xmlns="http://www.w3.org/2000/svg"><g><path fill="currentColor" d="M243.188 182.86 356.32 69.726c12.5-12.5 12.5-32.766 0-45.247L341.238 9.398c-12.504-12.503-32.77-12.503-45.25 0L182.86 122.528 69.727 9.374c-12.5-12.5-32.766-12.5-45.247 0L9.375 24.457c-12.5 12.504-12.5 32.77 0 45.25l113.152 113.152L9.398 295.99c-12.503 12.503-12.503 32.769 0 45.25L24.48 356.32c12.5 12.5 32.766 12.5 45.247 0l113.132-113.132L295.99 356.32c12.503 12.5 32.769 12.5 45.25 0l15.081-15.082c12.5-12.504 12.5-32.77 0-45.25zm0 0" /></g></svg>
                <svg class="qkcfg-switch__checkmark" xml:space="preserve" style="enable-background:new 0 0 512 512" viewBox="0 0 24 24" y="0" x="0" height="10" width="10" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" xmlns="http://www.w3.org/2000/svg"><g transform="translate(-0.4, 0.2)"><path fill="currentColor" d="M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z" /></g></svg>
              </div>
            </div>
          </label>
        </div>

        <div
          class="qkcfg-switch-item"
          :class="{ 'qkcfg-switch-item--active': config.permanently_delete }"
          style="--qkcfg-accent: #ef4444"
        >
          <div class="qkcfg-switch-item__main">
            <div class="qkcfg-switch-item__icon">
              <v-icon icon="mdi-delete-alert-outline" size="18" />
            </div>
            <div class="qkcfg-switch-item__text">
              <span class="qkcfg-switch-item__label">彻底删除</span>
            </div>
          </div>
          <label class="qkcfg-switch" style="--switch-checked-bg: #ef4444;">
            <input v-model="config.permanently_delete" type="checkbox" />
            <div class="qkcfg-switch__slider">
              <div class="qkcfg-switch__circle">
                <svg class="qkcfg-switch__cross" xml:space="preserve" style="enable-background:new 0 0 512 512" viewBox="0 0 365.696 365.696" y="0" x="0" height="6" width="6" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" xmlns="http://www.w3.org/2000/svg"><g><path fill="currentColor" d="M243.188 182.86 356.32 69.726c12.5-12.5 12.5-32.766 0-45.247L341.238 9.398c-12.504-12.503-32.77-12.503-45.25 0L182.86 122.528 69.727 9.374c-12.5-12.5-32.766-12.5-45.247 0L9.375 24.457c-12.5 12.504-12.5 32.77 0 45.25l113.152 113.152L9.398 295.99c-12.503 12.503-12.503 32.769 0 45.25L24.48 356.32c12.5 12.5 32.766 12.5 45.247 0l113.132-113.132L295.99 356.32c12.503 12.5 32.769 12.5 45.25 0l15.081-15.082c12.5-12.504 12.5-32.77 0-45.25zm0 0" /></g></svg>
                <svg class="qkcfg-switch__checkmark" xml:space="preserve" style="enable-background:new 0 0 512 512" viewBox="0 0 24 24" y="0" x="0" height="10" width="10" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" xmlns="http://www.w3.org/2000/svg"><g transform="translate(-0.4, 0.2)"><path fill="currentColor" d="M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z" /></g></svg>
              </div>
            </div>
          </label>
        </div>
      </div>

      <div class="qkcfg-divider" />

      <!-- 查询参数 -->
      <div class="qkcfg-field">
        <div class="qkcfg-field__header">
          <div class="qkcfg-field__title-main">
            <v-icon icon="mdi-sort-variant" size="18" color="#3b82f6" class="qkcfg-field__title-icon" />
            <div class="qkcfg-field__title-text">
              <label class="qkcfg-field__label">查询参数</label>
            </div>
          </div>
        </div>

        <div class="qkcfg-form-grid qkcfg-form-grid--settings">
          <div class="qkcfg-form-item">
            <v-text-field
              v-model.number="config.page_size"
              label="分页大小"
              type="number"
              density="compact"
              variant="outlined"
              hide-details="auto"
              min="1"
              max="200"
              class="qkcfg-input"
            />
            <div class="qkcfg-field-hint">建议 50 ~ 200，控制每次列表请求的文件数量</div>
          </div>

          <div class="qkcfg-form-item">
            <v-select
              v-model="config.sort_field"
              :items="sortFieldOptions"
              item-title="title"
              item-value="value"
              label="排序字段"
              density="compact"
              variant="outlined"
              hide-details="auto"
              class="qkcfg-input"
            />
            <div class="qkcfg-field-hint">选择文件列表的默认排序方式</div>
          </div>

          <div class="qkcfg-form-item">
            <v-select
              v-model="config.sort_order"
              :items="sortOrderOptions"
              item-title="title"
              item-value="value"
              label="排序方向"
              density="compact"
              variant="outlined"
              hide-details="auto"
              class="qkcfg-input"
            />
            <div class="qkcfg-field-hint">升序 A→Z，降序 Z→A</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 认证信息卡片 -->
    <div class="qkcfg-card">
      <div class="qkcfg-card__header">
        <span class="qkcfg-card__title d-flex align-center">
          <v-icon icon="mdi-key-outline" size="18" color="#f59e0b" class="mr-1" />
          认证信息
        </span>
      </div>

      <div class="qkcfg-field">
        <div class="qkcfg-field__header">
          <div class="qkcfg-field__title-main">
            <v-icon icon="mdi-cookie-outline" size="18" color="#f59e0b" class="qkcfg-field__title-icon" />
            <div class="qkcfg-field__title-text">
              <label class="qkcfg-field__label">Cookie</label>
            </div>
          </div>
          <v-btn
            variant="text"
            density="compact"
            :icon="showCookie ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
            @click="showCookie = !showCookie"
            size="small"
          />
        </div>

        <!-- 隐藏模式: v-text-field 支持 type=password 显示圆点 -->
        <v-text-field
          v-if="!showCookie"
          v-model="config.cookie"
          type="password"
          variant="outlined"
          density="compact"
          class="qkcfg-input"
          hide-details
          autocomplete="off"
          placeholder="扫码登录后自动填充，无需手动填写"
        />
        <!-- 显示模式: v-textarea 方便查看和编辑长 Cookie -->
        <v-textarea
          v-else
          v-model="config.cookie"
          variant="outlined"
          density="compact"
          class="qkcfg-input"
          hide-details
          rows="2"
          auto-grow
          autocomplete="off"
          placeholder="扫码登录后自动填充，无需手动填写"
        />
        <div class="qkcfg-field-hint">
          <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
          <span>通过状态页扫码登录自动获取，无需手动填写。如需手动填写，请从浏览器开发者工具复制完整 Cookie。</span>
        </div>
      </div>
    </div>

    <!-- 使用说明卡片 -->
    <div class="qkcfg-card">
      <div class="qkcfg-card__header">
        <span class="qkcfg-card__title d-flex align-center">
          <v-icon icon="mdi-book-information-variant" size="18" color="#6366f1" class="mr-1" />
          使用说明
        </span>
      </div>

      <div class="qkcfg-guide">
        <div class="qkcfg-guide__section">
          <p class="qkcfg-guide__paragraph">
            <v-icon icon="mdi-numeric-1-circle-outline" size="16" color="primary" class="mr-1" />
            <strong>扫码登录：</strong>请在状态页使用二维码，打开夸克 App 扫码完成授权登录
          </p>
          <p class="qkcfg-guide__paragraph">
            <v-icon icon="mdi-numeric-2-circle-outline" size="16" color="primary" class="mr-1" />
            <strong>Cookie 管理：</strong>登录成功后 Cookie 会自动保存，刷新页面后无需重新登录
          </p>
          <p class="qkcfg-guide__paragraph">
            <v-icon icon="mdi-numeric-3-circle-outline" size="16" color="primary" class="mr-1" />
            <strong>参数说明：</strong>分页大小建议 50-200，排序字段可选 file_name / updated_at / size 等
          </p>
          <p class="qkcfg-guide__paragraph">
            <v-icon icon="mdi-numeric-4-circle-outline" size="16" color="primary" class="mr-1" />
            <strong>彻底删除：</strong>开启后会先执行普通删除，再到回收站中匹配同项目并二次删除
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qkcfg-page {
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
.qkcfg-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 8px;
}

.qkcfg-topbar__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.qkcfg-topbar__meta {
  min-width: 0;
  flex: 1;
}

.qkcfg-topbar__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.qkcfg-topbar__right :deep(.v-btn-group) {
  flex-wrap: nowrap;
}

.qkcfg-topbar__icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: rgba(139, 92, 246, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8b5cf6;
  flex-shrink: 0;
}

.qkcfg-topbar__title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.qkcfg-topbar__sub {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== Toast ===== */
.qkcfg-toast {
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

.qkcfg-toast--success {
  background: rgba(34, 197, 94, 0.08);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.15);
}

.qkcfg-toast--error {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.15);
}

.qkcfg-toast--info {
  background: rgba(var(--v-theme-info), 0.08);
  color: rgb(var(--v-theme-info));
  border-color: rgba(var(--v-theme-info), 0.15);
}

.qkcfg-toast__close {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
  display: flex;
  transition: opacity 0.2s ease;
}

.qkcfg-toast__close:hover { opacity: 1; }

.qkcfg-slide-enter-active,
.qkcfg-slide-leave-active { transition: all 0.3s ease; }
.qkcfg-slide-enter-from,
.qkcfg-slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* ===== 卡片 ===== */
.qkcfg-card {
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

.qkcfg-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.qkcfg-card__title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* ===== 分割线 ===== */
.qkcfg-divider {
  height: 0.5px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  margin: 0 -4px;
}

/* ===== 字段区块 ===== */
.qkcfg-field {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.qkcfg-field__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.qkcfg-field__title-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qkcfg-field__title-icon {
  flex-shrink: 0;
}

.qkcfg-field__title-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.qkcfg-field__label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.qkcfg-field-hint {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  display: flex;
  align-items: center;
  line-height: 1.5;
}

/* ===== 开关网格 ===== */
.qkcfg-switch-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.qkcfg-switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 14px;
  background: rgba(var(--v-theme-surface), 0.78);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.qkcfg-switch-item--active {
  border-color: color-mix(in srgb, var(--qkcfg-accent) 45%, transparent);
  background: color-mix(in srgb, var(--qkcfg-accent) 7%, rgba(var(--v-theme-surface), 0.9));
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06), inset 0 0 0 1px color-mix(in srgb, var(--qkcfg-accent) 18%, transparent);
}

.qkcfg-switch-item__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.qkcfg-switch-item__icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--qkcfg-accent);
  background: color-mix(in srgb, var(--qkcfg-accent) 14%, transparent);
}

.qkcfg-switch-item__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.qkcfg-switch-item__label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.84);
}

/* ===== 表单网格 ===== */
.qkcfg-form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.qkcfg-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qkcfg-input :deep(.v-field) {
  border-radius: 12px;
  background: rgba(var(--v-theme-surface), 0.72);
}

/* ===== 使用说明 ===== */
.qkcfg-guide {
  font-size: 13px;
  line-height: 1.7;
  color: rgba(var(--v-theme-on-surface), 0.72);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qkcfg-guide__section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.qkcfg-guide__paragraph {
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.78);
  display: flex;
  align-items: flex-start;
  line-height: 1.6;
}

.qkcfg-guide__paragraph strong {
  font-weight: 600;
}

/* ===== 自定义开关 ===== */
.qkcfg-switch {
  --switch-width: 36px;
  --switch-height: 20px;
  --switch-bg: rgba(var(--v-theme-on-surface), 0.22);
  --switch-checked-bg: rgb(var(--v-theme-primary));
  --switch-offset: calc((var(--switch-height) - var(--circle-diameter)) / 2);
  --switch-transition: all 0.2s cubic-bezier(0.27, 0.2, 0.25, 1.51);
  --circle-diameter: 16px;
  --circle-bg: #fff;
  --circle-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
  --circle-checked-shadow: -1px 1px 2px rgba(0, 0, 0, 0.2);
  --circle-transition: var(--switch-transition);
  --icon-transition: all 0.2s cubic-bezier(0.27, 0.2, 0.25, 1.51);
  --icon-cross-color: rgba(0, 0, 0, 0.4);
  --icon-cross-size: 6px;
  --icon-checkmark-color: var(--switch-checked-bg);
  --icon-checkmark-size: 10px;
  --effect-width: calc(var(--circle-diameter) / 2);
  --effect-height: calc(var(--effect-width) / 2 - 1px);
  --effect-bg: var(--circle-bg);
  --effect-border-radius: 1px;
  --effect-transition: all 0.2s ease-in-out;
  display: inline-block;
  flex-shrink: 0;
  user-select: none;
}

.qkcfg-switch input { display: none; }

.qkcfg-switch svg {
  transition: var(--icon-transition);
  position: absolute;
  height: auto;
}

.qkcfg-switch__checkmark {
  width: var(--icon-checkmark-size);
  color: var(--icon-checkmark-color);
  transform: scale(0);
}

.qkcfg-switch__cross {
  width: var(--icon-cross-size);
  color: var(--icon-cross-color);
}

.qkcfg-switch__slider {
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

.qkcfg-switch__circle {
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
  left: var(--switch-offset);
}

.qkcfg-switch__slider::before {
  content: "";
  position: absolute;
  width: var(--effect-width);
  height: var(--effect-height);
  left: calc(var(--switch-offset) + (var(--effect-width) / 2));
  background: var(--effect-bg);
  border-radius: var(--effect-border-radius);
  transition: var(--effect-transition);
}

.qkcfg-switch input:checked + .qkcfg-switch__slider {
  background: var(--switch-checked-bg);
}

.qkcfg-switch input:checked + .qkcfg-switch__slider .qkcfg-switch__checkmark {
  transform: scale(1);
}

.qkcfg-switch input:checked + .qkcfg-switch__slider .qkcfg-switch__cross {
  transform: scale(0);
}

.qkcfg-switch input:checked + .qkcfg-switch__slider::before {
  left: calc(100% - var(--effect-width) - (var(--effect-width) / 2) - var(--switch-offset));
}

.qkcfg-switch input:checked + .qkcfg-switch__slider .qkcfg-switch__circle {
  left: calc(100% - var(--circle-diameter) - var(--switch-offset));
  box-shadow: var(--circle-checked-shadow);
}

.qkcfg-switch input:disabled + .qkcfg-switch__slider {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 响应式 ===== */
@media (max-width: 960px) {
  .qkcfg-form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .qkcfg-page {
    padding: 14px;
  }

  .qkcfg-switch-grid {
    grid-template-columns: 1fr;
  }

  .qkcfg-topbar {
    align-items: center;
    flex-wrap: nowrap;
  }

  .qkcfg-topbar__left {
    min-width: 0;
    flex: 1;
  }

  .qkcfg-topbar__meta {
    min-width: 0;
  }

  .qkcfg-topbar__right {
    justify-content: flex-end;
    flex-shrink: 0;
  }

  .qkcfg-topbar__right :deep(.v-btn) {
    min-width: 36px !important;
    padding-inline: 0 !important;
  }

  .qkcfg-switch-item,
  .qkcfg-switch-item__main {
    align-items: flex-start;
  }

  .qkcfg-switch-item {
    padding: 14px;
  }
}
</style>
