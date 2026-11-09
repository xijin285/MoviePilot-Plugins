import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Page_vue_vue_type_style_index_0_scoped_85f3b621_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,withCtx:_withCtx,createTextVNode:_createTextVNode,normalizeClass:_normalizeClass,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,Transition:_Transition,createBlock:_createBlock,renderList:_renderList,Fragment:_Fragment,normalizeStyle:_normalizeStyle} = await importShared('vue');


const _hoisted_1 = { class: "ikuai-page" };
const _hoisted_2 = { class: "ikuai-topbar" };
const _hoisted_3 = { class: "ikuai-topbar__left" };
const _hoisted_4 = { class: "ikuai-topbar__icon" };
const _hoisted_5 = { class: "ikuai-topbar__meta" };
const _hoisted_6 = { class: "ikuai-topbar__sub" };
const _hoisted_7 = { class: "ikuai-topbar__right" };
const _hoisted_8 = { class: "ikuai-stats" };
const _hoisted_9 = {
  class: "ikuai-stat",
  style: {"--accent":"#3b82f6"}
};
const _hoisted_10 = { class: "ikuai-stat__icon" };
const _hoisted_11 = { class: "ikuai-stat__value" };
const _hoisted_12 = {
  class: "ikuai-stat",
  style: {"--accent":"#8b5cf6"}
};
const _hoisted_13 = { class: "ikuai-stat__icon" };
const _hoisted_14 = { class: "ikuai-stat__value" };
const _hoisted_15 = {
  class: "ikuai-stat",
  style: {"--accent":"#22c55e"}
};
const _hoisted_16 = { class: "ikuai-stat__icon" };
const _hoisted_17 = { class: "ikuai-stat__value" };
const _hoisted_18 = {
  class: "ikuai-stat",
  style: {"--accent":"#f59e0b"}
};
const _hoisted_19 = { class: "ikuai-stat__icon" };
const _hoisted_20 = { class: "ikuai-stat__value" };
const _hoisted_21 = {
  class: "ikuai-stat",
  style: {"--accent":"#06b6d4"}
};
const _hoisted_22 = { class: "ikuai-stat__icon" };
const _hoisted_23 = { class: "ikuai-stat__value" };
const _hoisted_24 = {
  class: "ikuai-stat",
  style: {"--accent":"#6366f1"}
};
const _hoisted_25 = { class: "ikuai-stat__icon" };
const _hoisted_26 = { class: "ikuai-stat__value" };
const _hoisted_27 = { class: "ikuai-card" };
const _hoisted_28 = { class: "ikuai-card__header" };
const _hoisted_29 = { class: "ikuai-card__title d-flex align-center" };
const _hoisted_30 = { class: "d-flex align-center flex-wrap ga-2" };
const _hoisted_31 = {
  key: 0,
  class: "ikuai-logs"
};
const _hoisted_32 = { class: "ikuai-log__body" };
const _hoisted_33 = { class: "ikuai-log__title" };
const _hoisted_34 = { class: "ikuai-log__msg" };
const _hoisted_35 = {
  key: 0,
  class: "ikuai-log__targets"
};
const _hoisted_36 = {
  key: 1,
  class: "ikuai-log__targets ikuai-log__targets--fail"
};
const _hoisted_37 = { class: "ikuai-log__meta" };
const _hoisted_38 = { class: "ikuai-log__time" };
const _hoisted_39 = {
  key: 1,
  class: "ikuai-empty"
};
const _hoisted_40 = {
  key: 1,
  class: "restore-list"
};
const _hoisted_41 = ["title"];
const _hoisted_42 = { class: "restore-time" };
const _hoisted_43 = {
  key: 2,
  class: "text-caption text-medium-emphasis text-center py-2"
};
const _hoisted_44 = { class: "ikuai-card" };
const _hoisted_45 = { class: "ikuai-card__header" };
const _hoisted_46 = { class: "ikuai-card__title d-flex align-center" };
const _hoisted_47 = { class: "d-flex align-center ga-2" };
const _hoisted_48 = {
  key: 0,
  class: "text-caption text-medium-emphasis"
};
const _hoisted_49 = {
  key: 0,
  class: "alert-list"
};
const _hoisted_50 = { class: "alert-kind" };
const _hoisted_51 = { class: "alert-detail" };
const _hoisted_52 = { class: "alert-threshold" };
const _hoisted_53 = { class: "alert-time" };
const _hoisted_54 = {
  key: 0,
  class: "alert-dur"
};
const _hoisted_55 = {
  key: 1,
  class: "ikuai-empty"
};
const _hoisted_56 = { class: "ikuai-card" };
const _hoisted_57 = { class: "ikuai-card__header" };
const _hoisted_58 = { class: "ikuai-card__title d-flex align-center" };
const _hoisted_59 = { class: "ikuai-guide" };

const {computed,onBeforeUnmount,onMounted,reactive,ref} = await importShared('vue');


const PLUGIN_ID = 'IkuaiRouterBackup';
const REFRESH_MS = 30000;


const _sfc_main = {
  __name: 'Page',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
},
  emits: ['close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const status = reactive({ cpu: null, mem: null, up_speed: '', down_speed: '', online_devices: null, uptime: 0, error: '' });
const interfaces = ref([]);
const backupHistory = ref([]);
const backupActivity = ref('空闲');
const restoreActivity = ref('空闲');

// 备份历史落点（本地 / 网盘 / WebDAV）
const targetsText = (log) => {
  const labels = [];
  for (const t of log?.targets || []) {
    const kind = String(t?.kind || '');
    let label;
    if (kind === 'local') label = '本地磁盘';
    else if (kind === 'webdav') label = 'WebDAV';
    else if (kind === 'cloud') label = `网盘·${t?.label || ''}`;
    else label = String(t?.label || kind);
    if (label && !labels.includes(label)) labels.push(label);
  }
  return labels.join(' + ')
};
const failedText = (log) => (log?.failed || []).filter(Boolean).join('、');
const loading = ref(false);
const backingUp = ref(false);
const toast = reactive({ show: false, type: 'success', text: '' });
let timer = null;
let toastTimer = null;

const showToast = (text, type = 'success') => {
  toast.text = text;
  toast.type = type;
  toast.show = true;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.show = false), 3500);
};

async function runBackupNow() {
  backingUp.value = true;
  try {
    const apiPath = `plugin/${PLUGIN_ID}/backup`;
    const result = props.api?.post
      ? await props.api.post(apiPath, {})
      : await (await fetch(`/api/v1/${apiPath}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })).json();
    if (result?.success) {
      showToast(result.message || '备份任务已启动');
      setTimeout(loadAll, 3000);
    } else {
      showToast(result?.message || '启动备份任务失败', 'error');
    }
  } catch (error) {
    showToast('启动备份任务失败', 'error');
  } finally {
    backingUp.value = false;
  }
}

const fmtSpeed = (bps) => {
  const v = Number(bps) || 0;
  if (v >= 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024).toFixed(2) + ' GB/s'
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(1) + ' MB/s'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' KB/s'
  return v + ' B/s'
};

const fmtUptime = (sec) => {
  const s = Number(sec) || 0;
  if (!s) return ''
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d > 0) return `${d}天${h}时`
  if (h > 0) return `${h}时${m}分`
  return `${m}分`
};

const busy = computed(() => {
  const b = String(backupActivity.value || '');
  const r = String(restoreActivity.value || '');
  return (b && b !== '空闲') || (r && r !== '空闲')
});

// ============ 恢复备份 ============
const restoreDialog = reactive({ show: false, loading: false, restoring: '', enableRestore: false, backups: [] });
const restoreConfirm = reactive({ show: false, backup: null });

const sourceChipColor = (source) => {
  if (!source) return 'primary'
  if (source.includes('网盘')) return 'info'
  if (source.includes('WebDAV')) return 'purple'
  return 'primary'
};

const fmtTime = (ts) => {
  if (!ts) return '-'
  try {
    return new Date(Number(ts) * 1000).toLocaleString()
  } catch (error) {
    return '-'
  }
};

const openRestoreDialog = async () => {
  restoreDialog.show = true;
  restoreDialog.loading = true;
  restoreDialog.restoring = '';
  try {
    const data = await request('/available_backups');
    restoreDialog.enableRestore = !!data?.enable_restore;
    restoreDialog.backups = data?.backups || [];
  } catch (error) {
    restoreDialog.enableRestore = false;
    restoreDialog.backups = [];
  } finally {
    restoreDialog.loading = false;
  }
};

const askRestore = (backup) => {
  restoreConfirm.backup = backup;
  restoreConfirm.show = true;
};

// ============ 备份文件下载 / 删除 ============
const downloading = ref('');
const deleteConfirm = reactive({ show: false, loading: false, backup: null });

const backupParams = (b) => ({
  filename: b.filename,
  source: b.source || '本地备份',
  storage: b.storage || '',
  remote_dir: b.remote_dir || '',
});

async function downloadBackup(b) {
  downloading.value = b.filename;
  try {
    const apiPath = `plugin/${PLUGIN_ID}/download_backup`;
    const params = backupParams(b);
    let data;
    if (props.api?.get) {
      data = await props.api.get(apiPath, { params });
    } else {
      const qs = new URLSearchParams(params).toString();
      data = await (await fetch(`/api/v1/${apiPath}?${qs}`)).json();
    }
    if (!data?.ok) throw new Error(data?.error || '读取备份文件失败')
    const bin = atob(data.content || '');
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
    const blob = new Blob([bytes], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = data.filename || b.filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast(`已下载 ${a.download}（${((data.size || 0) / 1024).toFixed(1)} KB）`);
  } catch (error) {
    showToast(error?.message || '下载备份失败', 'error');
  } finally {
    downloading.value = '';
  }
}

const askDelete = (b) => {
  deleteConfirm.backup = b;
  deleteConfirm.show = true;
};

async function doDelete() {
  const b = deleteConfirm.backup;
  if (!b) return
  deleteConfirm.loading = true;
  try {
    const apiPath = `plugin/${PLUGIN_ID}/delete_backup`;
    const body = backupParams(b);
    const result = props.api?.post
      ? await props.api.post(apiPath, body)
      : await (await fetch(`/api/v1/${apiPath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })).json();
    if (result?.ok) {
      showToast(result?.msg || '已删除备份文件');
      deleteConfirm.show = false;
      await openRestoreDialog();
    } else {
      showToast(result?.msg || result?.error || '删除失败', 'error');
    }
  } catch (error) {
    showToast('删除备份失败', 'error');
  } finally {
    deleteConfirm.loading = false;
  }
}

const doRestore = async () => {
  const b = restoreConfirm.backup;
  if (!b) return
  restoreDialog.restoring = b.filename;
  try {
    const apiPath = `plugin/${PLUGIN_ID}/restore`;
    const body = {
      filename: b.filename,
      source: b.source || '本地备份',
      storage: b.storage || '',
      remote_dir: b.remote_dir || '',
    };
    const result = props.api?.post
      ? await props.api.post(apiPath, body)
      : await (await fetch(`/api/v1/${apiPath}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    if (result?.success === false) {
      showToast(result?.message || '启动恢复失败', 'error');
    } else {
      showToast('恢复任务已启动，恢复完成后路由器将应用备份配置');
      restoreConfirm.show = false;
      restoreDialog.show = false;
      setTimeout(loadHistories, 3000);
    }
  } catch (error) {
    showToast('启动恢复失败', 'error');
  } finally {
    restoreDialog.restoring = '';
  }
};

async function request(path, method = 'GET', body = null) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`;
  if (method === 'POST') {
    if (props.api?.post) {
      return await props.api.post(apiPath, body || {})
    }
    const response = await fetch(`/api/v1/${apiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    return await response.json()
  }
  if (props.api?.get) {
    return await props.api.get(apiPath, {})
  }
  const response = await fetch(`/api/v1/${apiPath}`);
  return await response.json()
}

async function loadStatus() {
  try {
    const data = await request('/status');
    if (data && typeof data === 'object') {
      status.cpu = data.cpu_usage != null ? Number(data.cpu_usage) : null;
      status.mem = data.mem_usage != null ? Number(data.mem_usage) : null;
      status.up_speed = fmtSpeed(data.upload_speed);
      status.down_speed = fmtSpeed(data.download_speed);
      status.uptime = data.uptime || 0;
      status.hostname = data.hostname || '';
      status.version = data.version || '';
      status.error = data.ok === false ? (data.error || '获取状态失败') : '';
      interfaces.value = Array.isArray(data.interfaces) ? data.interfaces : [];
    }
  } catch (error) {
    status.error = '获取路由器状态失败';
  }
  try {
    const data = await request('/devices');
    if (data && typeof data === 'object') {
      status.online_devices = data.ok && Array.isArray(data.devices) ? data.devices.length : null;
    }
  } catch (error) {
    // 设备数获取失败不影响其他状态
  }
}

async function loadHistories() {
  try {
    const data = await request('/histories');
    if (data && typeof data === 'object') {
      backupHistory.value = Array.isArray(data.backup_history) ? data.backup_history : [];
      backupActivity.value = data.backup_activity || '空闲';
      restoreActivity.value = data.restore_activity || '空闲';
    }
  } catch (error) {
    // 静默失败，保留上一次结果
  }
}

async function loadAll() {
  loading.value = true;
  try {
    await Promise.all([loadStatus(), loadHistories(), loadAlerts()]);
  } finally {
    loading.value = false;
  }
}

// ============ 告警记录 ============
const alerts = reactive({ items: [], total: 0, active: null, enabled: false, cpu_threshold: 90, mem_threshold: 90 });
const alertsLoading = ref(false);

const fmtAlertTime = (ts) => {
  const n = Number(ts) || 0;
  if (!n) return '-'
  const d = new Date(n * 1000);
  const p = (x) => String(x).padStart(2, '0');
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
};

const fmtDuration = (sec) => {
  const s = Number(sec) || 0;
  if (s >= 3600) return `${Math.floor(s / 3600)} 小时 ${Math.floor((s % 3600) / 60)} 分`
  if (s >= 60) return `${Math.floor(s / 60)} 分钟`
  return `${s} 秒`
};

async function loadAlerts() {
  alertsLoading.value = true;
  try {
    const data = await request('/alert_history');
    if (data && typeof data === 'object' && data.ok !== false) {
      alerts.items = Array.isArray(data.items) ? data.items : [];
      alerts.total = data.total || 0;
      alerts.active = data.active || null;
      alerts.enabled = !!data.enabled;
      alerts.cpu_threshold = data.cpu_threshold ?? 90;
      alerts.mem_threshold = data.mem_threshold ?? 90;
    }
  } catch (error) {
    // 静默
  } finally {
    alertsLoading.value = false;
  }
}

async function clearAlerts() {
  try {
    const res = await request('/alert_history', 'POST', {});
    if (res?.ok) {
      showToast(res.msg || '告警记录已清空');
      loadAlerts();
    } else {
      showToast(res?.error || '清空失败', 'error');
    }
  } catch (error) {
    showToast('清空失败', 'error');
  }
}

onMounted(() => {
  loadAll();
  timer = setInterval(() => {
    loadStatus();
    loadAlerts();
  }, REFRESH_MS);
});

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-router-network",
            size: "24"
          })
        ]),
        _createElementVNode("div", _hoisted_5, [
          _cache[8] || (_cache[8] = _createElementVNode("div", { class: "ikuai-topbar__title" }, "爱快时光机", -1)),
          _createElementVNode("div", _hoisted_6, _toDisplayString(status.hostname ? `${status.hostname} ${status.version || ''}` : '配置备份 · 实时监控 · 负载告警'), 1)
        ])
      ]),
      _createElementVNode("div", _hoisted_7, [
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-refresh",
          loading: loading.value,
          onClick: loadAll
        }, {
          default: _withCtx(() => _cache[9] || (_cache[9] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "刷新", -1)
          ])),
          _: 1,
          __: [9]
        }, 8, ["loading"]),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "success",
          size: "small",
          "prepend-icon": "mdi-cloud-upload-outline",
          loading: backingUp.value,
          onClick: runBackupNow
        }, {
          default: _withCtx(() => _cache[10] || (_cache[10] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "立即备份", -1)
          ])),
          _: 1,
          __: [10]
        }, 8, ["loading"]),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-cog-outline",
          onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
        }, {
          default: _withCtx(() => _cache[11] || (_cache[11] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "插件配置", -1)
          ])),
          _: 1,
          __: [11]
        }),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-close",
          onClick: _cache[1] || (_cache[1] = $event => (emit('close')))
        }, {
          default: _withCtx(() => _cache[12] || (_cache[12] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "关闭", -1)
          ])),
          _: 1,
          __: [12]
        })
      ])
    ]),
    _createVNode(_Transition, { name: "toast-fade" }, {
      default: _withCtx(() => [
        (toast.show)
          ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: _normalizeClass(["ikuai-toast", toast.type === 'error' ? 'ikuai-toast--error' : 'ikuai-toast--success'])
            }, [
              _createVNode(_component_v_icon, { size: "16" }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(toast.type === 'error' ? 'mdi-alert-circle' : 'mdi-check-circle'), 1)
                ]),
                _: 1
              }),
              _createElementVNode("span", null, _toDisplayString(toast.text), 1)
            ], 2))
          : _createCommentVNode("", true)
      ]),
      _: 1
    }),
    _createElementVNode("div", _hoisted_8, [
      _createElementVNode("div", _hoisted_9, [
        _createElementVNode("div", _hoisted_10, [
          _createVNode(_component_v_icon, {
            icon: "mdi-cpu-64-bit",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_11, _toDisplayString(status.cpu != null ? status.cpu + '%' : '—'), 1),
        _cache[13] || (_cache[13] = _createElementVNode("div", { class: "ikuai-stat__label" }, "CPU 使用率", -1))
      ]),
      _createElementVNode("div", _hoisted_12, [
        _createElementVNode("div", _hoisted_13, [
          _createVNode(_component_v_icon, {
            icon: "mdi-memory",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_14, _toDisplayString(status.mem != null ? status.mem + '%' : '—'), 1),
        _cache[14] || (_cache[14] = _createElementVNode("div", { class: "ikuai-stat__label" }, "内存使用率", -1))
      ]),
      _createElementVNode("div", _hoisted_15, [
        _createElementVNode("div", _hoisted_16, [
          _createVNode(_component_v_icon, {
            icon: "mdi-arrow-up-bold",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_17, _toDisplayString(status.up_speed || '—'), 1),
        _cache[15] || (_cache[15] = _createElementVNode("div", { class: "ikuai-stat__label" }, "WAN 上行", -1))
      ]),
      _createElementVNode("div", _hoisted_18, [
        _createElementVNode("div", _hoisted_19, [
          _createVNode(_component_v_icon, {
            icon: "mdi-arrow-down-bold",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_20, _toDisplayString(status.down_speed || '—'), 1),
        _cache[16] || (_cache[16] = _createElementVNode("div", { class: "ikuai-stat__label" }, "WAN 下行", -1))
      ]),
      _createElementVNode("div", _hoisted_21, [
        _createElementVNode("div", _hoisted_22, [
          _createVNode(_component_v_icon, {
            icon: "mdi-devices",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_23, _toDisplayString(status.online_devices != null ? status.online_devices : '—'), 1),
        _cache[17] || (_cache[17] = _createElementVNode("div", { class: "ikuai-stat__label" }, "在线设备", -1))
      ]),
      _createElementVNode("div", _hoisted_24, [
        _createElementVNode("div", _hoisted_25, [
          _createVNode(_component_v_icon, {
            icon: "mdi-clock-outline",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_26, _toDisplayString(fmtUptime(status.uptime) || '—'), 1),
        _cache[18] || (_cache[18] = _createElementVNode("div", { class: "ikuai-stat__label" }, "运行时间", -1))
      ])
    ]),
    (status.error)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 0,
          type: "warning",
          variant: "tonal",
          density: "compact",
          class: "mb-3"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(status.error) + "（请检查插件配置或路由器连接） ", 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createElementVNode("div", _hoisted_27, [
      _createElementVNode("div", _hoisted_28, [
        _createElementVNode("span", _hoisted_29, [
          _createVNode(_component_v_icon, {
            icon: "mdi-content-save-check",
            size: "18",
            color: "#22c55e",
            class: "mr-1"
          }),
          _cache[19] || (_cache[19] = _createTextVNode(" 备份管理 "))
        ]),
        _createElementVNode("span", _hoisted_30, [
          _createVNode(_component_v_btn, {
            variant: "tonal",
            color: "primary",
            size: "small",
            "prepend-icon": "mdi-cloud-upload-outline",
            loading: backingUp.value,
            disabled: busy.value,
            onClick: runBackupNow
          }, {
            default: _withCtx(() => _cache[20] || (_cache[20] = [
              _createTextVNode(" 立即备份 ")
            ])),
            _: 1,
            __: [20]
          }, 8, ["loading", "disabled"]),
          _createVNode(_component_v_btn, {
            variant: "tonal",
            color: "error",
            size: "small",
            "prepend-icon": "mdi-backup-restore",
            onClick: openRestoreDialog
          }, {
            default: _withCtx(() => _cache[21] || (_cache[21] = [
              _createTextVNode(" 恢复备份 ")
            ])),
            _: 1,
            __: [21]
          })
        ])
      ]),
      (backupHistory.value.length)
        ? (_openBlock(), _createElementBlock("div", _hoisted_31, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(backupHistory.value.slice(0, 6), (log, index) => {
              return (_openBlock(), _createElementBlock("div", {
                key: index,
                class: "ikuai-log"
              }, [
                _createElementVNode("span", {
                  class: "ikuai-log__dot",
                  style: _normalizeStyle({ background: log.success ? '#22c55e' : '#ef4444' })
                }, null, 4),
                _createElementVNode("div", _hoisted_32, [
                  _createElementVNode("div", _hoisted_33, _toDisplayString(log.filename || log.message || '备份任务'), 1),
                  _createElementVNode("div", _hoisted_34, [
                    _createTextVNode(_toDisplayString(log.message || '') + " ", 1),
                    (targetsText(log))
                      ? (_openBlock(), _createElementBlock("span", _hoisted_35, "落点：" + _toDisplayString(targetsText(log)), 1))
                      : _createCommentVNode("", true),
                    (failedText(log))
                      ? (_openBlock(), _createElementBlock("span", _hoisted_36, "未成功：" + _toDisplayString(failedText(log)), 1))
                      : _createCommentVNode("", true)
                  ])
                ]),
                _createElementVNode("div", _hoisted_37, [
                  _createElementVNode("span", {
                    class: "ikuai-log__result",
                    style: _normalizeStyle({ color: log.success ? '#22c55e' : '#ef4444' })
                  }, _toDisplayString(log.success ? '成功' : '失败'), 5),
                  _createElementVNode("span", _hoisted_38, _toDisplayString(log.time || ''), 1)
                ])
              ]))
            }), 128))
          ]))
        : (_openBlock(), _createElementBlock("div", _hoisted_39, "暂无备份记录，可点击右上角「立即备份」或在「插件配置」中设置定时备份"))
    ]),
    _createVNode(_component_v_dialog, {
      modelValue: restoreDialog.show,
      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((restoreDialog.show) = $event)),
      "max-width": "640",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-file-cog-outline",
                  size: "20",
                  color: "primary",
                  class: "mr-2"
                }),
                _cache[23] || (_cache[23] = _createTextVNode(" 备份文件 ")),
                _createVNode(_component_v_chip, {
                  size: "x-small",
                  variant: "tonal",
                  class: "ml-2"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(restoreDialog.backups.length) + " 个", 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  size: "x-small",
                  variant: "text",
                  "prepend-icon": "mdi-refresh",
                  loading: restoreDialog.loading,
                  onClick: openRestoreDialog
                }, {
                  default: _withCtx(() => _cache[22] || (_cache[22] = [
                    _createTextVNode("刷新")
                  ])),
                  _: 1,
                  __: [22]
                }, 8, ["loading"])
              ]),
              _: 1,
              __: [23]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_alert, {
                  type: "warning",
                  variant: "tonal",
                  density: "compact",
                  class: "mb-3"
                }, {
                  default: _withCtx(() => _cache[24] || (_cache[24] = [
                    _createTextVNode(" 恢复会用备份文件覆盖路由器当前全部配置，操作前会自动创建恢复点。下载 / 删除只影响备份文件本身，不影响路由器。 ")
                  ])),
                  _: 1,
                  __: [24]
                }),
                (!restoreDialog.enableRestore)
                  ? (_openBlock(), _createBlock(_component_v_alert, {
                      key: 0,
                      type: "info",
                      variant: "tonal",
                      density: "compact",
                      class: "mb-3"
                    }, {
                      default: _withCtx(() => _cache[25] || (_cache[25] = [
                        _createTextVNode(" 恢复功能未启用（插件配置 → 恢复设置）。当前仍可下载或删除备份文件。 ")
                      ])),
                      _: 1,
                      __: [25]
                    }))
                  : _createCommentVNode("", true),
                (restoreDialog.backups.length)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_40, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(restoreDialog.backups, (b, idx) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: idx,
                          class: "restore-row"
                        }, [
                          _createVNode(_component_v_icon, {
                            size: "16",
                            color: "primary"
                          }, {
                            default: _withCtx(() => _cache[26] || (_cache[26] = [
                              _createTextVNode("mdi-file-cog-outline")
                            ])),
                            _: 1,
                            __: [26]
                          }),
                          _createElementVNode("span", {
                            class: "restore-name",
                            title: b.filename
                          }, _toDisplayString(b.filename), 9, _hoisted_41),
                          _createVNode(_component_v_chip, {
                            size: "x-small",
                            variant: "outlined",
                            class: "mx-1",
                            color: sourceChipColor(b.source)
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(b.source || '本地备份'), 1)
                            ]),
                            _: 2
                          }, 1032, ["color"]),
                          _createElementVNode("span", _hoisted_42, _toDisplayString(b.time ? fmtTime(b.time) : ''), 1),
                          _createVNode(_component_v_btn, {
                            size: "x-small",
                            variant: "tonal",
                            color: "error",
                            disabled: !restoreDialog.enableRestore,
                            loading: restoreDialog.restoring === b.filename,
                            onClick: $event => (askRestore(b))
                          }, {
                            default: _withCtx(() => _cache[27] || (_cache[27] = [
                              _createTextVNode("恢复")
                            ])),
                            _: 2,
                            __: [27]
                          }, 1032, ["disabled", "loading", "onClick"]),
                          _createVNode(_component_v_btn, {
                            size: "x-small",
                            variant: "text",
                            icon: "mdi-download",
                            title: "下载到浏览器",
                            loading: downloading.value === b.filename,
                            onClick: $event => (downloadBackup(b))
                          }, null, 8, ["loading", "onClick"]),
                          _createVNode(_component_v_btn, {
                            size: "x-small",
                            variant: "text",
                            icon: "mdi-trash-can-outline",
                            color: "error",
                            title: "删除备份",
                            onClick: $event => (askDelete(b))
                          }, null, 8, ["onClick"])
                        ]))
                      }), 128))
                    ]))
                  : (_openBlock(), _createElementBlock("div", _hoisted_43, _toDisplayString(restoreDialog.loading ? '加载中...' : '暂无可用的备份文件，请先执行备份'), 1))
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[2] || (_cache[2] = $event => (restoreDialog.show = false))
                }, {
                  default: _withCtx(() => _cache[28] || (_cache[28] = [
                    _createTextVNode("关闭")
                  ])),
                  _: 1,
                  __: [28]
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: deleteConfirm.show,
      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((deleteConfirm.show) = $event)),
      "max-width": "420",
      persistent: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-trash-can-outline",
                  size: "20",
                  color: "error",
                  class: "mr-2"
                }),
                _cache[29] || (_cache[29] = _createTextVNode(" 删除备份文件？ "))
              ]),
              _: 1,
              __: [29]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _cache[30] || (_cache[30] = _createTextVNode(" 将从 ")),
                _createElementVNode("b", null, _toDisplayString(deleteConfirm.backup?.source || '本地备份'), 1),
                _cache[31] || (_cache[31] = _createTextVNode(" 中永久删除 ")),
                _createElementVNode("b", null, _toDisplayString(deleteConfirm.backup?.filename), 1),
                _cache[32] || (_cache[32] = _createTextVNode("，删除后不可恢复。 "))
              ]),
              _: 1,
              __: [30,31,32]
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[4] || (_cache[4] = $event => (deleteConfirm.show = false))
                }, {
                  default: _withCtx(() => _cache[33] || (_cache[33] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1,
                  __: [33]
                }),
                _createVNode(_component_v_btn, {
                  color: "error",
                  variant: "tonal",
                  loading: deleteConfirm.loading,
                  onClick: doDelete
                }, {
                  default: _withCtx(() => _cache[34] || (_cache[34] = [
                    _createTextVNode("确认删除")
                  ])),
                  _: 1,
                  __: [34]
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: restoreConfirm.show,
      "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((restoreConfirm.show) = $event)),
      "max-width": "420",
      persistent: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-alert-octagon-outline",
                  size: "20",
                  color: "error",
                  class: "mr-2"
                }),
                _cache[35] || (_cache[35] = _createTextVNode(" 确认恢复？ "))
              ]),
              _: 1,
              __: [35]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _cache[36] || (_cache[36] = _createTextVNode(" 将使用 ")),
                _createElementVNode("b", null, _toDisplayString(restoreConfirm.backup?.filename), 1),
                _createTextVNode("（" + _toDisplayString(restoreConfirm.backup?.source || '本地备份') + "） 覆盖路由器当前配置，恢复期间路由器可能短暂离线。确定继续吗？ ", 1)
              ]),
              _: 1,
              __: [36]
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[6] || (_cache[6] = $event => (restoreConfirm.show = false))
                }, {
                  default: _withCtx(() => _cache[37] || (_cache[37] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1,
                  __: [37]
                }),
                _createVNode(_component_v_btn, {
                  color: "error",
                  variant: "tonal",
                  loading: restoreDialog.restoring === restoreConfirm.backup?.filename,
                  onClick: doRestore
                }, {
                  default: _withCtx(() => _cache[38] || (_cache[38] = [
                    _createTextVNode("确认恢复")
                  ])),
                  _: 1,
                  __: [38]
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createElementVNode("div", _hoisted_44, [
      _createElementVNode("div", _hoisted_45, [
        _createElementVNode("span", _hoisted_46, [
          _createVNode(_component_v_icon, {
            icon: "mdi-bell-alert-outline",
            size: "18",
            color: "#f59e0b",
            class: "mr-1"
          }),
          _cache[40] || (_cache[40] = _createTextVNode(" 告警记录 ")),
          _createVNode(_component_v_chip, {
            size: "x-small",
            variant: "tonal",
            class: "ml-2",
            color: alerts.enabled ? 'success' : 'grey'
          }, {
            default: _withCtx(() => [
              _createTextVNode(_toDisplayString(alerts.enabled ? '监控中' : '未启用'), 1)
            ]),
            _: 1
          }, 8, ["color"]),
          (alerts.active)
            ? (_openBlock(), _createBlock(_component_v_chip, {
                key: 0,
                size: "x-small",
                variant: "tonal",
                color: "error",
                class: "ml-1"
              }, {
                default: _withCtx(() => _cache[39] || (_cache[39] = [
                  _createTextVNode("告警中")
                ])),
                _: 1,
                __: [39]
              }))
            : _createCommentVNode("", true)
        ]),
        _createElementVNode("span", _hoisted_47, [
          (alerts.enabled)
            ? (_openBlock(), _createElementBlock("span", _hoisted_48, " CPU ≥ " + _toDisplayString(alerts.cpu_threshold) + "% / 内存 ≥ " + _toDisplayString(alerts.mem_threshold) + "% ", 1))
            : _createCommentVNode("", true),
          _createVNode(_component_v_btn, {
            size: "small",
            variant: "text",
            "prepend-icon": "mdi-refresh",
            loading: alertsLoading.value,
            onClick: loadAlerts
          }, {
            default: _withCtx(() => _cache[41] || (_cache[41] = [
              _createTextVNode("刷新")
            ])),
            _: 1,
            __: [41]
          }, 8, ["loading"]),
          (alerts.items.length)
            ? (_openBlock(), _createBlock(_component_v_btn, {
                key: 1,
                size: "small",
                variant: "text",
                color: "error",
                onClick: clearAlerts
              }, {
                default: _withCtx(() => _cache[42] || (_cache[42] = [
                  _createTextVNode("清空")
                ])),
                _: 1,
                __: [42]
              }))
            : _createCommentVNode("", true)
        ])
      ]),
      (alerts.items.length)
        ? (_openBlock(), _createElementBlock("div", _hoisted_49, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(alerts.items.slice(0, 8), (a, idx) => {
              return (_openBlock(), _createElementBlock("div", {
                key: a.id || idx,
                class: "alert-row"
              }, [
                _createElementVNode("span", {
                  class: "alert-dot",
                  style: _normalizeStyle({ background: a.end ? 'rgba(34,197,94,0.9)' : 'rgba(239,68,68,0.9)' })
                }, null, 4),
                _createElementVNode("span", _hoisted_50, _toDisplayString(a.kind), 1),
                _createElementVNode("span", _hoisted_51, [
                  _createTextVNode(" CPU " + _toDisplayString(a.peak_cpu) + "% / 内存 " + _toDisplayString(a.peak_mem) + "% ", 1),
                  _createElementVNode("span", _hoisted_52, "阈值 " + _toDisplayString(a.cpu_limit) + "% / " + _toDisplayString(a.mem_limit) + "%", 1)
                ]),
                _createElementVNode("span", _hoisted_53, [
                  _createTextVNode(_toDisplayString(fmtAlertTime(a.start)) + " ", 1),
                  _cache[43] || (_cache[43] = _createElementVNode("span", { class: "alert-sep" }, "→", -1)),
                  _createElementVNode("span", {
                    style: _normalizeStyle({ color: a.end ? '#22c55e' : '#ef4444' })
                  }, _toDisplayString(a.end ? fmtAlertTime(a.end) : '持续中'), 5),
                  (a.end && a.duration)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_54, "（" + _toDisplayString(fmtDuration(a.duration)) + "）", 1))
                    : _createCommentVNode("", true)
                ])
              ]))
            }), 128))
          ]))
        : (_openBlock(), _createElementBlock("div", _hoisted_55, _toDisplayString(alerts.enabled ? '暂无告警记录，负载正常时会保持安静' : '负载告警未启用，可在「插件配置 → 监控与告警」中打开'), 1))
    ]),
    _createElementVNode("div", _hoisted_56, [
      _createElementVNode("div", _hoisted_57, [
        _createElementVNode("span", _hoisted_58, [
          _createVNode(_component_v_icon, {
            icon: "mdi-information-outline",
            size: "18",
            color: "#6366f1",
            class: "mr-1"
          }),
          _cache[44] || (_cache[44] = _createTextVNode(" 完整监控 "))
        ])
      ]),
      _createElementVNode("div", _hoisted_59, [
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-view-dashboard-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[45] || (_cache[45] = _createTextVNode(" 实时监控（性能负载 / 终端排行 / 协议排行 / 在线终端等 14 视图）/ 线路监控 / 系统日志，请到左侧导航「")),
          _cache[46] || (_cache[46] = _createElementVNode("strong", null, "爱快路由", -1)),
          _cache[47] || (_cache[47] = _createTextVNode("」页面查看。 "))
        ]),
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-cog-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[48] || (_cache[48] = _createTextVNode(" 定时备份 / 存储备份 / WebDAV / 负载告警等设置，点击右上角「")),
          _cache[49] || (_cache[49] = _createElementVNode("strong", null, "插件配置", -1)),
          _cache[50] || (_cache[50] = _createTextVNode("」。 "))
        ])
      ])
    ])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-85f3b621"]]);

export { Page as default };
