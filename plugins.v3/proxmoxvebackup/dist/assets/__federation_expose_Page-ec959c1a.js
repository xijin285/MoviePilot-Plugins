import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Page_vue_vue_type_style_index_0_scoped_4441b53c_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "status-row" };
const _hoisted_2 = { class: "status-row" };
const _hoisted_3 = { class: "status-row" };
const _hoisted_4 = { class: "status-row" };
const _hoisted_5 = { class: "status-row" };
const _hoisted_6 = { class: "status-row" };
const _hoisted_7 = { class: "status-row" };
const _hoisted_8 = { class: "status-row" };
const _hoisted_9 = { class: "status-row" };
const _hoisted_10 = { class: "status-row" };
const _hoisted_11 = { class: "text-caption text-medium-emphasis" };
const _hoisted_12 = { class: "stat-cell" };
const _hoisted_13 = { class: "text-caption text-medium-emphasis" };
const _hoisted_14 = {
  key: 0,
  class: "text-caption text-medium-emphasis mt-2"
};

const {computed,onBeforeUnmount,onMounted,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: { api: { type: [Object, Function], required: true } },
  emits: ['switch', 'close'],
  setup(__props) {

const props = __props;


const status = ref({});
const pve = ref({});
const history = ref([]);
const backups = ref([]);
const refreshing = ref(false);
const snackbar = ref(false);
let timer = null;

const statCells = computed(() => [
  { label: '本地备份', value: backups.value.filter(b => b.source === '本地备份').length, color: '' },
  { label: 'WebDAV 备份', value: backups.value.filter(b => b.source === 'WebDAV备份').length, color: '' },
  { label: '网盘备份', value: backups.value.filter(b => b.source && b.source.endsWith('网盘')).length, color: '' },
  { label: '备份记录', value: history.value.length, color: '' },
]);

const lastBackup = computed(() => {
  const ok = history.value.filter(h => h.success);
  return ok.length ? ok[0] : null;
});

function fmtTime(ts) {
  if (!ts) return '';
  try {
    return new Date(ts * 1000).toLocaleString();
  } catch {
    return '';
  }
}

async function fetchStatus() {
  try {
    status.value = (await props.api.get('plugin/ProxmoxVEBackup/status')) || {};
  } catch { /* 忽略 */ }
}

async function fetchPve() {
  try {
    pve.value = (await props.api.get('plugin/ProxmoxVEBackup/pve_status')) || {};
  } catch { /* 忽略 */ }
}

async function fetchOverview() {
  try {
    const [files, hist] = await Promise.all([
      props.api.get('plugin/ProxmoxVEBackup/available_backups'),
      props.api.get('plugin/ProxmoxVEBackup/backup_history'),
    ]);
    backups.value = Array.isArray(files) ? files : [];
    history.value = Array.isArray(hist) ? hist : [];
  } catch { /* 忽略 */ }
}

async function refreshAll() {
  refreshing.value = true;
  await Promise.all([fetchStatus(), fetchPve(), fetchOverview()]);
  refreshing.value = false;
  snackbar.value = true;
}

onMounted(async () => {
  await refreshAll();
  timer = setInterval(refreshAll, 30000);
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_snackbar = _resolveComponent("v-snackbar");

  return (_openBlock(), _createBlock(_component_v_card, {
    flat: "",
    class: "plugin-page glass-card"
  }, {
    default: _withCtx(() => [
      _createVNode(_component_v_card_title, {
        class: "d-flex align-center flex-wrap ga-3",
        style: {"padding":"14px 16px 6px"}
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_icon, {
            color: "primary",
            size: "26"
          }, {
            default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
              _createTextVNode("mdi-server", -1)
            ]))]),
            _: 1
          }),
          _cache[8] || (_cache[8] = _createElementVNode("span", { class: "text-h6 font-weight-bold" }, "PVE 守护神", -1)),
          _createVNode(_component_v_chip, {
            color: status.value.enabled ? 'success' : 'grey',
            size: "small",
            variant: "tonal"
          }, {
            default: _withCtx(() => [
              _createTextVNode(_toDisplayString(status.value.enabled ? '已启用' : '未启用'), 1)
            ]),
            _: 1
          }, 8, ["color"]),
          (pve.value.online)
            ? (_openBlock(), _createBlock(_component_v_chip, {
                key: 0,
                size: "small",
                variant: "tonal",
                color: "info",
                class: "text-caption"
              }, {
                default: _withCtx(() => [
                  _createTextVNode(" PVE " + _toDisplayString(pve.value.pve_version || '') + " · " + _toDisplayString(pve.value.hostname || ''), 1)
                ]),
                _: 1
              }))
            : _createCommentVNode("", true),
          _createVNode(_component_v_spacer),
          _createVNode(_component_v_btn, {
            size: "small",
            variant: "tonal",
            loading: refreshing.value,
            onClick: refreshAll
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                size: "16",
                class: "mr-1"
              }, {
                default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                  _createTextVNode("mdi-refresh", -1)
                ]))]),
                _: 1
              }),
              _cache[5] || (_cache[5] = _createTextVNode("刷新 ", -1))
            ]),
            _: 1
          }, 8, ["loading"]),
          _createVNode(_component_v_btn, {
            size: "small",
            variant: "tonal",
            "prepend-icon": "mdi-cog",
            onClick: _cache[0] || (_cache[0] = $event => (_ctx.$emit('switch')))
          }, {
            default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
              _createTextVNode("配置", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_btn, {
            icon: "",
            size: "small",
            variant: "text",
            onClick: _cache[1] || (_cache[1] = $event => (_ctx.$emit('close')))
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, { size: "22" }, {
                default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                  _createTextVNode("mdi-close", -1)
                ]))]),
                _: 1
              })
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createVNode(_component_v_card_text, { style: {"padding":"8px 16px 16px"} }, {
        default: _withCtx(() => [
          (!status.value.enabled)
            ? (_openBlock(), _createBlock(_component_v_alert, {
                key: 0,
                type: "info",
                variant: "tonal",
                density: "compact",
                class: "mb-3"
              }, {
                default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                  _createTextVNode(" 插件尚未启用，请点击右上角「配置」开启后使用。 ", -1)
                ]))]),
                _: 1
              }))
            : (pve.value.online === false)
              ? (_openBlock(), _createBlock(_component_v_alert, {
                  key: 1,
                  type: "warning",
                  variant: "tonal",
                  density: "compact",
                  class: "mb-3"
                }, {
                  default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
                    _createTextVNode(" PVE 主机连接失败，请检查配置中的 SSH 连接设置。 ", -1)
                  ]))]),
                  _: 1
                }))
              : _createCommentVNode("", true),
          _createVNode(_component_v_row, null, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, {
                cols: "12",
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card, {
                    variant: "outlined",
                    class: "fill-height"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card_title, { class: "d-flex align-center py-2" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            color: "primary",
                            size: "20",
                            class: "mr-2"
                          }, {
                            default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                              _createTextVNode("mdi-clock-check-outline", -1)
                            ]))]),
                            _: 1
                          }),
                          _cache[12] || (_cache[12] = _createElementVNode("span", { class: "text-subtitle-1" }, "运行状态", -1))
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_card_text, { class: "pt-0" }, {
                        default: _withCtx(() => [
                          _createElementVNode("div", _hoisted_1, [
                            _cache[13] || (_cache[13] = _createElementVNode("span", null, "定时计划", -1)),
                            _createElementVNode("b", null, _toDisplayString(status.value.cron || '未配置'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_2, [
                            _cache[14] || (_cache[14] = _createElementVNode("span", null, "下次执行", -1)),
                            _createElementVNode("b", null, _toDisplayString(status.value.next_run_time || '待调度'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_3, [
                            _cache[15] || (_cache[15] = _createElementVNode("span", null, "备份任务", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: status.value.backup_activity && status.value.backup_activity !== '空闲' ? 'warning' : 'success',
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(status.value.backup_activity || '空闲'), 1)
                              ]),
                              _: 1
                            }, 8, ["color"])
                          ]),
                          _createElementVNode("div", _hoisted_4, [
                            _cache[16] || (_cache[16] = _createElementVNode("span", null, "恢复任务", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: status.value.restore_activity && status.value.restore_activity !== '空闲' ? 'warning' : 'success',
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(status.value.restore_activity || '空闲'), 1)
                              ]),
                              _: 1
                            }, 8, ["color"])
                          ]),
                          _createElementVNode("div", _hoisted_5, [
                            _cache[17] || (_cache[17] = _createElementVNode("span", null, "恢复功能", -1)),
                            _createElementVNode("b", null, _toDisplayString(status.value.enable_restore ? '已开启' : '已关闭'), 1)
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
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card, {
                    variant: "outlined",
                    class: "fill-height"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card_title, { class: "d-flex align-center py-2" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            color: "teal",
                            size: "20",
                            class: "mr-2"
                          }, {
                            default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
                              _createTextVNode("mdi-cpu-64-bit", -1)
                            ]))]),
                            _: 1
                          }),
                          _cache[19] || (_cache[19] = _createElementVNode("span", { class: "text-subtitle-1" }, "PVE 主机", -1))
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_card_text, { class: "pt-0" }, {
                        default: _withCtx(() => [
                          _createElementVNode("div", _hoisted_6, [
                            _cache[20] || (_cache[20] = _createElementVNode("span", null, "连接", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: pve.value.online ? 'success' : 'error',
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(pve.value.online ? '在线' : '离线'), 1)
                              ]),
                              _: 1
                            }, 8, ["color"])
                          ]),
                          _createElementVNode("div", _hoisted_7, [
                            _cache[21] || (_cache[21] = _createElementVNode("span", null, "主机名", -1)),
                            _createElementVNode("b", null, _toDisplayString(pve.value.hostname || '-'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_8, [
                            _cache[22] || (_cache[22] = _createElementVNode("span", null, "PVE 版本", -1)),
                            _createElementVNode("b", null, _toDisplayString(pve.value.pve_version || '-'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_9, [
                            _cache[23] || (_cache[23] = _createElementVNode("span", null, "CPU 使用率", -1)),
                            _createElementVNode("b", null, _toDisplayString(pve.value.cpu_usage != null ? pve.value.cpu_usage + '%' : '-'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_10, [
                            _cache[24] || (_cache[24] = _createElementVNode("span", null, "内存使用率", -1)),
                            _createElementVNode("b", null, _toDisplayString(pve.value.mem_usage != null ? pve.value.mem_usage + '%' : '-'), 1)
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
                  _createVNode(_component_v_card, { variant: "outlined" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card_title, { class: "d-flex align-center py-2" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            color: "amber-darken-2",
                            size: "20",
                            class: "mr-2"
                          }, {
                            default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
                              _createTextVNode("mdi-backup-restore", -1)
                            ]))]),
                            _: 1
                          }),
                          _cache[26] || (_cache[26] = _createElementVNode("span", { class: "text-subtitle-1" }, "备份概览", -1)),
                          _createVNode(_component_v_spacer),
                          _createElementVNode("span", _hoisted_11, "共 " + _toDisplayString(backups.value.length) + " 个备份文件", 1)
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_card_text, { class: "pt-0" }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_row, { dense: "" }, {
                            default: _withCtx(() => [
                              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(statCells.value, (cell) => {
                                return (_openBlock(), _createBlock(_component_v_col, {
                                  key: cell.label,
                                  cols: "6",
                                  sm: "3"
                                }, {
                                  default: _withCtx(() => [
                                    _createElementVNode("div", _hoisted_12, [
                                      _createElementVNode("div", _hoisted_13, _toDisplayString(cell.label), 1),
                                      _createElementVNode("div", {
                                        class: _normalizeClass(["text-h6 font-weight-bold", cell.color])
                                      }, _toDisplayString(cell.value), 3)
                                    ])
                                  ]),
                                  _: 2
                                }, 1024))
                              }), 128))
                            ]),
                            _: 1
                          }),
                          (lastBackup.value)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_14, [
                                _createTextVNode(" 最近一次备份：" + _toDisplayString(fmtTime(lastBackup.value.timestamp)) + " ", 1),
                                (lastBackup.value.filename)
                                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                      _createTextVNode(" · " + _toDisplayString(lastBackup.value.filename), 1)
                                    ], 64))
                                  : _createCommentVNode("", true)
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
              })
            ]),
            _: 1
          }),
          _createVNode(_component_v_alert, {
            type: "info",
            variant: "tonal",
            density: "compact",
            class: "mt-3"
          }, {
            default: _withCtx(() => [...(_cache[27] || (_cache[27] = [
              _createTextVNode(" 完整功能（虚拟机管理、备份下载恢复、主机操作等）已移至左侧导航 ", -1),
              _createElementVNode("b", null, "「PVE 守护神」", -1),
              _createTextVNode("，点击即可使用。 ", -1)
            ]))]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createVNode(_component_v_snackbar, {
        modelValue: snackbar.value,
        "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((snackbar).value = $event)),
        timeout: "2000"
      }, {
        default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
          _createTextVNode("已刷新", -1)
        ]))]),
        _: 1
      }, 8, ["modelValue"])
    ]),
    _: 1
  }))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-4441b53c"]]);

export { Page as default };
