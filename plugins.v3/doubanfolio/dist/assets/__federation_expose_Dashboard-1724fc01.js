import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Dashboard_vue_vue_type_style_index_0_scoped_efd833d5_lang = '';

const {toDisplayString:_toDisplayString,createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createBlock:_createBlock,withModifiers:_withModifiers} = await importShared('vue');


const _hoisted_1 = { class: "dbfdash" };
const _hoisted_2 = { class: "dbfdash-stats" };
const _hoisted_3 = { class: "dbfdash-stat" };
const _hoisted_4 = { class: "dbfdash-stat__value" };
const _hoisted_5 = { class: "dbfdash-stat" };
const _hoisted_6 = { class: "dbfdash-stat__value" };
const _hoisted_7 = { class: "dbfdash-stat" };
const _hoisted_8 = { class: "dbfdash-stat__value" };
const _hoisted_9 = {
  key: 0,
  class: "dbfdash-loading"
};
const _hoisted_10 = { class: "dbfdash-row" };
const _hoisted_11 = ["href", "title"];
const _hoisted_12 = { class: "dbfdash-item__poster" };
const _hoisted_13 = ["src"];
const _hoisted_14 = { class: "dbfdash-item__title" };
const _hoisted_15 = {
  key: 2,
  class: "dbfdash-loading"
};
const _hoisted_16 = { class: "dbfdash-foot" };
const _hoisted_17 = {
  key: 0,
  class: "dbfdash-foot__log"
};
const _hoisted_18 = {
  key: 1,
  class: "dbfdash-foot__log"
};

const {computed,onMounted,onBeforeUnmount,reactive,ref} = await importShared('vue');


const PLUGIN_ID = 'DoubanFolio';


const _sfc_main = {
  __name: 'Dashboard',
  props: {
  api: { type: Object, default: () => ({}) },
  config: { type: Object, default: () => ({ attrs: {} }) },
  allowRefresh: { type: Boolean, default: false },
  refreshInterval: { type: Number, default: 0 },
},
  setup(__props) {

const props = __props;

const summary = reactive({
  wish: 0,
  doing: 0,
  done: 0,
  recent: [],
});
const lastLog = ref(null);
const loading = ref(false);
const posterUrls = reactive({});
const posterTried = new Set();
let timer = null;

async function fetchCoverBlob(poster) {
  const path = String(poster || '').replace(/^https:\/\/img\d+\.doubanio\.com/, '');
  const url = `https://img1.doubanio.com${path}`;
  if (props.api?.get) {
    return await props.api.get(`plugin/${PLUGIN_ID}/cover`, { params: { img: url }, responseType: 'blob' })
  }
  const resp = await fetch(`/api/v1/plugin/${PLUGIN_ID}/cover?img=${encodeURIComponent(url)}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return await resp.blob()
}

async function resolvePosters(list) {
  for (const it of list) {
    const poster = it.poster_hd || it.poster;
    if (!poster || posterUrls[it.sid] || posterTried.has(it.sid)) continue
    posterTried.add(it.sid);
    try {
      const blob = await fetchCoverBlob(poster);
      if (blob && blob.size > 100) posterUrls[it.sid] = URL.createObjectURL(blob);
    } catch (err) {
      // 保持占位图标
    }
  }
}

function releasePosters() {
  for (const url of Object.values(posterUrls)) {
    try { URL.revokeObjectURL(url); } catch (err) { /* ignore */ }
  }
  for (const key of Object.keys(posterUrls)) delete posterUrls[key];
  posterTried.clear();
}

async function request(path) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`;
  if (props.api?.get) return await props.api.get(apiPath, {})
  const response = await fetch(`/api/v1/${apiPath}`);
  return await response.json()
}

async function load() {
  loading.value = true;
  try {
    const data = await request('/collection/summary');
    if (data?.success) {
      summary.wish = Number(data.wish || 0);
      summary.doing = Number(data.doing || 0);
      summary.done = Number(data.done || 0);
      summary.recent = data.recent || [];
      resolvePosters(summary.recent);
    }
  } catch (error) {
    // 静默失败
  }
  try {
    const logs = await request('/logs');
    if (logs?.success && Array.isArray(logs.data) && logs.data.length) {
      lastLog.value = logs.data[0];
    }
  } catch (error) {
    // 静默失败
  }
  loading.value = false;
}

function goFullPage() {
  window.location.hash = '#/plugin-app/DoubanFolio/main';
}

onMounted(() => {
  load();
  const interval = Number(props.refreshInterval || props.config?.attrs?.refresh || 0);
  if (interval > 0) {
    timer = setInterval(load, interval * 1000);
  }
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
  releasePosters();
});

return (_ctx, _cache) => {
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_icon = _resolveComponent("v-icon");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, _toDisplayString(summary.doing), 1),
        _cache[0] || (_cache[0] = _createElementVNode("div", { class: "dbfdash-stat__label" }, "在看", -1))
      ]),
      _createElementVNode("div", _hoisted_5, [
        _createElementVNode("div", _hoisted_6, _toDisplayString(summary.wish), 1),
        _cache[1] || (_cache[1] = _createElementVNode("div", { class: "dbfdash-stat__label" }, "想看", -1))
      ]),
      _createElementVNode("div", _hoisted_7, [
        _createElementVNode("div", _hoisted_8, _toDisplayString(summary.done), 1),
        _cache[2] || (_cache[2] = _createElementVNode("div", { class: "dbfdash-stat__label" }, "看过", -1))
      ])
    ]),
    (loading.value && !summary.recent.length)
      ? (_openBlock(), _createElementBlock("div", _hoisted_9, [
          _createVNode(_component_v_progress_circular, {
            indeterminate: "",
            color: "primary",
            size: "22"
          }),
          _cache[3] || (_cache[3] = _createElementVNode("span", null, "正在加载在看收藏…", -1))
        ]))
      : _createCommentVNode("", true),
    (summary.recent.length)
      ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
          _cache[4] || (_cache[4] = _createElementVNode("div", { class: "dbfdash-sub" }, "最近在看", -1)),
          _createElementVNode("div", _hoisted_10, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(summary.recent, (it) => {
              return (_openBlock(), _createElementBlock("a", {
                key: it.sid,
                class: "dbfdash-item",
                href: `https://movie.douban.com/subject/${it.sid}/`,
                target: "_blank",
                title: it.title
              }, [
                _createElementVNode("div", _hoisted_12, [
                  (posterUrls[it.sid])
                    ? (_openBlock(), _createElementBlock("img", {
                        key: 0,
                        src: posterUrls[it.sid],
                        alt: ""
                      }, null, 8, _hoisted_13))
                    : (_openBlock(), _createBlock(_component_v_icon, {
                        key: 1,
                        icon: "mdi-image-off-outline",
                        size: "18"
                      }))
                ]),
                _createElementVNode("div", _hoisted_14, _toDisplayString(it.title), 1)
              ], 8, _hoisted_11))
            }), 128))
          ])
        ], 64))
      : (!loading.value)
        ? (_openBlock(), _createElementBlock("div", _hoisted_15, "暂无在看条目"))
        : _createCommentVNode("", true),
    _createElementVNode("div", _hoisted_16, [
      (lastLog.value)
        ? (_openBlock(), _createElementBlock("span", _hoisted_17, " 最近同步：" + _toDisplayString(lastLog.value.title) + " · " + _toDisplayString(lastLog.value.result === 'success' ? '成功' : lastLog.value.result === 'not_found' ? '未收录' : '失败'), 1))
        : (_openBlock(), _createElementBlock("span", _hoisted_18, "播放媒体后自动同步到豆瓣")),
      _createElementVNode("a", {
        class: "dbfdash-foot__more",
        href: "#",
        onClick: _withModifiers(goFullPage, ["prevent"])
      }, "查看全部 →")
    ])
  ]))
}
}

};
const Dashboard = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-efd833d5"]]);

export { Dashboard as default };
