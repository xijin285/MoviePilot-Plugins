import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Page_vue_vue_type_style_index_0_scoped_d4114a08_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,normalizeClass:_normalizeClass,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,Transition:_Transition,mergeProps:_mergeProps,renderList:_renderList,Fragment:_Fragment,createBlock:_createBlock} = await importShared('vue');


const _hoisted_1 = { class: "title-actions" };
const _hoisted_2 = { class: "toast-text" };
const _hoisted_3 = { class: "preview-title-left" };
const _hoisted_4 = { class: "preview-title-right" };
const _hoisted_5 = { class: "preview-mode-selector" };
const _hoisted_6 = ["disabled"];
const _hoisted_7 = ["disabled"];
const _hoisted_8 = ["disabled"];
const _hoisted_9 = { class: "preview-download-item-icon" };
const _hoisted_10 = { class: "preview-download-item-icon" };
const _hoisted_11 = { class: "preview-container" };
const _hoisted_12 = {
  key: 0,
  class: "preview-loading"
};
const _hoisted_13 = {
  key: 1,
  class: "preview-error"
};
const _hoisted_14 = { class: "mt-4 text-error" };
const _hoisted_15 = {
  key: 2,
  class: "preview-image-container"
};
const _hoisted_16 = ["src", "alt"];
const _hoisted_17 = {
  key: 1,
  class: "preview-placeholder"
};
const _hoisted_18 = ["disabled"];
const _hoisted_19 = { class: "api-runtime-row" };
const _hoisted_20 = { class: "api-health-grid" };
const _hoisted_21 = { class: "api-health-name" };
const _hoisted_22 = { class: "source-monitor-grid" };
const _hoisted_23 = { class: "source-monitor-name" };
const _hoisted_24 = { class: "source-complete-row" };
const _hoisted_25 = { class: "stats-grid" };
const _hoisted_26 = { class: "stat-item" };
const _hoisted_27 = { class: "stat-number" };
const _hoisted_28 = { class: "stat-item" };
const _hoisted_29 = { class: "stat-number" };
const _hoisted_30 = { class: "stat-item" };
const _hoisted_31 = { class: "stat-number" };
const _hoisted_32 = { class: "stat-item" };
const _hoisted_33 = {
  class: "stat-number",
  style: {"color":"#ff9800"}
};
const _hoisted_34 = { class: "api-section" };
const _hoisted_35 = { class: "api-endpoint-card" };
const _hoisted_36 = { class: "api-endpoint-header" };
const _hoisted_37 = { class: "api-endpoint-icon" };
const _hoisted_38 = { class: "api-url-container" };
const _hoisted_39 = { class: "api-url" };
const _hoisted_40 = { class: "api-endpoint-card" };
const _hoisted_41 = { class: "api-endpoint-header" };
const _hoisted_42 = { class: "api-endpoint-icon" };
const _hoisted_43 = { class: "api-url-container" };
const _hoisted_44 = { class: "api-url" };
const _hoisted_45 = { class: "api-endpoint-card" };
const _hoisted_46 = { class: "api-endpoint-header" };
const _hoisted_47 = { class: "api-endpoint-icon" };
const _hoisted_48 = { class: "api-url-container" };
const _hoisted_49 = { class: "api-url" };
const _hoisted_50 = { class: "api-endpoint-card" };
const _hoisted_51 = { class: "api-endpoint-header" };
const _hoisted_52 = { class: "api-endpoint-icon" };
const _hoisted_53 = { class: "api-url-container" };
const _hoisted_54 = { class: "api-url" };

const {ref,reactive,onMounted,onUnmounted,computed} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, required: true }
},
  emits: ['close', 'switch'],
  setup(__props) {

const props = __props;



// 响应式数据
const status = reactive({
  enable: false,
  api_status: "disabled",
  api_endpoints: {
    auto: false,
    pc: false,
    mobile: false,
    stats: false,
  },
  pc_path: "",
  mobile_path: "",
  pc_count: 0,
  mobile_count: 0,
  total_count: 0,
  today_visits: 0,
  network_image_url_pc: "",
  network_image_url_mobile: "",
  network_image_url: "",
});

// 新增：详细统计
const statusDetail = ref({
  local: { pc: 0, mobile: 0 },
  network: { pc: 0, mobile: 0 }
});

const apiHealthItems = computed(() => [
  {
    key: 'auto',
    label: '自动识别',
    icon: 'mdi-auto-fix',
    available: Boolean(status.api_endpoints?.auto),
  },
  {
    key: 'pc',
    label: '横屏图片',
    icon: 'mdi-monitor',
    available: Boolean(status.api_endpoints?.pc),
  },
  {
    key: 'mobile',
    label: '竖屏图片',
    icon: 'mdi-cellphone',
    available: Boolean(status.api_endpoints?.mobile),
  },
  {
    key: 'stats',
    label: '统计数据',
    icon: 'mdi-chart-box-outline',
    available: Boolean(status.api_endpoints?.stats),
  },
]);

const sourceMonitorItems = computed(() => {
  const commonNetworkConfigured = Boolean(status.network_image_url);
  return [
    {
      key: 'local-pc',
      label: '本地横屏',
      icon: 'mdi-monitor',
      configured: Boolean(status.pc_path),
      custom: Boolean(status.pc_path_custom),
    },
    {
      key: 'local-mobile',
      label: '本地竖屏',
      icon: 'mdi-cellphone',
      configured: Boolean(status.mobile_path),
      custom: Boolean(status.mobile_path_custom),
    },
    {
      key: 'network-pc',
      label: '网络横屏',
      icon: 'mdi-cloud-outline',
      configured: Boolean(status.network_image_url_pc || commonNetworkConfigured),
    },
    {
      key: 'network-mobile',
      label: '网络竖屏',
      icon: 'mdi-cloud-outline',
      configured: Boolean(status.network_image_url_mobile || commonNetworkConfigured),
    },
  ];
});

const sourceBadgeText = (source) => {
  if (source.custom !== undefined) {
    if (!source.configured) return '未配置';
    return source.custom ? '自定义' : '默认';
  }
  return source.configured ? '已配置' : '未配置';
};

const sourceBadgeColor = (source) => {
  if (source.custom !== undefined) {
    if (!source.configured) return 'grey';
    return source.custom ? 'warning' : 'success';
  }
  return source.configured ? 'success' : 'grey';
};

const sourceConfigComplete = computed(() => {
  const pcConfigured = Boolean(
    status.pc_path || status.network_image_url_pc || status.network_image_url,
  );
  const mobileConfigured = Boolean(
    status.mobile_path || status.network_image_url_mobile || status.network_image_url,
  );
  return pcConfigured && mobileConfigured;
});

const previewType = ref('auto');
const previewImageUrl = ref('');
const previewObjectUrl = ref('');
const previewLoading = ref(false);
const previewError = ref('');

const refreshing = ref(false);

// 悬浮通知状态（标题栏下方，3秒自动消失）
const notificationVisible = ref(false);
const notificationText = ref('');
const notificationType = ref('success');
let notificationTimer = null;

const showNotification = (text, type = 'success') => {
  notificationText.value = text;
  notificationType.value = type;
  notificationVisible.value = true;
  // 重置计时器，避免连续提示时提前隐藏
  if (notificationTimer) {
    clearTimeout(notificationTimer);
  }
  notificationTimer = setTimeout(() => {
    notificationVisible.value = false;
    notificationTimer = null;
  }, 3000);
};

const getApiUrl = (endpoint) => {
  return `${window.location.origin}/api/v1/plugin/RandomPic${endpoint}`;
};

const refreshStatus = async () => {
  refreshing.value = true;
  try {
    const statusData = await props.api.get('plugin/RandomPic/status');
    Object.assign(status, statusData);
    if (statusData.detail) {
      statusDetail.value = statusData.detail;
    }
    showNotification('状态已刷新', 'success');
  } catch (error) {
    showNotification('刷新状态失败', 'error');
  } finally {
    refreshing.value = false;
  }
};

const loadPreview = async () => {
  if (!status.enable) {
    previewError.value = '插件未启用';
    previewLoading.value = false;
    return;
  }
  previewLoading.value = true;
  previewError.value = '';
  try {
    const params = previewType.value === 'auto' ? {} : { type: previewType.value };
    const image = await props.api.get('plugin/RandomPic/preview', {
      params: { ...params, t: Date.now() },
      responseType: 'blob',
    });
    if (previewObjectUrl.value) {
      URL.revokeObjectURL(previewObjectUrl.value);
    }
    previewObjectUrl.value = URL.createObjectURL(image);
    previewImageUrl.value = previewObjectUrl.value;
  } catch (error) {
    previewError.value = error?.response?.data?.detail || '加载预览失败';
    showNotification(previewError.value, 'error');
  } finally {
    previewLoading.value = false;
  }
};

const handlePreviewError = () => {
  previewLoading.value = false;
  previewError.value = '图片加载失败';
};

const switchPreviewType = (type) => {
  if (previewType.value === type) {
    // 如果点击的是当前已选中的类型，则刷新图片
    loadPreview();
  } else {
    // 如果点击的是不同的类型，则切换类型并自动刷新
    previewType.value = type;
    loadPreview();
  }
};

const savingToLocal = ref(false);

const savePreviewToLocal = async () => {
  if (!previewObjectUrl.value) {
    showNotification('没有可保存的预览图片', 'error');
    return;
  }
  savingToLocal.value = true;
  try {
    const blob = await fetch(previewObjectUrl.value).then((res) => res.blob());
    const formData = new FormData();
    formData.append('file', blob, 'preview-image.jpg');
    const result = await props.api.post('plugin/RandomPic/preview/save', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    showNotification(result?.msg || '已保存到本地目录', result?.success === false ? 'error' : 'success');
  } catch (error) {
    showNotification('保存到本地目录失败', 'error');
  } finally {
    savingToLocal.value = false;
  }
};

const downloadPreview = () => {
  // 直接取页面上 img 的 src，保证和显示一致
  const img = document.querySelector('.preview-image');
  if (!img || !img.src) return;
  const link = document.createElement('a');
  link.href = img.src;
  link.download = `random-image-${Date.now()}.jpg`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showNotification('图片下载已开始', 'success');
};

const openPreviewInNewTab = () => {
  const img = document.querySelector('.preview-image');
  if (!img || !img.src) return;
  window.open(img.src, '_blank');
};

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    showNotification('链接已复制到剪贴板', 'success');
  } catch (err) {
    // 降级方案：使用传统的复制方法
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showNotification('链接已复制到剪贴板', 'success');
  }
};

// 生命周期
onMounted(async () => {
  await refreshStatus();
  loadPreview();
});

onUnmounted(() => {
  if (previewObjectUrl.value) {
    URL.revokeObjectURL(previewObjectUrl.value);
  }
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_list_item_subtitle = _resolveComponent("v-list-item-subtitle");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_menu = _resolveComponent("v-menu");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_divider = _resolveComponent("v-divider");

  return (_openBlock(), _createBlock(_component_v_card, {
    flat: "",
    class: "gallery-page"
  }, {
    default: _withCtx(() => [
      _createVNode(_component_v_card_title, { class: "section-title d-flex align-center mb-4" }, {
        default: _withCtx(() => [
          _createVNode(_component_v_icon, {
            class: "mr-2",
            color: "primary",
            size: "28"
          }, {
            default: _withCtx(() => _cache[10] || (_cache[10] = [
              _createTextVNode("mdi-image-multiple")
            ])),
            _: 1,
            __: [10]
          }),
          _cache[15] || (_cache[15] = _createElementVNode("span", { class: "text-h5 font-weight-bold" }, "随机图库状态", -1)),
          _createVNode(_component_v_spacer),
          _createElementVNode("div", _hoisted_1, [
            _createVNode(_component_v_btn, {
              class: "btn-gradient-status",
              size: "small",
              onClick: _cache[0] || (_cache[0] = $event => (_ctx.$emit('switch')))
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, { class: "btn-icon" }, {
                  default: _withCtx(() => _cache[11] || (_cache[11] = [
                    _createTextVNode("mdi-cog")
                  ])),
                  _: 1,
                  __: [11]
                }),
                _cache[12] || (_cache[12] = _createElementVNode("span", { class: "btn-text" }, "插件配置", -1))
              ]),
              _: 1,
              __: [12]
            }),
            _createVNode(_component_v_btn, {
              class: "btn-gradient-close",
              size: "small",
              onClick: _cache[1] || (_cache[1] = $event => (_ctx.$emit('close')))
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, { class: "btn-icon" }, {
                  default: _withCtx(() => _cache[13] || (_cache[13] = [
                    _createTextVNode("mdi-close")
                  ])),
                  _: 1,
                  __: [13]
                }),
                _cache[14] || (_cache[14] = _createElementVNode("span", { class: "btn-text" }, "关闭", -1))
              ]),
              _: 1,
              __: [14]
            })
          ])
        ]),
        _: 1,
        __: [15]
      }),
      _createVNode(_Transition, { name: "toast-fade" }, {
        default: _withCtx(() => [
          (notificationVisible.value)
            ? (_openBlock(), _createElementBlock("div", {
                key: 0,
                class: _normalizeClass(["toast-toast", notificationType.value === 'error' ? 'toast-error' : 'toast-success'])
              }, [
                _createVNode(_component_v_icon, {
                  size: "16",
                  class: "toast-icon"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(notificationType.value === 'error' ? 'mdi-alert-circle' : 'mdi-check-circle'), 1)
                  ]),
                  _: 1
                }),
                _createElementVNode("span", _hoisted_2, _toDisplayString(notificationText.value), 1)
              ], 2))
            : _createCommentVNode("", true)
        ]),
        _: 1
      }),
      _createVNode(_component_v_row, {
        class: "main-content",
        align: "stretch"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_col, {
            cols: "12",
            md: "8",
            class: "preview-column"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_card, {
                class: "glass-card preview-card",
                elevation: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card_title, { class: "preview-title-container" }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_3, [
                        _createVNode(_component_v_icon, {
                          color: "primary",
                          size: "24",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[16] || (_cache[16] = [
                            _createTextVNode("mdi-image-search")
                          ])),
                          _: 1,
                          __: [16]
                        }),
                        _cache[17] || (_cache[17] = _createElementVNode("span", null, "图片预览", -1))
                      ]),
                      _createElementVNode("div", _hoisted_4, [
                        _createElementVNode("div", _hoisted_5, [
                          _createElementVNode("button", {
                            class: _normalizeClass(['mode-btn', previewType.value === 'pc' ? 'mode-btn-active' : '']),
                            onClick: _cache[2] || (_cache[2] = $event => (switchPreviewType('pc')))
                          }, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              class: "mode-icon"
                            }, {
                              default: _withCtx(() => _cache[18] || (_cache[18] = [
                                _createTextVNode("mdi-monitor")
                              ])),
                              _: 1,
                              __: [18]
                            }),
                            _cache[19] || (_cache[19] = _createElementVNode("span", { class: "mode-text" }, "横屏", -1))
                          ], 2),
                          _createElementVNode("button", {
                            class: _normalizeClass(['mode-btn', previewType.value === 'mobile' ? 'mode-btn-active' : '']),
                            onClick: _cache[3] || (_cache[3] = $event => (switchPreviewType('mobile')))
                          }, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              class: "mode-icon"
                            }, {
                              default: _withCtx(() => _cache[20] || (_cache[20] = [
                                _createTextVNode("mdi-cellphone")
                              ])),
                              _: 1,
                              __: [20]
                            }),
                            _cache[21] || (_cache[21] = _createElementVNode("span", { class: "mode-text" }, "竖屏", -1))
                          ], 2),
                          _createElementVNode("button", {
                            class: _normalizeClass(['mode-btn', previewType.value === 'auto' ? 'mode-btn-active' : '']),
                            onClick: _cache[4] || (_cache[4] = $event => (switchPreviewType('auto')))
                          }, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              class: "mode-icon"
                            }, {
                              default: _withCtx(() => _cache[22] || (_cache[22] = [
                                _createTextVNode("mdi-auto-fix")
                              ])),
                              _: 1,
                              __: [22]
                            }),
                            _cache[23] || (_cache[23] = _createElementVNode("span", { class: "mode-text" }, "自动", -1))
                          ], 2),
                          _cache[41] || (_cache[41] = _createElementVNode("div", { class: "mode-separator" }, null, -1)),
                          _createElementVNode("button", {
                            class: "mode-btn mode-btn-refresh",
                            onClick: loadPreview,
                            disabled: previewLoading.value
                          }, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              class: _normalizeClass(["mode-icon", { 'rotating': previewLoading.value }])
                            }, {
                              default: _withCtx(() => _cache[24] || (_cache[24] = [
                                _createTextVNode("mdi-refresh")
                              ])),
                              _: 1,
                              __: [24]
                            }, 8, ["class"]),
                            _cache[25] || (_cache[25] = _createElementVNode("span", { class: "mode-text" }, "刷新", -1))
                          ], 8, _hoisted_6),
                          _createElementVNode("button", {
                            class: "mode-btn",
                            onClick: openPreviewInNewTab,
                            disabled: !previewImageUrl.value || previewLoading.value
                          }, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              class: "mode-icon"
                            }, {
                              default: _withCtx(() => _cache[26] || (_cache[26] = [
                                _createTextVNode("mdi-open-in-new")
                              ])),
                              _: 1,
                              __: [26]
                            }),
                            _cache[27] || (_cache[27] = _createElementVNode("span", { class: "mode-text" }, "打开", -1))
                          ], 8, _hoisted_7),
                          _createVNode(_component_v_menu, {
                            location: "bottom end",
                            disabled: !previewImageUrl.value || previewLoading.value
                          }, {
                            activator: _withCtx(({ props: menuProps }) => [
                              _createElementVNode("button", _mergeProps({ class: "mode-btn" }, menuProps, {
                                disabled: !previewImageUrl.value || previewLoading.value
                              }), [
                                _createVNode(_component_v_icon, {
                                  size: "16",
                                  class: "mode-icon"
                                }, {
                                  default: _withCtx(() => _cache[28] || (_cache[28] = [
                                    _createTextVNode("mdi-download")
                                  ])),
                                  _: 1,
                                  __: [28]
                                }),
                                _cache[30] || (_cache[30] = _createElementVNode("span", { class: "mode-text" }, "下载", -1)),
                                _createVNode(_component_v_icon, {
                                  size: "14",
                                  class: "mode-icon"
                                }, {
                                  default: _withCtx(() => _cache[29] || (_cache[29] = [
                                    _createTextVNode("mdi-menu-down")
                                  ])),
                                  _: 1,
                                  __: [29]
                                })
                              ], 16, _hoisted_8)
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list, {
                                density: "compact",
                                class: "preview-download-menu"
                              }, {
                                default: _withCtx(() => [
                                  _cache[39] || (_cache[39] = _createElementVNode("div", { class: "preview-download-menu-title" }, "下载方式", -1)),
                                  _createVNode(_component_v_list_item, {
                                    class: "preview-download-item",
                                    onClick: savePreviewToLocal,
                                    disabled: savingToLocal.value
                                  }, {
                                    prepend: _withCtx(() => [
                                      _createElementVNode("div", _hoisted_9, [
                                        _createVNode(_component_v_icon, { size: "18" }, {
                                          default: _withCtx(() => _cache[31] || (_cache[31] = [
                                            _createTextVNode("mdi-folder-download")
                                          ])),
                                          _: 1,
                                          __: [31]
                                        })
                                      ])
                                    ]),
                                    append: _withCtx(() => [
                                      _createVNode(_component_v_icon, {
                                        size: "16",
                                        class: "preview-download-item-arrow"
                                      }, {
                                        default: _withCtx(() => _cache[34] || (_cache[34] = [
                                          _createTextVNode("mdi-chevron-right")
                                        ])),
                                        _: 1,
                                        __: [34]
                                      })
                                    ]),
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_list_item_title, null, {
                                        default: _withCtx(() => _cache[32] || (_cache[32] = [
                                          _createTextVNode("保存到本地目录")
                                        ])),
                                        _: 1,
                                        __: [32]
                                      }),
                                      _createVNode(_component_v_list_item_subtitle, null, {
                                        default: _withCtx(() => _cache[33] || (_cache[33] = [
                                          _createTextVNode("自动按横屏/竖屏分类")
                                        ])),
                                        _: 1,
                                        __: [33]
                                      })
                                    ]),
                                    _: 1
                                  }, 8, ["disabled"]),
                                  _cache[40] || (_cache[40] = _createElementVNode("div", { class: "preview-download-menu-divider" }, null, -1)),
                                  _createVNode(_component_v_list_item, {
                                    class: "preview-download-item",
                                    onClick: downloadPreview
                                  }, {
                                    prepend: _withCtx(() => [
                                      _createElementVNode("div", _hoisted_10, [
                                        _createVNode(_component_v_icon, { size: "18" }, {
                                          default: _withCtx(() => _cache[35] || (_cache[35] = [
                                            _createTextVNode("mdi-download-box")
                                          ])),
                                          _: 1,
                                          __: [35]
                                        })
                                      ])
                                    ]),
                                    append: _withCtx(() => [
                                      _createVNode(_component_v_icon, {
                                        size: "16",
                                        class: "preview-download-item-arrow"
                                      }, {
                                        default: _withCtx(() => _cache[38] || (_cache[38] = [
                                          _createTextVNode("mdi-chevron-right")
                                        ])),
                                        _: 1,
                                        __: [38]
                                      })
                                    ]),
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_list_item_title, null, {
                                        default: _withCtx(() => _cache[36] || (_cache[36] = [
                                          _createTextVNode("下载到本机")
                                        ])),
                                        _: 1,
                                        __: [36]
                                      }),
                                      _createVNode(_component_v_list_item_subtitle, null, {
                                        default: _withCtx(() => _cache[37] || (_cache[37] = [
                                          _createTextVNode("保存到浏览器默认下载目录")
                                        ])),
                                        _: 1,
                                        __: [37]
                                      })
                                    ]),
                                    _: 1
                                  })
                                ]),
                                _: 1,
                                __: [39,40]
                              })
                            ]),
                            _: 1
                          }, 8, ["disabled"])
                        ])
                      ])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_card_text, null, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_11, [
                        (previewLoading.value && !previewImageUrl.value)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_12, [
                              _createVNode(_component_v_progress_circular, {
                                indeterminate: "",
                                color: "primary",
                                size: "64"
                              }),
                              _cache[42] || (_cache[42] = _createElementVNode("div", { class: "mt-4" }, "正在加载图片...", -1))
                            ]))
                          : (previewError.value)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_13, [
                                _createVNode(_component_v_icon, {
                                  color: "error",
                                  size: "64"
                                }, {
                                  default: _withCtx(() => _cache[43] || (_cache[43] = [
                                    _createTextVNode("mdi-image-broken")
                                  ])),
                                  _: 1,
                                  __: [43]
                                }),
                                _createElementVNode("div", _hoisted_14, _toDisplayString(previewError.value), 1),
                                _createVNode(_component_v_btn, {
                                  color: "primary",
                                  onClick: loadPreview,
                                  class: "mt-4"
                                }, {
                                  default: _withCtx(() => _cache[44] || (_cache[44] = [
                                    _createTextVNode("重试")
                                  ])),
                                  _: 1,
                                  __: [44]
                                })
                              ]))
                            : (_openBlock(), _createElementBlock("div", _hoisted_15, [
                                (previewImageUrl.value)
                                  ? (_openBlock(), _createElementBlock("img", {
                                      key: 0,
                                      src: previewImageUrl.value,
                                      alt: '随机图片预览 - ' + previewType.value,
                                      class: "preview-image",
                                      onLoad: _cache[5] || (_cache[5] = $event => (previewLoading.value = false)),
                                      onError: handlePreviewError
                                    }, null, 40, _hoisted_16))
                                  : (_openBlock(), _createElementBlock("div", _hoisted_17, [
                                      _createVNode(_component_v_icon, {
                                        color: "grey",
                                        size: "64"
                                      }, {
                                        default: _withCtx(() => _cache[45] || (_cache[45] = [
                                          _createTextVNode("mdi-image")
                                        ])),
                                        _: 1,
                                        __: [45]
                                      }),
                                      _cache[46] || (_cache[46] = _createElementVNode("div", { class: "mt-4 text-grey" }, "点击下方按钮预览图片", -1))
                                    ]))
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
            md: "4",
            class: "status-column"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_row, {
                class: "status-cards-vertical",
                dense: ""
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card, {
                        class: "glass-card",
                        elevation: "4",
                        style: {"height":"189px !important","min-height":"189px !important"}
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                color: status.enable ? 'success' : 'grey',
                                size: "24",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(status.enable ? 'mdi-api' : 'mdi-api-off'), 1)
                                ]),
                                _: 1
                              }, 8, ["color"]),
                              _cache[48] || (_cache[48] = _createElementVNode("span", null, "API 状态", -1)),
                              _createVNode(_component_v_spacer),
                              _createElementVNode("button", {
                                class: "mode-btn status-refresh-btn",
                                onClick: refreshStatus,
                                disabled: refreshing.value
                              }, [
                                _createVNode(_component_v_icon, {
                                  size: "16",
                                  class: _normalizeClass(["mode-icon", { 'rotating': refreshing.value }])
                                }, {
                                  default: _withCtx(() => _cache[47] || (_cache[47] = [
                                    _createTextVNode("mdi-refresh")
                                  ])),
                                  _: 1,
                                  __: [47]
                                }, 8, ["class"])
                              ], 8, _hoisted_18)
                            ]),
                            _: 1,
                            __: [48]
                          }),
                          _createVNode(_component_v_card_text, null, {
                            default: _withCtx(() => [
                              _createElementVNode("div", _hoisted_19, [
                                _cache[49] || (_cache[49] = _createElementVNode("span", { class: "label" }, "运行状态：", -1)),
                                _createVNode(_component_v_chip, {
                                  color: status.enable ? 'success' : 'grey',
                                  size: "small"
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(status.enable ? '可用' : '已禁用'), 1)
                                  ]),
                                  _: 1
                                }, 8, ["color"])
                              ]),
                              _createElementVNode("div", _hoisted_20, [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(apiHealthItems.value, (endpoint) => {
                                  return (_openBlock(), _createElementBlock("div", {
                                    key: endpoint.key,
                                    class: "api-health-item"
                                  }, [
                                    _createElementVNode("div", _hoisted_21, [
                                      _createVNode(_component_v_icon, {
                                        size: "16",
                                        color: endpoint.available ? 'success' : 'grey'
                                      }, {
                                        default: _withCtx(() => [
                                          _createTextVNode(_toDisplayString(endpoint.icon), 1)
                                        ]),
                                        _: 2
                                      }, 1032, ["color"]),
                                      _createElementVNode("span", null, _toDisplayString(endpoint.label), 1)
                                    ]),
                                    _createVNode(_component_v_chip, {
                                      color: endpoint.available ? 'success' : 'grey',
                                      size: "x-small"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(endpoint.available ? '正常' : '不可用'), 1)
                                      ]),
                                      _: 2
                                    }, 1032, ["color"])
                                  ]))
                                }), 128))
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
                  _createVNode(_component_v_col, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card, {
                        class: "glass-card",
                        elevation: "4",
                        style: {"height":"189px !important","min-height":"189px !important"}
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                color: "info",
                                size: "24",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => _cache[50] || (_cache[50] = [
                                  _createTextVNode("mdi-folder-check")
                                ])),
                                _: 1,
                                __: [50]
                              }),
                              _cache[51] || (_cache[51] = _createElementVNode("span", null, "目录监控", -1))
                            ]),
                            _: 1,
                            __: [51]
                          }),
                          _createVNode(_component_v_card_text, null, {
                            default: _withCtx(() => [
                              _createElementVNode("div", _hoisted_22, [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(sourceMonitorItems.value, (source) => {
                                  return (_openBlock(), _createElementBlock("div", {
                                    key: source.key,
                                    class: "source-monitor-item"
                                  }, [
                                    _createElementVNode("div", _hoisted_23, [
                                      _createVNode(_component_v_icon, {
                                        size: "15",
                                        color: source.configured ? 'success' : 'grey'
                                      }, {
                                        default: _withCtx(() => [
                                          _createTextVNode(_toDisplayString(source.icon), 1)
                                        ]),
                                        _: 2
                                      }, 1032, ["color"]),
                                      _createElementVNode("span", null, _toDisplayString(source.label), 1)
                                    ]),
                                    _createVNode(_component_v_chip, {
                                      color: sourceBadgeColor(source),
                                      size: "x-small"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(sourceBadgeText(source)), 1)
                                      ]),
                                      _: 2
                                    }, 1032, ["color"])
                                  ]))
                                }), 128))
                              ]),
                              _createElementVNode("div", _hoisted_24, [
                                _cache[52] || (_cache[52] = _createElementVNode("span", { class: "label" }, "配置完整性：", -1)),
                                _createVNode(_component_v_chip, {
                                  color: sourceConfigComplete.value ? 'success' : 'warning',
                                  size: "small"
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(sourceConfigComplete.value ? '完整' : '不完整'), 1)
                                  ]),
                                  _: 1
                                }, 8, ["color"])
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
                  _createVNode(_component_v_col, { cols: "12" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card, {
                        class: "glass-card",
                        elevation: "4",
                        style: {"height":"190px !important","min-height":"190px !important"}
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                color: "info",
                                size: "24",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => _cache[53] || (_cache[53] = [
                                  _createTextVNode("mdi-image")
                                ])),
                                _: 1,
                                __: [53]
                              }),
                              _cache[54] || (_cache[54] = _createElementVNode("span", null, "图片统计", -1))
                            ]),
                            _: 1,
                            __: [54]
                          }),
                          _createVNode(_component_v_card_text, null, {
                            default: _withCtx(() => [
                              _createElementVNode("div", _hoisted_25, [
                                _createElementVNode("div", _hoisted_26, [
                                  _createElementVNode("div", _hoisted_27, _toDisplayString(status.total_count || 0), 1),
                                  _cache[55] || (_cache[55] = _createElementVNode("div", { class: "stat-label" }, "总图片数", -1))
                                ]),
                                _createElementVNode("div", _hoisted_28, [
                                  _createElementVNode("div", _hoisted_29, _toDisplayString(status.pc_count || 0), 1),
                                  _cache[56] || (_cache[56] = _createElementVNode("div", { class: "stat-label" }, "横屏图片", -1))
                                ]),
                                _createElementVNode("div", _hoisted_30, [
                                  _createElementVNode("div", _hoisted_31, _toDisplayString(status.mobile_count || 0), 1),
                                  _cache[57] || (_cache[57] = _createElementVNode("div", { class: "stat-label" }, "竖屏图片", -1))
                                ]),
                                _createElementVNode("div", _hoisted_32, [
                                  _createElementVNode("div", _hoisted_33, _toDisplayString(status.today_visits), 1),
                                  _cache[58] || (_cache[58] = _createElementVNode("div", { class: "stat-label" }, "今日访问", -1))
                                ])
                              ])
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
              })
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createElementVNode("div", _hoisted_34, [
        _createVNode(_component_v_card, {
          class: "glass-card",
          elevation: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: "success",
                  size: "24",
                  class: "mr-2"
                }, {
                  default: _withCtx(() => _cache[59] || (_cache[59] = [
                    _createTextVNode("mdi-api")
                  ])),
                  _: 1,
                  __: [59]
                }),
                _cache[60] || (_cache[60] = _createElementVNode("span", null, "API 接口", -1))
              ]),
              _: 1,
              __: [60]
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_row, { class: "api-endpoint-grid" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "6",
                      md: "3"
                    }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_35, [
                          _createElementVNode("div", _hoisted_36, [
                            _createElementVNode("div", _hoisted_37, [
                              _createVNode(_component_v_icon, {
                                color: "primary",
                                size: "24"
                              }, {
                                default: _withCtx(() => _cache[61] || (_cache[61] = [
                                  _createTextVNode("mdi-web")
                                ])),
                                _: 1,
                                __: [61]
                              })
                            ]),
                            _cache[62] || (_cache[62] = _createElementVNode("div", { class: "api-endpoint-info" }, [
                              _createElementVNode("h3", { class: "api-endpoint-title" }, "自动识别设备"),
                              _createElementVNode("p", { class: "api-endpoint-desc" }, "根据设备类型自动返回横屏或竖屏图片")
                            ], -1))
                          ]),
                          _createElementVNode("div", _hoisted_38, [
                            _createElementVNode("div", _hoisted_39, _toDisplayString(getApiUrl('/random')), 1),
                            _createElementVNode("button", {
                              class: "api-copy-btn",
                              onClick: _cache[6] || (_cache[6] = $event => (copyToClipboard(getApiUrl('/random')))),
                              title: "复制链接"
                            }, [
                              _createVNode(_component_v_icon, { size: "16" }, {
                                default: _withCtx(() => _cache[63] || (_cache[63] = [
                                  _createTextVNode("mdi-content-copy")
                                ])),
                                _: 1,
                                __: [63]
                              })
                            ])
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "6",
                      md: "3"
                    }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_40, [
                          _createElementVNode("div", _hoisted_41, [
                            _createElementVNode("div", _hoisted_42, [
                              _createVNode(_component_v_icon, {
                                color: "success",
                                size: "24"
                              }, {
                                default: _withCtx(() => _cache[64] || (_cache[64] = [
                                  _createTextVNode("mdi-monitor")
                                ])),
                                _: 1,
                                __: [64]
                              })
                            ]),
                            _cache[65] || (_cache[65] = _createElementVNode("div", { class: "api-endpoint-info" }, [
                              _createElementVNode("h3", { class: "api-endpoint-title" }, "指定横屏图片"),
                              _createElementVNode("p", { class: "api-endpoint-desc" }, "强制返回横屏图片")
                            ], -1))
                          ]),
                          _createElementVNode("div", _hoisted_43, [
                            _createElementVNode("div", _hoisted_44, _toDisplayString(getApiUrl('/random?type=pc')), 1),
                            _createElementVNode("button", {
                              class: "api-copy-btn",
                              onClick: _cache[7] || (_cache[7] = $event => (copyToClipboard(getApiUrl('/random?type=pc')))),
                              title: "复制链接"
                            }, [
                              _createVNode(_component_v_icon, { size: "16" }, {
                                default: _withCtx(() => _cache[66] || (_cache[66] = [
                                  _createTextVNode("mdi-content-copy")
                                ])),
                                _: 1,
                                __: [66]
                              })
                            ])
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "6",
                      md: "3"
                    }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_45, [
                          _createElementVNode("div", _hoisted_46, [
                            _createElementVNode("div", _hoisted_47, [
                              _createVNode(_component_v_icon, {
                                color: "warning",
                                size: "24"
                              }, {
                                default: _withCtx(() => _cache[67] || (_cache[67] = [
                                  _createTextVNode("mdi-cellphone")
                                ])),
                                _: 1,
                                __: [67]
                              })
                            ]),
                            _cache[68] || (_cache[68] = _createElementVNode("div", { class: "api-endpoint-info" }, [
                              _createElementVNode("h3", { class: "api-endpoint-title" }, "指定竖屏图片"),
                              _createElementVNode("p", { class: "api-endpoint-desc" }, "强制返回竖屏图片")
                            ], -1))
                          ]),
                          _createElementVNode("div", _hoisted_48, [
                            _createElementVNode("div", _hoisted_49, _toDisplayString(getApiUrl('/random?type=mobile')), 1),
                            _createElementVNode("button", {
                              class: "api-copy-btn",
                              onClick: _cache[8] || (_cache[8] = $event => (copyToClipboard(getApiUrl('/random?type=mobile')))),
                              title: "复制链接"
                            }, [
                              _createVNode(_component_v_icon, { size: "16" }, {
                                default: _withCtx(() => _cache[69] || (_cache[69] = [
                                  _createTextVNode("mdi-content-copy")
                                ])),
                                _: 1,
                                __: [69]
                              })
                            ])
                          ])
                        ])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "6",
                      md: "3"
                    }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_50, [
                          _createElementVNode("div", _hoisted_51, [
                            _createElementVNode("div", _hoisted_52, [
                              _createVNode(_component_v_icon, {
                                color: "info",
                                size: "24"
                              }, {
                                default: _withCtx(() => _cache[70] || (_cache[70] = [
                                  _createTextVNode("mdi-chart-bar")
                                ])),
                                _: 1,
                                __: [70]
                              })
                            ]),
                            _cache[71] || (_cache[71] = _createElementVNode("div", { class: "api-endpoint-info" }, [
                              _createElementVNode("h3", { class: "api-endpoint-title" }, "统计数据"),
                              _createElementVNode("p", { class: "api-endpoint-desc" }, "获取图片数量和访问统计")
                            ], -1))
                          ]),
                          _createElementVNode("div", _hoisted_53, [
                            _createElementVNode("div", _hoisted_54, _toDisplayString(getApiUrl('/stats')), 1),
                            _createElementVNode("button", {
                              class: "api-copy-btn",
                              onClick: _cache[9] || (_cache[9] = $event => (copyToClipboard(getApiUrl('/stats')))),
                              title: "复制链接"
                            }, [
                              _createVNode(_component_v_icon, { size: "16" }, {
                                default: _withCtx(() => _cache[72] || (_cache[72] = [
                                  _createTextVNode("mdi-content-copy")
                                ])),
                                _: 1,
                                __: [72]
                              })
                            ])
                          ])
                        ])
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
        })
      ]),
      _createVNode(_component_v_divider)
    ]),
    _: 1
  }))
}
}

};
const PageComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-d4114a08"]]);

export { PageComponent as default };
