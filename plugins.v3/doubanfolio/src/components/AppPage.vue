<template>
  <div class="dbfapp">
    <!-- 顶栏 -->
    <div class="dbfapp-topbar">
      <div class="dbfapp-topbar__left">
        <div class="dbfapp-topbar__icon">
          <v-icon icon="mdi-movie-open-outline" size="22" />
        </div>
        <div>
          <div class="dbfapp-topbar__title">豆瓣档案</div>
          <div class="dbfapp-topbar__sub">我的书影音收藏</div>
        </div>
      </div>
      <div class="dbfapp-topbar__right">
        <template v-if="account.logged_in">
          <div class="dbfapp-user">
            <img v-if="account.avatar" :src="account.avatar" alt="" class="dbfapp-user__img" />
            <v-icon v-else icon="mdi-account" size="18" />
            <span>{{ account.nickname || '豆瓣账号' }}</span>
          </div>
        </template>
        <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-refresh" :loading="loading" @click="refresh(true)">
          刷新
        </v-btn>
      </div>
    </div>

    <template v-if="account.logged_in">
      <!-- 页签 -->
      <div class="dbfapp-tabs">
        <button
          v-for="s in STATUS_TABS"
          :key="s.key"
          class="dbfapp-tab"
          :class="{ 'dbfapp-tab--on': currentStatus === s.key }"
          @click="switchStatus(s.key)"
        >
          {{ s.label }}<b v-if="totals[s.key] >= 0">&nbsp;{{ totals[s.key] }}</b>
        </button>
        <div style="flex: 1"></div>
        <template v-if="currentStatus !== 'sync'">
          <button
            v-for="t in TYPE_TABS"
            :key="t.key"
            class="dbfapp-tab dbfapp-tab--type"
            :class="{ 'dbfapp-tab--on': currentType === t.key }"
            @click="switchType(t.key)"
          >
            {{ t.label }}
          </button>
        </template>
      </div>

      <!-- 内容 -->
      <div class="dbfapp-panel">
        <div class="dbfapp-panel__head">
          <span v-if="currentStatus === 'sync'">同步记录（{{ shown.length }}）</span>
          <span v-else>{{ statusLabel }} · {{ typeLabel }}（{{ shown.length }}）</span>
          <span class="dbfapp-panel__meta">
            {{ currentStatus === 'sync' ? '媒体库同步到豆瓣的记录 · 最多保留 50 条' : '缓存 30 分钟 · 点击海报直达豆瓣' }}
          </span>
        </div>
        <div v-if="currentStatus !== 'sync' && items.length" class="dbfapp-controls">
          <v-text-field
            v-model="keyword"
            density="compact"
            variant="outlined"
            hide-details
            clearable
            placeholder="搜索标题…"
            prepend-inner-icon="mdi-magnify"
            class="dbfapp-controls__search"
          />
          <v-select
            v-model="sortKey"
            :items="Object.entries(SORTERS).map(([value, s]) => ({ title: s.label, value }))"
            density="compact"
            variant="outlined"
            hide-details
            class="dbfapp-controls__sort"
          />
        </div>

        <div v-if="loading && !items.length" class="dbfapp-empty">
          <v-progress-circular indeterminate color="primary" size="26" />
          <div style="margin-top: 8px">{{ currentStatus === 'sync' ? '正在加载同步记录…' : '正在加载收藏…' }}</div>
        </div>

        <div v-else-if="error" class="dbfapp-empty dbfapp-empty--bad">{{ error }}</div>

        <!-- 同步记录卡片 -->
        <div v-else-if="currentStatus === 'sync' && shown.length" class="dbfapp-grid">
          <div v-for="rec in shown" :key="`${rec.time}-${rec.title}`" class="dbfapp-cell dbfapp-cell--sync">
            <div class="dbfapp-cell__poster" :class="{ 'dbfapp-cell__poster--sync': !posterUrls[recKey(rec)] }">
              <img v-if="posterUrls[recKey(rec)]" :src="posterUrls[recKey(rec)]" alt="" />
              <v-icon v-else :icon="syncIcon(rec.result)" size="26" />
              <span class="dbfapp-cell__flag" :class="`dbfapp-sync-flag--${rec.result}`">{{ syncLabel(rec.result) }}</span>
            </div>
            <div class="dbfapp-cell__title" :title="rec.title">{{ rec.title }}</div>
            <div class="dbfapp-cell__meta" :title="rec.message">
              {{ rec.time }}<template v-if="rec.type">&nbsp;·&nbsp;{{ rec.type }}</template>
            </div>
            <div v-if="rec.message" class="dbfapp-cell__msg" :title="rec.message">{{ rec.message }}</div>
          </div>
        </div>

        <div v-else-if="shown.length" class="dbfapp-grid">
          <a
            v-for="it in shown"
            :key="it.sid"
            class="dbfapp-cell"
            :href="`https://movie.douban.com/subject/${it.sid}/`"
            target="_blank"
          >
            <div class="dbfapp-cell__poster">
              <img v-if="posterUrls[it.sid]" :src="posterUrls[it.sid]" alt="" />
              <v-icon v-else icon="mdi-image-off-outline" size="26" />
              <span v-if="mpStatus[it.sid]" class="dbfapp-cell__flag" :class="`dbfapp-cell__flag--${mpStatus[it.sid]}`">
                {{ mpStatus[it.sid] === 'library' ? '已入库' : '已订阅' }}
              </span>
              <span v-if="it.private" class="dbfapp-cell__lock" title="仅自己可见">
                <v-icon icon="mdi-lock-outline" size="11" />
              </span>
              <v-btn
                v-if="canUnmark(it)"
                class="dbfapp-cell__unmark"
                icon="mdi-bookmark-remove-outline"
                variant="tonal"
                color="warning"
                size="x-small"
                :loading="unmarkBusy[it.sid]"
                :title="`删除豆瓣「${statusLabel}」标记`"
                @click.prevent="confirmUnmark(it)"
              />
              <v-btn
                v-if="canSubscribe(it)"
                class="dbfapp-cell__sub"
                icon="mdi-plus"
                variant="tonal"
                color="primary"
                size="x-small"
                :loading="subBusy[it.sid]"
                title="加入 MoviePilot 订阅"
                @click.prevent="subscribeItem(it)"
              />
            </div>
            <div class="dbfapp-cell__title" :title="it.title">{{ it.title }}</div>
            <div class="dbfapp-cell__meta">
              {{ metaLine(it) }}
            </div>
            <div class="dbfapp-cell__rate">
              <span v-if="it.my_rating" class="dbfapp-cell__stars">
                <v-icon v-for="n in it.my_rating" :key="n" icon="mdi-star" size="11" color="#BA7517" />
              </span>
              <span v-if="it.douban_rating" class="dbfapp-cell__score">{{ it.douban_rating.toFixed(1) }}</span>
            </div>
          </a>
        </div>

        <div v-else class="dbfapp-empty">{{ currentStatus === 'sync' ? '暂无同步记录' : '该分类下暂无条目' }}</div>

        <div v-if="currentStatus !== 'sync' && hasMore && !error" class="dbfapp-more">
          <v-btn variant="tonal" color="primary" size="small" :loading="loading" @click="loadMore">
            加载更多
          </v-btn>
          <v-btn variant="outlined" color="primary" size="small" :loading="loadingAll" @click="loadAll">
            全部加载（共 {{ total }} 条）
          </v-btn>
        </div>
      </div>
    </template>

    <div v-else class="dbfapp-panel">
      <div class="dbfapp-empty">尚未登录豆瓣，请到插件配置页扫码登录后再查看收藏。</div>
    </div>

    <v-snackbar v-model="toast.show" :color="toast.color" location="bottom right" timeout="3000">
      {{ toast.text }}
    </v-snackbar>

    <!-- 删除豆瓣标记确认 -->
    <v-dialog v-model="unmarkDialog.show" max-width="380">
      <v-card class="dbfapp-dialog">
        <v-card-title class="text-subtitle-1">删除豆瓣标记</v-card-title>
        <v-card-text>
          确定删除《{{ unmarkDialog.item?.title }}》的「{{ statusLabel }}」标记吗？<br />
          此操作会同步删除豆瓣上的该标记（豆瓣中称为「删除」/「删除该标记」），且不可恢复。
          <template v-if="currentStatus === 'wish'"><br /><br />同时会取消 MoviePilot 中该条目的订阅，之后重新标记想看才会再次自动订阅。</template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" size="small" @click="unmarkDialog.show = false">取消</v-btn>
          <v-btn variant="tonal" color="warning" size="small" :loading="unmarkDialog.busy" @click="doUnmark">删除标记</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
})

const PLUGIN_ID = 'DoubanFolio'
const PAGE_SIZE = 30

const STATUS_TABS = [
  { key: 'sync', label: '同步' },
  { key: 'do', label: '在看' },
  { key: 'wish', label: '想看' },
  { key: 'collect', label: '看过' },
]
const TYPE_TABS = [
  { key: 'all', label: '全部' },
  { key: 'movie', label: '电影' },
  { key: 'tv', label: '剧集' },
  { key: 'book', label: '图书' },
  { key: 'music', label: '音乐' },
]

const account = reactive({ logged_in: false, nickname: '', avatar: '' })
const totals = reactive({ sync: -1, do: -1, wish: -1, collect: -1 })
const currentStatus = ref('sync')
const currentType = ref('all')
const items = ref([])
const total = ref(0)
const loading = ref(false)
const loadingAll = ref(false)
const error = ref('')

// 筛选与排序
const keyword = ref('')
const sortKey = ref('time')
const SORTERS = {
  time: { label: '标记时间', fn: () => 0 }, // 后端默认 sort=time，保持原序
  my_rating: { label: '我的评分', fn: (a, b) => (b.my_rating || 0) - (a.my_rating || 0) },
  douban_rating: { label: '豆瓣评分', fn: (a, b) => (b.douban_rating || 0) - (a.douban_rating || 0) },
  title: { label: '标题', fn: (a, b) => String(a.title).localeCompare(String(b.title), 'zh-Hans-CN') },
}

// 同步记录（媒体库同步到豆瓣）
const syncRecords = ref([])

const syncIconMap = {
  success: 'mdi-check-circle-outline',
  fail: 'mdi-alert-circle-outline',
  not_found: 'mdi-magnify',
}
function syncIcon(result) {
  return syncIconMap[result] || 'mdi-information-outline'
}
function syncLabel(result) {
  return { success: '成功', fail: '失败', not_found: '未匹配' }[result] || '同步'
}
function recKey(rec) {
  return `${rec.time}-${rec.title}`
}

// MP 入库/订阅状态角标与订阅操作
const mpStatus = reactive({})
const mpPending = new Set()
const subBusy = reactive({})
const unmarkBusy = reactive({})
const unmarkDialog = reactive({ show: false, busy: false, item: null })
// 「自动订阅想看」开关状态：开启时隐藏「＋订阅」按钮（默认隐藏，配置加载后同步）
const autoSubEnabled = ref(true)

// 海报经鉴权接口拉取 blob 后转 objectURL，key 为条目 sid
const posterUrls = reactive({})
const posterTried = new Set()

const statusLabel = computed(() => STATUS_TABS.find((s) => s.key === currentStatus.value)?.label || '')
const typeLabel = computed(() => TYPE_TABS.find((t) => t.key === currentType.value)?.label || '')

// 图书/音乐是独立站点分类；电影/剧集在 movie 分类下按 subtype 前端过滤
const category = computed(() => (currentType.value === 'book' ? 'book' : currentType.value === 'music' ? 'music' : 'movie'))
const shown = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  const source = currentStatus.value === 'sync' ? syncRecords.value : items.value
  let list = source
  if (currentStatus.value !== 'sync') {
    list = list.filter((it) => {
      // subtype 未知（条目详情暂未补全）时归入「电影」页签兜底展示，补全后自动归位
      if (currentType.value === 'movie') return it.subtype !== 'tv'
      if (currentType.value === 'tv') return it.subtype === 'tv'
      return true
    })
  }
  if (kw) list = list.filter((it) => String(it.title || '').toLowerCase().includes(kw))
  const sorter = SORTERS[sortKey.value]
  if (currentStatus.value !== 'sync' && sorter && sortKey.value !== 'time') list = [...list].sort(sorter.fn)
  return list
})
const hasMore = computed(() => total.value > 0 && items.value.length < Math.min(total.value, 300))

function coverPath(poster) {
  return String(poster || '').replace(/^https:\/\/img\d+\.doubanio\.com/, '')
}

async function fetchCoverBlob(poster) {
  const url = `https://img1.doubanio.com${coverPath(poster)}`
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
      // 加载失败保持占位图标
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

async function loadLogs() {
  try {
    const data = await request('/logs')
    if (data?.success) {
      syncRecords.value = Array.isArray(data.data) ? data.data : []
      totals.sync = syncRecords.value.length
      resolveSyncPosters(syncRecords.value)
    }
  } catch (err) {
    // 静默失败
  }
}

// 同步记录海报加载（key 用 时间-标题，与收藏卡片的 sid 键隔离）
async function resolveSyncPosters(list) {
  for (const rec of list) {
    if (!rec.poster) continue
    const key = recKey(rec)
    if (posterUrls[key] || posterTried.has(key)) continue
    posterTried.add(key)
    try {
      const blob = await fetchCoverBlob(rec.poster)
      if (blob && blob.size > 100) posterUrls[key] = URL.createObjectURL(blob)
    } catch (err) {
      // 加载失败保持占位图标
    }
  }
}

async function queryMpStatus(list) {
  const targets = list.filter((it) => it.subtype !== 'book' && it.subtype !== 'music' && !mpPending.has(it.sid))
  if (!targets.length) return
  for (const it of targets) mpPending.add(it.sid)
  try {
    const data = await requestPost('/mp_status', {
      items: targets.map((it) => ({ sid: it.sid, title: it.title, year: it.year, subtype: it.subtype })),
    })
    if (data?.success && data.statuses) {
      for (const [sid, st] of Object.entries(data.statuses)) mpStatus[sid] = st
    }
  } catch (err) {
    // 静默失败，角标不显示
  } finally {
    for (const it of targets) mpPending.delete(it.sid)
  }
}

async function subscribeItem(it) {
  if (subBusy[it.sid]) return
  subBusy[it.sid] = true
  try {
    const data = await requestPost('/subscribe', { sid: it.sid, title: it.title, year: it.year, subtype: it.subtype })
    if (data?.success) {
      mpStatus[it.sid] = 'subscribed'
      pushToast(`《${it.title}》${data.message || '订阅成功'}`, 'success')
    } else {
      pushToast(`《${it.title}》订阅失败：${data?.message || '未知错误'}`, 'error')
    }
  } catch (err) {
    pushToast(`订阅请求失败：${err.message}`, 'error')
  } finally {
    subBusy[it.sid] = false
  }
}

const toast = reactive({ show: false, text: '', color: 'success' })
let toastTimer = null
function pushToast(text, color = 'success') {
  toast.show = true
  toast.text = text
  toast.color = color
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.show = false), 3000)
}

function canSubscribe(it) {
  // 「自动订阅想看」开启时不再显示手动订阅按钮（删除标记即取消订阅，闭环由自动订阅完成）
  if (autoSubEnabled.value) return false
  return (
    currentStatus.value === 'wish' &&
    (it.subtype === 'movie' || it.subtype === 'tv') &&
    mpStatus[it.sid] !== 'library' &&
    mpStatus[it.sid] !== 'subscribed'
  )
}

// 收藏卡片左下角显示删除标记按钮（豆瓣里叫「删除」/「删除该标记」）
// 想看 / 在看 / 看过页签均可用，走豆瓣网页「删除」同款接口，删除整个标记
function canUnmark(it) {
  return currentStatus.value !== 'sync' && Boolean(it.sid)
}

function confirmUnmark(it) {
  unmarkDialog.item = it
  unmarkDialog.show = true
}

async function doUnmark() {
  const it = unmarkDialog.item
  if (!it || unmarkDialog.busy) return
  unmarkDialog.busy = true
  unmarkBusy[it.sid] = true
  try {
    const data = await requestPost('/unmark', {
      sid: it.sid,
      mark_id: it.mark_id || '',
      title: it.title,
      status: currentStatus.value,
      category: category.value,
    })
    if (data?.success) {
      items.value = items.value.filter((x) => x.sid !== it.sid)
      total.value = Math.max(0, total.value - 1)
      const tKey = { do: 'do', wish: 'wish', collect: 'collect' }[currentStatus.value]
      if (tKey && totals[tKey] > 0) totals[tKey] -= 1
      delete posterUrls[it.sid]
      if (currentStatus.value === 'wish' || data.unsubscribed) delete mpStatus[it.sid]
      pushToast(`《${it.title}》${data.message || '已删除豆瓣标记'}`, 'success')
      unmarkDialog.show = false
    } else {
      pushToast(`删除失败：${data?.message || '未知错误'}`, 'error')
    }
  } catch (err) {
    pushToast(`删除请求失败：${err.message}`, 'error')
  } finally {
    unmarkDialog.busy = false
    unmarkBusy[it.sid] = false
  }
}

function metaLine(it) {
  const parts = []
  if (it.year) parts.push(it.year)
  if (it.subtype === 'tv') parts.push('剧集')
  else if (it.subtype === 'movie') parts.push('电影')
  else if (it.subtype === 'book') parts.push('图书')
  else if (it.subtype === 'music') parts.push('音乐')
  if (it.date) parts.push(it.date)
  return parts.join(' · ') || '—'
}

async function request(path) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`
  if (props.api?.get) return await props.api.get(apiPath, {})
  const response = await fetch(`/api/v1/${apiPath}`)
  return await response.json()
}

async function requestPost(path, body) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`
  if (props.api?.post) return await props.api.post(apiPath, body)
  const resp = await fetch(`/api/v1/${apiPath}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  return await resp.json()
}

async function loadAccount() {
  try {
    const data = await request('/config')
    if (data && typeof data === 'object') {
      account.logged_in = Boolean(data.logged_in)
      account.nickname = data.nickname || ''
      account.avatar = data.avatar || ''
      // 自动订阅开启时「＋订阅」按钮冗余（新想看会自动订阅），隐藏；关闭时保留作手动兜底
      autoSubEnabled.value = Boolean(data.auto_subscribe)
    }
  } catch (error) {
    // 静默失败
  }
}

async function loadTotals() {
  try {
    const data = await request('/collection/summary')
    if (data?.success) {
      totals.do = Number(data.doing || 0)
      totals.wish = Number(data.wish || 0)
      totals.collect = Number(data.done || 0)
    }
  } catch (error) {
    // 静默失败
  }
}

async function loadItems(reset = true, force = false) {
  loading.value = true
  error.value = ''
  try {
    const start = reset ? 0 : items.value.length
    const forceParam = force ? '&force=1' : ''
    const data = await request(`/collection?status=${currentStatus.value}&start=${start}&category=${category.value}${forceParam}`)
    if (!data?.success) {
      error.value = data?.message || '获取收藏失败'
      if (reset) items.value = []
      return
    }
    total.value = Number(data.total || 0)
    const pageItems = data.items || []
    if (reset) {
      items.value = pageItems
    } else {
      const known = new Set(items.value.map((it) => it.sid))
      for (const it of pageItems) {
        if (!known.has(it.sid)) items.value.push(it)
      }
    }
    resolvePosters(pageItems)
    queryMpStatus(pageItems)
  } catch (err) {
    error.value = `获取收藏失败：${err.message}`
  } finally {
    loading.value = false
  }
}

async function switchStatus(key) {
  if (currentStatus.value === key) {
    // 再点一次当前页签即手动刷新（想看/同步走实时通道）
    refresh()
    return
  }
  currentStatus.value = key
  items.value = []
  total.value = 0
  if (key === 'sync') {
    syncRecords.value = []
    await loadLogs()
  } else {
    if (key === 'wish') {
      // 想看准实时：每次切换都现查总数，不走 60 秒节流
      lastTotalsAt = Date.now()
      await loadTotals()
    } else {
      await ensureFreshTotals()
    }
    await loadItems(true)
  }
}

async function switchType(key) {
  if (currentType.value === key) return
  const needReload = (key === 'book') !== (currentType.value === 'book') || (key === 'music') !== (currentType.value === 'music')
  currentType.value = key
  if (needReload) {
    items.value = []
    total.value = 0
    await ensureFreshTotals()
    await loadItems(true)
  }
}

async function loadMore() {
  // 每次多拉一页（豆瓣每页 15 条，连续拉两页）
  await loadItems(false)
  if (!error.value && hasMore.value) await loadItems(false)
}

async function loadAll() {
  if (loading.value || loadingAll.value) return
  loadingAll.value = true
  try {
    while (total.value > 0 && items.value.length < Math.min(total.value, 300)) {
      const before = items.value.length
      await loadItems(false)
      if (error.value || items.value.length === before) break
    }
  } finally {
    loadingAll.value = false
  }
}

// 进入页签前先刷新总数（后端会校验缓存与豆瓣总数，不一致自动作废页缓存）
// 60 秒内已校验过则跳过，避免频繁切页签打太多请求
let lastTotalsAt = 0
async function ensureFreshTotals() {
  if (Date.now() - lastTotalsAt < 60_000) return
  lastTotalsAt = Date.now()
  await loadTotals()
}

async function refresh(force = false) {
  lastTotalsAt = 0 // 打开页面/手动刷新时强制现查总数
  await Promise.all([loadAccount(), ensureFreshTotals()])
  if (currentStatus.value === 'sync') {
    await loadLogs()
  } else {
    await loadItems(true, force)
  }
}

// 想看 / 同步页签准实时刷新：30 秒轮询 + 页面回到前台立即刷新。
// 在看 / 看过是长缓存（12~24 小时），不轮询，避免无谓请求。
const REALTIME_POLL_MS = 30_000
let pollTimer = null

async function refreshRealtimeTab() {
  if (currentStatus.value === 'sync') {
    await loadLogs()
  } else if (currentStatus.value === 'wish') {
    await loadItems(true)
    await loadTotals()
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (typeof document !== 'undefined' && document.hidden) return
    if (loading.value) return
    await refreshRealtimeTab()
  }, REALTIME_POLL_MS)
  document.addEventListener('visibilitychange', onVisibilityChange)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisibilityChange)
}

function onVisibilityChange() {
  if (!document.hidden && (currentStatus.value === 'wish' || currentStatus.value === 'sync')) {
    refreshRealtimeTab()
  }
}

onMounted(() => {
  refresh()
  startPolling()
})
onUnmounted(() => {
  stopPolling()
  releasePosters()
})
</script>

<style scoped>
.dbfapp {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: rgba(var(--v-theme-on-surface), 0.85);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
}

.dbfapp-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dbfapp-topbar__left { display: flex; align-items: center; gap: 12px; }
.dbfapp-topbar__right { display: flex; align-items: center; gap: 10px; }

.dbfapp-topbar__icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
  display: flex;
  align-items: center;
  justify-content: center;
}

.dbfapp-topbar__title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.dbfapp-topbar__sub {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 1px;
}

.dbfapp-user {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 3px 10px 3px 3px;
  border-radius: 18px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.dbfapp-user__img {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.dbfapp-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.dbfapp-tab {
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.14);
  background: rgba(var(--v-theme-on-surface), 0.02);
  color: rgba(var(--v-theme-on-surface), 0.72);
  border-radius: 18px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
}

.dbfapp-tab b { font-weight: 600; }

.dbfapp-tab--on {
  background: rgba(var(--v-theme-primary), 0.14);
  border-color: rgba(var(--v-theme-primary), 0.4);
  color: rgb(var(--v-theme-primary));
}

.dbfapp-tab--type { padding: 6px 12px; }

.dbfapp-panel {
  background: rgba(var(--v-theme-on-surface), 0.03);
  backdrop-filter: blur(20px) saturate(150%);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 14px 16px;
}

.dbfapp-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 12px;
}

.dbfapp-panel__meta {
  font-size: 11px;
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.42);
}

.dbfapp-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.dbfapp-controls__search {
  flex: 1;
  max-width: 260px;
}

.dbfapp-controls__sort {
  width: 128px;
  flex-shrink: 0;
}

/* 同步记录卡片 */
.dbfapp-cell--sync { cursor: default; }

.dbfapp-cell__poster--sync {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.dbfapp-sync-flag--success {
  background: rgba(46, 150, 61, 0.88);
}

.dbfapp-sync-flag--fail {
  background: rgba(211, 47, 47, 0.88);
}

.dbfapp-sync-flag--not_found {
  background: rgba(230, 130, 20, 0.88);
}

.dbfapp-cell__msg {
  font-size: 10.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dbfapp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 12px;
}

.dbfapp-cell { text-decoration: none; }

.dbfapp-cell__poster {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(var(--v-theme-on-surface), 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.dbfapp-cell__poster img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.dbfapp-cell__lock {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dbfapp-cell__flag {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 9.5px;
  line-height: 1;
  padding: 3px 6px;
  border-radius: 0 0 6px 0;
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.dbfapp-cell__flag--library {
  background: rgba(46, 150, 61, 0.88);
}

.dbfapp-cell__flag--subscribed {
  background: rgba(33, 115, 210, 0.88);
}

.dbfapp-cell__sub {
  position: absolute;
  bottom: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.dbfapp-cell__unmark {
  position: absolute;
  bottom: 4px;
  left: 4px;
  opacity: 0.8;
  transition: opacity 0.15s ease;
}

.dbfapp-cell:hover .dbfapp-cell__sub,
.dbfapp-cell__sub:focus-visible,
.dbfapp-cell:hover .dbfapp-cell__unmark,
.dbfapp-cell__unmark:focus-visible {
  opacity: 1;
}

.dbfapp-dialog {
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.dbfapp-cell__title {
  margin-top: 6px;
  font-size: 11.5px;
  color: rgba(var(--v-theme-on-surface), 0.85);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dbfapp-cell__meta {
  font-size: 10.5px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dbfapp-cell__rate {
  margin-top: 2px;
  min-height: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dbfapp-cell__stars { display: inline-flex; }

.dbfapp-cell__score {
  font-size: 10.5px;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.dbfapp-empty {
  text-align: center;
  padding: 30px 0;
  font-size: 12.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.dbfapp-empty--bad { color: rgba(var(--v-theme-error), 0.85); }

.dbfapp-more {
  display: flex;
  justify-content: center;
  margin-top: 14px;
}

@media (max-width: 600px) {
  .dbfapp { padding: 12px; }
  .dbfapp-grid { grid-template-columns: repeat(auto-fill, minmax(82px, 1fr)); gap: 9px; }
}
</style>
