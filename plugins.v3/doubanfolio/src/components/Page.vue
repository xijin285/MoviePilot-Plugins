<template>
  <div class="dbfpage">
    <!-- 顶栏 -->
    <div class="dbfpage-topbar">
      <div class="dbfpage-topbar__left">
        <div class="dbfpage-topbar__icon">
          <v-icon icon="mdi-movie-open-outline" size="24" />
        </div>
        <div class="dbfpage-topbar__meta">
          <div class="dbfpage-topbar__title">豆瓣档案</div>
          <div class="dbfpage-topbar__sub">观影记录自动同步到豆瓣</div>
        </div>
      </div>
      <div class="dbfpage-topbar__right">
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-refresh" :loading="loading" @click="loadStatus">
          <span class="d-none d-sm-inline">刷新</span>
        </v-btn>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-cog-outline" @click="emit('switch')">
          <span class="d-none d-sm-inline">配置</span>
        </v-btn>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-close" @click="emit('close')">
          <span class="d-none d-sm-inline">关闭</span>
        </v-btn>
      </div>
    </div>

    <!-- 账号状态 -->
    <div class="dbfpage-card dbfpage-card--hero">
      <div class="dbfpage-hero">
        <div class="dbfpage-hero__avatar" :class="{ 'dbfpage-hero__avatar--off': !status.logged_in }">
          <img
            v-if="status.logged_in && status.avatar"
            :src="status.avatar"
            alt=""
            class="dbfpage-hero__img"
            referrerpolicy="no-referrer"
          />
          <v-icon v-else :icon="status.logged_in ? 'mdi-account-check' : 'mdi-account-off-outline'" size="30" />
        </div>
        <div class="dbfpage-hero__info">
          <div class="dbfpage-hero__name">
            {{ status.logged_in ? (status.nickname || '豆瓣账号') : '未登录' }}
          </div>
          <div class="dbfpage-hero__desc">
            <template v-if="status.logged_in">
              Cookie 有效，播放记录会自动同步
              <span v-if="status.uid" class="dbfpage-hero__uid">UID {{ status.uid }}</span>
            </template>
            <template v-else>
              请到配置页扫码登录，或手动填写 Cookie
            </template>
          </div>
        </div>
        <v-chip :color="status.logged_in ? 'success' : 'warning'" variant="tonal" size="small" :prepend-icon="status.logged_in ? 'mdi-check-decagram' : 'mdi-alert-circle-outline'">
          {{ status.logged_in ? '运行中' : '待配置' }}
        </v-chip>
      </div>
    </div>

    <!-- 数据统计 -->
    <div class="dbfpage-stats">
      <div class="dbfpage-stat" style="--accent: #2e963d">
        <div class="dbfpage-stat__icon"><v-icon icon="mdi-check-circle-outline" size="18" /></div>
        <div class="dbfpage-stat__value">{{ status.processed_count }}</div>
        <div class="dbfpage-stat__label">已同步条目</div>
      </div>
      <div class="dbfpage-stat" style="--accent: #f59e0b">
        <div class="dbfpage-stat__icon"><v-icon icon="mdi-timer-sand" size="18" /></div>
        <div class="dbfpage-stat__value">{{ status.wait_count }}</div>
        <div class="dbfpage-stat__label">等待处理</div>
      </div>
      <div class="dbfpage-stat" style="--accent: #3b82f6">
        <div class="dbfpage-stat__icon"><v-icon icon="mdi-power-plug-outline" size="18" /></div>
        <div class="dbfpage-stat__value">{{ status.enabled ? '已启用' : '已停用' }}</div>
        <div class="dbfpage-stat__label">插件状态</div>
      </div>
      <div class="dbfpage-stat" style="--accent: #8b5cf6">
        <div class="dbfpage-stat__icon"><v-icon icon="mdi-bell-outline" size="18" /></div>
        <div class="dbfpage-stat__value">{{ status.notify ? '开' : '关' }}</div>
        <div class="dbfpage-stat__label">失效通知</div>
      </div>
    </div>

    <!-- 同步记录 -->
    <div class="dbfpage-card">
      <div class="dbfpage-card__header">
        <span class="dbfpage-card__title d-flex align-center">
          <v-icon icon="mdi-history" size="18" color="#3b82f6" class="mr-1" />
          同步记录
        </span>
        <span v-if="logs.length" class="dbfpage-log__count">最近 {{ logs.length }} 条</span>
      </div>
      <div v-if="logs.length" class="dbfpage-logs">
        <div v-for="(log, index) in logs" :key="index" class="dbfpage-log">
          <span class="dbfpage-log__dot" :style="{ background: logColor(log.result) }" />
          <div class="dbfpage-log__body">
            <div class="dbfpage-log__title" :class="{ 'dbfpage-log__title--bad': log.result !== 'success' }">
              {{ log.title }}
            </div>
            <div class="dbfpage-log__msg">{{ log.message }}</div>
          </div>
          <div class="dbfpage-log__meta">
            <span class="dbfpage-log__result" :style="{ color: logColor(log.result) }">{{ logLabel(log.result) }}</span>
            <span class="dbfpage-log__time">{{ log.time }}</span>
          </div>
        </div>
      </div>
      <div v-else class="dbfpage-log__empty">暂无同步记录，播放媒体后会自动记录每次同步结果</div>
    </div>

    <!-- 同步规则 -->
    <div class="dbfpage-card">
      <div class="dbfpage-card__header">
        <span class="dbfpage-card__title d-flex align-center">
          <v-icon icon="mdi-sync" size="18" color="#2e963d" class="mr-1" />
          同步规则
        </span>
      </div>
      <div class="dbfpage-rules">
        <div class="dbfpage-rule">
          <span class="dbfpage-rule__dot" style="background: #3b82f6" />
          <span class="dbfpage-rule__text"><strong>开始播放</strong> → 条目标记为「在看」</span>
        </div>
        <div class="dbfpage-rule">
          <span class="dbfpage-rule__dot" style="background: #22c55e" />
          <span class="dbfpage-rule__text"><strong>播放完成</strong> → 条目标记为「看过」并写入进度</span>
        </div>
        <div class="dbfpage-rule">
          <span class="dbfpage-rule__dot" style="background: #f59e0b" />
          <span class="dbfpage-rule__text"><strong>Cookie 失效</strong> → 每小时检测一次，按设置推送通知</span>
        </div>
      </div>
    </div>

    <!-- 说明 -->
    <div class="dbfpage-card">
      <div class="dbfpage-card__header">
        <span class="dbfpage-card__title d-flex align-center">
          <v-icon icon="mdi-information-outline" size="18" color="#6366f1" class="mr-1" />
          前提条件
        </span>
      </div>
      <div class="dbfpage-guide">
        <p><v-icon icon="mdi-numeric-1-circle-outline" size="15" color="primary" class="mr-1" />媒体服务器需开启 <strong>Webhook</strong>，否则接收不到播放事件。</p>
        <p><v-icon icon="mdi-numeric-2-circle-outline" size="15" color="primary" class="mr-1" />配置页扫码登录后，Cookie 由插件自动维护与续期。</p>
        <p><v-icon icon="mdi-numeric-3-circle-outline" size="15" color="primary" class="mr-1" />豆瓣条目匹配依赖片名，命名不规范时可能匹配失败。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'switch'])

const PLUGIN_ID = 'DoubanFolio'

const status = reactive({
  logged_in: false,
  nickname: '',
  uid: '',
  avatar: '',
  enabled: false,
  notify: false,
  processed_count: 0,
  wait_count: 0,
})
const logs = ref([])
const loading = ref(false)

const RESULT_META = {
  success: { label: '成功', color: '#22c55e' },
  fail: { label: '失败', color: '#ef4444' },
  not_found: { label: '豆瓣未收录', color: '#f59e0b' },
}

function logColor(result) {
  return (RESULT_META[result] || RESULT_META.fail).color
}

function logLabel(result) {
  return (RESULT_META[result] || RESULT_META.fail).label
}

async function request(path) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`
  if (props.api?.get) {
    return await props.api.get(apiPath, {})
  }
  const response = await fetch(`/api/v1/${apiPath}`)
  return await response.json()
}

async function loadStatus() {
  loading.value = true
  try {
    const data = await request('/status')
    if (data && typeof data === 'object') {
      status.logged_in = Boolean(data.logged_in)
      status.nickname = data.nickname || ''
      status.uid = data.uid || ''
      status.avatar = data.avatar || ''
      status.enabled = Boolean(data.enabled)
      status.notify = Boolean(data.notify)
      status.processed_count = Number(data.processed_count || 0)
      status.wait_count = Number(data.wait_count || 0)
    }
  } catch (error) {
    // 静默失败，保留上一次结果
  } finally {
    loading.value = false
  }
  try {
    const data = await request('/logs')
    if (data && Array.isArray(data.data)) {
      logs.value = data.data
    }
  } catch (error) {
    // 静默失败，保留上一次结果
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.dbfpage {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: rgba(var(--v-theme-on-surface), 0.85);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
}

.dbfpage-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 8px;
}

.dbfpage-topbar__left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.dbfpage-topbar__meta { min-width: 0; flex: 1; }
.dbfpage-topbar__right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.dbfpage-topbar__icon {
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

.dbfpage-topbar__title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfpage-topbar__sub {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 2px;
}

.dbfpage-card {
  background: rgba(var(--v-theme-on-surface), 0.03);
  backdrop-filter: blur(20px) saturate(150%);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dbfpage-card__header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }

.dbfpage-card__title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfpage-hero { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }

.dbfpage-hero__avatar {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: rgba(46, 150, 61, 0.12);
  color: #2e963d;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dbfpage-hero__avatar--off {
  background: rgba(var(--v-theme-on-surface), 0.06);
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.dbfpage-hero__img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.dbfpage-hero__info { flex: 1; min-width: 160px; }

.dbfpage-hero__name {
  font-size: 15px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.dbfpage-hero__desc {
  font-size: 11.5px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 3px;
}

.dbfpage-hero__uid {
  margin-left: 8px;
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  font-family: 'SF Mono', Menlo, monospace;
  font-size: 10.5px;
}

.dbfpage-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
}

.dbfpage-stat {
  background: rgba(var(--v-theme-on-surface), 0.03);
  backdrop-filter: blur(20px) saturate(150%);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dbfpage-stat__icon {
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

.dbfpage-stat__value {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.dbfpage-stat__label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.dbfpage-rules { display: flex; flex-direction: column; gap: 9px; }

/* ---------- 同步记录 ---------- */
.dbfpage-log__count {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.45);
}

.dbfpage-logs {
  display: flex;
  flex-direction: column;
  max-height: 300px;
  overflow-y: auto;
}

.dbfpage-log {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 2px;
  border-bottom: 0.5px solid rgba(var(--v-theme-on-surface), 0.06);
}

.dbfpage-log:last-child { border-bottom: none; }

.dbfpage-log__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.dbfpage-log__body { flex: 1; min-width: 0; }

.dbfpage-log__title {
  font-size: 12.5px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.82);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dbfpage-log__title--bad {
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.dbfpage-log__msg {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 2px;
}

.dbfpage-log__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.dbfpage-log__result {
  font-size: 11px;
  font-weight: 600;
}

.dbfpage-log__time {
  font-size: 10.5px;
  font-family: 'SF Mono', Menlo, monospace;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.dbfpage-log__empty {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  padding: 6px 0;
}

.dbfpage-rule { display: flex; align-items: center; gap: 9px; }

.dbfpage-rule__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dbfpage-rule__text {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.62);
}

.dbfpage-rule__text strong {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.78);
}

.dbfpage-guide { display: flex; flex-direction: column; gap: 7px; }

.dbfpage-guide p {
  margin: 0;
  font-size: 12px;
  line-height: 1.65;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.dbfpage-guide strong {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.78);
}

.dbfpage-desc {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  padding-top: 8px;
  border-top: 0.5px solid rgba(var(--v-theme-on-surface), 0.07);
}

@media (max-width: 600px) {
  .dbfpage { padding: 12px 12px; }
  .dbfpage-topbar__sub { display: none; }
}
</style>
