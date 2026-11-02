import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Config_vue_vue_type_style_index_0_scoped_de617850_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,normalizeClass:_normalizeClass,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,Transition:_Transition,createTextVNode:_createTextVNode,vModelCheckbox:_vModelCheckbox,withDirectives:_withDirectives,createBlock:_createBlock} = await importShared('vue');


const _hoisted_1 = { class: "qkcfg-page" };
const _hoisted_2 = { class: "qkcfg-topbar" };
const _hoisted_3 = { class: "qkcfg-topbar__left" };
const _hoisted_4 = { class: "qkcfg-topbar__icon" };
const _hoisted_5 = { class: "qkcfg-topbar__right" };
const _hoisted_6 = { class: "qkcfg-card" };
const _hoisted_7 = { class: "qkcfg-card__header" };
const _hoisted_8 = { class: "qkcfg-card__title d-flex align-center" };
const _hoisted_9 = { class: "qkcfg-switch-grid" };
const _hoisted_10 = { class: "qkcfg-switch-item__main" };
const _hoisted_11 = { class: "qkcfg-switch-item__icon" };
const _hoisted_12 = {
  class: "qkcfg-switch",
  style: {"--switch-checked-bg":"#8b5cf6"}
};
const _hoisted_13 = { class: "qkcfg-switch__slider" };
const _hoisted_14 = { class: "qkcfg-switch__circle" };
const _hoisted_15 = {
  class: "qkcfg-switch__cross",
  "xml:space": "preserve",
  style: {"enable-background":"new 0 0 512 512"},
  viewBox: "0 0 365.696 365.696",
  y: "0",
  x: "0",
  height: "6",
  width: "6",
  "xmlns:xlink": "http://www.w3.org/1999/xlink",
  version: "1.1",
  xmlns: "http://www.w3.org/2000/svg"
};
const _hoisted_16 = {
  class: "qkcfg-switch__checkmark",
  "xml:space": "preserve",
  style: {"enable-background":"new 0 0 512 512"},
  viewBox: "0 0 24 24",
  y: "0",
  x: "0",
  height: "10",
  width: "10",
  "xmlns:xlink": "http://www.w3.org/1999/xlink",
  version: "1.1",
  xmlns: "http://www.w3.org/2000/svg"
};
const _hoisted_17 = { class: "qkcfg-switch-item__main" };
const _hoisted_18 = { class: "qkcfg-switch-item__icon" };
const _hoisted_19 = {
  class: "qkcfg-switch",
  style: {"--switch-checked-bg":"#ef4444"}
};
const _hoisted_20 = { class: "qkcfg-switch__slider" };
const _hoisted_21 = { class: "qkcfg-switch__circle" };
const _hoisted_22 = {
  class: "qkcfg-switch__cross",
  "xml:space": "preserve",
  style: {"enable-background":"new 0 0 512 512"},
  viewBox: "0 0 365.696 365.696",
  y: "0",
  x: "0",
  height: "6",
  width: "6",
  "xmlns:xlink": "http://www.w3.org/1999/xlink",
  version: "1.1",
  xmlns: "http://www.w3.org/2000/svg"
};
const _hoisted_23 = {
  class: "qkcfg-switch__checkmark",
  "xml:space": "preserve",
  style: {"enable-background":"new 0 0 512 512"},
  viewBox: "0 0 24 24",
  y: "0",
  x: "0",
  height: "10",
  width: "10",
  "xmlns:xlink": "http://www.w3.org/1999/xlink",
  version: "1.1",
  xmlns: "http://www.w3.org/2000/svg"
};
const _hoisted_24 = { class: "qkcfg-field" };
const _hoisted_25 = { class: "qkcfg-field__header" };
const _hoisted_26 = { class: "qkcfg-field__title-main" };
const _hoisted_27 = { class: "qkcfg-form-grid qkcfg-form-grid--settings" };
const _hoisted_28 = { class: "qkcfg-form-item" };
const _hoisted_29 = { class: "qkcfg-form-item" };
const _hoisted_30 = { class: "qkcfg-form-item" };
const _hoisted_31 = { class: "qkcfg-card" };
const _hoisted_32 = { class: "qkcfg-card__header" };
const _hoisted_33 = { class: "qkcfg-card__title d-flex align-center" };
const _hoisted_34 = { class: "qkcfg-field" };
const _hoisted_35 = { class: "qkcfg-field__header" };
const _hoisted_36 = { class: "qkcfg-field__title-main" };
const _hoisted_37 = { class: "qkcfg-field-hint" };
const _hoisted_38 = { class: "qkcfg-card" };
const _hoisted_39 = { class: "qkcfg-card__header" };
const _hoisted_40 = { class: "qkcfg-card__title d-flex align-center" };
const _hoisted_41 = { class: "qkcfg-guide" };
const _hoisted_42 = { class: "qkcfg-guide__section" };
const _hoisted_43 = { class: "qkcfg-guide__paragraph" };
const _hoisted_44 = { class: "qkcfg-guide__paragraph" };
const _hoisted_45 = { class: "qkcfg-guide__paragraph" };
const _hoisted_46 = { class: "qkcfg-guide__paragraph" };

const {onBeforeUnmount,onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
},
  emits: ['close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const config = reactive({
  enabled: false,
  permanently_delete: false,
  cookie: '',
  page_size: 50,
  sort_field: 'file_name',
  sort_order: 'asc',
  logged_in: false,
  ...props.initialConfig,
});

const loading = ref(false);
const saving = ref(false);
const showCookie = ref(false);
const message = reactive({ show: false, type: 'info', text: '' });
let messageTimer = null;

const sortOrderOptions = ref([
  { title: '升序', value: 'asc' },
  { title: '降序', value: 'desc' },
]);

const sortFieldOptions = ref([
  { title: '文件名', value: 'file_name' },
  { title: '更新时间', value: 'updated_at' },
  { title: '文件大小', value: 'size' },
  { title: '创建时间', value: 'created_at' },
]);

function clearMessageTimer() {
  if (messageTimer) {
    clearTimeout(messageTimer);
    messageTimer = null;
  }
}

function scheduleMessageClose(type = 'info') {
  clearMessageTimer();
  const timeout = type === 'error' ? 5000 : 3000;
  messageTimer = setTimeout(() => {
    message.show = false;
    messageTimer = null;
  }, timeout);
}

function pushMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  message.show = true;
  scheduleMessageClose(type);
}

function pluginUrl(path) {
  return `/api/v1/plugin/VueQuarkDisk${path}`
}

async function request(path, options = {}) {
  const apiPath = `plugin/VueQuarkDisk${path}`;
  if (options.method === 'POST') {
    if (props.api?.post) {
      return props.api.post(apiPath, options.body ? JSON.parse(options.body) : {}, options)
    }
  } else if (props.api?.get) {
    return props.api.get(apiPath, options)
  }

  const response = await fetch(pluginUrl(path), {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  return response.json()
}

function applyConfig(data = {}) {
  config.enabled = Boolean(data.enabled);
  config.permanently_delete = Boolean(data.permanently_delete);
  config.cookie = data.cookie || '';
  config.page_size = Number(data.page_size || 50);
  config.sort_field = data.sort_field || 'file_name';
  config.sort_order = data.sort_order || 'asc';
  config.logged_in = Boolean(data.logged_in);
}

async function loadConfig() {
  loading.value = true;
  try {
    const data = await request('/config');
    applyConfig(data);
  } catch (error) {
    pushMessage(`加载配置失败：${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  try {
    const result = await request('/config', {
      method: 'POST',
      body: JSON.stringify({ ...config }),
    });
    if (!result.success) {
      throw new Error(result.message || '保存失败')
    }
    applyConfig(result.data || {});
    pushMessage(result.message || '配置保存成功', 'success');
  } catch (error) {
    pushMessage(`保存配置失败：${error.message || error}`, 'error');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  loadConfig();
});

onBeforeUnmount(() => {
  clearMessageTimer();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_btn_group = _resolveComponent("v-btn-group");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_textarea = _resolveComponent("v-textarea");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-cloud-outline",
            size: "24"
          })
        ]),
        _cache[11] || (_cache[11] = _createElementVNode("div", { class: "qkcfg-topbar__meta" }, [
          _createElementVNode("div", { class: "qkcfg-topbar__title" }, "夸克网盘 · 配置"),
          _createElementVNode("div", { class: "qkcfg-topbar__sub" }, "插件参数、认证与文件操作管理")
        ], -1))
      ]),
      _createElementVNode("div", _hoisted_5, [
        _createVNode(_component_v_btn_group, {
          variant: "tonal",
          density: "compact",
          class: "elevation-0"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: _cache[0] || (_cache[0] = $event => (emit('switch'))),
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-view-dashboard",
                  size: "18",
                  class: "mr-sm-1"
                }),
                _cache[12] || (_cache[12] = _createElementVNode("span", { class: "btn-text d-none d-sm-inline" }, "状态页", -1))
              ]),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              color: "primary",
              loading: saving.value,
              onClick: saveConfig,
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-content-save",
                  size: "18",
                  class: "mr-sm-1"
                }),
                _cache[13] || (_cache[13] = _createElementVNode("span", { class: "btn-text d-none d-sm-inline" }, "保存", -1))
              ]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: _cache[1] || (_cache[1] = $event => (emit('close'))),
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-close",
                  size: "18"
                }),
                _cache[14] || (_cache[14] = _createElementVNode("span", { class: "btn-text d-none d-sm-inline" }, "关闭", -1))
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ])
    ]),
    _createVNode(_Transition, { name: "qkcfg-slide" }, {
      default: _withCtx(() => [
        (message.show)
          ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: _normalizeClass(["qkcfg-toast", `qkcfg-toast--${message.type}`])
            }, [
              _createVNode(_component_v_icon, {
                icon: message.type === 'success' ? 'mdi-check-circle' : message.type === 'error' ? 'mdi-alert-circle' : 'mdi-information',
                size: "18"
              }, null, 8, ["icon"]),
              _createElementVNode("span", null, _toDisplayString(message.text), 1),
              _createElementVNode("button", {
                class: "qkcfg-toast__close",
                onClick: _cache[2] || (_cache[2] = $event => (message.show = false))
              }, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-close",
                  size: "16"
                })
              ])
            ], 2))
          : _createCommentVNode("", true)
      ]),
      _: 1
    }),
    _createElementVNode("div", _hoisted_6, [
      _createElementVNode("div", _hoisted_7, [
        _createElementVNode("span", _hoisted_8, [
          _createVNode(_component_v_icon, {
            icon: "mdi-toggle-switch-outline",
            size: "18",
            color: "#8b5cf6",
            class: "mr-1"
          }),
          _cache[15] || (_cache[15] = _createTextVNode(" 基础设置 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_9, [
        _createElementVNode("div", {
          class: _normalizeClass(["qkcfg-switch-item", { 'qkcfg-switch-item--active': config.enabled }]),
          style: {"--qkcfg-accent":"#8b5cf6"}
        }, [
          _createElementVNode("div", _hoisted_10, [
            _createElementVNode("div", _hoisted_11, [
              _createVNode(_component_v_icon, {
                icon: "mdi-power-plug",
                size: "18"
              })
            ]),
            _cache[16] || (_cache[16] = _createElementVNode("div", { class: "qkcfg-switch-item__text" }, [
              _createElementVNode("span", { class: "qkcfg-switch-item__label" }, "启用插件")
            ], -1))
          ]),
          _createElementVNode("label", _hoisted_12, [
            _withDirectives(_createElementVNode("input", {
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.enabled) = $event)),
              type: "checkbox"
            }, null, 512), [
              [_vModelCheckbox, config.enabled]
            ]),
            _createElementVNode("div", _hoisted_13, [
              _createElementVNode("div", _hoisted_14, [
                (_openBlock(), _createElementBlock("svg", _hoisted_15, [...(_cache[17] || (_cache[17] = [
                  _createElementVNode("g", null, [
                    _createElementVNode("path", {
                      fill: "currentColor",
                      d: "M243.188 182.86 356.32 69.726c12.5-12.5 12.5-32.766 0-45.247L341.238 9.398c-12.504-12.503-32.77-12.503-45.25 0L182.86 122.528 69.727 9.374c-12.5-12.5-32.766-12.5-45.247 0L9.375 24.457c-12.5 12.504-12.5 32.77 0 45.25l113.152 113.152L9.398 295.99c-12.503 12.503-12.503 32.769 0 45.25L24.48 356.32c12.5 12.5 32.766 12.5 45.247 0l113.132-113.132L295.99 356.32c12.503 12.5 32.769 12.5 45.25 0l15.081-15.082c12.5-12.504 12.5-32.77 0-45.25zm0 0"
                    })
                  ], -1)
                ]))])),
                (_openBlock(), _createElementBlock("svg", _hoisted_16, [...(_cache[18] || (_cache[18] = [
                  _createElementVNode("g", { transform: "translate(-0.4, 0.2)" }, [
                    _createElementVNode("path", {
                      fill: "currentColor",
                      d: "M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z"
                    })
                  ], -1)
                ]))]))
              ])
            ])
          ])
        ], 2),
        _createElementVNode("div", {
          class: _normalizeClass(["qkcfg-switch-item", { 'qkcfg-switch-item--active': config.permanently_delete }]),
          style: {"--qkcfg-accent":"#ef4444"}
        }, [
          _createElementVNode("div", _hoisted_17, [
            _createElementVNode("div", _hoisted_18, [
              _createVNode(_component_v_icon, {
                icon: "mdi-delete-alert-outline",
                size: "18"
              })
            ]),
            _cache[19] || (_cache[19] = _createElementVNode("div", { class: "qkcfg-switch-item__text" }, [
              _createElementVNode("span", { class: "qkcfg-switch-item__label" }, "彻底删除")
            ], -1))
          ]),
          _createElementVNode("label", _hoisted_19, [
            _withDirectives(_createElementVNode("input", {
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.permanently_delete) = $event)),
              type: "checkbox"
            }, null, 512), [
              [_vModelCheckbox, config.permanently_delete]
            ]),
            _createElementVNode("div", _hoisted_20, [
              _createElementVNode("div", _hoisted_21, [
                (_openBlock(), _createElementBlock("svg", _hoisted_22, [...(_cache[20] || (_cache[20] = [
                  _createElementVNode("g", null, [
                    _createElementVNode("path", {
                      fill: "currentColor",
                      d: "M243.188 182.86 356.32 69.726c12.5-12.5 12.5-32.766 0-45.247L341.238 9.398c-12.504-12.503-32.77-12.503-45.25 0L182.86 122.528 69.727 9.374c-12.5-12.5-32.766-12.5-45.247 0L9.375 24.457c-12.5 12.504-12.5 32.77 0 45.25l113.152 113.152L9.398 295.99c-12.503 12.503-12.503 32.769 0 45.25L24.48 356.32c12.5 12.5 32.766 12.5 45.247 0l113.132-113.132L295.99 356.32c12.503 12.5 32.769 12.5 45.25 0l15.081-15.082c12.5-12.504 12.5-32.77 0-45.25zm0 0"
                    })
                  ], -1)
                ]))])),
                (_openBlock(), _createElementBlock("svg", _hoisted_23, [...(_cache[21] || (_cache[21] = [
                  _createElementVNode("g", { transform: "translate(-0.4, 0.2)" }, [
                    _createElementVNode("path", {
                      fill: "currentColor",
                      d: "M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z"
                    })
                  ], -1)
                ]))]))
              ])
            ])
          ])
        ], 2)
      ]),
      _cache[26] || (_cache[26] = _createElementVNode("div", { class: "qkcfg-divider" }, null, -1)),
      _createElementVNode("div", _hoisted_24, [
        _createElementVNode("div", _hoisted_25, [
          _createElementVNode("div", _hoisted_26, [
            _createVNode(_component_v_icon, {
              icon: "mdi-sort-variant",
              size: "18",
              color: "#3b82f6",
              class: "qkcfg-field__title-icon"
            }),
            _cache[22] || (_cache[22] = _createElementVNode("div", { class: "qkcfg-field__title-text" }, [
              _createElementVNode("label", { class: "qkcfg-field__label" }, "查询参数")
            ], -1))
          ])
        ]),
        _createElementVNode("div", _hoisted_27, [
          _createElementVNode("div", _hoisted_28, [
            _createVNode(_component_v_text_field, {
              modelValue: config.page_size,
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.page_size) = $event)),
              modelModifiers: { number: true },
              label: "分页大小",
              type: "number",
              density: "compact",
              variant: "outlined",
              "hide-details": "auto",
              min: "1",
              max: "200",
              class: "qkcfg-input"
            }, null, 8, ["modelValue"]),
            _cache[23] || (_cache[23] = _createElementVNode("div", { class: "qkcfg-field-hint" }, "建议 50 ~ 200，控制每次列表请求的文件数量", -1))
          ]),
          _createElementVNode("div", _hoisted_29, [
            _createVNode(_component_v_select, {
              modelValue: config.sort_field,
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.sort_field) = $event)),
              items: sortFieldOptions.value,
              "item-title": "title",
              "item-value": "value",
              label: "排序字段",
              density: "compact",
              variant: "outlined",
              "hide-details": "auto",
              class: "qkcfg-input"
            }, null, 8, ["modelValue", "items"]),
            _cache[24] || (_cache[24] = _createElementVNode("div", { class: "qkcfg-field-hint" }, "选择文件列表的默认排序方式", -1))
          ]),
          _createElementVNode("div", _hoisted_30, [
            _createVNode(_component_v_select, {
              modelValue: config.sort_order,
              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.sort_order) = $event)),
              items: sortOrderOptions.value,
              "item-title": "title",
              "item-value": "value",
              label: "排序方向",
              density: "compact",
              variant: "outlined",
              "hide-details": "auto",
              class: "qkcfg-input"
            }, null, 8, ["modelValue", "items"]),
            _cache[25] || (_cache[25] = _createElementVNode("div", { class: "qkcfg-field-hint" }, "升序 A→Z，降序 Z→A", -1))
          ])
        ])
      ])
    ]),
    _createElementVNode("div", _hoisted_31, [
      _createElementVNode("div", _hoisted_32, [
        _createElementVNode("span", _hoisted_33, [
          _createVNode(_component_v_icon, {
            icon: "mdi-key-outline",
            size: "18",
            color: "#f59e0b",
            class: "mr-1"
          }),
          _cache[27] || (_cache[27] = _createTextVNode(" 认证信息 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_34, [
        _createElementVNode("div", _hoisted_35, [
          _createElementVNode("div", _hoisted_36, [
            _createVNode(_component_v_icon, {
              icon: "mdi-cookie-outline",
              size: "18",
              color: "#f59e0b",
              class: "qkcfg-field__title-icon"
            }),
            _cache[28] || (_cache[28] = _createElementVNode("div", { class: "qkcfg-field__title-text" }, [
              _createElementVNode("label", { class: "qkcfg-field__label" }, "Cookie")
            ], -1))
          ]),
          _createVNode(_component_v_btn, {
            variant: "text",
            density: "compact",
            icon: showCookie.value ? 'mdi-eye-off-outline' : 'mdi-eye-outline',
            onClick: _cache[8] || (_cache[8] = $event => (showCookie.value = !showCookie.value)),
            size: "small"
          }, null, 8, ["icon"])
        ]),
        (!showCookie.value)
          ? (_openBlock(), _createBlock(_component_v_text_field, {
              key: 0,
              modelValue: config.cookie,
              "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.cookie) = $event)),
              type: "password",
              variant: "outlined",
              density: "compact",
              class: "qkcfg-input",
              "hide-details": "",
              autocomplete: "off",
              placeholder: "扫码登录后自动填充，无需手动填写"
            }, null, 8, ["modelValue"]))
          : (_openBlock(), _createBlock(_component_v_textarea, {
              key: 1,
              modelValue: config.cookie,
              "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.cookie) = $event)),
              variant: "outlined",
              density: "compact",
              class: "qkcfg-input",
              "hide-details": "",
              rows: "2",
              "auto-grow": "",
              autocomplete: "off",
              placeholder: "扫码登录后自动填充，无需手动填写"
            }, null, 8, ["modelValue"])),
        _createElementVNode("div", _hoisted_37, [
          _createVNode(_component_v_icon, {
            icon: "mdi-information-outline",
            size: "14",
            class: "mr-1"
          }),
          _cache[29] || (_cache[29] = _createElementVNode("span", null, "通过状态页扫码登录自动获取，无需手动填写。如需手动填写，请从浏览器开发者工具复制完整 Cookie。", -1))
        ])
      ])
    ]),
    _createElementVNode("div", _hoisted_38, [
      _createElementVNode("div", _hoisted_39, [
        _createElementVNode("span", _hoisted_40, [
          _createVNode(_component_v_icon, {
            icon: "mdi-book-information-variant",
            size: "18",
            color: "#6366f1",
            class: "mr-1"
          }),
          _cache[30] || (_cache[30] = _createTextVNode(" 使用说明 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_41, [
        _createElementVNode("div", _hoisted_42, [
          _createElementVNode("p", _hoisted_43, [
            _createVNode(_component_v_icon, {
              icon: "mdi-numeric-1-circle-outline",
              size: "16",
              color: "primary",
              class: "mr-1"
            }),
            _cache[31] || (_cache[31] = _createElementVNode("strong", null, "扫码登录：", -1)),
            _cache[32] || (_cache[32] = _createTextVNode("请在状态页使用二维码，打开夸克 App 扫码完成授权登录 ", -1))
          ]),
          _createElementVNode("p", _hoisted_44, [
            _createVNode(_component_v_icon, {
              icon: "mdi-numeric-2-circle-outline",
              size: "16",
              color: "primary",
              class: "mr-1"
            }),
            _cache[33] || (_cache[33] = _createElementVNode("strong", null, "Cookie 管理：", -1)),
            _cache[34] || (_cache[34] = _createTextVNode("登录成功后 Cookie 会自动保存，刷新页面后无需重新登录 ", -1))
          ]),
          _createElementVNode("p", _hoisted_45, [
            _createVNode(_component_v_icon, {
              icon: "mdi-numeric-3-circle-outline",
              size: "16",
              color: "primary",
              class: "mr-1"
            }),
            _cache[35] || (_cache[35] = _createElementVNode("strong", null, "参数说明：", -1)),
            _cache[36] || (_cache[36] = _createTextVNode("分页大小建议 50-200，排序字段可选 file_name / updated_at / size 等 ", -1))
          ]),
          _createElementVNode("p", _hoisted_46, [
            _createVNode(_component_v_icon, {
              icon: "mdi-numeric-4-circle-outline",
              size: "16",
              color: "primary",
              class: "mr-1"
            }),
            _cache[37] || (_cache[37] = _createElementVNode("strong", null, "彻底删除：", -1)),
            _cache[38] || (_cache[38] = _createTextVNode("开启后会先执行普通删除，再到回收站中匹配同项目并二次删除 ", -1))
          ])
        ])
      ])
    ])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-de617850"]]);

export { Config as default };
