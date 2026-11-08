import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Dashboard_vue_vue_type_style_index_0_scoped_9da668ae_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,toDisplayString:_toDisplayString,createElementVNode:_createElementVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,normalizeClass:_normalizeClass,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "dashboard-wrap pa-2" };
const _hoisted_2 = { class: "d-flex align-center ga-3 mb-2" };
const _hoisted_3 = { class: "text-subtitle-2 font-weight-bold" };
const _hoisted_4 = { class: "text-caption text-medium-emphasis" };
const _hoisted_5 = { class: "text-caption text-medium-emphasis d-flex justify-space-between" };
const _hoisted_6 = { class: "text-caption text-medium-emphasis d-flex justify-space-between" };
const _hoisted_7 = { class: "d-flex flex-wrap ga-3 mt-3" };
const _hoisted_8 = {
  key: 1,
  class: "d-flex align-center ga-2 py-4"
};
const _hoisted_9 = { class: "text-body-2" };

const {computed,onMounted,onUnmounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Dashboard',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'IkuaiRouterBackup' },
},
  setup(__props) {

const props = __props;

const status = reactive({ ok: false, error: '' });
const backupActivity = ref('');
const updatedAt = ref('');
let timer = null;

const cpuColor = computed(() => {
  const v = status.cpu_usage || 0;
  return v < 50 ? 'success' : v < 80 ? 'warning' : 'error'
});
const memColor = computed(() => {
  const v = status.mem_usage || 0;
  return v < 50 ? 'success' : v < 80 ? 'warning' : 'error'
});

const fmtSpeed = (bps) => {
  const v = Number(bps) || 0;
  if (v >= 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024).toFixed(2) + ' GB/s'
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(1) + ' MB/s'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' KB/s'
  return v + ' B/s'
};

const load = async () => {
  try {
    const data = await props.api.get(`plugin/${props.pluginId}/status`);
    if (data) Object.assign(status, data);
    updatedAt.value = new Date().toLocaleTimeString();
  } catch (e) {
    status.ok = false;
    status.error = '获取状态失败';
  }
  try {
    const hist = await props.api.get(`plugin/${props.pluginId}/histories`);
    backupActivity.value = hist?.backup_activity || '空闲';
  } catch (e) { /* 静默 */ }
};

onMounted(() => {
  load();
  timer = setInterval(load, 30000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    (status.ok)
      ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
          _createElementVNode("div", _hoisted_2, [
            _createVNode(_component_v_icon, {
              size: "18",
              color: "primary"
            }, {
              default: _withCtx(() => _cache[0] || (_cache[0] = [
                _createTextVNode("mdi-router-network")
              ])),
              _: 1,
              __: [0]
            }),
            _createElementVNode("span", _hoisted_3, _toDisplayString(status.hostname || '爱快路由'), 1),
            (status.version)
              ? (_openBlock(), _createBlock(_component_v_chip, {
                  key: 0,
                  size: "x-small",
                  variant: "tonal",
                  class: "text-caption"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(status.version), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_spacer),
            _createElementVNode("span", _hoisted_4, _toDisplayString(updatedAt.value), 1)
          ]),
          _createVNode(_component_v_row, { dense: "" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, { cols: "6" }, {
                default: _withCtx(() => [
                  _createElementVNode("div", _hoisted_5, [
                    _cache[1] || (_cache[1] = _createElementVNode("span", null, "CPU", -1)),
                    _createElementVNode("span", {
                      class: _normalizeClass(["font-weight-bold", cpuColor.value + '--text'])
                    }, _toDisplayString(status.cpu_usage) + "%", 3)
                  ]),
                  _createVNode(_component_v_progress_linear, {
                    "model-value": status.cpu_usage,
                    color: cpuColor.value,
                    height: "8",
                    rounded: ""
                  }, null, 8, ["model-value", "color"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "6" }, {
                default: _withCtx(() => [
                  _createElementVNode("div", _hoisted_6, [
                    _cache[2] || (_cache[2] = _createElementVNode("span", null, "内存", -1)),
                    _createElementVNode("span", {
                      class: _normalizeClass(["font-weight-bold", memColor.value + '--text'])
                    }, _toDisplayString(status.mem_usage) + "%", 3)
                  ]),
                  _createVNode(_component_v_progress_linear, {
                    "model-value": status.mem_usage,
                    color: memColor.value,
                    height: "8",
                    rounded: ""
                  }, null, 8, ["model-value", "color"])
                ]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createElementVNode("div", _hoisted_7, [
            _createVNode(_component_v_chip, {
              size: "small",
              variant: "tonal",
              color: "info",
              "prepend-icon": "mdi-arrow-up"
            }, {
              default: _withCtx(() => [
                _createTextVNode(" ↑ " + _toDisplayString(fmtSpeed(status.upload_speed)), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_chip, {
              size: "small",
              variant: "tonal",
              color: "success",
              "prepend-icon": "mdi-arrow-down"
            }, {
              default: _withCtx(() => [
                _createTextVNode(" ↓ " + _toDisplayString(fmtSpeed(status.download_speed)), 1)
              ]),
              _: 1
            }),
            (backupActivity.value && backupActivity.value !== '空闲')
              ? (_openBlock(), _createBlock(_component_v_chip, {
                  key: 0,
                  size: "small",
                  variant: "tonal",
                  color: "warning",
                  "prepend-icon": "mdi-content-save-cog"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(backupActivity.value), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true)
          ])
        ], 64))
      : (_openBlock(), _createElementBlock("div", _hoisted_8, [
          _createVNode(_component_v_icon, {
            color: "error",
            size: "20"
          }, {
            default: _withCtx(() => _cache[3] || (_cache[3] = [
              _createTextVNode("mdi-alert-circle-outline")
            ])),
            _: 1,
            __: [3]
          }),
          _createElementVNode("span", _hoisted_9, _toDisplayString(status.error || '无法连接爱快路由'), 1)
        ]))
  ]))
}
}

};
const Dashboard = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-9da668ae"]]);

export { Dashboard as default };
