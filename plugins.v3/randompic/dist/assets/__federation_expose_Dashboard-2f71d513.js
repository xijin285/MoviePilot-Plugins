import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Dashboard_vue_vue_type_style_index_0_scoped_1a5ad460_lang = '';

const {toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass,createElementVNode:_createElementVNode} = await importShared('vue');


const _hoisted_1 = { class: "dashboard-widget" };
const _hoisted_2 = {
  key: 0,
  class: "text-center py-2"
};
const _hoisted_3 = {
  key: 1,
  class: "text-error text-caption d-flex align-center"
};
const _hoisted_4 = { key: 2 };
const _hoisted_5 = {
  key: 3,
  class: "text-caption text-disabled text-center py-2"
};
const _hoisted_6 = { class: "text-caption text-disabled" };

const {ref,reactive,onMounted,onUnmounted,computed} = await importShared('vue');


// 接收props

const _sfc_main = {
  __name: 'Dashboard',
  props: {
  // API对象，用于调用插件API
  api: { 
    type: Object,
    required: true,
  },
  // 配置参数，来自get_dashboard方法的第二个返回值
  config: {
    type: Object,
    default: () => ({ attrs: {} }),
  },
  // 是否允许手动刷新
  allowRefresh: {
    type: Boolean,
    default: false,
  },
  // 自动刷新间隔（秒）
  refreshInterval: {
    type: Number,
    default: 0, // 0表示不自动刷新
  },
},
  setup(__props) {

const props = __props;

// 状态变量
const loading = ref(false);
const error = ref(null);
const initialDataLoaded = ref(false);
const summaryData = reactive({
  enable: false,
  api_status: 'disabled',
  total_count: 0,
  pc_count: 0,
  mobile_count: 0,
  today_visits: 0,
});
const lastRefreshedTimestamp = ref(null);

// 刷新计时器
let refreshTimer = null;

// 获取数据的函数
async function fetchData() {
  loading.value = true;
  error.value = null;
  
  try {
    // 调用插件API获取数据
    const data = await props.api.get('plugin/RandomPic/status');
    
    if (data) {
      // 更新数据
      summaryData.enable = Boolean(data.enable);
      summaryData.api_status = data.api_status || 'disabled';
      summaryData.total_count = data.total_count || 0;
      summaryData.pc_count = data.pc_count || 0;
      summaryData.mobile_count = data.mobile_count || 0;
      summaryData.today_visits = data.today_visits || 0;
      
      initialDataLoaded.value = true;
      lastRefreshedTimestamp.value = Date.now();
    } else {
      throw new Error('获取数据响应无效');
    }
  } catch (err) {
    console.error('获取仪表盘数据失败:', err);
    error.value = err.message || '获取数据失败';
  } finally {
    loading.value = false;
  }
}

// 最后刷新时间显示
const lastRefreshedTimeDisplay = computed(() => {
  if (!lastRefreshedTimestamp.value) return '';
  return `上次更新: ${new Date(lastRefreshedTimestamp.value).toLocaleTimeString()}`;
});

// 组件挂载时获取数据
onMounted(() => {
  fetchData();
  
  // 设置自动刷新
  if (props.allowRefresh && props.refreshInterval > 0) {
    refreshTimer = setInterval(fetchData, props.refreshInterval * 1000);
  }
});

// 组件卸载时清除计时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});

return (_ctx, _cache) => {
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_card_item = _resolveComponent("v-card-item");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_card, {
      flat: !props.config?.attrs?.border,
      loading: loading.value,
      class: "fill-height d-flex flex-column"
    }, {
      default: _withCtx(() => [
        (props.config?.attrs?.title || props.config?.attrs?.subtitle)
          ? (_openBlock(), _createBlock(_component_v_card_item, { key: 0 }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(props.config?.attrs?.title || '随机图库状态'), 1)
                  ]),
                  _: 1
                }),
                (props.config?.attrs?.subtitle)
                  ? (_openBlock(), _createBlock(_component_v_card_subtitle, { key: 0 }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(props.config.attrs.subtitle), 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }))
          : _createCommentVNode("", true),
        _createVNode(_component_v_card_text, { class: "flex-grow-1 pa-3" }, {
          default: _withCtx(() => [
            (loading.value && !initialDataLoaded.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_2, [
                  _createVNode(_component_v_progress_circular, {
                    indeterminate: "",
                    color: "primary",
                    size: "small"
                  })
                ]))
              : (error.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_3, [
                    _createVNode(_component_v_icon, {
                      size: "small",
                      color: "error",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => _cache[0] || (_cache[0] = [
                        _createTextVNode("mdi-alert-circle-outline")
                      ])),
                      _: 1,
                      __: [0]
                    }),
                    _createTextVNode(" " + _toDisplayString(error.value || '数据加载失败'), 1)
                  ]))
                : (initialDataLoaded.value && summaryData)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_4, [
                      _createVNode(_component_v_list, {
                        density: "compact",
                        class: "py-0"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_list_item, { class: "pa-0" }, {
                            prepend: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "small",
                                color: summaryData.enable ? 'success' : 'grey',
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(summaryData.enable ? 'mdi-api' : 'mdi-api-off'), 1)
                                ]),
                                _: 1
                              }, 8, ["color"])
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                default: _withCtx(() => [
                                  _cache[1] || (_cache[1] = _createTextVNode(" API 状态: ")),
                                  _createElementVNode("span", {
                                    class: _normalizeClass(summaryData.enable ? 'text-success' : 'text-grey')
                                  }, _toDisplayString(summaryData.enable ? '可用' : '已禁用'), 3)
                                ]),
                                _: 1,
                                __: [1]
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_divider, { class: "my-1" }),
                          _createVNode(_component_v_list_item, { class: "pa-0" }, {
                            prepend: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "small",
                                color: "info",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => _cache[2] || (_cache[2] = [
                                  _createTextVNode("mdi-image-multiple")
                                ])),
                                _: 1,
                                __: [2]
                              })
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                default: _withCtx(() => [
                                  _createTextVNode(" 总图片: " + _toDisplayString(summaryData.total_count || 0), 1)
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_list_item, { class: "pa-0" }, {
                            prepend: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "small",
                                color: "primary",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => _cache[3] || (_cache[3] = [
                                  _createTextVNode("mdi-monitor")
                                ])),
                                _: 1,
                                __: [3]
                              })
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                default: _withCtx(() => [
                                  _createTextVNode(" 横屏: " + _toDisplayString(summaryData.pc_count || 0), 1)
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_list_item, { class: "pa-0" }, {
                            prepend: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "small",
                                color: "success",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => _cache[4] || (_cache[4] = [
                                  _createTextVNode("mdi-cellphone")
                                ])),
                                _: 1,
                                __: [4]
                              })
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                default: _withCtx(() => [
                                  _createTextVNode(" 竖屏: " + _toDisplayString(summaryData.mobile_count || 0), 1)
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_divider, { class: "my-1" }),
                          _createVNode(_component_v_list_item, { class: "pa-0" }, {
                            prepend: _withCtx(() => [
                              _createVNode(_component_v_icon, {
                                size: "small",
                                color: "warning",
                                class: "mr-2"
                              }, {
                                default: _withCtx(() => _cache[5] || (_cache[5] = [
                                  _createTextVNode("mdi-chart-line")
                                ])),
                                _: 1,
                                __: [5]
                              })
                            ]),
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_title, { class: "text-caption" }, {
                                default: _withCtx(() => [
                                  _createTextVNode(" 今日访问: " + _toDisplayString(summaryData.today_visits || 0), 1)
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          })
                        ]),
                        _: 1
                      })
                    ]))
                  : (_openBlock(), _createElementBlock("div", _hoisted_5, " 暂无数据 "))
          ]),
          _: 1
        }),
        (props.allowRefresh)
          ? (_openBlock(), _createBlock(_component_v_divider, { key: 1 }))
          : _createCommentVNode("", true),
        (props.allowRefresh)
          ? (_openBlock(), _createBlock(_component_v_card_actions, {
              key: 2,
              class: "px-3 py-1"
            }, {
              default: _withCtx(() => [
                _createElementVNode("span", _hoisted_6, _toDisplayString(lastRefreshedTimeDisplay.value), 1),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  icon: "",
                  variant: "text",
                  size: "small",
                  onClick: fetchData,
                  loading: loading.value
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, { size: "small" }, {
                      default: _withCtx(() => _cache[6] || (_cache[6] = [
                        _createTextVNode("mdi-refresh")
                      ])),
                      _: 1,
                      __: [6]
                    })
                  ]),
                  _: 1
                }, 8, ["loading"])
              ]),
              _: 1
            }))
          : _createCommentVNode("", true)
      ]),
      _: 1
    }, 8, ["flat", "loading"])
  ]))
}
}

};
const Dashboard = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-1a5ad460"]]);

export { Dashboard as default };
