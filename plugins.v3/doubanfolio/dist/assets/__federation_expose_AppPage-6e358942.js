import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const AppPage_vue_vue_type_style_index_0_scoped_0462e306_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createBlock:_createBlock,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,withCtx:_withCtx,renderList:_renderList,Fragment:_Fragment,normalizeClass:_normalizeClass,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "dbfapp" };
const _hoisted_2 = { class: "dbfapp-topbar" };
const _hoisted_3 = { class: "dbfapp-topbar__left" };
const _hoisted_4 = { class: "dbfapp-topbar__icon" };
const _hoisted_5 = { class: "dbfapp-topbar__right" };
const _hoisted_6 = {
  key: 0,
  class: "dbfapp-user"
};
const _hoisted_7 = ["src"];
const _hoisted_8 = { class: "dbfapp-tabs" };
const _hoisted_9 = ["onClick"];
const _hoisted_10 = { key: 0 };
const _hoisted_11 = ["onClick"];
const _hoisted_12 = { class: "dbfapp-panel" };
const _hoisted_13 = { class: "dbfapp-panel__head" };
const _hoisted_14 = { key: 0 };
const _hoisted_15 = { key: 1 };
const _hoisted_16 = { class: "dbfapp-panel__meta" };
const _hoisted_17 = {
  key: 0,
  class: "dbfapp-controls"
};
const _hoisted_18 = {
  key: 1,
  class: "dbfapp-empty"
};
const _hoisted_19 = { style: {"margin-top":"8px"} };
const _hoisted_20 = {
  key: 2,
  class: "dbfapp-empty dbfapp-empty--bad"
};
const _hoisted_21 = {
  key: 3,
  class: "dbfapp-grid"
};
const _hoisted_22 = ["src"];
const _hoisted_23 = ["title"];
const _hoisted_24 = ["title"];
const _hoisted_25 = ["title"];
const _hoisted_26 = {
  key: 4,
  class: "dbfapp-grid"
};
const _hoisted_27 = ["href"];
const _hoisted_28 = { class: "dbfapp-cell__poster" };
const _hoisted_29 = ["src"];
const _hoisted_30 = {
  key: 3,
  class: "dbfapp-cell__lock",
  title: "仅自己可见"
};
const _hoisted_31 = ["title"];
const _hoisted_32 = { class: "dbfapp-cell__meta" };
const _hoisted_33 = { class: "dbfapp-cell__rate" };
const _hoisted_34 = {
  key: 0,
  class: "dbfapp-cell__stars"
};
const _hoisted_35 = {
  key: 1,
  class: "dbfapp-cell__score"
};
const _hoisted_36 = {
  key: 5,
  class: "dbfapp-empty"
};
const _hoisted_37 = {
  key: 6,
  class: "dbfapp-more"
};
const _hoisted_38 = {
  key: 1,
  class: "dbfapp-panel"
};

const {computed,onMounted,onUnmounted,reactive,ref} = await importShared('vue');


const PLUGIN_ID = 'DoubanFolio';

const REALTIME_POLL_MS = 30_000;

const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: { type: Object, default: () => ({}) },
},
  setup(__props) {

const props = __props;

const STATUS_TABS = [
  { key: 'sync', label: '同步' },
  { key: 'do', label: '在看' },
  { key: 'wish', label: '想看' },
  { key: 'collect', label: '看过' },
];
const TYPE_TABS = [
  { key: 'all', label: '全部' },
  { key: 'movie', label: '电影' },
  { key: 'tv', label: '剧集' },
  { key: 'book', label: '图书' },
  { key: 'music', label: '音乐' },
];

const account = reactive({ logged_in: false, nickname: '', avatar: '' });
const totals = reactive({ sync: -1, do: -1, wish: -1, collect: -1 });
const currentStatus = ref('sync');
const currentType = ref('all');
const items = ref([]);
const total = ref(0);
const loading = ref(false);
const loadingAll = ref(false);
const error = ref('');

// 筛选与排序
const keyword = ref('');
const sortKey = ref('time');
const SORTERS = {
  time: { label: '标记时间', fn: () => 0 }, // 后端默认 sort=time，保持原序
  my_rating: { label: '我的评分', fn: (a, b) => (b.my_rating || 0) - (a.my_rating || 0) },
  douban_rating: { label: '豆瓣评分', fn: (a, b) => (b.douban_rating || 0) - (a.douban_rating || 0) },
  title: { label: '标题', fn: (a, b) => String(a.title).localeCompare(String(b.title), 'zh-Hans-CN') },
};

// 同步记录（媒体库同步到豆瓣）
const syncRecords = ref([]);

const syncIconMap = {
  success: 'mdi-check-circle-outline',
  fail: 'mdi-alert-circle-outline',
  not_found: 'mdi-magnify',
};
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
const mpStatus = reactive({});
const mpPending = new Set();
const subBusy = reactive({});
const unmarkBusy = reactive({});
const unmarkDialog = reactive({ show: false, busy: false, item: null });
// 「自动订阅想看」开关状态：开启时隐藏「＋订阅」按钮（默认隐藏，配置加载后同步）
const autoSubEnabled = ref(true);

// 海报经鉴权接口拉取 blob 后转 objectURL，key 为条目 sid
const posterUrls = reactive({});
const posterTried = new Set();

const statusLabel = computed(() => STATUS_TABS.find((s) => s.key === currentStatus.value)?.label || '');
const typeLabel = computed(() => TYPE_TABS.find((t) => t.key === currentType.value)?.label || '');

// 图书/音乐是独立站点分类；电影/剧集在 movie 分类下按 subtype 前端过滤
const category = computed(() => (currentType.value === 'book' ? 'book' : currentType.value === 'music' ? 'music' : 'movie'));
const shown = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
  const source = currentStatus.value === 'sync' ? syncRecords.value : items.value;
  let list = source;
  if (currentStatus.value !== 'sync') {
    list = list.filter((it) => {
      // subtype 未知（条目详情暂未补全）时归入「电影」页签兜底展示，补全后自动归位
      if (currentType.value === 'movie') return it.subtype !== 'tv'
      if (currentType.value === 'tv') return it.subtype === 'tv'
      return true
    });
  }
  if (kw) list = list.filter((it) => String(it.title || '').toLowerCase().includes(kw));
  const sorter = SORTERS[sortKey.value];
  if (currentStatus.value !== 'sync' && sorter && sortKey.value !== 'time') list = [...list].sort(sorter.fn);
  return list
});
const hasMore = computed(() => total.value > 0 && items.value.length < Math.min(total.value, 300));

function coverPath(poster) {
  return String(poster || '').replace(/^https:\/\/img\d+\.doubanio\.com/, '')
}

async function fetchCoverBlob(poster) {
  const url = `https://img1.doubanio.com${coverPath(poster)}`;
  if (props.api?.get) {
    return await props.api.get(`plugin/${PLUGIN_ID}/cover`, { params: { img: url }, responseType: 'blob' })
  }
  const resp = await fetch(`/api/v1/plugin/${PLUGIN_ID}/cover?img=${encodeURIComponent(url)}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return await resp.blob()
}

async function resolvePosters(list) {
  for (const it of list) {
    const poster = it.poster_hd || it.poster;
    if (!poster || posterUrls[it.sid] || posterTried.has(it.sid)) continue
    posterTried.add(it.sid);
    try {
      const blob = await fetchCoverBlob(poster);
      if (blob && blob.size > 100) posterUrls[it.sid] = URL.createObjectURL(blob);
    } catch (err) {
      // 加载失败保持占位图标
    }
  }
}

function releasePosters() {
  for (const url of Object.values(posterUrls)) {
    try { URL.revokeObjectURL(url); } catch (err) { /* ignore */ }
  }
  for (const key of Object.keys(posterUrls)) delete posterUrls[key];
  posterTried.clear();
}

async function loadLogs() {
  try {
    const data = await request('/logs');
    if (data?.success) {
      syncRecords.value = Array.isArray(data.data) ? data.data : [];
      totals.sync = syncRecords.value.length;
      resolveSyncPosters(syncRecords.value);
    }
  } catch (err) {
    // 静默失败
  }
}

// 同步记录海报加载（key 用 时间-标题，与收藏卡片的 sid 键隔离）
async function resolveSyncPosters(list) {
  for (const rec of list) {
    if (!rec.poster) continue
    const key = recKey(rec);
    if (posterUrls[key] || posterTried.has(key)) continue
    posterTried.add(key);
    try {
      const blob = await fetchCoverBlob(rec.poster);
      if (blob && blob.size > 100) posterUrls[key] = URL.createObjectURL(blob);
    } catch (err) {
      // 加载失败保持占位图标
    }
  }
}

async function queryMpStatus(list) {
  const targets = list.filter((it) => it.subtype !== 'book' && it.subtype !== 'music' && !mpPending.has(it.sid));
  if (!targets.length) return
  for (const it of targets) mpPending.add(it.sid);
  try {
    const data = await requestPost('/mp_status', {
      items: targets.map((it) => ({ sid: it.sid, title: it.title, year: it.year, subtype: it.subtype })),
    });
    if (data?.success && data.statuses) {
      for (const [sid, st] of Object.entries(data.statuses)) mpStatus[sid] = st;
    }
  } catch (err) {
    // 静默失败，角标不显示
  } finally {
    for (const it of targets) mpPending.delete(it.sid);
  }
}

async function subscribeItem(it) {
  if (subBusy[it.sid]) return
  subBusy[it.sid] = true;
  try {
    const data = await requestPost('/subscribe', { sid: it.sid, title: it.title, year: it.year, subtype: it.subtype });
    if (data?.success) {
      mpStatus[it.sid] = 'subscribed';
      pushToast(`《${it.title}》${data.message || '订阅成功'}`, 'success');
    } else {
      pushToast(`《${it.title}》订阅失败：${data?.message || '未知错误'}`, 'error');
    }
  } catch (err) {
    pushToast(`订阅请求失败：${err.message}`, 'error');
  } finally {
    subBusy[it.sid] = false;
  }
}

const toast = reactive({ show: false, text: '', color: 'success' });
let toastTimer = null;
function pushToast(text, color = 'success') {
  toast.show = true;
  toast.text = text;
  toast.color = color;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.show = false), 3000);
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
  unmarkDialog.item = it;
  unmarkDialog.show = true;
}

async function doUnmark() {
  const it = unmarkDialog.item;
  if (!it || unmarkDialog.busy) return
  unmarkDialog.busy = true;
  unmarkBusy[it.sid] = true;
  try {
    const data = await requestPost('/unmark', {
      sid: it.sid,
      mark_id: it.mark_id || '',
      title: it.title,
      status: currentStatus.value,
      category: category.value,
    });
    if (data?.success) {
      items.value = items.value.filter((x) => x.sid !== it.sid);
      total.value = Math.max(0, total.value - 1);
      const tKey = { do: 'do', wish: 'wish', collect: 'collect' }[currentStatus.value];
      if (tKey && totals[tKey] > 0) totals[tKey] -= 1;
      delete posterUrls[it.sid];
      if (currentStatus.value === 'wish' || data.unsubscribed) delete mpStatus[it.sid];
      pushToast(`《${it.title}》${data.message || '已删除豆瓣标记'}`, 'success');
      unmarkDialog.show = false;
    } else {
      pushToast(`删除失败：${data?.message || '未知错误'}`, 'error');
    }
  } catch (err) {
    pushToast(`删除请求失败：${err.message}`, 'error');
  } finally {
    unmarkDialog.busy = false;
    unmarkBusy[it.sid] = false;
  }
}

function metaLine(it) {
  const parts = [];
  if (it.year) parts.push(it.year);
  if (it.subtype === 'tv') parts.push('剧集');
  else if (it.subtype === 'movie') parts.push('电影');
  else if (it.subtype === 'book') parts.push('图书');
  else if (it.subtype === 'music') parts.push('音乐');
  if (it.date) parts.push(it.date);
  return parts.join(' · ') || '—'
}

async function request(path) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`;
  if (props.api?.get) return await props.api.get(apiPath, {})
  const response = await fetch(`/api/v1/${apiPath}`);
  return await response.json()
}

async function requestPost(path, body) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`;
  if (props.api?.post) return await props.api.post(apiPath, body)
  const resp = await fetch(`/api/v1/${apiPath}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  return await resp.json()
}

async function loadAccount() {
  try {
    const data = await request('/config');
    if (data && typeof data === 'object') {
      account.logged_in = Boolean(data.logged_in);
      account.nickname = data.nickname || '';
      account.avatar = data.avatar || '';
      // 自动订阅开启时「＋订阅」按钮冗余（新想看会自动订阅），隐藏；关闭时保留作手动兜底
      autoSubEnabled.value = Boolean(data.auto_subscribe);
    }
  } catch (error) {
    // 静默失败
  }
}

async function loadTotals() {
  try {
    const data = await request('/collection/summary');
    if (data?.success) {
      totals.do = Number(data.doing || 0);
      totals.wish = Number(data.wish || 0);
      totals.collect = Number(data.done || 0);
    }
  } catch (error) {
    // 静默失败
  }
}

async function loadItems(reset = true, force = false) {
  loading.value = true;
  error.value = '';
  try {
    const start = reset ? 0 : items.value.length;
    const forceParam = force ? '&force=1' : '';
    const data = await request(`/collection?status=${currentStatus.value}&start=${start}&category=${category.value}${forceParam}`);
    if (!data?.success) {
      error.value = data?.message || '获取收藏失败';
      if (reset) items.value = [];
      return
    }
    total.value = Number(data.total || 0);
    const pageItems = data.items || [];
    if (reset) {
      items.value = pageItems;
    } else {
      const known = new Set(items.value.map((it) => it.sid));
      for (const it of pageItems) {
        if (!known.has(it.sid)) items.value.push(it);
      }
    }
    resolvePosters(pageItems);
    queryMpStatus(pageItems);
  } catch (err) {
    error.value = `获取收藏失败：${err.message}`;
  } finally {
    loading.value = false;
  }
}

async function switchStatus(key) {
  if (currentStatus.value === key) {
    // 再点一次当前页签即手动刷新（想看/同步走实时通道）
    refresh();
    return
  }
  currentStatus.value = key;
  items.value = [];
  total.value = 0;
  if (key === 'sync') {
    syncRecords.value = [];
    await loadLogs();
  } else {
    if (key === 'wish') {
      // 想看准实时：每次切换都现查总数，不走 60 秒节流
      lastTotalsAt = Date.now();
      await loadTotals();
    } else {
      await ensureFreshTotals();
    }
    await loadItems(true);
  }
}

async function switchType(key) {
  if (currentType.value === key) return
  const needReload = (key === 'book') !== (currentType.value === 'book') || (key === 'music') !== (currentType.value === 'music');
  currentType.value = key;
  if (needReload) {
    items.value = [];
    total.value = 0;
    await ensureFreshTotals();
    await loadItems(true);
  }
}

async function loadMore() {
  // 每次多拉一页（豆瓣每页 15 条，连续拉两页）
  await loadItems(false);
  if (!error.value && hasMore.value) await loadItems(false);
}

async function loadAll() {
  if (loading.value || loadingAll.value) return
  loadingAll.value = true;
  try {
    while (total.value > 0 && items.value.length < Math.min(total.value, 300)) {
      const before = items.value.length;
      await loadItems(false);
      if (error.value || items.value.length === before) break
    }
  } finally {
    loadingAll.value = false;
  }
}

// 进入页签前先刷新总数（后端会校验缓存与豆瓣总数，不一致自动作废页缓存）
// 60 秒内已校验过则跳过，避免频繁切页签打太多请求
let lastTotalsAt = 0;
async function ensureFreshTotals() {
  if (Date.now() - lastTotalsAt < 60_000) return
  lastTotalsAt = Date.now();
  await loadTotals();
}

async function refresh(force = false) {
  lastTotalsAt = 0; // 打开页面/手动刷新时强制现查总数
  await Promise.all([loadAccount(), ensureFreshTotals()]);
  if (currentStatus.value === 'sync') {
    await loadLogs();
  } else {
    await loadItems(true, force);
  }
}

// 想看 / 同步页签准实时刷新：30 秒轮询 + 页面回到前台立即刷新。
// 在看 / 看过是长缓存（12~24 小时），不轮询，避免无谓请求。
let pollTimer = null;

async function refreshRealtimeTab() {
  if (currentStatus.value === 'sync') {
    await loadLogs();
  } else if (currentStatus.value === 'wish') {
    await loadItems(true);
    await loadTotals();
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(async () => {
    if (typeof document !== 'undefined' && document.hidden) return
    if (loading.value) return
    await refreshRealtimeTab();
  }, REALTIME_POLL_MS);
  document.addEventListener('visibilitychange', onVisibilityChange);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisibilityChange);
}

function onVisibilityChange() {
  if (!document.hidden && (currentStatus.value === 'wish' || currentStatus.value === 'sync')) {
    refreshRealtimeTab();
  }
}

onMounted(() => {
  refresh();
  startPolling();
});
onUnmounted(() => {
  stopPolling();
  releasePosters();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_snackbar = _resolveComponent("v-snackbar");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-movie-open-outline",
            size: "22"
          })
        ]),
        _cache[6] || (_cache[6] = _createElementVNode("div", null, [
          _createElementVNode("div", { class: "dbfapp-topbar__title" }, "豆瓣档案"),
          _createElementVNode("div", { class: "dbfapp-topbar__sub" }, "我的书影音收藏")
        ], -1))
      ]),
      _createElementVNode("div", _hoisted_5, [
        (account.logged_in)
          ? (_openBlock(), _createElementBlock("div", _hoisted_6, [
              (account.avatar)
                ? (_openBlock(), _createElementBlock("img", {
                    key: 0,
                    src: account.avatar,
                    alt: "",
                    class: "dbfapp-user__img"
                  }, null, 8, _hoisted_7))
                : (_openBlock(), _createBlock(_component_v_icon, {
                    key: 1,
                    icon: "mdi-account",
                    size: "18"
                  })),
              _createElementVNode("span", null, _toDisplayString(account.nickname || '豆瓣账号'), 1)
            ]))
          : _createCommentVNode("", true),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-refresh",
          loading: loading.value,
          onClick: _cache[0] || (_cache[0] = $event => (refresh(true)))
        }, {
          default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
            _createTextVNode(" 刷新 ", -1)
          ]))]),
          _: 1
        }, 8, ["loading"])
      ])
    ]),
    (account.logged_in)
      ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
          _createElementVNode("div", _hoisted_8, [
            (_openBlock(), _createElementBlock(_Fragment, null, _renderList(STATUS_TABS, (s) => {
              return _createElementVNode("button", {
                key: s.key,
                class: _normalizeClass(["dbfapp-tab", { 'dbfapp-tab--on': currentStatus.value === s.key }]),
                onClick: $event => (switchStatus(s.key))
              }, [
                _createTextVNode(_toDisplayString(s.label), 1),
                (totals[s.key] >= 0)
                  ? (_openBlock(), _createElementBlock("b", _hoisted_10, " " + _toDisplayString(totals[s.key]), 1))
                  : _createCommentVNode("", true)
              ], 10, _hoisted_9)
            }), 64)),
            _cache[8] || (_cache[8] = _createElementVNode("div", { style: {"flex":"1"} }, null, -1)),
            (currentStatus.value !== 'sync')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, _renderList(TYPE_TABS, (t) => {
                  return _createElementVNode("button", {
                    key: t.key,
                    class: _normalizeClass(["dbfapp-tab dbfapp-tab--type", { 'dbfapp-tab--on': currentType.value === t.key }]),
                    onClick: $event => (switchType(t.key))
                  }, _toDisplayString(t.label), 11, _hoisted_11)
                }), 64))
              : _createCommentVNode("", true)
          ]),
          _createElementVNode("div", _hoisted_12, [
            _createElementVNode("div", _hoisted_13, [
              (currentStatus.value === 'sync')
                ? (_openBlock(), _createElementBlock("span", _hoisted_14, "同步记录（" + _toDisplayString(shown.value.length) + "）", 1))
                : (_openBlock(), _createElementBlock("span", _hoisted_15, _toDisplayString(statusLabel.value) + " · " + _toDisplayString(typeLabel.value) + "（" + _toDisplayString(shown.value.length) + "）", 1)),
              _createElementVNode("span", _hoisted_16, _toDisplayString(currentStatus.value === 'sync' ? '媒体库同步到豆瓣的记录 · 最多保留 50 条' : '缓存 30 分钟 · 点击海报直达豆瓣'), 1)
            ]),
            (currentStatus.value !== 'sync' && items.value.length)
              ? (_openBlock(), _createElementBlock("div", _hoisted_17, [
                  _createVNode(_component_v_text_field, {
                    modelValue: keyword.value,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((keyword).value = $event)),
                    density: "compact",
                    variant: "outlined",
                    "hide-details": "",
                    clearable: "",
                    placeholder: "搜索标题…",
                    "prepend-inner-icon": "mdi-magnify",
                    class: "dbfapp-controls__search"
                  }, null, 8, ["modelValue"]),
                  _createVNode(_component_v_select, {
                    modelValue: sortKey.value,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((sortKey).value = $event)),
                    items: Object.entries(SORTERS).map(([value, s]) => ({ title: s.label, value })),
                    density: "compact",
                    variant: "outlined",
                    "hide-details": "",
                    class: "dbfapp-controls__sort"
                  }, null, 8, ["modelValue", "items"])
                ]))
              : _createCommentVNode("", true),
            (loading.value && !items.value.length)
              ? (_openBlock(), _createElementBlock("div", _hoisted_18, [
                  _createVNode(_component_v_progress_circular, {
                    indeterminate: "",
                    color: "primary",
                    size: "26"
                  }),
                  _createElementVNode("div", _hoisted_19, _toDisplayString(currentStatus.value === 'sync' ? '正在加载同步记录…' : '正在加载收藏…'), 1)
                ]))
              : (error.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_20, _toDisplayString(error.value), 1))
                : (currentStatus.value === 'sync' && shown.value.length)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_21, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(shown.value, (rec) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: `${rec.time}-${rec.title}`,
                          class: "dbfapp-cell dbfapp-cell--sync"
                        }, [
                          _createElementVNode("div", {
                            class: _normalizeClass(["dbfapp-cell__poster", { 'dbfapp-cell__poster--sync': !posterUrls[recKey(rec)] }])
                          }, [
                            (posterUrls[recKey(rec)])
                              ? (_openBlock(), _createElementBlock("img", {
                                  key: 0,
                                  src: posterUrls[recKey(rec)],
                                  alt: ""
                                }, null, 8, _hoisted_22))
                              : (_openBlock(), _createBlock(_component_v_icon, {
                                  key: 1,
                                  icon: syncIcon(rec.result),
                                  size: "26"
                                }, null, 8, ["icon"])),
                            _createElementVNode("span", {
                              class: _normalizeClass(["dbfapp-cell__flag", `dbfapp-sync-flag--${rec.result}`])
                            }, _toDisplayString(syncLabel(rec.result)), 3)
                          ], 2),
                          _createElementVNode("div", {
                            class: "dbfapp-cell__title",
                            title: rec.title
                          }, _toDisplayString(rec.title), 9, _hoisted_23),
                          _createElementVNode("div", {
                            class: "dbfapp-cell__meta",
                            title: rec.message
                          }, [
                            _createTextVNode(_toDisplayString(rec.time), 1),
                            (rec.type)
                              ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                  _createTextVNode(" · " + _toDisplayString(rec.type), 1)
                                ], 64))
                              : _createCommentVNode("", true)
                          ], 8, _hoisted_24),
                          (rec.message)
                            ? (_openBlock(), _createElementBlock("div", {
                                key: 0,
                                class: "dbfapp-cell__msg",
                                title: rec.message
                              }, _toDisplayString(rec.message), 9, _hoisted_25))
                            : _createCommentVNode("", true)
                        ]))
                      }), 128))
                    ]))
                  : (shown.value.length)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_26, [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(shown.value, (it) => {
                          return (_openBlock(), _createElementBlock("a", {
                            key: it.sid,
                            class: "dbfapp-cell",
                            href: `https://movie.douban.com/subject/${it.sid}/`,
                            target: "_blank"
                          }, [
                            _createElementVNode("div", _hoisted_28, [
                              (posterUrls[it.sid])
                                ? (_openBlock(), _createElementBlock("img", {
                                    key: 0,
                                    src: posterUrls[it.sid],
                                    alt: ""
                                  }, null, 8, _hoisted_29))
                                : (_openBlock(), _createBlock(_component_v_icon, {
                                    key: 1,
                                    icon: "mdi-image-off-outline",
                                    size: "26"
                                  })),
                              (mpStatus[it.sid])
                                ? (_openBlock(), _createElementBlock("span", {
                                    key: 2,
                                    class: _normalizeClass(["dbfapp-cell__flag", `dbfapp-cell__flag--${mpStatus[it.sid]}`])
                                  }, _toDisplayString(mpStatus[it.sid] === 'library' ? '已入库' : '已订阅'), 3))
                                : _createCommentVNode("", true),
                              (it.private)
                                ? (_openBlock(), _createElementBlock("span", _hoisted_30, [
                                    _createVNode(_component_v_icon, {
                                      icon: "mdi-lock-outline",
                                      size: "11"
                                    })
                                  ]))
                                : _createCommentVNode("", true),
                              (canUnmark(it))
                                ? (_openBlock(), _createBlock(_component_v_btn, {
                                    key: 4,
                                    class: "dbfapp-cell__unmark",
                                    icon: "mdi-bookmark-remove-outline",
                                    variant: "tonal",
                                    color: "warning",
                                    size: "x-small",
                                    loading: unmarkBusy[it.sid],
                                    title: `删除豆瓣「${statusLabel.value}」标记`,
                                    onClick: _withModifiers($event => (confirmUnmark(it)), ["prevent"])
                                  }, null, 8, ["loading", "title", "onClick"]))
                                : _createCommentVNode("", true),
                              (canSubscribe(it))
                                ? (_openBlock(), _createBlock(_component_v_btn, {
                                    key: 5,
                                    class: "dbfapp-cell__sub",
                                    icon: "mdi-plus",
                                    variant: "tonal",
                                    color: "primary",
                                    size: "x-small",
                                    loading: subBusy[it.sid],
                                    title: "加入 MoviePilot 订阅",
                                    onClick: _withModifiers($event => (subscribeItem(it)), ["prevent"])
                                  }, null, 8, ["loading", "onClick"]))
                                : _createCommentVNode("", true)
                            ]),
                            _createElementVNode("div", {
                              class: "dbfapp-cell__title",
                              title: it.title
                            }, _toDisplayString(it.title), 9, _hoisted_31),
                            _createElementVNode("div", _hoisted_32, _toDisplayString(metaLine(it)), 1),
                            _createElementVNode("div", _hoisted_33, [
                              (it.my_rating)
                                ? (_openBlock(), _createElementBlock("span", _hoisted_34, [
                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(it.my_rating, (n) => {
                                      return (_openBlock(), _createBlock(_component_v_icon, {
                                        key: n,
                                        icon: "mdi-star",
                                        size: "11",
                                        color: "#BA7517"
                                      }))
                                    }), 128))
                                  ]))
                                : _createCommentVNode("", true),
                              (it.douban_rating)
                                ? (_openBlock(), _createElementBlock("span", _hoisted_35, _toDisplayString(it.douban_rating.toFixed(1)), 1))
                                : _createCommentVNode("", true)
                            ])
                          ], 8, _hoisted_27))
                        }), 128))
                      ]))
                    : (_openBlock(), _createElementBlock("div", _hoisted_36, _toDisplayString(currentStatus.value === 'sync' ? '暂无同步记录' : '该分类下暂无条目'), 1)),
            (currentStatus.value !== 'sync' && hasMore.value && !error.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_37, [
                  _createVNode(_component_v_btn, {
                    variant: "tonal",
                    color: "primary",
                    size: "small",
                    loading: loading.value,
                    onClick: loadMore
                  }, {
                    default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                      _createTextVNode(" 加载更多 ", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"]),
                  _createVNode(_component_v_btn, {
                    variant: "outlined",
                    color: "primary",
                    size: "small",
                    loading: loadingAll.value,
                    onClick: loadAll
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(" 全部加载（共 " + _toDisplayString(total.value) + " 条） ", 1)
                    ]),
                    _: 1
                  }, 8, ["loading"])
                ]))
              : _createCommentVNode("", true)
          ])
        ], 64))
      : (_openBlock(), _createElementBlock("div", _hoisted_38, [...(_cache[10] || (_cache[10] = [
          _createElementVNode("div", { class: "dbfapp-empty" }, "尚未登录豆瓣，请到插件配置页扫码登录后再查看收藏。", -1)
        ]))])),
    _createVNode(_component_v_snackbar, {
      modelValue: toast.show,
      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((toast.show) = $event)),
      color: toast.color,
      location: "bottom right",
      timeout: "3000"
    }, {
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(toast.text), 1)
      ]),
      _: 1
    }, 8, ["modelValue", "color"]),
    _createVNode(_component_v_dialog, {
      modelValue: unmarkDialog.show,
      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((unmarkDialog.show) = $event)),
      "max-width": "380"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, { class: "dbfapp-dialog" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                _createTextVNode("删除豆瓣标记", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createTextVNode(" 确定删除《" + _toDisplayString(unmarkDialog.item?.title) + "》的「" + _toDisplayString(statusLabel.value) + "」标记吗？", 1),
                _cache[15] || (_cache[15] = _createElementVNode("br", null, null, -1)),
                _cache[16] || (_cache[16] = _createTextVNode(" 此操作会同步删除豆瓣上的该标记（豆瓣中称为「删除」/「删除该标记」），且不可恢复。 ", -1)),
                (currentStatus.value === 'wish')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                      _cache[12] || (_cache[12] = _createElementVNode("br", null, null, -1)),
                      _cache[13] || (_cache[13] = _createElementVNode("br", null, null, -1)),
                      _cache[14] || (_cache[14] = _createTextVNode("同时会取消 MoviePilot 中该条目的订阅，之后重新标记想看才会再次自动订阅。", -1))
                    ], 64))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  size: "small",
                  onClick: _cache[4] || (_cache[4] = $event => (unmarkDialog.show = false))
                }, {
                  default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  variant: "tonal",
                  color: "warning",
                  size: "small",
                  loading: unmarkDialog.busy,
                  onClick: doUnmark
                }, {
                  default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
                    _createTextVNode("删除标记", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"])
  ]))
}
}

};
const AppPage = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-0462e306"]]);

export { AppPage as default };
