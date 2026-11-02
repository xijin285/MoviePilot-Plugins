import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Config_vue_vue_type_style_index_0_scoped_438c2f5f_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,vModelCheckbox:_vModelCheckbox,withDirectives:_withDirectives,openBlock:_openBlock,createElementBlock:_createElementBlock,toDisplayString:_toDisplayString,normalizeClass:_normalizeClass,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment} = await importShared('vue');


const _hoisted_1 = { class: "plugin-config" };
const _hoisted_2 = { class: "config-wrapper" };
const _hoisted_3 = { class: "title-bar" };
const _hoisted_4 = { class: "title-left" };
const _hoisted_5 = { class: "title-right" };
const _hoisted_6 = { class: "title-actions" };
const _hoisted_7 = { class: "config-body" };
const _hoisted_8 = { class: "mp-card config-section basic-settings" };
const _hoisted_9 = { class: "section-title" };
const _hoisted_10 = { class: "card-inner" };
const _hoisted_11 = { class: "config-switch-row" };
const _hoisted_12 = { class: "switch" };
const _hoisted_13 = { class: "mp-card config-section local-directory-settings" };
const _hoisted_14 = { class: "section-title" };
const _hoisted_15 = { class: "card-inner" };
const _hoisted_16 = { class: "directory-card pc-directory" };
const _hoisted_17 = { class: "directory-header" };
const _hoisted_18 = { class: "directory-card mobile-directory" };
const _hoisted_19 = { class: "directory-header" };
const _hoisted_20 = { class: "mp-card config-section network-directory-settings" };
const _hoisted_21 = { class: "section-title" };
const _hoisted_22 = { class: "card-inner" };
const _hoisted_23 = { class: "directory-card pc-directory" };
const _hoisted_24 = { class: "directory-header" };
const _hoisted_25 = { class: "directory-card mobile-directory" };
const _hoisted_26 = { class: "directory-header" };
const _hoisted_27 = { class: "mp-card config-section download-manage-settings" };
const _hoisted_28 = { class: "section-title" };
const _hoisted_29 = { class: "card-inner" };
const _hoisted_30 = { class: "download-progress-text" };
const _hoisted_31 = {
  key: 0,
  class: "text-center py-6 text-grey"
};
const _hoisted_32 = {
  key: 1,
  class: "candidate-grid"
};
const _hoisted_33 = ["onClick"];
const _hoisted_34 = ["src", "alt", "onError"];
const _hoisted_35 = { class: "candidate-check" };

const {ref,reactive,computed,onMounted,onUnmounted} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, required: true },
  initialConfig: { type: Object, default: () => ({}) }
},
  emits: ['close', 'switch', 'save', 'config-updated-on-server'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

// 响应式数据
const config = reactive({
  enable: false,
  pc_path: "",
  mobile_path: "",
  network_image_url_pc: "",
  network_image_url_mobile: "",
  network_image_url: "", // 兼容老配置
  download_count: 20,
});

// 默认本地目录（来自后端，用于空值占位提示）
const defaultPcPath = ref("");
const defaultMobilePath = ref("");

const saving = ref(false);

const successMessage = ref(null);
const errorMessage = ref(null);

// 下载管理
const downloadSource = ref('both');
const downloadSourceOptions = [
  { title: '横屏+竖屏（Auto）', value: 'both' },
  { title: '仅横屏源（PC）', value: 'pc' },
  { title: '仅竖屏源（Mobile）', value: 'mobile' },
];
const downloadRunning = ref(false);
const downloadStatus = ref(null);
let downloadPollTimer = null;

// 候选图片预览选择
const candidateDialog = ref(false);
const candidateLoading = ref(false);
const candidateItems = ref([]);

const selectedCount = computed(() => candidateItems.value.filter((item) => item.selected).length);
const allSelected = computed(
  () => candidateItems.value.length > 0 && selectedCount.value === candidateItems.value.length,
);

const downloadStatusText = computed(() => {
  if (downloadRunning.value) return '下载中...';
  if (!downloadStatus.value) return '尚未开始';
  const s = downloadStatus.value;
  if (s.running) return `下载中 ${s.done}/${s.total}`;
  return s.total > 0 ? '下载完成' : '无下载记录';
});

const downloadStatusColor = computed(() => {
  if (downloadRunning.value || downloadStatus.value?.running) return 'text-warning';
  if (downloadStatus.value?.total > 0) return 'text-success';
  return 'text-grey';
});

const downloadProgressText = computed(() => {
  const s = downloadStatus.value;
  if (!s || s.total === 0) return '';
  const pct = s.total > 0 ? Math.round((s.done / s.total) * 100) : 0;
  return `进度 ${pct}% | 完成 ${s.done}/${s.total} | 成功 ${s.success} | 横屏 ${s.pc_saved || 0} | 竖屏 ${s.mobile_saved || 0} | 失败 ${s.failed} | 跳过 ${s.skipped}`;
});

const loadCandidates = async () => {
  if (!config.enable) {
    showNotification('请先启用插件', 'error');
    return;
  }
  candidateLoading.value = true;
  try {
    const result = await props.api.get('plugin/RandomPic/download/candidates', {
      params: {
        source: downloadSource.value,
        count: Number(config.download_count) || 30,
      },
    });
    const urls = result?.data?.urls || [];
    candidateItems.value = urls.map((url) => ({ url, selected: true }));
    candidateDialog.value = true;
    if (urls.length === 0) {
      showNotification('未获取到候选图片，请检查网络源配置', 'error');
    }
  } catch (error) {
    showNotification('获取候选图片失败', 'error');
  } finally {
    candidateLoading.value = false;
  }
};

const toggleCandidate = (index) => {
  const item = candidateItems.value[index];
  if (item) {
    item.selected = !item.selected;
  }
};

const toggleAllCandidates = () => {
  const next = !allSelected.value;
  candidateItems.value.forEach((item) => {
    item.selected = next;
  });
};

const invertCandidates = () => {
  candidateItems.value.forEach((item) => {
    item.selected = !item.selected;
  });
};

const handleImageError = (index) => {
  const item = candidateItems.value[index];
  if (item) {
    item.url = '';
  }
};

const confirmDownload = async () => {
  const urls = candidateItems.value.filter((item) => item.selected && item.url).map((item) => item.url);
  if (urls.length === 0) {
    showNotification('未选择可用的图片地址', 'error');
    return;
  }
  downloadRunning.value = true;
  try {
    const result = await props.api.post('plugin/RandomPic/download', { urls });
    if (result && result.msg) {
      showNotification(result.msg, 'success');
    }
    candidateDialog.value = false;
    pollDownloadStatus();
  } catch (error) {
    downloadRunning.value = false;
    showNotification('启动下载失败', 'error');
  }
};

const pollDownloadStatus = async () => {
  stopPollDownloadStatus();
  downloadPollTimer = setInterval(async () => {
    try {
      const status = await props.api.get('plugin/RandomPic/download/status');
      downloadStatus.value = status || null;
      if (!status || !status.running) {
        downloadRunning.value = false;
        stopPollDownloadStatus();
      }
    } catch (error) {
      downloadRunning.value = false;
      stopPollDownloadStatus();
    }
  }, 2000);
};

const stopPollDownloadStatus = () => {
  if (downloadPollTimer) {
    clearInterval(downloadPollTimer);
    downloadPollTimer = null;
  }
};

const isConfigValid = () => {
  if (!config.enable) return true;
  const hasPc = (config.pc_path || defaultPcPath.value) || config.network_image_url_pc;
  const hasMobile = (config.mobile_path || defaultMobilePath.value) || config.network_image_url_mobile;
  return Boolean(hasPc && hasMobile);
};

// 方法
const showNotification = (text, type = 'success') => {
  if (type === 'success') {
    successMessage.value = text;
    errorMessage.value = null;
  } else {
    errorMessage.value = text;
    successMessage.value = null;
  }
  // 3秒后自动清除消息
  setTimeout(() => {
    successMessage.value = null;
    errorMessage.value = null;
  }, 3000);
};

const resetConfig = () => {
  Object.assign(config, {
    enable: false,
    pc_path: "",
    mobile_path: "",
    network_image_url_pc: "",
    network_image_url_mobile: "",
    network_image_url: "",
    download_count: 20,
  });
  showNotification('配置已重置', 'success');
};

const saveConfig = async () => {
  if (!isConfigValid()) {
    showNotification('请完善配置信息', 'error');
    return;
  }

  saving.value = true;
  try {
    const payload = {
      enable: config.enable,
      pc_path: config.pc_path,
      mobile_path: config.mobile_path,
      network_image_url_pc: config.network_image_url_pc,
      network_image_url_mobile: config.network_image_url_mobile,
      network_image_url: config.network_image_url,
      download_count: config.download_count,
    };
    await props.api.post('plugin/RandomPic/config', payload);
    showNotification('配置保存成功', 'success');
    emit('save', JSON.parse(JSON.stringify(payload)));
    emit('config-updated-on-server', payload);
  } catch (error) {
    showNotification('配置保存失败', 'error');
  } finally {
    saving.value = false;
  }
};

// 生命周期
onMounted(() => {
  if (props.initialConfig) {
    Object.assign(config, props.initialConfig);
    defaultPcPath.value = props.initialConfig.default_pc_path || "";
    defaultMobilePath.value = props.initialConfig.default_mobile_path || "";
  }
  if (config.enable) {
    pollDownloadStatus();
  }
});

onUnmounted(() => {
  stopPollDownloadStatus();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_dialog = _resolveComponent("v-dialog");
  const _component_v_alert = _resolveComponent("v-alert");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "rounded border"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_2, [
              _createElementVNode("div", _hoisted_3, [
                _createElementVNode("div", _hoisted_4, [
                  _createVNode(_component_v_icon, {
                    size: "28",
                    color: "primary",
                    class: "mr-2"
                  }, {
                    default: _withCtx(() => _cache[12] || (_cache[12] = [
                      _createTextVNode("mdi-cog")
                    ])),
                    _: 1,
                    __: [12]
                  }),
                  _cache[13] || (_cache[13] = _createElementVNode("div", { class: "title-texts" }, [
                    _createElementVNode("div", { class: "title-main" }, "图库配置"),
                    _createElementVNode("div", { class: "title-sub" }, "配置您的随机图片服务")
                  ], -1))
                ]),
                _createElementVNode("div", _hoisted_5, [
                  _createElementVNode("div", _hoisted_6, [
                    _createVNode(_component_v_btn, {
                      class: "btn-gradient-status",
                      onClick: _cache[0] || (_cache[0] = $event => (_ctx.$emit('switch'))),
                      disabled: saving.value,
                      size: "small"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, { class: "btn-icon" }, {
                          default: _withCtx(() => _cache[14] || (_cache[14] = [
                            _createTextVNode("mdi-view-dashboard")
                          ])),
                          _: 1,
                          __: [14]
                        }),
                        _cache[15] || (_cache[15] = _createElementVNode("span", { class: "btn-text" }, "状态页", -1))
                      ]),
                      _: 1,
                      __: [15]
                    }, 8, ["disabled"]),
                    _createVNode(_component_v_btn, {
                      class: "btn-gradient-reset",
                      onClick: resetConfig,
                      disabled: saving.value,
                      size: "small"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, { class: "btn-icon" }, {
                          default: _withCtx(() => _cache[16] || (_cache[16] = [
                            _createTextVNode("mdi-restore")
                          ])),
                          _: 1,
                          __: [16]
                        }),
                        _cache[17] || (_cache[17] = _createElementVNode("span", { class: "btn-text" }, "重置", -1))
                      ]),
                      _: 1,
                      __: [17]
                    }, 8, ["disabled"]),
                    _createVNode(_component_v_btn, {
                      class: "btn-gradient-save",
                      disabled: !isConfigValid() || saving.value,
                      onClick: saveConfig,
                      loading: saving.value,
                      size: "small"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, { class: "btn-icon" }, {
                          default: _withCtx(() => _cache[18] || (_cache[18] = [
                            _createTextVNode("mdi-content-save")
                          ])),
                          _: 1,
                          __: [18]
                        }),
                        _cache[19] || (_cache[19] = _createElementVNode("span", { class: "btn-text" }, "保存配置", -1))
                      ]),
                      _: 1,
                      __: [19]
                    }, 8, ["disabled", "loading"]),
                    _createVNode(_component_v_btn, {
                      class: "btn-gradient-close",
                      onClick: _cache[1] || (_cache[1] = $event => (_ctx.$emit('close'))),
                      disabled: saving.value,
                      size: "small"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, { class: "btn-icon" }, {
                          default: _withCtx(() => _cache[20] || (_cache[20] = [
                            _createTextVNode("mdi-close")
                          ])),
                          _: 1,
                          __: [20]
                        }),
                        _cache[21] || (_cache[21] = _createElementVNode("span", { class: "btn-text" }, "关闭", -1))
                      ]),
                      _: 1,
                      __: [21]
                    }, 8, ["disabled"])
                  ])
                ])
              ]),
              _createElementVNode("div", _hoisted_7, [
                _createElementVNode("div", _hoisted_8, [
                  _cache[28] || (_cache[28] = _createElementVNode("div", { class: "card-overlay" }, null, -1)),
                  _createElementVNode("div", _hoisted_9, [
                    _createVNode(_component_v_icon, {
                      class: "mr-2",
                      color: "primary"
                    }, {
                      default: _withCtx(() => _cache[22] || (_cache[22] = [
                        _createTextVNode("mdi-tune")
                      ])),
                      _: 1,
                      __: [22]
                    }),
                    _cache[23] || (_cache[23] = _createTextVNode(" 基本设置 "))
                  ]),
                  _createElementVNode("div", _hoisted_10, [
                    _createVNode(_component_v_card_text, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, { dense: "" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_11, [
                                  _createVNode(_component_v_icon, {
                                    size: "18",
                                    class: "switch-icon",
                                    color: config.enable ? 'success' : 'grey'
                                  }, {
                                    default: _withCtx(() => _cache[24] || (_cache[24] = [
                                      _createTextVNode("mdi-power")
                                    ])),
                                    _: 1,
                                    __: [24]
                                  }, 8, ["color"]),
                                  _cache[26] || (_cache[26] = _createElementVNode("span", { class: "switch-label" }, "启用插件", -1)),
                                  _createElementVNode("label", _hoisted_12, [
                                    _withDirectives(_createElementVNode("input", {
                                      type: "checkbox",
                                      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.enable) = $event))
                                    }, null, 512), [
                                      [_vModelCheckbox, config.enable]
                                    ]),
                                    _cache[25] || (_cache[25] = _createElementVNode("div", { class: "slider" }, [
                                      _createElementVNode("div", { class: "circle" }, [
                                        _createElementVNode("svg", {
                                          class: "cross",
                                          viewBox: "0 0 365.696 365.696",
                                          height: "6",
                                          width: "6",
                                          xmlns: "http://www.w3.org/2000/svg"
                                        }, [
                                          _createElementVNode("path", {
                                            fill: "currentColor",
                                            d: "M243.188 182.86 356.32 69.726c12.5-12.5 12.5-32.766 0-45.247L341.238 9.398c-12.504-12.503-32.77-12.503-45.25 0L182.86 122.528 69.727 9.374c-12.5-12.5-32.766-12.5-45.247 0L9.375 24.457c-12.5 12.504-12.5 32.77 0 45.25l113.152 113.152L9.398 295.99c-12.503 12.503-12.503 32.769 0 45.25L24.48 356.32c12.5 12.5 32.766 12.5 45.247 0l113.132-113.132L295.99 356.32c12.503 12.5 32.769 12.5 45.25 0l15.081-15.082c12.5-12.504 12.5-32.77 0-45.25zm0 0"
                                          })
                                        ]),
                                        _createElementVNode("svg", {
                                          class: "checkmark",
                                          viewBox: "0 0 24 24",
                                          height: "10",
                                          width: "10",
                                          xmlns: "http://www.w3.org/2000/svg"
                                        }, [
                                          _createElementVNode("path", {
                                            fill: "currentColor",
                                            d: "M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z"
                                          })
                                        ])
                                      ])
                                    ], -1))
                                  ]),
                                  _cache[27] || (_cache[27] = _createElementVNode("span", { class: "service-mode-hint" }, "API 由当前插件直接提供", -1))
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
                  ])
                ]),
                _createElementVNode("div", _hoisted_13, [
                  _cache[37] || (_cache[37] = _createElementVNode("div", { class: "card-overlay" }, null, -1)),
                  _createElementVNode("div", _hoisted_14, [
                    _createVNode(_component_v_icon, {
                      class: "mr-2",
                      color: "info"
                    }, {
                      default: _withCtx(() => _cache[29] || (_cache[29] = [
                        _createTextVNode("mdi-folder-multiple-image")
                      ])),
                      _: 1,
                      __: [29]
                    }),
                    _cache[30] || (_cache[30] = _createTextVNode(" 本地目录配置 "))
                  ]),
                  _createElementVNode("div", _hoisted_15, [
                    _createVNode(_component_v_card_text, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, {
                          dense: "",
                          class: "mb-4"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_16, [
                                  _createElementVNode("div", _hoisted_17, [
                                    _createVNode(_component_v_icon, {
                                      color: "primary",
                                      size: "24",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[31] || (_cache[31] = [
                                        _createTextVNode("mdi-monitor")
                                      ])),
                                      _: 1,
                                      __: [31]
                                    }),
                                    _cache[33] || (_cache[33] = _createElementVNode("span", { class: "directory-title" }, "横屏本地图片目录", -1)),
                                    _createVNode(_component_v_chip, {
                                      color: "primary",
                                      size: "small",
                                      class: "ml-2"
                                    }, {
                                      default: _withCtx(() => _cache[32] || (_cache[32] = [
                                        _createTextVNode("PC/横屏")
                                      ])),
                                      _: 1,
                                      __: [32]
                                    })
                                  ]),
                                  _createVNode(_component_v_text_field, {
                                    modelValue: config.pc_path,
                                    "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.pc_path) = $event)),
                                    label: "横屏图片路径",
                                    placeholder: defaultPcPath.value || '/path/pc/images',
                                    "prepend-inner-icon": "mdi-folder",
                                    hint: "留空时使用默认目录",
                                    "persistent-hint": "",
                                    dense: ""
                                  }, null, 8, ["modelValue", "placeholder"])
                                ])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_row, { dense: "" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_18, [
                                  _createElementVNode("div", _hoisted_19, [
                                    _createVNode(_component_v_icon, {
                                      color: "success",
                                      size: "24",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[34] || (_cache[34] = [
                                        _createTextVNode("mdi-cellphone")
                                      ])),
                                      _: 1,
                                      __: [34]
                                    }),
                                    _cache[36] || (_cache[36] = _createElementVNode("span", { class: "directory-title" }, "竖屏本地图片目录", -1)),
                                    _createVNode(_component_v_chip, {
                                      color: "success",
                                      size: "small",
                                      class: "ml-2"
                                    }, {
                                      default: _withCtx(() => _cache[35] || (_cache[35] = [
                                        _createTextVNode("Mobile/竖屏")
                                      ])),
                                      _: 1,
                                      __: [35]
                                    })
                                  ]),
                                  _createVNode(_component_v_text_field, {
                                    modelValue: config.mobile_path,
                                    "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.mobile_path) = $event)),
                                    label: "竖屏图片路径",
                                    placeholder: defaultMobilePath.value || '/path/mobile/images',
                                    "prepend-inner-icon": "mdi-folder",
                                    hint: "留空时使用默认目录",
                                    "persistent-hint": "",
                                    dense: ""
                                  }, null, 8, ["modelValue", "placeholder"])
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
                  ])
                ]),
                _createElementVNode("div", _hoisted_20, [
                  _cache[46] || (_cache[46] = _createElementVNode("div", { class: "card-overlay" }, null, -1)),
                  _createElementVNode("div", _hoisted_21, [
                    _createVNode(_component_v_icon, {
                      class: "mr-2",
                      color: "primary"
                    }, {
                      default: _withCtx(() => _cache[38] || (_cache[38] = [
                        _createTextVNode("mdi-link-variant")
                      ])),
                      _: 1,
                      __: [38]
                    }),
                    _cache[39] || (_cache[39] = _createTextVNode(" 网络目录配置 "))
                  ]),
                  _createElementVNode("div", _hoisted_22, [
                    _createVNode(_component_v_card_text, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_row, {
                          dense: "",
                          class: "mb-4"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_23, [
                                  _createElementVNode("div", _hoisted_24, [
                                    _createVNode(_component_v_icon, {
                                      color: "primary",
                                      size: "24",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[40] || (_cache[40] = [
                                        _createTextVNode("mdi-monitor")
                                      ])),
                                      _: 1,
                                      __: [40]
                                    }),
                                    _cache[42] || (_cache[42] = _createElementVNode("span", { class: "directory-title" }, "横屏网络图片地址", -1)),
                                    _createVNode(_component_v_chip, {
                                      color: "primary",
                                      size: "small",
                                      class: "ml-2"
                                    }, {
                                      default: _withCtx(() => _cache[41] || (_cache[41] = [
                                        _createTextVNode("PC/横屏")
                                      ])),
                                      _: 1,
                                      __: [41]
                                    })
                                  ]),
                                  _createVNode(_component_v_text_field, {
                                    modelValue: config.network_image_url_pc,
                                    "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.network_image_url_pc) = $event)),
                                    label: "横屏网络图片地址",
                                    placeholder: "https://example.com/your-pc-image.jpg，支持多个逗号分隔",
                                    "prepend-inner-icon": "mdi-link",
                                    hint: "支持图片直链、API、json/txt等，多个用英文逗号分隔，优先级高于本地横屏目录",
                                    "persistent-hint": "",
                                    dense: ""
                                  }, null, 8, ["modelValue"])
                                ])
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_row, { dense: "" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_25, [
                                  _createElementVNode("div", _hoisted_26, [
                                    _createVNode(_component_v_icon, {
                                      color: "success",
                                      size: "24",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[43] || (_cache[43] = [
                                        _createTextVNode("mdi-cellphone-link")
                                      ])),
                                      _: 1,
                                      __: [43]
                                    }),
                                    _cache[45] || (_cache[45] = _createElementVNode("span", { class: "directory-title" }, "竖屏网络图片地址", -1)),
                                    _createVNode(_component_v_chip, {
                                      color: "success",
                                      size: "small",
                                      class: "ml-2"
                                    }, {
                                      default: _withCtx(() => _cache[44] || (_cache[44] = [
                                        _createTextVNode("Mobile/竖屏")
                                      ])),
                                      _: 1,
                                      __: [44]
                                    })
                                  ]),
                                  _createVNode(_component_v_text_field, {
                                    modelValue: config.network_image_url_mobile,
                                    "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.network_image_url_mobile) = $event)),
                                    label: "竖屏网络图片地址",
                                    placeholder: "https://example.com/your-mobile-image.jpg，支持多个逗号分隔",
                                    "prepend-inner-icon": "mdi-link",
                                    hint: "支持图片直链、API、json/txt等，多个用英文逗号分隔，优先级高于本地竖屏目录",
                                    "persistent-hint": "",
                                    dense: ""
                                  }, null, 8, ["modelValue"])
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
                  ])
                ])
              ])
            ]),
            _createElementVNode("div", _hoisted_27, [
              _cache[51] || (_cache[51] = _createElementVNode("div", { class: "card-overlay" }, null, -1)),
              _createElementVNode("div", _hoisted_28, [
                _createVNode(_component_v_icon, {
                  class: "mr-2",
                  color: "warning"
                }, {
                  default: _withCtx(() => _cache[47] || (_cache[47] = [
                    _createTextVNode("mdi-download-multiple")
                  ])),
                  _: 1,
                  __: [47]
                }),
                _cache[48] || (_cache[48] = _createTextVNode(" 下载管理 "))
              ]),
              _createElementVNode("div", _hoisted_29, [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_row, { dense: "" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "12",
                          sm: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_text_field, {
                              modelValue: config.download_count,
                              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.download_count) = $event)),
                              modelModifiers: { number: true },
                              label: "候选图片数量",
                              type: "number",
                              min: "1",
                              max: "100",
                              "prepend-inner-icon": "mdi-counter",
                              hint: "预览时从网络源获取的候选图片数量（1-100）",
                              "persistent-hint": "",
                              dense: ""
                            }, null, 8, ["modelValue"])
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_col, {
                          cols: "12",
                          sm: "6"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_select, {
                              modelValue: downloadSource.value,
                              "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((downloadSource).value = $event)),
                              items: downloadSourceOptions,
                              label: "下载源",
                              "prepend-inner-icon": "mdi-source-branch",
                              hint: "Auto 同时使用横屏+竖屏网络源；PC/Mobile 仅使用对应网络源",
                              "persistent-hint": "",
                              dense: "",
                              class: "source-select"
                            }, null, 8, ["modelValue"])
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_row, {
                      dense: "",
                      class: "mt-1"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, { cols: "12" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_btn, {
                              color: "warning",
                              variant: "tonal",
                              loading: candidateLoading.value,
                              disabled: !config.enable || candidateLoading.value,
                              onClick: loadCandidates
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  start: "",
                                  size: "18"
                                }, {
                                  default: _withCtx(() => _cache[49] || (_cache[49] = [
                                    _createTextVNode("mdi-image-search")
                                  ])),
                                  _: 1,
                                  __: [49]
                                }),
                                _cache[50] || (_cache[50] = _createTextVNode(" 预览候选图片 "))
                              ]),
                              _: 1,
                              __: [50]
                            }, 8, ["loading", "disabled"]),
                            _createElementVNode("span", {
                              class: _normalizeClass(["download-status-text ml-3", downloadStatusColor.value])
                            }, _toDisplayString(downloadStatusText.value), 3)
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    (downloadProgressText.value)
                      ? (_openBlock(), _createBlock(_component_v_row, {
                          key: 0,
                          dense: "",
                          class: "mt-1"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_col, { cols: "12" }, {
                              default: _withCtx(() => [
                                _createElementVNode("div", _hoisted_30, _toDisplayString(downloadProgressText.value), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ])
            ]),
            _createVNode(_component_v_dialog, {
              modelValue: candidateDialog.value,
              "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((candidateDialog).value = $event)),
              "max-width": "880",
              persistent: ""
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          color: "warning",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[52] || (_cache[52] = [
                            _createTextVNode("mdi-image-multiple")
                          ])),
                          _: 1,
                          __: [52]
                        }),
                        _createTextVNode(" 选择要下载的图片（已选 " + _toDisplayString(selectedCount.value) + "/" + _toDisplayString(candidateItems.value.length) + "） ", 1),
                        _createVNode(_component_v_spacer),
                        _createVNode(_component_v_btn, {
                          icon: "",
                          size: "small",
                          onClick: _cache[9] || (_cache[9] = $event => (candidateDialog.value = false))
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, null, {
                              default: _withCtx(() => _cache[53] || (_cache[53] = [
                                _createTextVNode("mdi-close")
                              ])),
                              _: 1,
                              __: [53]
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_text, null, {
                      default: _withCtx(() => [
                        (candidateItems.value.length === 0)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_31, " 未获取到候选图片，请检查网络源配置 "))
                          : (_openBlock(), _createElementBlock("div", _hoisted_32, [
                              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(candidateItems.value, (item, index) => {
                                return (_openBlock(), _createElementBlock("div", {
                                  key: item.url,
                                  class: _normalizeClass(["candidate-item", { 'candidate-selected': item.selected }]),
                                  onClick: $event => (toggleCandidate(index))
                                }, [
                                  _createElementVNode("img", {
                                    src: item.url,
                                    alt: '候选图片 ' + (index + 1),
                                    loading: "lazy",
                                    onError: $event => (handleImageError(index))
                                  }, null, 40, _hoisted_34),
                                  _createElementVNode("div", _hoisted_35, [
                                    (item.selected)
                                      ? (_openBlock(), _createBlock(_component_v_icon, {
                                          key: 0,
                                          color: "success",
                                          size: "18"
                                        }, {
                                          default: _withCtx(() => _cache[54] || (_cache[54] = [
                                            _createTextVNode("mdi-check-circle")
                                          ])),
                                          _: 1,
                                          __: [54]
                                        }))
                                      : (_openBlock(), _createBlock(_component_v_icon, {
                                          key: 1,
                                          color: "white",
                                          size: "18"
                                        }, {
                                          default: _withCtx(() => _cache[55] || (_cache[55] = [
                                            _createTextVNode("mdi-checkbox-blank-circle-outline")
                                          ])),
                                          _: 1,
                                          __: [55]
                                        }))
                                  ])
                                ], 10, _hoisted_33))
                              }), 128))
                            ]))
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card_actions, null, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_btn, {
                          size: "small",
                          variant: "tonal",
                          onClick: toggleAllCandidates
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              start: "",
                              size: "16"
                            }, {
                              default: _withCtx(() => _cache[56] || (_cache[56] = [
                                _createTextVNode("mdi-select-all")
                              ])),
                              _: 1,
                              __: [56]
                            }),
                            _createTextVNode(" " + _toDisplayString(allSelected.value ? '取消全选' : '全选'), 1)
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_btn, {
                          size: "small",
                          variant: "tonal",
                          onClick: invertCandidates,
                          class: "ml-1"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              start: "",
                              size: "16"
                            }, {
                              default: _withCtx(() => _cache[57] || (_cache[57] = [
                                _createTextVNode("mdi-select-inverse")
                              ])),
                              _: 1,
                              __: [57]
                            }),
                            _cache[58] || (_cache[58] = _createTextVNode(" 反选 "))
                          ]),
                          _: 1,
                          __: [58]
                        }),
                        _createVNode(_component_v_spacer),
                        _createVNode(_component_v_btn, {
                          size: "small",
                          variant: "tonal",
                          onClick: _cache[10] || (_cache[10] = $event => (candidateDialog.value = false))
                        }, {
                          default: _withCtx(() => _cache[59] || (_cache[59] = [
                            _createTextVNode("取消")
                          ])),
                          _: 1,
                          __: [59]
                        }),
                        _createVNode(_component_v_btn, {
                          color: "warning",
                          size: "small",
                          disabled: selectedCount.value === 0 || downloadRunning.value,
                          loading: downloadRunning.value,
                          onClick: confirmDownload
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              start: "",
                              size: "16"
                            }, {
                              default: _withCtx(() => _cache[60] || (_cache[60] = [
                                _createTextVNode("mdi-download")
                              ])),
                              _: 1,
                              __: [60]
                            }),
                            _createTextVNode(" 确认下载（" + _toDisplayString(selectedCount.value) + "） ", 1)
                          ]),
                          _: 1
                        }, 8, ["disabled", "loading"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"]),
            (successMessage.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 0,
                  type: "success",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(successMessage.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (errorMessage.value)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 1,
                  type: "error",
                  density: "compact",
                  class: "mb-2 text-caption",
                  variant: "tonal",
                  closable: ""
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(errorMessage.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true)
          ]),
          _: 1
        })
      ]),
      _: 1
    })
  ]))
}
}

};
const ConfigComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-438c2f5f"]]);

export { ConfigComponent as default };
