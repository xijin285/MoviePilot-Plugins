import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Dashboard_vue_vue_type_style_index_0_scoped_da87547d_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createBlock:_createBlock,Fragment:_Fragment} = await importShared('vue');


const _hoisted_1 = { class: "pve-dash pa-2" };
const _hoisted_2 = { class: "d-flex align-center mb-1" };
const _hoisted_3 = { class: "text-caption text-medium-emphasis" };
const _hoisted_4 = {
  key: 0,
  class: "text-error text-caption d-flex align-center py-2"
};
const _hoisted_5 = { class: "d-flex flex-wrap ga-1 mb-2" };
const _hoisted_6 = { class: "text-caption d-flex align-center" };
const _hoisted_7 = { class: "ml-1 font-weight-medium" };
const _hoisted_8 = {
  key: 0,
  class: "text-caption d-flex align-center mt-1"
};
const _hoisted_9 = { class: "ml-1 font-weight-medium" };

const {computed,onMounted,onUnmounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Dashboard',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'ProxmoxVEBackup' },
},
  setup(__props) {

const props = __props;

const loading = ref(false);
const error = ref('');
const updatedAt = ref('');
const backupCount = ref(0);
const status = reactive({
  enabled: false,
  pve_host: '',
  backup_activity: '空闲',
  restore_activity: '空闲',
  next_run_time: '',
});

let timer = null;

const statusApi = computed(() => `plugin/${props.pluginId}/status`);
const filesApi = computed(() => `plugin/${props.pluginId}/available_backups`);

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const data = await props.api.get(statusApi.value);
    if (data && !data.error) {
      Object.assign(status, data);
      updatedAt.value = new Date().toLocaleTimeString();
    } else {
      error.value = '获取状态失败';
    }
  } catch (e) {
    error.value = '获取状态失败';
  }
  try {
    const files = await props.api.get(filesApi.value);
    backupCount.value = Array.isArray(files) ? files.length : 0;
  } catch (e) {
    backupCount.value = 0;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  load();
  timer = setInterval(load, 30000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_chip = _resolveComponent("v-chip");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createVNode(_component_v_icon, {
        size: "18",
        color: "primary",
        class: "mr-2"
      }, {
        default: _withCtx(() => [...(_cache[0] || (_cache[0] = [
          _createTextVNode("mdi-server", -1)
        ]))]),
        _: 1
      }),
      _cache[2] || (_cache[2] = _createElementVNode("span", { class: "text-subtitle-2 font-weight-bold" }, "PVE 守护神", -1)),
      _createVNode(_component_v_spacer),
      _createElementVNode("span", _hoisted_3, _toDisplayString(updatedAt.value), 1),
      _createVNode(_component_v_btn, {
        icon: "",
        variant: "text",
        size: "x-small",
        loading: loading.value,
        onClick: load
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_icon, { size: "16" }, {
            default: _withCtx(() => [...(_cache[1] || (_cache[1] = [
              _createTextVNode("mdi-refresh", -1)
            ]))]),
            _: 1
          })
        ]),
        _: 1
      }, 8, ["loading"])
    ]),
    (error.value)
      ? (_openBlock(), _createElementBlock("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            size: "small",
            color: "error",
            class: "mr-1"
          }, {
            default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
              _createTextVNode("mdi-alert-circle-outline", -1)
            ]))]),
            _: 1
          }),
          _createTextVNode(" " + _toDisplayString(error.value), 1)
        ]))
      : (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
          _createElementVNode("div", _hoisted_5, [
            _createVNode(_component_v_chip, {
              size: "x-small",
              variant: "tonal",
              color: status.enabled ? 'success' : 'grey'
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(status.enabled ? '已启用' : '已禁用'), 1)
              ]),
              _: 1
            }, 8, ["color"]),
            _createVNode(_component_v_chip, {
              size: "x-small",
              variant: "tonal",
              color: "info",
              "prepend-icon": "mdi-archive"
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(backupCount.value) + " 个备份 ", 1)
              ]),
              _: 1
            }),
            (status.backup_activity && status.backup_activity !== '空闲')
              ? (_openBlock(), _createBlock(_component_v_chip, {
                  key: 0,
                  size: "x-small",
                  variant: "tonal",
                  color: "warning",
                  "prepend-icon": "mdi-database-arrow-up"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(status.backup_activity), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            (status.restore_activity && status.restore_activity !== '空闲')
              ? (_openBlock(), _createBlock(_component_v_chip, {
                  key: 1,
                  size: "x-small",
                  variant: "tonal",
                  color: "warning",
                  "prepend-icon": "mdi-database-arrow-down"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(status.restore_activity), 1)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true)
          ]),
          _createElementVNode("div", _hoisted_6, [
            _createVNode(_component_v_icon, {
              size: "14",
              class: "mr-1 text-medium-emphasis"
            }, {
              default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                _createTextVNode("mdi-lan-connect", -1)
              ]))]),
              _: 1
            }),
            _cache[5] || (_cache[5] = _createElementVNode("span", { class: "text-medium-emphasis" }, "主机", -1)),
            _createElementVNode("span", _hoisted_7, _toDisplayString(status.pve_host || '未配置'), 1)
          ]),
          (status.next_run_time)
            ? (_openBlock(), _createElementBlock("div", _hoisted_8, [
                _createVNode(_component_v_icon, {
                  size: "14",
                  class: "mr-1 text-medium-emphasis"
                }, {
                  default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                    _createTextVNode("mdi-timer-outline", -1)
                  ]))]),
                  _: 1
                }),
                _cache[7] || (_cache[7] = _createElementVNode("span", { class: "text-medium-emphasis" }, "下次备份", -1)),
                _createElementVNode("span", _hoisted_9, _toDisplayString(status.next_run_time), 1)
              ]))
            : _createCommentVNode("", true)
        ], 64))
  ]))
}
}

};
const Dashboard = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-da87547d"]]);

export { Dashboard as default };
