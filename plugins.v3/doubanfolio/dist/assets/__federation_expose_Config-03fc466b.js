import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

const Config_vue_vue_type_style_index_0_scoped_25c6cfd8_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,normalizeClass:_normalizeClass,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,Transition:_Transition,createTextVNode:_createTextVNode,createBlock:_createBlock,Fragment:_Fragment} = await importShared('vue');


const _hoisted_1 = { class: "dbfcfg-page" };
const _hoisted_2 = { class: "dbfcfg-topbar" };
const _hoisted_3 = { class: "dbfcfg-topbar__left" };
const _hoisted_4 = { class: "dbfcfg-topbar__icon" };
const _hoisted_5 = { class: "dbfcfg-topbar__right" };
const _hoisted_6 = { class: "dbfcfg-card" };
const _hoisted_7 = { class: "dbfcfg-card__header" };
const _hoisted_8 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_9 = {
  key: 0,
  class: "dbfcfg-account"
};
const _hoisted_10 = { class: "dbfcfg-account__avatar" };
const _hoisted_11 = ["src"];
const _hoisted_12 = { class: "dbfcfg-account__info" };
const _hoisted_13 = { class: "dbfcfg-account__name" };
const _hoisted_14 = { class: "dbfcfg-account__desc" };
const _hoisted_15 = {
  key: 0,
  class: "dbfcfg-account__cookie"
};
const _hoisted_16 = {
  key: 1,
  class: "dbfcfg-qr"
};
const _hoisted_17 = { class: "dbfcfg-qr__box" };
const _hoisted_18 = ["src"];
const _hoisted_19 = {
  key: 0,
  class: "dbfcfg-qr__mask"
};
const _hoisted_20 = {
  key: 1,
  class: "dbfcfg-qr__mask"
};
const _hoisted_21 = {
  key: 1,
  class: "dbfcfg-qr__placeholder"
};
const _hoisted_22 = { class: "mt-2" };
const _hoisted_23 = { class: "dbfcfg-qr__side" };
const _hoisted_24 = { class: "dbfcfg-qr__title" };
const _hoisted_25 = { class: "dbfcfg-qr__text" };
const _hoisted_26 = {
  key: 0,
  class: "dbfcfg-qr__error"
};
const _hoisted_27 = { class: "dbfcfg-qr__actions" };
const _hoisted_28 = { class: "dbfcfg-card" };
const _hoisted_29 = { class: "dbfcfg-card__header" };
const _hoisted_30 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_31 = { class: "dbfcfg-switch-grid" };
const _hoisted_32 = { class: "dbfcfg-switch-item__main" };
const _hoisted_33 = { class: "dbfcfg-switch-item__main" };
const _hoisted_34 = { class: "dbfcfg-switch-item__main" };
const _hoisted_35 = { class: "dbfcfg-switch-item__main" };
const _hoisted_36 = { class: "dbfcfg-hint" };
const _hoisted_37 = { class: "dbfcfg-card" };
const _hoisted_38 = { class: "dbfcfg-card__header" };
const _hoisted_39 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_40 = { class: "dbfcfg-switch-grid" };
const _hoisted_41 = { class: "dbfcfg-switch-item__main" };
const _hoisted_42 = { class: "dbfcfg-switch-item__main" };
const _hoisted_43 = { class: "dbfcfg-form-grid" };
const _hoisted_44 = { class: "dbfcfg-form-item" };
const _hoisted_45 = { class: "dbfcfg-hint" };
const _hoisted_46 = { class: "dbfcfg-card" };
const _hoisted_47 = { class: "dbfcfg-card__header" };
const _hoisted_48 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_49 = { class: "dbfcfg-form-grid" };
const _hoisted_50 = { class: "dbfcfg-form-item" };
const _hoisted_51 = { class: "dbfcfg-form-item" };
const _hoisted_52 = { class: "dbfcfg-card" };
const _hoisted_53 = { class: "dbfcfg-card__header" };
const _hoisted_54 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_55 = { class: "dbfcfg-form-grid dbfcfg-form-grid--four" };
const _hoisted_56 = { class: "dbfcfg-form-item" };
const _hoisted_57 = { class: "dbfcfg-form-item" };
const _hoisted_58 = { class: "dbfcfg-form-item" };
const _hoisted_59 = { class: "dbfcfg-form-item" };
const _hoisted_60 = { class: "dbfcfg-card" };
const _hoisted_61 = { class: "dbfcfg-card__header" };
const _hoisted_62 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_63 = { class: "dbfcfg-hint" };
const _hoisted_64 = { class: "dbfcfg-card" };
const _hoisted_65 = { class: "dbfcfg-card__header" };
const _hoisted_66 = { class: "dbfcfg-card__title d-flex align-center" };
const _hoisted_67 = { class: "dbfcfg-guide" };

const {computed,onBeforeUnmount,onMounted,reactive,ref} = await importShared('vue');


const PLUGIN_ID = 'DoubanFolio';
const POLL_INTERVAL = 2000;


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
  private: true,
  first: true,
  user: '',
  exclude: '',
  cookie: '',
  pc_month: 3,
  pc_num: 50,
  mobile_month: 2,
  mobile_num: 15,
  notify: false,
  auto_subscribe: false,
  auto_subscribe_interval: 5,
  auto_subscribe_existing: false,
  ...props.initialConfig,
});

const status = reactive({ logged_in: false, nickname: '', avatar: '' });
const qr = reactive({ img: '', status: 'idle', error: '', expire_in: 0 });
const loading = ref(false);
const saving = ref(false);
const autoChecking = ref(false);
const qrLoading = ref(false);
const showCookie = ref(false);
const message = reactive({ show: false, type: 'info', text: '' });

let messageTimer = null;
let pollTimer = null;
let countdownTimer = null;
let pollSeq = 0;

const cookiePreview = computed(() => {
  const raw = String(config.cookie || '');
  if (!raw) return ''
  const hit = raw.match(/dbcl2="?(\d+):/i);
  return hit ? `UID ${hit[1]}` : ''
});

const countdownText = computed(() => {
  if (!qr.expire_in || qr.expire_in <= 0) return ''
  if (qr.status === 'login') return ''
  return `${Math.floor(qr.expire_in / 60)} 分 ${qr.expire_in % 60} 秒后过期`
});

const qrTitle = computed(() => {
  if (qr.status === 'scanned') return '已扫码，请在手机上确认'
  if (qr.status === 'expired') return '二维码已过期'
  if (qr.status === 'error') return '二维码状态异常'
  return '使用豆瓣 APP 扫码登录'
});

const qrTip = computed(() => {
  if (qr.status === 'scanned') return '确认后本页面会自动填入 Cookie，无需手动操作。'
  if (qr.status === 'expired') return '点击「刷新二维码」重新获取即可。'
  if (qr.status === 'error') return qr.error || '可点击刷新重试，或手动填写下方 Cookie。'
  return '打开豆瓣 APP → 右上角扫一扫 → 扫描左侧二维码 → 确认登录。'
});

const qrColor = computed(() => {
  if (qr.status === 'scanned') return '#22c55e'
  if (qr.status === 'expired' || qr.status === 'error') return '#f59e0b'
  return '#2e963d'
});

const qrIcon = computed(() => {
  if (qr.status === 'scanned') return 'mdi-cellphone-check'
  if (qr.status === 'expired') return 'mdi-qrcode-remove'
  if (qr.status === 'error') return 'mdi-alert-circle-outline'
  return 'mdi-qrcode-scan'
});

function clearMessageTimer() {
  if (messageTimer) {
    clearTimeout(messageTimer);
    messageTimer = null;
  }
}

function pushMessage(text, type = 'info') {
  clearMessageTimer();
  message.text = text;
  message.type = type;
  message.show = true;
  messageTimer = setTimeout(() => {
    message.show = false;
    messageTimer = null;
  }, type === 'error' ? 6000 : 3500);
}

async function request(path, options = {}) {
  const apiPath = `plugin/${PLUGIN_ID}${path}`;
  const method = (options.method || 'GET').toUpperCase();
  try {
    if (method === 'POST') {
      if (props.api?.post) {
        return await props.api.post(apiPath, options.body || {}, {})
      }
    } else if (props.api?.get) {
      return await props.api.get(apiPath, options.params || {})
    }
    const response = await fetch(`/api/v1/${apiPath}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: method === 'POST' ? JSON.stringify(options.body || {}) : undefined,
    });
    return await response.json()
  } catch (error) {
    throw new Error(error?.message || '请求失败')
  }
}

function applyConfig(data = {}) {
  if (!data || typeof data !== 'object') return
  if ('enabled' in data) config.enabled = Boolean(data.enabled);
  if ('private' in data) config.private = Boolean(data.private);
  if ('first' in data) config.first = Boolean(data.first);
  if ('user' in data) config.user = data.user || '';
  if ('exclude' in data) config.exclude = data.exclude || '';
  if ('cookie' in data) config.cookie = data.cookie || '';
  if ('pc_month' in data) config.pc_month = Number(data.pc_month || 3);
  if ('pc_num' in data) config.pc_num = Number(data.pc_num || 50);
  if ('mobile_month' in data) config.mobile_month = Number(data.mobile_month || 2);
  if ('mobile_num' in data) config.mobile_num = Number(data.mobile_num || 15);
  if ('notify' in data) config.notify = Boolean(data.notify);
  if ('auto_subscribe' in data) config.auto_subscribe = Boolean(data.auto_subscribe);
  if ('auto_subscribe_interval' in data) config.auto_subscribe_interval = Number(data.auto_subscribe_interval || 5);
  if ('auto_subscribe_existing' in data) config.auto_subscribe_existing = Boolean(data.auto_subscribe_existing);
  if ('logged_in' in data) status.logged_in = Boolean(data.logged_in);
  if ('nickname' in data) status.nickname = data.nickname || '';
  if ('avatar' in data) status.avatar = data.avatar || '';
}

async function loadConfig() {
  loading.value = true;
  try {
    const data = await request('/config');
    applyConfig(data);
    if (status.logged_in) {
      stopPolling();
    } else {
      await startQr();
    }
  } catch (error) {
    pushMessage(`加载配置失败：${error.message}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function saveConfig(silent = false) {
  saving.value = true;
  try {
    const result = await request('/config', {
      method: 'POST',
      body: {
        enabled: config.enabled,
        private: config.private,
        first: config.first,
        user: config.user,
        exclude: config.exclude,
        cookie: config.cookie,
        pc_month: Number(config.pc_month) || 3,
        pc_num: Number(config.pc_num) || 50,
        mobile_month: Number(config.mobile_month) || 2,
        mobile_num: Number(config.mobile_num) || 15,
        notify: config.notify,
        auto_subscribe: config.auto_subscribe,
        auto_subscribe_interval: Number(config.auto_subscribe_interval) || 5,
        auto_subscribe_existing: config.auto_subscribe_existing,
      },
    });
    if (result && result.success === false) {
      throw new Error(result.message || '保存失败')
    }
    if (result?.data) applyConfig(result.data);
    if (!silent) pushMessage('配置已保存', 'success');
    return true
  } catch (error) {
    pushMessage(`保存失败：${error.message}`, 'error');
    return false
  } finally {
    saving.value = false;
  }
}

async function runAutoCheck() {
  if (!config.auto_subscribe) {
    pushMessage('请先开启「自动订阅想看」并保存', 'info');
    return
  }
  autoChecking.value = true;
  try {
    const data = await request('/auto_subscribe/check', { method: 'POST', body: { force: true } });
    if (data?.success) pushMessage(data.message || '检查完成', 'success');
    else pushMessage(data?.message || '检查失败', 'error');
  } catch (error) {
    pushMessage(`检查失败：${error.message}`, 'error');
  } finally {
    autoChecking.value = false;
  }
}

function stopPolling() {
  pollSeq += 1;
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

function startCountdown() {
  stopCountdown();
  countdownTimer = setInterval(() => {
    if (status.logged_in) return
    if (qr.status !== 'pending' && qr.status !== 'scanned') return
    if (qr.expire_in > 0) {
      qr.expire_in -= 1;
      if (qr.expire_in === 0) {
        qr.status = 'expired';
        stopPolling();
      }
    }
  }, 1000);
}

async function startQr() {
  if (qrLoading.value) return
  qrLoading.value = true;
  stopPolling();
  try {
    const data = await request('/qr/start');
    qr.img = data?.img || '';
    qr.status = data?.status || 'pending';
    qr.error = data?.error || '';
    qr.expire_in = Number(data?.expire_in || 0);
    if (qr.status === 'login' && data?.cookie) {
      await handleLogin(data);
      return
    }
    if (qr.status === 'pending' || qr.status === 'scanned') {
      beginPolling();
      startCountdown();
    } else if (qr.error) {
      pushMessage(qr.error, 'error');
    }
  } catch (error) {
    qr.status = 'error';
    qr.error = error.message;
    pushMessage(`获取二维码失败：${error.message}`, 'error');
  } finally {
    qrLoading.value = false;
  }
}

function beginPolling() {
  stopPolling();
  const seq = ++pollSeq;
  const tick = async () => {
    if (seq !== pollSeq) return
    try {
      const data = await request('/qr/poll');
      if (seq !== pollSeq) return
      if (data?.img) qr.img = data.img;
      if (data?.error) qr.error = data.error;
      if (data?.status) qr.status = data.status;
      if (typeof data?.expire_in === 'number') qr.expire_in = data.expire_in;
      if (qr.status === 'login') {
        await handleLogin(data || {});
        return
      }
      if (qr.status === 'expired' || qr.status === 'error') {
        stopPolling();
        return
      }
    } catch (error) {
      // 单次轮询失败不打断，交给下一轮
    }
    if (seq === pollSeq) {
      pollTimer = setTimeout(tick, POLL_INTERVAL);
    }
  };
  pollTimer = setTimeout(tick, 1200);
}

async function handleLogin(data) {
  stopPolling();
  stopCountdown();
  const cookie = data?.cookie || '';
  status.logged_in = true;
  status.nickname = data?.nickname || '';
  status.avatar = data?.avatar || '';
  if (cookie) config.cookie = cookie;
  qr.status = 'login';
  qr.error = '';
  await saveConfig(true);
  // 保存后重新拉取一次配置，带回头像等登录信息
  try {
    const fresh = await request('/config');
    applyConfig(fresh);
  } catch (error) {
    // 静默失败，保留本地状态
  }
  const who = status.nickname ? `：${status.nickname}` : '';
  pushMessage(`扫码登录成功${who}，Cookie 已保存`, 'success');
}

async function relogin() {
  status.logged_in = false;
  status.nickname = '';
  status.avatar = '';
  config.cookie = '';
  qr.img = '';
  qr.status = 'idle';
  qr.error = '';
  qr.expire_in = 0;
  await startQr();
}

onMounted(loadConfig);

onBeforeUnmount(() => {
  stopPolling();
  stopCountdown();
  clearMessageTimer();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_btn_group = _resolveComponent("v-btn-group");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_textarea = _resolveComponent("v-textarea");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-movie-open-outline",
            size: "24"
          })
        ]),
        _cache[21] || (_cache[21] = _createElementVNode("div", { class: "dbfcfg-topbar__meta" }, [
          _createElementVNode("div", { class: "dbfcfg-topbar__title" }, "豆瓣档案 · 配置"),
          _createElementVNode("div", { class: "dbfcfg-topbar__sub" }, "扫码登录与同步参数设置")
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
                _cache[22] || (_cache[22] = _createElementVNode("span", { class: "d-none d-sm-inline" }, "状态页", -1))
              ]),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              color: "primary",
              loading: saving.value,
              onClick: _cache[1] || (_cache[1] = $event => (saveConfig())),
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
                _cache[23] || (_cache[23] = _createElementVNode("span", { class: "d-none d-sm-inline" }, "保存", -1))
              ]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: _cache[2] || (_cache[2] = $event => (emit('close'))),
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-close",
                  size: "18"
                }),
                _cache[24] || (_cache[24] = _createElementVNode("span", { class: "d-none d-sm-inline" }, "关闭", -1))
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ])
    ]),
    _createVNode(_Transition, { name: "dbfcfg-slide" }, {
      default: _withCtx(() => [
        (message.show)
          ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: _normalizeClass(["dbfcfg-toast", `dbfcfg-toast--${message.type}`])
            }, [
              _createVNode(_component_v_icon, {
                icon: message.type === 'success' ? 'mdi-check-circle' : message.type === 'error' ? 'mdi-alert-circle' : 'mdi-information',
                size: "18"
              }, null, 8, ["icon"]),
              _createElementVNode("span", null, _toDisplayString(message.text), 1),
              _createElementVNode("button", {
                class: "dbfcfg-toast__close",
                onClick: _cache[3] || (_cache[3] = $event => (message.show = false))
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
            icon: "mdi-account-circle-outline",
            size: "18",
            color: "#2e963d",
            class: "mr-1"
          }),
          _cache[25] || (_cache[25] = _createTextVNode(" 豆瓣账号 ", -1))
        ]),
        (status.logged_in)
          ? (_openBlock(), _createBlock(_component_v_chip, {
              key: 0,
              size: "x-small",
              variant: "tonal",
              color: "success",
              "prepend-icon": "mdi-check-decagram"
            }, {
              default: _withCtx(() => [...(_cache[26] || (_cache[26] = [
                _createTextVNode(" 已登录 ", -1)
              ]))]),
              _: 1
            }))
          : (_openBlock(), _createBlock(_component_v_chip, {
              key: 1,
              size: "x-small",
              variant: "tonal",
              color: "warning",
              "prepend-icon": "mdi-alert-circle-outline"
            }, {
              default: _withCtx(() => [...(_cache[27] || (_cache[27] = [
                _createTextVNode(" 未登录 ", -1)
              ]))]),
              _: 1
            }))
      ]),
      (status.logged_in)
        ? (_openBlock(), _createElementBlock("div", _hoisted_9, [
            _createElementVNode("div", _hoisted_10, [
              (status.avatar)
                ? (_openBlock(), _createElementBlock("img", {
                    key: 0,
                    src: status.avatar,
                    alt: "",
                    class: "dbfcfg-account__img",
                    referrerpolicy: "no-referrer"
                  }, null, 8, _hoisted_11))
                : (_openBlock(), _createBlock(_component_v_icon, {
                    key: 1,
                    icon: "mdi-account",
                    size: "26"
                  }))
            ]),
            _createElementVNode("div", _hoisted_12, [
              _createElementVNode("div", _hoisted_13, _toDisplayString(status.nickname || '豆瓣账号'), 1),
              _createElementVNode("div", _hoisted_14, [
                _cache[28] || (_cache[28] = _createTextVNode(" Cookie 已保存，可正常同步观影记录 ", -1)),
                (cookiePreview.value)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_15, _toDisplayString(cookiePreview.value), 1))
                  : _createCommentVNode("", true)
              ])
            ]),
            _createVNode(_component_v_btn, {
              variant: "tonal",
              color: "primary",
              size: "small",
              "prepend-icon": "mdi-qrcode-scan",
              onClick: relogin
            }, {
              default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
                _createTextVNode(" 重新扫码 ", -1)
              ]))]),
              _: 1
            })
          ]))
        : (_openBlock(), _createElementBlock("div", _hoisted_16, [
            _createElementVNode("div", _hoisted_17, [
              (qr.img)
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                    _createElementVNode("img", {
                      src: qr.img,
                      alt: "豆瓣登录二维码",
                      class: "dbfcfg-qr__image"
                    }, null, 8, _hoisted_18),
                    (qr.status === 'scanned')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-cellphone-check",
                            size: "34",
                            color: "#22c55e"
                          }),
                          _cache[30] || (_cache[30] = _createElementVNode("span", null, "已扫码，请在手机确认", -1))
                        ]))
                      : (qr.status === 'expired')
                        ? (_openBlock(), _createElementBlock("div", _hoisted_20, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-qrcode-remove",
                              size: "34",
                              color: "#f59e0b"
                            }),
                            _cache[31] || (_cache[31] = _createElementVNode("span", null, "二维码已过期", -1))
                          ]))
                        : _createCommentVNode("", true)
                  ], 64))
                : (_openBlock(), _createElementBlock("div", _hoisted_21, [
                    (qrLoading.value)
                      ? (_openBlock(), _createBlock(_component_v_progress_circular, {
                          key: 0,
                          indeterminate: "",
                          size: "28",
                          color: "primary"
                        }))
                      : (_openBlock(), _createBlock(_component_v_icon, {
                          key: 1,
                          icon: "mdi-qrcode",
                          size: "56",
                          color: "grey"
                        })),
                    _createElementVNode("span", _hoisted_22, _toDisplayString(qrLoading.value ? '正在获取二维码...' : '二维码未加载'), 1)
                  ]))
            ]),
            _createElementVNode("div", _hoisted_23, [
              _createElementVNode("div", _hoisted_24, [
                _createVNode(_component_v_icon, {
                  icon: qrIcon.value,
                  size: "18",
                  color: qrColor.value,
                  class: "mr-1"
                }, null, 8, ["icon", "color"]),
                _createTextVNode(" " + _toDisplayString(qrTitle.value), 1)
              ]),
              _createElementVNode("div", _hoisted_25, _toDisplayString(qrTip.value), 1),
              (qr.error)
                ? (_openBlock(), _createElementBlock("div", _hoisted_26, _toDisplayString(qr.error), 1))
                : _createCommentVNode("", true),
              _createElementVNode("div", _hoisted_27, [
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "tonal",
                  color: "primary",
                  "prepend-icon": "mdi-refresh",
                  loading: qrLoading.value,
                  onClick: _cache[4] || (_cache[4] = $event => (startQr()))
                }, {
                  default: _withCtx(() => [...(_cache[32] || (_cache[32] = [
                    _createTextVNode(" 刷新二维码 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"]),
                (countdownText.value)
                  ? (_openBlock(), _createElementBlock("span", {
                      key: 0,
                      class: _normalizeClass(["dbfcfg-qr__countdown", { 'dbfcfg-qr__countdown--warn': qr.expire_in <= 30 }])
                    }, [
                      _createVNode(_component_v_icon, {
                        icon: "mdi-timer-outline",
                        size: "14",
                        class: "mr-1"
                      }),
                      _createTextVNode(_toDisplayString(countdownText.value), 1)
                    ], 2))
                  : _createCommentVNode("", true)
              ])
            ])
          ]))
    ]),
    _createElementVNode("div", _hoisted_28, [
      _createElementVNode("div", _hoisted_29, [
        _createElementVNode("span", _hoisted_30, [
          _createVNode(_component_v_icon, {
            icon: "mdi-toggle-switch-outline",
            size: "18",
            color: "#8b5cf6",
            class: "mr-1"
          }),
          _cache[33] || (_cache[33] = _createTextVNode(" 基础设置 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_31, [
        _createElementVNode("div", {
          class: _normalizeClass(["dbfcfg-switch-item", { 'dbfcfg-switch-item--active': config.enabled }]),
          style: {"--accent":"#8b5cf6"}
        }, [
          _createElementVNode("div", _hoisted_32, [
            _createVNode(_component_v_icon, {
              icon: "mdi-power-plug",
              size: "18"
            }),
            _cache[34] || (_cache[34] = _createElementVNode("span", null, "启用插件", -1))
          ]),
          _createVNode(_component_v_switch, {
            modelValue: config.enabled,
            "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.enabled) = $event)),
            color: "#8b5cf6",
            density: "compact",
            "hide-details": "",
            inset: ""
          }, null, 8, ["modelValue"])
        ], 2),
        _createElementVNode("div", {
          class: _normalizeClass(["dbfcfg-switch-item", { 'dbfcfg-switch-item--active': config.private }]),
          style: {"--accent":"#22c55e"}
        }, [
          _createElementVNode("div", _hoisted_33, [
            _createVNode(_component_v_icon, {
              icon: "mdi-eye-off-outline",
              size: "18"
            }),
            _cache[35] || (_cache[35] = _createElementVNode("span", null, "仅自己可见", -1))
          ]),
          _createVNode(_component_v_switch, {
            modelValue: config.private,
            "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.private) = $event)),
            color: "#22c55e",
            density: "compact",
            "hide-details": "",
            inset: ""
          }, null, 8, ["modelValue"])
        ], 2),
        _createElementVNode("div", {
          class: _normalizeClass(["dbfcfg-switch-item", { 'dbfcfg-switch-item--active': config.first }]),
          style: {"--accent":"#3b82f6"}
        }, [
          _createElementVNode("div", _hoisted_34, [
            _createVNode(_component_v_icon, {
              icon: "mdi-playlist-check",
              size: "18"
            }),
            _cache[36] || (_cache[36] = _createElementVNode("span", null, "首集同步", -1))
          ]),
          _createVNode(_component_v_switch, {
            modelValue: config.first,
            "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.first) = $event)),
            color: "#3b82f6",
            density: "compact",
            "hide-details": "",
            inset: ""
          }, null, 8, ["modelValue"])
        ], 2),
        _createElementVNode("div", {
          class: _normalizeClass(["dbfcfg-switch-item", { 'dbfcfg-switch-item--active': config.notify }]),
          style: {"--accent":"#f59e0b"}
        }, [
          _createElementVNode("div", _hoisted_35, [
            _createVNode(_component_v_icon, {
              icon: "mdi-bell-outline",
              size: "18"
            }),
            _cache[37] || (_cache[37] = _createElementVNode("span", null, "发送通知", -1))
          ]),
          _createVNode(_component_v_switch, {
            modelValue: config.notify,
            "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.notify) = $event)),
            color: "#f59e0b",
            density: "compact",
            "hide-details": "",
            inset: ""
          }, null, 8, ["modelValue"])
        ], 2)
      ]),
      _createElementVNode("div", _hoisted_36, [
        _createVNode(_component_v_icon, {
          icon: "mdi-information-outline",
          size: "14",
          class: "mr-1"
        }),
        _cache[38] || (_cache[38] = _createTextVNode(" 首集同步会在播放第一集时把剧集整体标记为「在看」；通知用于 Cookie 失效提醒。 ", -1))
      ])
    ]),
    _createElementVNode("div", _hoisted_37, [
      _createElementVNode("div", _hoisted_38, [
        _createElementVNode("span", _hoisted_39, [
          _createVNode(_component_v_icon, {
            icon: "mdi-auto-fix",
            size: "18",
            color: "#2e963d",
            class: "mr-1"
          }),
          _cache[39] || (_cache[39] = _createTextVNode(" 想看自动订阅 ", -1))
        ]),
        _createVNode(_component_v_btn, {
          variant: "tonal",
          color: "primary",
          size: "small",
          "prepend-icon": "mdi-play-circle-outline",
          loading: autoChecking.value,
          onClick: runAutoCheck
        }, {
          default: _withCtx(() => [...(_cache[40] || (_cache[40] = [
            _createTextVNode(" 立即检查 ", -1)
          ]))]),
          _: 1
        }, 8, ["loading"])
      ]),
      _createElementVNode("div", _hoisted_40, [
        _createElementVNode("div", {
          class: _normalizeClass(["dbfcfg-switch-item", { 'dbfcfg-switch-item--active': config.auto_subscribe }]),
          style: {"--accent":"#2e963d"}
        }, [
          _createElementVNode("div", _hoisted_41, [
            _createVNode(_component_v_icon, {
              icon: "mdi-movie-plus-outline",
              size: "18"
            }),
            _cache[41] || (_cache[41] = _createElementVNode("span", null, "自动订阅想看", -1))
          ]),
          _createVNode(_component_v_switch, {
            modelValue: config.auto_subscribe,
            "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.auto_subscribe) = $event)),
            color: "#2e963d",
            density: "compact",
            "hide-details": "",
            inset: ""
          }, null, 8, ["modelValue"])
        ], 2),
        _createElementVNode("div", {
          class: _normalizeClass(["dbfcfg-switch-item", { 'dbfcfg-switch-item--active': config.auto_subscribe_existing }]),
          style: {"--accent":"#f59e0b"}
        }, [
          _createElementVNode("div", _hoisted_42, [
            _createVNode(_component_v_icon, {
              icon: "mdi-playlist-plus-outline",
              size: "18"
            }),
            _cache[42] || (_cache[42] = _createElementVNode("span", null, "已有想看也订阅", -1))
          ]),
          _createVNode(_component_v_switch, {
            modelValue: config.auto_subscribe_existing,
            "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.auto_subscribe_existing) = $event)),
            color: "#f59e0b",
            density: "compact",
            "hide-details": "",
            inset: ""
          }, null, 8, ["modelValue"])
        ], 2)
      ]),
      _createElementVNode("div", _hoisted_43, [
        _createElementVNode("div", _hoisted_44, [
          _createVNode(_component_v_text_field, {
            modelValue: config.auto_subscribe_interval,
            "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.auto_subscribe_interval) = $event)),
            modelModifiers: { number: true },
            label: "检查间隔（分钟）",
            type: "number",
            min: "1",
            max: "59",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[43] || (_cache[43] = _createElementVNode("div", { class: "dbfcfg-hint" }, "每 N 分钟检查豆瓣新增「想看」并自动加入 MoviePilot 订阅；保存后若未生效请重载插件", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_45, [
        _createVNode(_component_v_icon, {
          icon: "mdi-information-outline",
          size: "14",
          class: "mr-1"
        }),
        _cache[44] || (_cache[44] = _createTextVNode(" 首次开启只建立基线，不会批量订阅已有想看；只有勾选「已有想看也订阅」时才会处理现有条目。自动订阅结果会写入「同步」页签。 ", -1))
      ])
    ]),
    _createElementVNode("div", _hoisted_46, [
      _createElementVNode("div", _hoisted_47, [
        _createElementVNode("span", _hoisted_48, [
          _createVNode(_component_v_icon, {
            icon: "mdi-account-filter-outline",
            size: "18",
            color: "#2e963d",
            class: "mr-1"
          }),
          _cache[45] || (_cache[45] = _createTextVNode(" 同步范围 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_49, [
        _createElementVNode("div", _hoisted_50, [
          _createVNode(_component_v_text_field, {
            modelValue: config.user,
            "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.user) = $event)),
            label: "只同步这些用户",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            placeholder: "用英文逗号分隔，留空为全部",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[46] || (_cache[46] = _createElementVNode("div", { class: "dbfcfg-hint" }, "按媒体服务器用户名过滤，多个用 , 分隔", -1))
        ]),
        _createElementVNode("div", _hoisted_51, [
          _createVNode(_component_v_text_field, {
            modelValue: config.exclude,
            "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.exclude) = $event)),
            label: "排除的剧名",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            placeholder: "用英文逗号分隔",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[47] || (_cache[47] = _createElementVNode("div", { class: "dbfcfg-hint" }, "命中关键词的条目不会同步到豆瓣", -1))
        ])
      ])
    ]),
    _createElementVNode("div", _hoisted_52, [
      _createElementVNode("div", _hoisted_53, [
        _createElementVNode("span", _hoisted_54, [
          _createVNode(_component_v_icon, {
            icon: "mdi-format-list-numbered",
            size: "18",
            color: "#6366f1",
            class: "mr-1"
          }),
          _cache[48] || (_cache[48] = _createTextVNode(" 展示数量 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_55, [
        _createElementVNode("div", _hoisted_56, [
          _createVNode(_component_v_text_field, {
            modelValue: config.pc_month,
            "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.pc_month) = $event)),
            modelModifiers: { number: true },
            label: "大屏月数",
            type: "number",
            min: "1",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[49] || (_cache[49] = _createElementVNode("div", { class: "dbfcfg-hint" }, "大屏仪表盘展示最近几个月", -1))
        ]),
        _createElementVNode("div", _hoisted_57, [
          _createVNode(_component_v_text_field, {
            modelValue: config.pc_num,
            "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.pc_num) = $event)),
            modelModifiers: { number: true },
            label: "大屏条数",
            type: "number",
            min: "1",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[50] || (_cache[50] = _createElementVNode("div", { class: "dbfcfg-hint" }, "大屏每次最多显示的条目数", -1))
        ]),
        _createElementVNode("div", _hoisted_58, [
          _createVNode(_component_v_text_field, {
            modelValue: config.mobile_month,
            "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((config.mobile_month) = $event)),
            modelModifiers: { number: true },
            label: "小屏月数",
            type: "number",
            min: "1",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[51] || (_cache[51] = _createElementVNode("div", { class: "dbfcfg-hint" }, "手机端展示最近几个月", -1))
        ]),
        _createElementVNode("div", _hoisted_59, [
          _createVNode(_component_v_text_field, {
            modelValue: config.mobile_num,
            "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((config.mobile_num) = $event)),
            modelModifiers: { number: true },
            label: "小屏条数",
            type: "number",
            min: "1",
            density: "compact",
            variant: "outlined",
            "hide-details": "auto",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]),
          _cache[52] || (_cache[52] = _createElementVNode("div", { class: "dbfcfg-hint" }, "手机端每次最多显示的条目数", -1))
        ])
      ])
    ]),
    _createElementVNode("div", _hoisted_60, [
      _createElementVNode("div", _hoisted_61, [
        _createElementVNode("span", _hoisted_62, [
          _createVNode(_component_v_icon, {
            icon: "mdi-cookie-outline",
            size: "18",
            color: "#f59e0b",
            class: "mr-1"
          }),
          _cache[53] || (_cache[53] = _createTextVNode(" 手动填写 Cookie ", -1))
        ]),
        _createVNode(_component_v_btn, {
          variant: "text",
          density: "compact",
          size: "small",
          icon: showCookie.value ? 'mdi-eye-off-outline' : 'mdi-eye-outline',
          onClick: _cache[18] || (_cache[18] = $event => (showCookie.value = !showCookie.value))
        }, null, 8, ["icon"])
      ]),
      (!showCookie.value)
        ? (_openBlock(), _createBlock(_component_v_text_field, {
            key: 0,
            modelValue: config.cookie,
            "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((config.cookie) = $event)),
            type: "password",
            density: "compact",
            variant: "outlined",
            "hide-details": "",
            autocomplete: "off",
            placeholder: "扫码登录后自动填充，一般无需手动填写",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"]))
        : (_openBlock(), _createBlock(_component_v_textarea, {
            key: 1,
            modelValue: config.cookie,
            "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((config.cookie) = $event)),
            density: "compact",
            variant: "outlined",
            "hide-details": "",
            rows: "2",
            "auto-grow": "",
            autocomplete: "off",
            placeholder: "扫码登录后自动填充，一般无需手动填写",
            class: "dbfcfg-input"
          }, null, 8, ["modelValue"])),
      _createElementVNode("div", _hoisted_63, [
        _createVNode(_component_v_icon, {
          icon: "mdi-information-outline",
          size: "14",
          class: "mr-1"
        }),
        _cache[54] || (_cache[54] = _createTextVNode(" Cookie 由扫码登录自动维护，一般无需手动填写；也可粘贴从浏览器复制的豆瓣 Cookie。 ", -1))
      ])
    ]),
    _createElementVNode("div", _hoisted_64, [
      _createElementVNode("div", _hoisted_65, [
        _createElementVNode("span", _hoisted_66, [
          _createVNode(_component_v_icon, {
            icon: "mdi-book-information-variant",
            size: "18",
            color: "#6366f1",
            class: "mr-1"
          }),
          _cache[55] || (_cache[55] = _createTextVNode(" 使用说明 ", -1))
        ])
      ]),
      _createElementVNode("div", _hoisted_67, [
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-1-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[56] || (_cache[56] = _createElementVNode("strong", null, "扫码登录：", -1)),
          _cache[57] || (_cache[57] = _createTextVNode("用豆瓣 APP 扫描上方二维码，在手机上确认后 Cookie 会自动填入并保存，无需手动复制。", -1))
        ]),
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-2-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[58] || (_cache[58] = _createElementVNode("strong", null, "开启 Webhook：", -1)),
          _cache[59] || (_cache[59] = _createTextVNode("需要在媒体服务器中配置 webhook，播放事件才会触发同步。", -1))
        ]),
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-3-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[60] || (_cache[60] = _createElementVNode("strong", null, "同步规则：", -1)),
          _cache[61] || (_cache[61] = _createTextVNode("播放开始标记为「在看」，播放完成标记为「看过」，剧集进度会累积到对应条目。", -1))
        ]),
        _createElementVNode("p", null, [
          _createVNode(_component_v_icon, {
            icon: "mdi-numeric-4-circle-outline",
            size: "15",
            color: "primary",
            class: "mr-1"
          }),
          _cache[62] || (_cache[62] = _createElementVNode("strong", null, "Cookie 失效：", -1)),
          _cache[63] || (_cache[63] = _createTextVNode("插件每小时检测一次，失效时会按设置发送通知，重新扫码即可。", -1))
        ])
      ])
    ])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-25c6cfd8"]]);

export { Config as default };
