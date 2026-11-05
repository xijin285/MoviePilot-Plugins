import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Page_vue_vue_type_style_index_0_scoped_22124396_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,createBlock:_createBlock,normalizeClass:_normalizeClass,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,Fragment:_Fragment,renderList:_renderList,normalizeStyle:_normalizeStyle,createStaticVNode:_createStaticVNode} = await importShared('vue');


const _hoisted_1 = { class: "dbfpage" };
const _hoisted_2 = { class: "dbfpage-topbar" };
const _hoisted_3 = { class: "dbfpage-topbar__left" };
const _hoisted_4 = { class: "dbfpage-topbar__icon" };
const _hoisted_5 = { class: "dbfpage-topbar__right" };
const _hoisted_6 = { class: "dbfpage-card dbfpage-card--hero" };
const _hoisted_7 = { class: "dbfpage-hero" };
const _hoisted_8 = ["src"];
const _hoisted_9 = { class: "dbfpage-hero__info" };
const _hoisted_10 = { class: "dbfpage-hero__name" };
const _hoisted_11 = { class: "dbfpage-hero__desc" };
const _hoisted_12 = {
  key: 0,
  class: "dbfpage-hero__uid"
};
const _hoisted_13 = { class: "dbfpage-stats" };
const _hoisted_14 = {
  class: "dbfpage-stat",
  style: {"--accent":"#2e963d"}
};
const _hoisted_15 = { class: "dbfpage-stat__icon" };
const _hoisted_16 = { class: "dbfpage-stat__value" };
const _hoisted_17 = {
  class: "dbfpage-stat",
  style: {"--accent":"#f59e0b"}
};
const _hoisted_18 = { class: "dbfpage-stat__icon" };
const _hoisted_19 = { class: "dbfpage-stat__value" };
const _hoisted_20 = {
  class: "dbfpage-stat",
  style: {"--accent":"#3b82f6"}
};
const _hoisted_21 = { class: "dbfpage-stat__icon" };
const _hoisted_22 = { class: "dbfpage-stat__value" };
const _hoisted_23 = {
  class: "dbfpage-stat",
  style: {"--accent":"#8b5cf6"}
};
const _hoisted_24 = { class: "dbfpage-stat__icon" };
const _hoisted_25 = { class: "dbfpage-stat__value" };
const _hoisted_26 = { class: "dbfpage-card" };
const _hoisted_27 = { class: "dbfpage-card__header" };
const _hoisted_28 = { class: "dbfpage-card__title d-flex align-center" };
const _hoisted_29 = {
  key: 0,
  class: "dbfpage-log__count"
};
const _hoisted_30 = {
  key: 0,
  class: "dbfpage-logs"
};
const _hoisted_31 = { class: "dbfpage-log__body" };
const _hoisted_32 = { class: "dbfpage-log__msg" };
const _hoisted_33 = { class: "dbfpage-log__meta" };
const _hoisted_34 = { class: "dbfpage-log__time" };
const _hoisted_35 = {
  key: 1,
  class: "dbfpage-log__empty"
};
const _hoisted_36 = { class: "dbfpage-card" };
const _hoisted_37 = { class: "dbfpage-card__header" };
const _hoisted_38 = { class: "dbfpage-card__title d-flex align-center" };
const _hoisted_39 = { class: "dbfpage-card" };
const _hoisted_40 = { class: "dbfpage-card__header" };
const _hoisted_41 = { class: "dbfpage-card__title d-flex align-center" };
const _hoisted_42 = { class: "dbfpage-guide" };

const {onMounted,reactive,ref} = await importShared('vue');


const PLUGIN_ID = 'DoubanFolio';


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

const status = reactive({
  logged_in: false,
  nickname: '',
  uid: '',
  avatar: '',
  enabled: false,
  notify: false,
  processed_count: 0,
  wait_count: 0,
});
const logs = ref([]);
const loading = ref(false);

const RESULT_META = {
  success: { label: '成功', color: '#22c55e' },
  fail: { label: '失败', color: '#ef4444' },
  not_found: { label: '豆瓣未收录', color: '#f59e0b' },
};

function logColor(result) {
  return (RESULT_META[result] || RESULT_META.fail).color
}

function logLabel(result) {
  return (RESULT_META[result] || RESULT_META.fail).label
}

async function request(path) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`;
  if (props.api?.get) {
    return await props.api.get(apiPath, {})
  }
  const response = await fetch(`/api/v1/${apiPath}`);
  return await response.json()
}

async function loadStatus() {
  loading.value = true;
  try {
    const data = await request('/status');
    if (data && typeof data === 'object') {
      status.logged_in = Boolean(data.logged_in);
      status.nickname = data.nickname || '';
      status.uid = data.uid || '';
      status.avatar = data.avatar || '';
      status.enabled = Boolean(data.enabled);
      status.notify = Boolean(data.notify);
      status.processed_count = Number(data.processed_count || 0);
      status.wait_count = Number(data.wait_count || 0);
    }
  } catch (error) {
    // 静默失败，保留上一次结果
  } finally {
    loading.value = false;
  }
  try {
    const data = await request('/logs');
    if (data && Array.isArray(data.data)) {
      logs.value = data.data;
    }
  } catch (error) {
    // 静默失败，保留上一次结果
  }
}

onMounted(loadStatus);

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_chip = _resolveComponent("v-chip");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-movie-open-outline",
            size: "24"
          })
        ]),
        _cache[2] || (_cache[2] = _createElementVNode("div", { class: "dbfpage-topbar__meta" }, [
          _createElementVNode("div", { class: "dbfpage-topbar__title" }, "豆瓣档案"),
          _createElementVNode("div", { class: "dbfpage-topbar__sub" }, "观影记录自动同步到豆瓣")
        ], -1))
      ]),
      _createElementVNode("div", _hoisted_5, [
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-refresh",
          loading: loading.value,
          onClick: loadStatus
        }, {
          default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "刷新", -1)
          ]))]),
          _: 1
        }, 8, ["loading"]),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-cog-outline",
          onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
        }, {
          default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "配置", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-close",
          onClick: _cache[1] || (_cache[1] = $event => (emit('close')))
        }, {
          default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
            _createElementVNode("span", { class: "d-none d-sm-inline" }, "关闭", -1)
          ]))]),
          _: 1
        })
      ])
    ]),
    _createElementVNode("div", _hoisted_6, [
      _createElementVNode("div", _hoisted_7, [
        _createElementVNode("div", {
          class: _normalizeClass(["dbfpage-hero__avatar", { 'dbfpage-hero__avatar--off': !status.logged_in }])
        }, [
          (status.logged_in && status.avatar)
            ? (_openBlock(), _createElementBlock("img", {
                key: 0,
                src: status.avatar,
                alt: "",
                class: "dbfpage-hero__img",
                referrerpolicy: "no-referrer"
              }, null, 8, _hoisted_8))
            : (_openBlock(), _createBlock(_component_v_icon, {
                key: 1,
                icon: status.logged_in ? 'mdi-account-check' : 'mdi-account-off-outline',
                size: "30"
              }, null, 8, ["icon"]))
        ], 2),
        _createElementVNode("div", _hoisted_9, [
          _createElementVNode("div", _hoisted_10, _toDisplayString(status.logged_in ? (status.nickname || '豆瓣账号') : '未登录'), 1),
          _createElementVNode("div", _hoisted_11, [
            (status.logged_in)
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                  _cache[6] || (_cache[6] = _createTextVNode(" Cookie 有效，播放记录会自动同步 ", -1)),
                  (status.uid)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_12, "UID " + _toDisplayString(status.uid), 1))
                    : _createCommentVNode("", true)
                ], 64))
              : (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                  _createTextVNode(" 请到配置页扫码登录，或手动填写 Cookie ")
                ], 64))
          ])
        ]),
        _createVNode(_component_v_chip, {
          color: status.logged_in ? 'success' : 'warning',
          variant: "tonal",
          size: "small",
          "prepend-icon": status.logged_in ? 'mdi-check-decagram' : 'mdi-alert-circle-outline'
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(status.logged_in ? '运行中' : '待配置'), 1)
          ]),
          _: 1
        }, 8, ["color", "prepend-icon"])
      ])
    ]),
    _createElementVNode("div", _hoisted_13, [
      _createElementVNode("div", _hoisted_14, [
        _createElementVNode("div", _hoisted_15, [
          _createVNode(_component_v_icon, {
            icon: "mdi-check-circle-outline",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_16, _toDisplayString(status.processed_count), 1),
        _cache[7] || (_cache[7] = _createElementVNode("div", { class: "dbfpage-stat__label" }, "已同步条目", -1))
      ]),
      _createElementVNode("div", _hoisted_17, [
        _createElementVNode("div", _hoisted_18, [
          _createVNode(_component_v_icon, {
            icon: "mdi-timer-sand",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_19, _toDisplayString(status.wait_count), 1),
        _cache[8] || (_cache[8] = _createElementVNode("div", { class: "dbfpage-stat__label" }, "等待处理", -1))
      ]),
      _createElementVNode("div", _hoisted_20, [
        _createElementVNode("div", _hoisted_21, [
          _createVNode(_component_v_icon, {
            icon: "mdi-power-plug-outline",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_22, _toDisplayString(status.enabled ? '已启用' : '已停用'), 1),
        _cache[9] || (_cache[9] = _createElementVNode("div", { class: "dbfpage-stat__label" }, "插件状态", -1))
      ]),
      _createElementVNode("div", _hoisted_23, [
        _createElementVNode("div", _hoisted_24, [
          _createVNode(_component_v_icon, {
            icon: "mdi-bell-outline",
            size: "18"
          })
        ]),
        _createElementVNode("div", _hoisted_25, _toDisplayString(status.notify ? '开' : '关'), 1),
        _cache[10] || (_cache[10] = _createElementVNode("div", { class: "dbfpage-stat__label" }, "失效通知", -1))
      ])
    ]),
    _createElementVNode("div", _hoisted_26, [
      _createElementVNode("div", _hoisted_27, [
        _createElementVNode("span", _hoisted_28, [
          _createVNode(_component_v_icon, {
            icon: "mdi-history",
            size: "18",
            color: "#3b82f6",
            class: "mr-1"
          }),
          _cache[11] || (_cache[11] = _createTextVNode(" 同步记录 ", -1))
        ]),
        (logs.value.length)
          ? (_openBlock(), _createElementBlock("span", _hoisted_29, "最近 " + _toDisplayString(logs.value.length) + " 条", 1))
          : _createCommentVNode("", true)
      ]),
      (logs.value.length)
        ? (_openBlock(), _createElementBlock("div", _hoisted_30, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(logs.value, (log, index) => {
              return (_openBlock(), _createElementBlock("div", {
                key: index,
                class: "dbfpage-log"
              }, [
                _createElementVNode("span", {
                  class: "dbfpage-log__dot",
                  style: _normalizeStyle({ background: logColor(log.result) })
                }, null, 4),
                _createElementVNode("div", _hoisted_31, [
                  _createElementVNode("div", {
                    class: _normalizeClass(["dbfpage-log__title", { 'dbfpage-log__title--bad': log.result !== 'success' }])
                  }, _toDisplayString(log.title), 3),
                  _createElementVNode("div", _hoisted_32, _toDisplayString(log.message), 1)
                ]),
                _createElementVNode("div", _hoisted_33, [
                  _createElementVNode("span", {
                    class: "dbfpage-log__result",
                    style: _normalizeStyle({ color: logColor(log.result) })
                  }, _toDisplayString(logLabel(log.result)), 5),
                  _createElementVNode("span", _hoisted_34, _toDisplayString(log.time), 1)
                ])
              ]))
            }), 128))
          ]))
        : (_openBlock(), _createElementBlock("div", _hoisted_35, "暂无同步记录，播放媒体后会自动记录每次同步结果"))
    ]),
    _createElementVNode("div", _hoisted_36, [
      _createElementVNode("div", _hoisted_37, [
        _createElementVNode("span", _hoisted_38, [
          _createVNode(_component_v_icon, {
            icon: "mdi-sync",
            size: "18",
            color: "#2e963d",
            class: "mr-1"
          }),
          _cache[12] || (_cache[12] = _createTextVNode(" 同步规则 ", -1))
        ])
      ]),
      _cache[13] || (_cache[13] = _createStaticVNode("<div class=\"dbfpage-rules\" data-v-22124396><div class=\"dbfpage-rule\" data-v-22124396><span class=\"dbfpage-rule__dot\" style=\"background:#3b82f6;\" data-v-22124396></span><span class=\"dbfpage-rule__text\" data-v-22124396><strong data-v-22124396>开始播放</strong> → 条目标记为「在看」</span></div><div class=\"dbfpage-rule\" data-v-22124396><span class=\"dbfpage-rule__dot\" style=\"background:#22c55e;\" data-v-22124396></span><span class=\"dbfpage-rule__text\" data-v-22124396><strong data-v-22124396>播放完成</strong> → 条目标记为「看过」并写入进度</span></div><div class=\"dbfpage-rule\" data-v-22124396><span class=\"dbfpage-rule__dot\" style=\"background:#f59e0b;\" data-v-22124396></span><span class=\"dbfpage-rule__text\" data-v-22124396><strong data-v-22124396>Cookie 失效</strong> → 每小时检测一次，按设置推送通知</span></div></div>", 1))
    ]),
    _createElementVNode("div", _hoisted_39, [
      _createElementVNode("div", _hoisted_40, [
        _createElementVNode("span", _hoisted_41, [
          _createVNode(_component_v_icon, {
            icon: "mdi-information-outline",
            size: "18",
            color: "#6366f1",
            class: "mr-1"
          }),
          _cache[14] || (_cache[14] = _createTextVNode(" 前提条件 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_42, [
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-1-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[15] || (_cache[15] = _createTextVNode("媒体服务器需开启 ", -1)),
          _cache[16] || (_cache[16] = _createElementVNode("strong", null, "Webhook", -1)),
          _cache[17] || (_cache[17] = _createTextVNode("，否则接收不到播放事件。", -1))
        ]),
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-2-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[18] || (_cache[18] = _createTextVNode("配置页扫码登录后，Cookie 由插件自动维护与续期。", -1))
        ]),
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-3-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[19] || (_cache[19] = _createTextVNode("豆瓣条目匹配依赖片名，命名不规范时可能匹配失败。", -1))
        ])
      ])
    ])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-22124396"]]);

export { Page as default };
