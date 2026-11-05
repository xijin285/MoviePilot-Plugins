<template>
  <div class="dbfdash">
    <!-- 统计 -->
    <div class="dbfdash-stats">
      <div class="dbfdash-stat">
        <div class="dbfdash-stat__value">{{ summary.doing }}</div>
        <div class="dbfdash-stat__label">在看</div>
      </div>
      <div class="dbfdash-stat">
        <div class="dbfdash-stat__value">{{ summary.wish }}</div>
        <div class="dbfdash-stat__label">想看</div>
      </div>
      <div class="dbfdash-stat">
        <div class="dbfdash-stat__value">{{ summary.done }}</div>
        <div class="dbfdash-stat__label">看过</div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading && !summary.recent.length" class="dbfdash-loading">
      <v-progress-circular indeterminate color="primary" size="22" />
      <span>正在加载在看收藏…</span>
    </div>

    <!-- 最近在看 -->
    <template v-if="summary.recent.length">
      <div class="dbfdash-sub">最近在看</div>
      <div class="dbfdash-row">
        <a
          v-for="it in summary.recent"
          :key="it.sid"
          class="dbfdash-item"
          :href="`https://movie.douban.com/subject/${it.sid}/`"
          target="_blank"
          :title="it.title"
        >
          <div class="dbfdash-item__poster">
            <img v-if="posterUrls[it.sid]" :src="posterUrls[it.sid]" alt="" />
            <v-icon v-else icon="mdi-image-off-outline" size="18" />
          </div>
          <div class="dbfdash-item__title">{{ it.title }}</div>
        </a>
      </div>
    </template>

    <div v-else-if="!loading" class="dbfdash-loading">暂无在看条目</div>

    <!-- 底部 -->
    <div class="dbfdash-foot">
      <span v-if="lastLog" class="dbfdash-foot__log">
        最近同步：{{ lastLog.title }} · {{ lastLog.result === 'success' ? '成功' : lastLog.result === 'not_found' ? '未收录' : '失败' }}
      </span>
      <span v-else class="dbfdash-foot__log">播放媒体后自动同步到豆瓣</span>
      <a class="dbfdash-foot__more" href="#" @click.prevent="goFullPage">查看全部 →</a>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  config: { type: Object, default: () => ({ attrs: {} }) },
  allowRefresh: { type: Boolean, default: false },
  refreshInterval: { type: Number, default: 0 },
})

const PLUGIN_ID = 'DoubanFolio'

const summary = reactive({
  wish: 0,
  doing: 0,
  done: 0,
  recent: [],
})
const lastLog = ref(null)
const loading = ref(false)
const posterUrls = reactive({})
const posterTried = new Set()
let timer = null

async function fetchCoverBlob(poster) {
  const path = String(poster || '').replace(/^https:\/\/img\d+\.doubanio\.com/, '')
  const url = `https://img1.doubanio.com${path}`
  if (props.api?.get) {
    return await props.api.get(`plugin/${PLUGIN_ID}/cover`, { params: { img: url }, responseType: 'blob' })
  }
  const resp = await fetch(`/api/v1/plugin/${PLUGIN_ID}/cover?img=${encodeURIComponent(url)}`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return await resp.blob()
}

async function resolvePosters(list) {
  for (const it of list) {
    const poster = it.poster_hd || it.poster
    if (!poster || posterUrls[it.sid] || posterTried.has(it.sid)) continue
    posterTried.add(it.sid)
    try {
      const blob = await fetchCoverBlob(poster)
      if (blob && blob.size > 100) posterUrls[it.sid] = URL.createObjectURL(blob)
    } catch (err) {
      // 保持占位图标
    }
  }
}

function releasePosters() {
  for (const url of Object.values(posterUrls)) {
    try { URL.revokeObjectURL(url) } catch (err) { /* ignore */ }
  }
  for (const key of Object.keys(posterUrls)) delete posterUrls[key]
  posterTried.clear()
}

async function request(path) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`
  if (props.api?.get) return await props.api.get(apiPath, {})
  const response = await fetch(`/api/v1/${apiPath}`)
  return await response.json()
}

async function load() {
  loading.value = true
  try {
    const data = await request('/collection/summary')
    if (data?.success) {
      summary.wish = Number(data.wish || 0)
      summary.doing = Number(data.doing || 0)
      summary.done = Number(data.done || 0)
      summary.recent = data.recent || []
      resolvePosters(summary.recent)
    }
  } catch (error) {
    // 静默失败
  }
  try {
    const logs = await request('/logs')
    if (logs?.success && Array.isArray(logs.data) && logs.data.length) {
      lastLog.value = logs.data[0]
    }
  } catch (error) {
    // 静默失败
  }
  loading.value = false
}

function goFullPage() {
  window.location.hash = '#/plugin-app/DoubanFolio/main'
}

onMounted(() => {
  load()
  const interval = Number(props.refreshInterval || props.config?.attrs?.refresh || 0)
  if (interval > 0) {
    timer = setInterval(load, interval * 1000)
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  releasePosters()
})
</script>

<style scoped>
.dbfdash {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 2px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfdash-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.dbfdash-stat {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.07);
  border-radius: 10px;
  padding: 10px 12px;
}

.dbfdash-stat__value {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.dbfdash-stat__label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 1px;
}

.dbfdash-sub {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.62);
}

.dbfdash-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.dbfdash-item {
  flex-shrink: 0;
  width: 60px;
  text-decoration: none;
}

.dbfdash-item__poster {
  aspect-ratio: 2 / 3;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(var(--v-theme-on-surface), 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.dbfdash-item__poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.dbfdash-item__title {
  font-size: 10.5px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dbfdash-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  padding: 6px 0;
}

.dbfdash-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.dbfdash-foot__log {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dbfdash-foot__more {
  font-size: 12px;
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  flex-shrink: 0;
  cursor: pointer;
}
</style>
