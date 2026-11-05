import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const AppPage_vue_vue_type_style_index_0_scoped_bdb2a0d8_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,normalizeStyle:_normalizeStyle,createCommentVNode:_createCommentVNode,createBlock:_createBlock,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "app-page" };
const _hoisted_2 = { class: "page-header d-flex align-center flex-wrap ga-3 mb-4" };
const _hoisted_3 = { class: "stat-card-body" };
const _hoisted_4 = { class: "stat-card-number" };
const _hoisted_5 = { class: "stat-card-label" };
const _hoisted_6 = {
  key: 0,
  class: "stat-card-sub"
};
const _hoisted_7 = { class: "mode-selector" };
const _hoisted_8 = ["onClick"];
const _hoisted_9 = { class: "mode-text" };
const _hoisted_10 = ["disabled"];
const _hoisted_11 = ["disabled"];
const _hoisted_12 = { class: "preview-container" };
const _hoisted_13 = {
  key: 0,
  class: "preview-center"
};
const _hoisted_14 = {
  key: 1,
  class: "preview-center"
};
const _hoisted_15 = { class: "mt-3 text-error" };
const _hoisted_16 = {
  key: 2,
  class: "preview-image-wrap"
};
const _hoisted_17 = ["src"];
const _hoisted_18 = {
  key: 3,
  class: "preview-center"
};
const _hoisted_19 = { class: "source-grid" };
const _hoisted_20 = { class: "source-name" };
const _hoisted_21 = { class: "source-count" };
const _hoisted_22 = { class: "d-flex flex-wrap ga-2" };
const _hoisted_23 = {
  key: 0,
  class: "ml-1 font-weight-bold"
};
const _hoisted_24 = {
  key: 1,
  class: "ml-1"
};
const _hoisted_25 = {
  key: 2,
  class: "ml-1"
};
const _hoisted_26 = { class: "d-flex align-center flex-wrap ga-2 mb-3" };
const _hoisted_27 = { class: "text-caption text-medium-emphasis mb-1" };
const _hoisted_28 = { key: 0 };
const _hoisted_29 = { class: "text-caption d-flex ga-3" };
const _hoisted_30 = { class: "text-success" };
const _hoisted_31 = { class: "text-info" };
const _hoisted_32 = { class: "text-info" };
const _hoisted_33 = { class: "text-warning" };
const _hoisted_34 = { class: "text-error" };
const _hoisted_35 = {
  key: 1,
  class: "text-caption text-medium-emphasis"
};
const _hoisted_36 = { class: "trend-row" };
const _hoisted_37 = ["title"];
const _hoisted_38 = { class: "trend-count" };
const _hoisted_39 = { class: "trend-bar-wrap" };
const _hoisted_40 = { class: "trend-label" };
const _hoisted_41 = {
  key: 1,
  class: "visit-table"
};
const _hoisted_42 = { class: "visit-time" };
const _hoisted_43 = {
  key: 2,
  class: "text-caption text-medium-emphasis text-center py-2"
};
const _hoisted_44 = { class: "api-endpoint-row" };
const _hoisted_45 = { class: "api-endpoint-info" };
const _hoisted_46 = { class: "api-endpoint-title" };
const _hoisted_47 = { class: "api-url" };
const _hoisted_48 = {
  key: 0,
  class: "examples-wrap"
};
const _hoisted_49 = { class: "d-flex align-center mb-1" };
const _hoisted_50 = { class: "text-caption font-weight-bold" };
const _hoisted_51 = { class: "example-code" };

const {ref,reactive,computed,onMounted,onUnmounted} = await importShared('vue');



const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'RandomPic' },
  navKey: { type: String, default: 'main' },
},
  setup(__props) {

const props = __props;

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
// 来源列：按访问入口显示 —— 本地 / 局域网 / 实际域名
const sourceDisplay = (v) => {
  if (!v) return "-";
  const s = v.source;
  if (s === "local") return "本地";
  if (s === "lan") return "局域网";
  if (s === "domain") return v.domain || "域名";
  if (s === "network") return v.domain || "域名"; // 兼容旧记录（网络图源）
  return s || "-";
};

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

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_tooltip = _resolveComponent("v-tooltip");
  const _component_v_expand_transition = _resolveComponent("v-expand-transition");
  const _component_v_snackbar = _resolveComponent("v-snackbar");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createVNode(_component_v_icon, {
        color: "primary",
        size: "28"
      }, {
        default: _withCtx(() => _cache[4] || (_cache[4] = [
          _createTextVNode("mdi-image-multiple-outline")
        ])),
        _: 1,
        __: [4]
      }),
      _cache[7] || (_cache[7] = _createElementVNode("span", { class: "text-h5 font-weight-bold" }, "随机图库仪表盘", -1)),
      _createVNode(_component_v_chip, {
        color: status.enable ? 'success' : 'grey',
        size: "small",
        variant: "tonal"
      }, {
        default: _withCtx(() => [
          _createTextVNode(_toDisplayString(status.enable ? 'API 可用' : 'API 已禁用'), 1)
        ]),
        _: 1
      }, 8, ["color"]),
      _createVNode(_component_v_spacer),
      _createVNode(_component_v_btn, {
        size: "small",
        variant: "tonal",
        color: "primary",
        loading: refreshing.value,
        onClick: refreshAll
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_icon, {
            size: "16",
            class: "mr-1"
          }, {
            default: _withCtx(() => _cache[5] || (_cache[5] = [
              _createTextVNode("mdi-refresh")
            ])),
            _: 1,
            __: [5]
          }),
          _cache[6] || (_cache[6] = _createTextVNode(" 刷新 "))
        ]),
        _: 1,
        __: [6]
      }, 8, ["loading"])
    ]),
    _createVNode(_component_v_row, {
      dense: "",
      class: "mb-1"
    }, {
      default: _withCtx(() => [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(statCards.value, (card) => {
          return (_openBlock(), _createBlock(_component_v_col, {
            cols: "6",
            md: "3",
            key: card.label
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_card, {
                class: "stat-card",
                elevation: "2"
              }, {
                default: _withCtx(() => [
                  _createElementVNode("div", {
                    class: "stat-card-icon",
                    style: _normalizeStyle({ background: card.bg })
                  }, [
                    _createVNode(_component_v_icon, {
                      color: card.color,
                      size: "26"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(card.icon), 1)
                      ]),
                      _: 2
                    }, 1032, ["color"])
                  ], 4),
                  _createElementVNode("div", _hoisted_3, [
                    _createElementVNode("div", _hoisted_4, _toDisplayString(card.value), 1),
                    _createElementVNode("div", _hoisted_5, _toDisplayString(card.label), 1),
                    (card.sub)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_6, _toDisplayString(card.sub), 1))
                      : _createCommentVNode("", true)
                  ])
                ]),
                _: 2
              }, 1024)
            ]),
            _: 2
          }, 1024))
        }), 128))
      ]),
      _: 1
    }),
    _createVNode(_component_v_row, { align: "stretch" }, {
      default: _withCtx(() => [
        _createVNode(_component_v_col, {
          cols: "12",
          md: "7"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: "glass-card fill-height",
              elevation: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "d-flex align-center flex-wrap ga-2" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "primary",
                      size: "22",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => _cache[8] || (_cache[8] = [
                        _createTextVNode("mdi-image-search")
                      ])),
                      _: 1,
                      __: [8]
                    }),
                    _cache[14] || (_cache[14] = _createElementVNode("span", null, "图片预览", -1)),
                    _createVNode(_component_v_spacer),
                    _createElementVNode("div", _hoisted_7, [
                      (_openBlock(), _createElementBlock(_Fragment, null, _renderList(previewTypes, (t) => {
                        return _createElementVNode("button", {
                          key: t.key,
                          class: _normalizeClass(['mode-btn', previewType.value === t.key ? 'mode-btn-active' : '']),
                          onClick: $event => (switchPreviewType(t.key))
                        }, [
                          _createVNode(_component_v_icon, {
                            size: "15",
                            class: "mode-icon"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(t.icon), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createElementVNode("span", _hoisted_9, _toDisplayString(t.label), 1)
                        ], 10, _hoisted_8)
                      }), 64)),
                      _cache[13] || (_cache[13] = _createElementVNode("div", { class: "mode-separator" }, null, -1)),
                      _createElementVNode("button", {
                        class: "mode-btn",
                        onClick: loadPreview,
                        disabled: previewLoading.value
                      }, [
                        _createVNode(_component_v_icon, {
                          size: "15",
                          class: _normalizeClass(["mode-icon", { rotating: previewLoading.value }])
                        }, {
                          default: _withCtx(() => _cache[9] || (_cache[9] = [
                            _createTextVNode("mdi-refresh")
                          ])),
                          _: 1,
                          __: [9]
                        }, 8, ["class"]),
                        _cache[10] || (_cache[10] = _createElementVNode("span", { class: "mode-text" }, "换一张", -1))
                      ], 8, _hoisted_10),
                      _createElementVNode("button", {
                        class: "mode-btn",
                        onClick: savePreviewToLocal,
                        disabled: !previewImageUrl.value || savingToLocal.value
                      }, [
                        _createVNode(_component_v_icon, {
                          size: "15",
                          class: "mode-icon"
                        }, {
                          default: _withCtx(() => _cache[11] || (_cache[11] = [
                            _createTextVNode("mdi-folder-download")
                          ])),
                          _: 1,
                          __: [11]
                        }),
                        _cache[12] || (_cache[12] = _createElementVNode("span", { class: "mode-text" }, "收藏", -1))
                      ], 8, _hoisted_11)
                    ])
                  ]),
                  _: 1,
                  __: [14]
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_12, [
                      (previewLoading.value && !previewImageUrl.value)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_13, [
                            _createVNode(_component_v_progress_circular, {
                              indeterminate: "",
                              color: "primary",
                              size: "56"
                            }),
                            _cache[15] || (_cache[15] = _createElementVNode("div", { class: "mt-3 text-medium-emphasis" }, "正在加载图片...", -1))
                          ]))
                        : (previewError.value)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_14, [
                              _createVNode(_component_v_icon, {
                                color: "error",
                                size: "56"
                              }, {
                                default: _withCtx(() => _cache[16] || (_cache[16] = [
                                  _createTextVNode("mdi-image-broken")
                                ])),
                                _: 1,
                                __: [16]
                              }),
                              _createElementVNode("div", _hoisted_15, _toDisplayString(previewError.value), 1),
                              _createVNode(_component_v_btn, {
                                color: "primary",
                                variant: "tonal",
                                class: "mt-3",
                                onClick: loadPreview
                              }, {
                                default: _withCtx(() => _cache[17] || (_cache[17] = [
                                  _createTextVNode("重试")
                                ])),
                                _: 1,
                                __: [17]
                              })
                            ]))
                          : (previewImageUrl.value)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
                                _createElementVNode("img", {
                                  src: previewImageUrl.value,
                                  class: "preview-image",
                                  alt: "随机图片预览",
                                  onError: handlePreviewError
                                }, null, 40, _hoisted_17)
                              ]))
                            : (_openBlock(), _createElementBlock("div", _hoisted_18, [
                                _createVNode(_component_v_icon, {
                                  color: "grey",
                                  size: "56"
                                }, {
                                  default: _withCtx(() => _cache[18] || (_cache[18] = [
                                    _createTextVNode("mdi-image")
                                  ])),
                                  _: 1,
                                  __: [18]
                                }),
                                _cache[19] || (_cache[19] = _createElementVNode("div", { class: "mt-3 text-medium-emphasis" }, "暂无预览", -1))
                              ]))
                    ])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "12",
          md: "5"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: "glass-card mb-4",
              elevation: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "info",
                      size: "22",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => _cache[20] || (_cache[20] = [
                        _createTextVNode("mdi-heart-pulse")
                      ])),
                      _: 1,
                      __: [20]
                    }),
                    _cache[23] || (_cache[23] = _createElementVNode("span", null, "运行状态", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      size: "x-small",
                      variant: "text",
                      color: "info",
                      loading: pinging.value,
                      onClick: runPing
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "14",
                          class: "mr-1"
                        }, {
                          default: _withCtx(() => _cache[21] || (_cache[21] = [
                            _createTextVNode("mdi-speedometer")
                          ])),
                          _: 1,
                          __: [21]
                        }),
                        _cache[22] || (_cache[22] = _createTextVNode(" 测速 "))
                      ]),
                      _: 1,
                      __: [22]
                    }, 8, ["loading"])
                  ]),
                  _: 1,
                  __: [23]
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_19, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(sourceMonitorItems.value, (s) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: s.key,
                          class: "source-item"
                        }, [
                          _createElementVNode("div", _hoisted_20, [
                            _createVNode(_component_v_icon, {
                              size: "15",
                              color: s.configured ? 'success' : 'grey'
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(s.icon), 1)
                              ]),
                              _: 2
                            }, 1032, ["color"]),
                            _createElementVNode("span", null, _toDisplayString(s.label), 1)
                          ]),
                          _createElementVNode("span", _hoisted_21, _toDisplayString(s.count), 1),
                          _createVNode(_component_v_chip, {
                            color: s.configured ? 'success' : 'grey',
                            size: "x-small",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(s.configured ? '已配置' : '未配置'), 1)
                            ]),
                            _: 2
                          }, 1032, ["color"])
                        ]))
                      }), 128))
                    ]),
                    (pingResults.value)
                      ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                          _createVNode(_component_v_divider, { class: "my-3" }),
                          _createElementVNode("div", _hoisted_22, [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(pingResults.value, (r, key) => {
                              return (_openBlock(), _createBlock(_component_v_chip, {
                                key: key,
                                size: "small",
                                color: !r.configured ? 'grey' : r.ok ? 'success' : 'error',
                                variant: "tonal"
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "13",
                                    class: "mr-1"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(!r.configured ? 'mdi-minus' : r.ok ? 'mdi-check' : 'mdi-close'), 1)
                                    ]),
                                    _: 2
                                  }, 1024),
                                  _createTextVNode(" " + _toDisplayString(r.label) + " ", 1),
                                  (r.configured && r.ok)
                                    ? (_openBlock(), _createElementBlock("span", _hoisted_23, _toDisplayString(r.ms) + "ms", 1))
                                    : (r.configured)
                                      ? (_openBlock(), _createElementBlock("span", _hoisted_24, "失败"))
                                      : (_openBlock(), _createElementBlock("span", _hoisted_25, "未配置"))
                                ]),
                                _: 2
                              }, 1032, ["color"]))
                            }), 128))
                          ])
                        ], 64))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card, {
              class: "glass-card",
              elevation: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "warning",
                      size: "22",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => _cache[24] || (_cache[24] = [
                        _createTextVNode("mdi-cloud-download")
                      ])),
                      _: 1,
                      __: [24]
                    }),
                    _cache[25] || (_cache[25] = _createElementVNode("span", null, "网络图片下载", -1))
                  ]),
                  _: 1,
                  __: [25]
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_26, [
                      _createVNode(_component_v_text_field, {
                        modelValue: downloadCount.value,
                        "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((downloadCount).value = $event)),
                        type: "number",
                        min: "1",
                        max: "500",
                        density: "compact",
                        "hide-details": "",
                        label: "数量",
                        style: {"max-width":"96px"}
                      }, null, 8, ["modelValue"]),
                      _createVNode(_component_v_select, {
                        modelValue: downloadSource.value,
                        "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((downloadSource).value = $event)),
                        items: downloadSources,
                        density: "compact",
                        "hide-details": "",
                        label: "来源",
                        style: {"max-width":"130px"}
                      }, null, 8, ["modelValue"]),
                      _createVNode(_component_v_btn, {
                        color: "primary",
                        variant: "tonal",
                        disabled: downloadStatus.running,
                        onClick: startDownload
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            size: "16",
                            class: "mr-1"
                          }, {
                            default: _withCtx(() => _cache[26] || (_cache[26] = [
                              _createTextVNode("mdi-play")
                            ])),
                            _: 1,
                            __: [26]
                          }),
                          _cache[27] || (_cache[27] = _createTextVNode(" 立即下载 "))
                        ]),
                        _: 1,
                        __: [27]
                      }, 8, ["disabled"])
                    ]),
                    (downloadStatus.running || downloadStatus.total)
                      ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                          _createElementVNode("div", _hoisted_27, [
                            _createTextVNode(_toDisplayString(downloadStatus.message || '下载任务') + " ", 1),
                            (downloadStatus.total)
                              ? (_openBlock(), _createElementBlock("span", _hoisted_28, " （" + _toDisplayString(downloadStatus.done) + "/" + _toDisplayString(downloadStatus.total) + "） ", 1))
                              : _createCommentVNode("", true)
                          ]),
                          _createVNode(_component_v_progress_linear, {
                            "model-value": downloadProgress.value,
                            color: "primary",
                            height: "8",
                            rounded: "",
                            class: "mb-2"
                          }, null, 8, ["model-value"]),
                          _createElementVNode("div", _hoisted_29, [
                            _createElementVNode("span", _hoisted_30, "成功 " + _toDisplayString(downloadStatus.success || 0), 1),
                            _createElementVNode("span", _hoisted_31, "横屏 " + _toDisplayString(downloadStatus.pc_saved || 0), 1),
                            _createElementVNode("span", _hoisted_32, "竖屏 " + _toDisplayString(downloadStatus.mobile_saved || 0), 1),
                            _createElementVNode("span", _hoisted_33, "跳过 " + _toDisplayString(downloadStatus.skipped || 0), 1),
                            _createElementVNode("span", _hoisted_34, "失败 " + _toDisplayString(downloadStatus.failed || 0), 1)
                          ])
                        ], 64))
                      : (_openBlock(), _createElementBlock("div", _hoisted_35, " 从配置的网络图源批量下载图片，自动按横竖屏分类保存到本地目录。 "))
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_card, {
      class: "glass-card mt-4",
      elevation: "4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              color: "warning",
              size: "22",
              class: "mr-1"
            }, {
              default: _withCtx(() => _cache[28] || (_cache[28] = [
                _createTextVNode("mdi-chart-areaspline")
              ])),
              _: 1,
              __: [28]
            }),
            _cache[31] || (_cache[31] = _createElementVNode("span", null, "访问统计", -1)),
            _cache[32] || (_cache[32] = _createElementVNode("span", { class: "text-caption text-medium-emphasis ml-2" }, "近 7 天 API 调用趋势与最近访问记录", -1)),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              size: "small",
              variant: "text",
              loading: visitsLoading.value,
              onClick: loadVisits
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  size: "16",
                  class: "mr-1"
                }, {
                  default: _withCtx(() => _cache[29] || (_cache[29] = [
                    _createTextVNode("mdi-refresh")
                  ])),
                  _: 1,
                  __: [29]
                }),
                _cache[30] || (_cache[30] = _createTextVNode(" 刷新 "))
              ]),
              _: 1,
              __: [30]
            }, 8, ["loading"])
          ]),
          _: 1,
          __: [31,32]
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_36, [
              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(visitDaily.value, (day) => {
                return (_openBlock(), _createElementBlock("div", {
                  key: day.date,
                  class: "trend-col",
                  title: `${day.label}：${day.count} 次`
                }, [
                  _createElementVNode("span", _hoisted_38, _toDisplayString(day.count), 1),
                  _createElementVNode("div", _hoisted_39, [
                    _createElementVNode("div", {
                      class: _normalizeClass(["trend-bar", { 'trend-bar-empty': day.count === 0 }]),
                      style: _normalizeStyle({ height: trendBarHeight(day.count) })
                    }, null, 6)
                  ]),
                  _createElementVNode("span", _hoisted_40, _toDisplayString(day.label), 1)
                ], 8, _hoisted_37))
              }), 128))
            ]),
            (visitRecent.value.length)
              ? (_openBlock(), _createBlock(_component_v_divider, {
                  key: 0,
                  class: "my-3"
                }))
              : _createCommentVNode("", true),
            (visitRecent.value.length)
              ? (_openBlock(), _createElementBlock("div", _hoisted_41, [
                  _cache[33] || (_cache[33] = _createElementVNode("div", { class: "visit-row visit-row-head" }, [
                    _createElementVNode("span", null, "时间"),
                    _createElementVNode("span", null, "接口"),
                    _createElementVNode("span", null, "类型"),
                    _createElementVNode("span", null, "来源"),
                    _createElementVNode("span", null, "耗时"),
                    _createElementVNode("span", null, "结果")
                  ], -1)),
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(visitRecent.value.slice(0, 12), (v, idx) => {
                    return (_openBlock(), _createElementBlock("div", {
                      key: idx,
                      class: "visit-row"
                    }, [
                      _createElementVNode("span", _hoisted_42, _toDisplayString(v.time), 1),
                      _createElementVNode("span", null, _toDisplayString(endpointLabel(v.endpoint)), 1),
                      _createElementVNode("span", null, _toDisplayString(typeLabel(v.type)), 1),
                      _createElementVNode("span", null, _toDisplayString(sourceDisplay(v)), 1),
                      _createElementVNode("span", null, _toDisplayString(v.elapsed_ms) + "ms", 1),
                      _createElementVNode("span", null, [
                        _createVNode(_component_v_icon, {
                          size: "14",
                          color: v.ok ? 'success' : 'error'
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(v.ok ? 'mdi-check-circle' : 'mdi-close-circle'), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"])
                      ])
                    ]))
                  }), 128))
                ]))
              : (_openBlock(), _createElementBlock("div", _hoisted_43, " 暂无调用记录，等待 API 被访问后展示 "))
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_card, {
      class: "glass-card mt-4",
      elevation: "4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "d-flex align-center flex-wrap ga-2" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              color: "success",
              size: "22",
              class: "mr-1"
            }, {
              default: _withCtx(() => _cache[34] || (_cache[34] = [
                _createTextVNode("mdi-api")
              ])),
              _: 1,
              __: [34]
            }),
            _cache[36] || (_cache[36] = _createElementVNode("span", null, "API 接口", -1)),
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(apiHealthItems.value, (ep) => {
              return (_openBlock(), _createBlock(_component_v_chip, {
                key: ep.key,
                color: ep.available ? 'success' : 'grey',
                size: "x-small",
                variant: "tonal"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_icon, {
                    size: "12",
                    class: "mr-1"
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode(_toDisplayString(ep.icon), 1)
                    ]),
                    _: 2
                  }, 1024),
                  _createTextVNode(" " + _toDisplayString(ep.label), 1)
                ]),
                _: 2
              }, 1032, ["color"]))
            }), 128)),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              size: "small",
              variant: "text",
              "append-icon": showExamples.value ? 'mdi-chevron-up' : 'mdi-chevron-down',
              onClick: _cache[2] || (_cache[2] = $event => (showExamples.value = !showExamples.value))
            }, {
              default: _withCtx(() => _cache[35] || (_cache[35] = [
                _createTextVNode(" 使用示例 ")
              ])),
              _: 1,
              __: [35]
            }, 8, ["append-icon"])
          ]),
          _: 1,
          __: [36]
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_row, { dense: "" }, {
              default: _withCtx(() => [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(apiEndpoints.value, (ep) => {
                  return (_openBlock(), _createBlock(_component_v_col, {
                    cols: "12",
                    md: "6",
                    key: ep.url
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_44, [
                        _createVNode(_component_v_icon, {
                          color: ep.color,
                          size: "20",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(ep.icon), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"]),
                        _createElementVNode("div", _hoisted_45, [
                          _createElementVNode("div", _hoisted_46, _toDisplayString(ep.title), 1),
                          _createElementVNode("div", _hoisted_47, _toDisplayString(ep.url), 1)
                        ]),
                        _createVNode(_component_v_btn, {
                          icon: "",
                          size: "small",
                          variant: "text",
                          onClick: $event => (copyToClipboard(ep.url))
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, { size: "16" }, {
                              default: _withCtx(() => _cache[37] || (_cache[37] = [
                                _createTextVNode("mdi-content-copy")
                              ])),
                              _: 1,
                              __: [37]
                            }),
                            _createVNode(_component_v_tooltip, {
                              activator: "parent",
                              location: "top"
                            }, {
                              default: _withCtx(() => _cache[38] || (_cache[38] = [
                                _createTextVNode("复制链接")
                              ])),
                              _: 1,
                              __: [38]
                            })
                          ]),
                          _: 2
                        }, 1032, ["onClick"])
                      ])
                    ]),
                    _: 2
                  }, 1024))
                }), 128))
              ]),
              _: 1
            }),
            _createVNode(_component_v_expand_transition, null, {
              default: _withCtx(() => [
                (showExamples.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_48, [
                      _createVNode(_component_v_divider, { class: "my-2" }),
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(usageExamples.value, (ex) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: ex.title,
                          class: "example-item"
                        }, [
                          _createElementVNode("div", _hoisted_49, [
                            _createVNode(_component_v_icon, {
                              size: "15",
                              color: "primary",
                              class: "mr-1"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(ex.icon), 1)
                              ]),
                              _: 2
                            }, 1024),
                            _createElementVNode("span", _hoisted_50, _toDisplayString(ex.title), 1),
                            _createVNode(_component_v_spacer),
                            _createVNode(_component_v_btn, {
                              icon: "",
                              size: "x-small",
                              variant: "text",
                              onClick: $event => (copyToClipboard(ex.code))
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, { size: "14" }, {
                                  default: _withCtx(() => _cache[39] || (_cache[39] = [
                                    _createTextVNode("mdi-content-copy")
                                  ])),
                                  _: 1,
                                  __: [39]
                                })
                              ]),
                              _: 2
                            }, 1032, ["onClick"])
                          ]),
                          _createElementVNode("pre", _hoisted_51, _toDisplayString(ex.code), 1)
                        ]))
                      }), 128))
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_snackbar, {
      modelValue: snackbar.visible,
      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((snackbar.visible) = $event)),
      color: snackbar.color,
      timeout: "2500",
      location: "top"
    }, {
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(snackbar.text), 1)
      ]),
      _: 1
    }, 8, ["modelValue", "color"])
  ]))
}
}

};
const AppPage = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-bdb2a0d8"]]);

export { AppPage as default };
