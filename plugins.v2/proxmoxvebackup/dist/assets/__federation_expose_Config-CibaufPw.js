import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,normalizeClass:_normalizeClass,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock,Transition:_Transition,renderList:_renderList,Fragment:_Fragment,createStaticVNode:_createStaticVNode} = await importShared('vue');


const _hoisted_1 = { class: "guardian-visual" };
const _hoisted_2 = { class: "q-guardian-avatar-wrapper" };
const _hoisted_3 = ["innerHTML"];
const _hoisted_4 = { class: "guardian-level" };
const _hoisted_5 = {
  key: 0,
  class: "blessing-bubble"
};
const _hoisted_6 = { class: "glass-card base-settings" };
const _hoisted_7 = { class: "section-title" };
const _hoisted_8 = { class: "nav-bar-crystal" };
const _hoisted_9 = ["onClick"];
const _hoisted_10 = { class: "crystal-inner" };
const _hoisted_11 = ["innerHTML"];
const _hoisted_12 = {
  class: "crystal-ball",
  viewBox: "0 0 100 100"
};
const _hoisted_13 = ["cx", "cy", "fill"];
const _hoisted_14 = ["begin"];
const _hoisted_15 = { class: "crystal-label" };
const _hoisted_16 = { class: "glass-card content-area" };
const _hoisted_17 = { key: 0 };
const _hoisted_18 = { class: "section-subtitle mb-2" };
const _hoisted_19 = { key: 1 };
const _hoisted_20 = { key: 2 };
const _hoisted_21 = {
  class: "switch-flex-row backup-options",
  style: {"margin-bottom":"8px"}
};
const _hoisted_22 = { class: "switch-flex-item" };
const _hoisted_23 = { class: "switch-flex-item" };
const _hoisted_24 = {
  class: "switch-flex-row",
  style: {"margin-bottom":"18px"}
};
const _hoisted_25 = { class: "switch-flex-item" };
const _hoisted_26 = { class: "switch-flex-item" };
const _hoisted_27 = { class: "switch-flex-item" };
const _hoisted_28 = { key: 3 };
const _hoisted_29 = { class: "risk-warning mb-4" };
const _hoisted_30 = { class: "cleanup-switch-row" };
const _hoisted_31 = { class: "feature-list" };
const _hoisted_32 = { key: 4 };
const _hoisted_33 = { class: "section-title" };
const _hoisted_34 = { class: "declaration-section command-section" };
const _hoisted_35 = { class: "declaration-subtitle" };
const _hoisted_36 = { class: "command-hint" };
const _hoisted_37 = { class: "declaration-section warning-section" };
const _hoisted_38 = { class: "declaration-subtitle" };
const _hoisted_39 = { class: "declaration-section" };
const _hoisted_40 = { class: "declaration-subtitle" };
const _hoisted_41 = { class: "action-btns" };
const _hoisted_42 = { class: "left-btns" };
const _hoisted_43 = { class: "right-btns" };

const {ref,reactive,onMounted,computed,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: { api: { type: [Object, Function], required: true } },
  emits: ['switch', 'close', 'save'],
  setup(__props, { emit: __emit }) {

onMounted(() => {
  document.body.classList.add('theme-light');
});
const props = __props;
const emit = __emit;

// 选项数据
const backupModeOptions = [
  { title: '快照（推荐）', value: 'snapshot' },
  { title: '停止', value: 'stop' },
  { title: '挂起', value: 'suspend' }
];
const compressModeOptions = [
  { title: 'ZSTD（快又好）', value: 'zstd' },
  { title: 'LZO', value: 'lzo' },
  { title: 'GZIP', value: 'gzip' },
  { title: '无压缩', value: 'none' }
];
const messageTypeOptions = [
  { title: '插件', value: 'Plugin' },
  { title: '系统', value: 'System' },
  { title: '全部', value: 'All' }
];
const pollIntervalOptions = [
  { title: '5秒', value: 5000 },
  { title: '10秒', value: 10000 },
  { title: '15秒', value: 15000 },
  { title: '30秒（推荐）', value: 30000 },
  { title: '1分钟', value: 60000 },
  { title: '2分钟', value: 120000 },
  { title: '5分钟', value: 300000 }
];

// 密码显示切换
const showSshPassword = ref(false);
const showWebdavPassword = ref(false);

const loading = ref(false);
const saving = ref(false);
const error = ref(null);

const config = reactive({
  enabled: false,
  notify: false,
  retry_count: 0,
  retry_interval: 60,
  notification_message_type: '插件',
  onlyonce: false,
  pve_host: '',
  ssh_port: '22',
  ssh_username: '',
  ssh_password: '',
  ssh_key_file: '',
  enable_local_backup: true,
  backup_path: '/config/plugins/ProxmoxVEBackup/actual_backups',
  keep_backup_num: 0,
  enable_webdav: false,
  webdav_url: '',
  webdav_username: '',
  webdav_password: '',
  webdav_path: '',
  webdav_keep_backup_num: 0,
  storage_name: 'local',
  backup_vmid: '',
  backup_mode: 'snapshot',
  compress_mode: 'zstd',
  auto_delete_after_download: true,
  download_all_backups: true,
  enable_restore: false,
  restore_force: false,
  restore_skip_existing: true,
  restore_storage: '',
  restore_vmid: '',
  restore_now: false,
  restore_file: '',
  clear_history: false,
  // 新增cron字段
  cron: '0 3 * * *',
  // 新增：自动清理临时空间
  auto_cleanup_tmp: true,
  // 新增系统日志清理配置
  enable_log_cleanup: false,
  log_journal_days: 0,
  log_vzdump_keep: 0,
  log_pve_keep: 0,
  log_dpkg_keep: 0,
  cleanup_template_images: false,
  // 状态页轮询配置（单位：毫秒）
  status_poll_interval: 30000, // 默认30秒
  container_poll_interval: 30000, // 默认30秒
});

async function fetchConfig() {
  loading.value = true;
  error.value = null;
  try {
    const data = await props.api.get('plugin/ProxmoxVEBackup/config');
    if (data) {
      Object.assign(config, data);
      if (!config.ssh_username) config.ssh_username = 'root';
      if (typeof config.auto_cleanup_tmp === 'undefined') config.auto_cleanup_tmp = true;
      // 新增系统日志清理配置默认
      if (typeof config.enable_log_cleanup === 'undefined') config.enable_log_cleanup = false;
      if (typeof config.log_journal_days === 'undefined') config.log_journal_days = 0;
      if (typeof config.log_vzdump_keep === 'undefined') config.log_vzdump_keep = 0;
      if (typeof config.log_pve_keep === 'undefined') config.log_pve_keep = 0;
      if (typeof config.log_dpkg_keep === 'undefined') config.log_dpkg_keep = 0;
      if (typeof config.cleanup_template_images === 'undefined') config.cleanup_template_images = false;
      // 状态页轮询配置：确保是数字类型，并设置推荐默认值
      if (typeof config.status_poll_interval === 'undefined' || config.status_poll_interval === 0 || config.status_poll_interval === null) {
        config.status_poll_interval = 30000; // 推荐30秒
      } else {
        // 确保是数字类型（可能从后端返回的是字符串）
        config.status_poll_interval = Number(config.status_poll_interval) || 30000;
      }
      if (typeof config.container_poll_interval === 'undefined' || config.container_poll_interval === 0 || config.container_poll_interval === null) {
        config.container_poll_interval = 30000; // 默认30秒
      } else {
        // 确保是数字类型（可能从后端返回的是字符串）
        config.container_poll_interval = Number(config.container_poll_interval) || 30000;
      }
    } else {
      throw new Error('获取配置响应无效或为空');
    }
  } catch (err) {
    error.value = err.message || '获取插件配置失败';
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  error.value = null;
  try {
    // 注意：保存配置时不会影响守护神等级和能量
    const pureConfig = {
      enabled: Boolean(config.enabled),
      notify: Boolean(config.notify),
      retry_count: Number(config.retry_count) || 0,
      retry_interval: Number(config.retry_interval) || 60,
      notification_message_type: String(config.notification_message_type || ''),
      onlyonce: Boolean(config.onlyonce),
      pve_host: String(config.pve_host || ''),
      ssh_port: Number(config.ssh_port) || 22,
      ssh_username: String(config.ssh_username || ''),
      ssh_password: String(config.ssh_password || ''),
      ssh_key_file: String(config.ssh_key_file || ''),
      enable_local_backup: Boolean(config.enable_local_backup),
      backup_path: String(config.backup_path || ''),
      keep_backup_num: Number(config.keep_backup_num) || 0,
      enable_webdav: Boolean(config.enable_webdav),
      webdav_url: String(config.webdav_url || ''),
      webdav_username: String(config.webdav_username || ''),
      webdav_password: String(config.webdav_password || ''),
      webdav_path: String(config.webdav_path || ''),
      webdav_keep_backup_num: Number(config.webdav_keep_backup_num) || 0,
      storage_name: String(config.storage_name || ''),
      backup_vmid: String(config.backup_vmid || ''),
      backup_mode: String(config.backup_mode || ''),
      compress_mode: String(config.compress_mode || ''),
      auto_delete_after_download: Boolean(config.auto_delete_after_download),
      download_all_backups: Boolean(config.download_all_backups),
      enable_restore: Boolean(config.enable_restore),
      restore_force: Boolean(config.restore_force),
      restore_skip_existing: Boolean(config.restore_skip_existing),
      restore_storage: String(config.restore_storage || ''),
      restore_vmid: String(config.restore_vmid || ''),
      restore_now: Boolean(config.restore_now),
      restore_file: String(config.restore_file || ''),
      clear_history: Boolean(config.clear_history),
      // 新增cron字段
      cron: String(config.cron || ''),
      // 新增：自动清理临时空间
      auto_cleanup_tmp: Boolean(config.auto_cleanup_tmp),
      // 新增：系统日志清理配置
      enable_log_cleanup: Boolean(config.enable_log_cleanup),
      log_journal_days: Number(config.log_journal_days) || 0,
      log_vzdump_keep: Number(config.log_vzdump_keep) || 0,
      log_pve_keep: Number(config.log_pve_keep) || 0,
      log_dpkg_keep: Number(config.log_dpkg_keep) || 0,
      cleanup_template_images: Boolean(config.cleanup_template_images),
      // 状态页轮询配置（单位：毫秒）
      status_poll_interval: Number(config.status_poll_interval) || 30000,
      container_poll_interval: Number(config.container_poll_interval) || 30000,
    };
    emit('save', pureConfig);
    // 保存成功后主动刷新状态，确保启用插件后立即生效
    await fetchConfig();
    // 如果启用了插件，主动获取一次状态确保服务已启动
    if (pureConfig.enabled) {
      try {
        await props.api.get('plugin/ProxmoxVEBackup/status');
      } catch (statusErr) {
        // 状态获取失败不影响保存流程
        console.warn('获取插件状态失败:', statusErr);
      }
    }
  } catch (err) {
    error.value = err.message || '保存配置失败';
  } finally {
    saving.value = false;
  }
}

function resetConfig() {
  // 只重置表单数据，不刷新页面
  Object.assign(config, {
    enabled: false,
    notify: false,
    retry_count: 0,
    retry_interval: 60,
    notification_message_type: '插件',
    onlyonce: false,
    pve_host: '',
    ssh_port: '22',
    ssh_username: '',
    ssh_password: '',
    ssh_key_file: '',
    enable_local_backup: true,
    backup_path: '/config/plugins/ProxmoxVEBackup/actual_backups',
    keep_backup_num: 0,
    enable_webdav: false,
    webdav_url: '',
    webdav_username: '',
    webdav_password: '',
    webdav_path: '',
    webdav_keep_backup_num: 0,
    storage_name: 'local',
    backup_vmid: '',
    backup_mode: 'snapshot',
    compress_mode: 'zstd',
    auto_delete_after_download: true,
    download_all_backups: true,
    enable_restore: false,
    restore_force: false,
    restore_skip_existing: true,
    restore_storage: '',
    restore_vmid: '',
    restore_now: false,
    restore_file: '',
    clear_history: false,
    // 新增cron字段
    cron: '0 3 * * *',
    auto_cleanup_tmp: true,
    cleanup_template_images: false,
    enable_log_cleanup: false,
    log_journal_days: 0,
    log_vzdump_keep: 0,
    log_pve_keep: 0,
    log_dpkg_keep: 0,
    // 状态页轮询配置（使用推荐值）
    status_poll_interval: 30000, // 默认30秒
    container_poll_interval: 30000, // 默认30秒
  });
  energy.value = 10;
  guardianLevel.value = 1;
  saveGuardianState();
}

const nodes = [
  { value: 'connection', label: '连接设置', level: 1, particleColor: '#00eaff', particleCount: 5, particleDelayBase: 0 },
  { value: 'local-backup', label: '备份目录', level: 2, particleColor: '#ffd54f', particleCount: 7, particleDelayBase: 0.12 },
  { value: 'backup-config', label: '备份还原', level: 4, particleColor: '#ba68c8', particleCount: 5, particleDelayBase: 0.22 },
  { value: 'cleanup', label: '系统设置', level: 6, particleColor: '#ffb300', particleCount: 6, particleDelayBase: 0.10 },
  { value: 'declaration', label: '插件说明', level: 7, particleColor: '#90caf9', particleCount: 5, particleDelayBase: 0.15 },
];
const activeNode = ref('connection');

// Q版守护神表情
const avatarSmile = ref(false);
// 能量槽与等级（持久化）
function loadGuardianState() {
  const e = Number(localStorage.getItem('pve_guardian_energy'));
  const l = Number(localStorage.getItem('pve_guardian_level'));
  return {
    energy: isNaN(e) ? 10 : e,
    level: isNaN(l) ? 1 : l
  };
}
const guardianState = loadGuardianState();
const energy = ref(guardianState.energy); // 0~100
const guardianLevel = ref(guardianState.level); // 1~5
function saveGuardianState() {
  localStorage.setItem('pve_guardian_energy', String(energy.value));
  localStorage.setItem('pve_guardian_level', String(guardianLevel.value));
}
// energyPercent 绑定 energy.value，确保能量槽进度同步
const energyPercent = computed(() => energy.value);
// 能量环颜色渐变（根据能量和等级变化）
const energyGradient = computed(() => {
  // 低能量灰蓝，高能量亮蓝，满级金色
  if (guardianLevel.value >= 5) return 'url(#energy-gold)';
  if (energy.value >= 80) return 'url(#energy-cyan)';
  if (energy.value >= 40) return 'url(#energy-blue)';
  return 'url(#energy-gray)';
});
// 祝福语气泡
const blessings = [
  '守护已就位！',
  '祝你数据无忧~',
  '备份顺利，安心无忧！',
  '守护神为你保驾护航！',
  '一切正常，放心使用！',
];
const showBlessingBubble = ref(false);
const currentBlessing = ref('');
const blessingType = ref('blessing'); // 'blessing' | 'energy' | 'levelup'
function showBlessing() {
  currentBlessing.value = blessings[Math.floor(Math.random() * blessings.length)];
  showBlessingBubble.value = true;
  setTimeout(() => showBlessingBubble.value = false, 1800);
}

// 移除watch相关代码，改为事件驱动
function onFeatureSwitch(key, val) {
  if (val) {
    energy.value = Math.min(energy.value + 20, 100);
    saveGuardianState();
    blessingType.value = 'energy';
    currentBlessing.value = `⚡ 能量+20！(${energy.value}/100)`;
    showBlessingBubble.value = true;
    setTimeout(() => showBlessingBubble.value = false, 1200);
    checkLevelUp();
  }
}

// 等级升级逻辑
const avatarLevelup = ref(false);
// 等级专属隐藏剧情/故事
const levelStories = [
  '', // Lv.0无
  // Lv.1
  '你好呀，我是你的PVE守护神！虽然现在还很小，但我会努力守护你的每一次备份。每当你点击按钮、完成一次操作，我都会变得更强大一点。让我们一起开启守护之旅吧！',
  // Lv.2
  '我感受到自己的能量在增长，守护的力量也更强了！现在的我，已经能帮你抵御一些小小的风险啦。每一次备份，都是我们共同的胜利！',
  // Lv.3
  '哇！我的机甲皮肤解锁啦！现在的我，拥有更强的防护力，可以为你的数据撑起坚实的盾牌。未来还有更多神秘力量等着我们去发现！',
  // Lv.4
  '最近，守护的任务变得更有挑战了。但别担心，我已经学会了更多技能，能帮你应对各种突发状况。只要你在，我就不会退缩！',
  // Lv.5
  '终于，金光降临！我已成为最强守护神，为你的PVE虚拟机和数据安全保驾护航。感谢你的陪伴和信任，未来还有更多彩蛋和故事等你来解锁！',
];
function checkLevelUp() {
  if (energy.value >= 100 && guardianLevel.value < 5) {
    energy.value = 0;
    guardianLevel.value++;
    saveGuardianState();
    avatarLevelup.value = true;
    blessingType.value = 'levelup';
    showBlessingBubble.value = true;
    // 升级时弹出专属剧情
    currentBlessing.value = levelStories[guardianLevel.value] || `守护神升级啦！Lv.${guardianLevel.value}`;
    setTimeout(() => {
      showBlessingBubble.value = false;
      avatarLevelup.value = false;
    }, 2600); // 剧情更长，气泡时间略延长
  } else {
    saveGuardianState();
  }
}

// 完全不同的守护神团队SVG头像（Lv.0~Lv.5）
function getGuardianSVG(level, smile) {
  switch (level) {
    case 0: // Lv.0 数据芽精灵 - 简单可爱的数据元素
      return `<svg width="88" height="88" viewBox="0 0 88 88">
        <defs>
          <linearGradient id="sprout-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#e8f5e8"/>
            <stop offset="100%" stop-color="#c8e6c9"/>
          </linearGradient>
        </defs>
        <circle cx="44" cy="44" r="40" fill="url(#sprout-gradient)" stroke="#81c784" stroke-width="4"/>
        <!-- 数据芽 -->
        <rect x="40" y="8" width="8" height="16" rx="4" fill="#4caf50"/>
        <rect x="42" y="4" width="4" height="8" rx="2" fill="#66bb6a"/>
        <rect x="43" y="2" width="2" height="4" rx="1" fill="#81c784"/>
        <!-- 叶子 -->
        <ellipse cx="36" cy="16" rx="6" ry="3" fill="#8bc34a" transform="rotate(-15 36 16)"/>
        <ellipse cx="52" cy="18" rx="5" ry="2.5" fill="#9ccc65" transform="rotate(20 52 18)"/>
        <!-- 能量环 -->
        <ellipse cx="44" cy="44" rx="36" ry="36" fill="none" stroke="#4caf50" stroke-width="2" opacity="0.6"/>
        <!-- 脸型+表情 -->
        <ellipse cx="44" cy="54" rx="20" ry="16" fill="#e8f5e8"/>
        <ellipse cx="36" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="52" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="36" cy="52" rx="3.5" ry="6" fill="#4caf50"/>
        <ellipse cx="52" cy="52" rx="3.5" ry="6" fill="#4caf50"/>
        <ellipse cx="36" cy="50" rx="1.8" ry="3" fill="#2e7d32"/>
        <ellipse cx="52" cy="50" rx="1.8" ry="3" fill="#2e7d32"/>
        <ellipse cx="44" cy="58" rx="1" ry="1.5" fill="#4caf50"/>
        ${smile ? '<path d="M38 64 Q44 68 50 64" stroke="#4caf50" stroke-width="2" fill="none"/>' : '<ellipse cx="44" cy="65" rx="3" ry="1" fill="#4caf50"/>'}
        <!-- 数据点装饰 -->
        <circle cx="28" cy="30" r="2" fill="#4caf50" opacity="0.7"/>
        <circle cx="60" cy="32" r="1.5" fill="#66bb6a" opacity="0.7"/>
        <circle cx="32" cy="70" r="1.5" fill="#81c784" opacity="0.7"/>
      </svg>`;
    case 1: // Lv.1 能量猫少女 - 可爱的猫特征
      return `<svg width="88" height="88" viewBox="0 0 88 88">
        <defs>
          <linearGradient id="cat-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fff3e0"/>
            <stop offset="100%" stop-color="#ffe0b2"/>
          </linearGradient>
        </defs>
        <circle cx="44" cy="44" r="40" fill="url(#cat-gradient)" stroke="#ff9800" stroke-width="4"/>
        <!-- 猫耳 -->
        <polygon points="26,12 34,4 30,24" fill="#ff9800"/>
        <polygon points="62,4 70,12 58,24" fill="#ff9800"/>
        <polygon points="28,14 32,8 30,22" fill="#ffb74d"/>
        <polygon points="60,8 64,14 58,22" fill="#ffb74d"/>
        <!-- 猫尾巴 -->
        <path d="M78 68 Q68 78 58 62 Q66 58 72 64" stroke="#ff9800" stroke-width="3" fill="none"/>
        <path d="M76 66 Q66 76 56 60 Q64 56 70 62" stroke="#ffb74d" stroke-width="2" fill="none"/>
        <!-- 能量环 -->
        <ellipse cx="44" cy="44" rx="36" ry="36" fill="none" stroke="#ff9800" stroke-width="2" opacity="0.6"/>
        <!-- 脸型+表情 -->
        <ellipse cx="44" cy="54" rx="20" ry="16" fill="#fff3e0"/>
        <ellipse cx="36" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="52" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="36" cy="52" rx="3.5" ry="6" fill="#ff9800"/>
        <ellipse cx="52" cy="52" rx="3.5" ry="6" fill="#ff9800"/>
        <ellipse cx="36" cy="50" rx="1.8" ry="3" fill="#e65100"/>
        <ellipse cx="52" cy="50" rx="1.8" ry="3" fill="#e65100"/>
        <ellipse cx="44" cy="58" rx="1" ry="1.5" fill="#ff9800"/>
        ${smile ? '<path d="M38 64 Q44 68 50 64" stroke="#ff9800" stroke-width="2" fill="none"/>' : '<ellipse cx="44" cy="65" rx="3" ry="1" fill="#ff9800"/>'}
        <!-- 猫胡须 -->
        <line x1="24" y1="52" x2="18" y2="50" stroke="#ff9800" stroke-width="1.5"/>
        <line x1="24" y1="54" x2="18" y2="54" stroke="#ff9800" stroke-width="1.5"/>
        <line x1="24" y1="56" x2="18" y2="58" stroke="#ff9800" stroke-width="1.5"/>
        <line x1="64" y1="50" x2="70" y2="50" stroke="#ff9800" stroke-width="1.5"/>
        <line x1="64" y1="54" x2="70" y2="54" stroke="#ff9800" stroke-width="1.5"/>
        <line x1="64" y1="58" x2="70" y2="56" stroke="#ff9800" stroke-width="1.5"/>
        <!-- 能量点 -->
        <circle cx="30" cy="28" r="2" fill="#ffb74d" opacity="0.8"/>
        <circle cx="58" cy="30" r="1.5" fill="#ffcc02" opacity="0.8"/>
      </svg>`;
    case 2: // Lv.2 机械AI少年 - 科技感机械元素
      return `<svg width="88" height="88" viewBox="0 0 88 88">
        <defs>
          <linearGradient id="mech-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#f3e5f5"/>
            <stop offset="100%" stop-color="#e1bee7"/>
          </linearGradient>
        </defs>
        <circle cx="44" cy="44" r="40" fill="url(#mech-gradient)" stroke="#9c27b0" stroke-width="4"/>
        <!-- 机械头盔 -->
        <rect x="32" y="8" width="24" height="12" rx="6" fill="#9c27b0"/>
        <rect x="36" y="4" width="16" height="6" rx="3" fill="#ba68c8"/>
        <!-- 电路板纹理 -->
        <rect x="34" y="10" width="4" height="2" fill="#e1bee7"/>
        <rect x="40" y="10" width="4" height="2" fill="#e1bee7"/>
        <rect x="46" y="10" width="4" height="2" fill="#e1bee7"/>
        <rect x="52" y="10" width="4" height="2" fill="#e1bee7"/>
        <!-- 齿轮装饰 -->
        <circle cx="28" cy="28" r="6" fill="#9c27b0" opacity="0.8"/>
        <circle cx="28" cy="28" r="4" fill="#ba68c8"/>
        <circle cx="28" cy="28" r="2" fill="#e1bee7"/>
        <rect x="26" y="22" width="4" height="12" rx="2" fill="#9c27b0"/>
        <rect x="22" y="26" width="12" height="4" rx="2" fill="#9c27b0"/>
        <!-- 能量环 -->
        <ellipse cx="44" cy="44" rx="36" ry="36" fill="none" stroke="#9c27b0" stroke-width="2" opacity="0.6"/>
        <!-- 脸型+表情 -->
        <ellipse cx="44" cy="54" rx="20" ry="16" fill="#f3e5f5"/>
        <ellipse cx="36" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="52" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="36" cy="52" rx="3.5" ry="6" fill="#9c27b0"/>
        <ellipse cx="52" cy="52" rx="3.5" ry="6" fill="#9c27b0"/>
        <ellipse cx="36" cy="50" rx="1.8" ry="3" fill="#6a1b9a"/>
        <ellipse cx="52" cy="50" rx="1.8" ry="3" fill="#6a1b9a"/>
        <ellipse cx="44" cy="58" rx="1" ry="1.5" fill="#9c27b0"/>
        ${smile ? '<path d="M38 64 Q44 68 50 64" stroke="#9c27b0" stroke-width="2" fill="none"/>' : '<ellipse cx="44" cy="65" rx="3" ry="1" fill="#9c27b0"/>'}
        <!-- 数据流装饰 -->
        <rect x="60" y="20" width="2" height="8" fill="#9c27b0" opacity="0.7"/>
        <rect x="64" y="24" width="2" height="8" fill="#ba68c8" opacity="0.7"/>
        <rect x="68" y="28" width="2" height="8" fill="#e1bee7" opacity="0.7"/>
        <!-- 扫描线 -->
        <rect x="32" y="40" width="24" height="1" fill="#9c27b0" opacity="0.6">
          <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite"/>
        </rect>
      </svg>`;
    case 3: // Lv.3 虚拟天使 - 神圣天使元素
      return `<svg width="88" height="88" viewBox="0 0 88 88">
        <defs>
          <linearGradient id="angel-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#e8f5e8"/>
            <stop offset="100%" stop-color="#c8e6c9"/>
          </linearGradient>
          <radialGradient id="halo-gradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#fff"/>
            <stop offset="100%" stop-color="#e8f5e8"/>
          </radialGradient>
        </defs>
        <circle cx="44" cy="44" r="40" fill="url(#angel-gradient)" stroke="#4caf50" stroke-width="4"/>
        <!-- 天使光环 -->
        <ellipse cx="44" cy="12" rx="20" ry="6" fill="url(#halo-gradient)" stroke="#4caf50" stroke-width="2"/>
        <ellipse cx="44" cy="12" rx="16" ry="4" fill="none" stroke="#81c784" stroke-width="1" opacity="0.7"/>
        <!-- 天使翅膀 -->
        <path d="M8 40 Q16 30 24 40 Q20 50 12 50 Z" fill="#e8f5e8" stroke="#4caf50" stroke-width="2"/>
        <path d="M80 40 Q72 30 64 40 Q68 50 76 50 Z" fill="#e8f5e8" stroke="#4caf50" stroke-width="2"/>
        <path d="M10 42 Q16 34 22 42 Q20 48 14 48 Z" fill="#c8e6c9" opacity="0.7"/>
        <path d="M78 42 Q72 34 66 42 Q68 48 74 48 Z" fill="#c8e6c9" opacity="0.7"/>
        <!-- 羽毛装饰 -->
        <path d="M6 38 Q10 36 12 38" stroke="#4caf50" stroke-width="1.5" fill="none"/>
        <path d="M82 38 Q78 36 76 38" stroke="#4caf50" stroke-width="1.5" fill="none"/>
        <!-- 能量环 -->
        <ellipse cx="44" cy="44" rx="36" ry="36" fill="none" stroke="#4caf50" stroke-width="2" opacity="0.6"/>
        <!-- 脸型+表情 -->
        <ellipse cx="44" cy="54" rx="20" ry="16" fill="#e8f5e8"/>
        <ellipse cx="36" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="52" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="36" cy="52" rx="3.5" ry="6" fill="#4caf50"/>
        <ellipse cx="52" cy="52" rx="3.5" ry="6" fill="#4caf50"/>
        <ellipse cx="36" cy="50" rx="1.8" ry="3" fill="#2e7d32"/>
        <ellipse cx="52" cy="50" rx="1.8" ry="3" fill="#2e7d32"/>
        <ellipse cx="44" cy="58" rx="1" ry="1.5" fill="#4caf50"/>
        ${smile ? '<path d="M38 64 Q44 68 50 64" stroke="#4caf50" stroke-width="2" fill="none"/>' : '<ellipse cx="44" cy="65" rx="3" ry="1" fill="#4caf50"/>'}
        <!-- 神圣光点 -->
        <circle cx="20" cy="20" r="2" fill="#fff" opacity="0.8"/>
        <circle cx="68" cy="24" r="1.5" fill="#e8f5e8" opacity="0.8"/>
        <circle cx="24" cy="70" r="1.5" fill="#c8e6c9" opacity="0.8"/>
        <circle cx="64" cy="68" r="1.5" fill="#a5d6a7" opacity="0.8"/>
        <!-- 光环动画 -->
        <ellipse cx="44" cy="12" rx="18" ry="5" fill="none" stroke="#fff" stroke-width="1" opacity="0.6">
          <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite"/>
        </ellipse>
      </svg>`;
    case 4: // Lv.4 数据龙战士 - 威武龙族特征
      return `<svg width="88" height="88" viewBox="0 0 88 88">
        <defs>
          <linearGradient id="dragon-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#e0f2f1"/>
            <stop offset="100%" stop-color="#b2dfdb"/>
          </linearGradient>
        </defs>
        <circle cx="44" cy="44" r="40" fill="url(#dragon-gradient)" stroke="#009688" stroke-width="4"/>
        <!-- 龙角 -->
        <polygon points="26,8 32,16 28,24" fill="#009688"/>
        <polygon points="62,8 68,16 60,24" fill="#009688"/>
        <polygon points="28,10 32,16 30,22" fill="#26a69a"/>
        <polygon points="60,10 64,16 62,22" fill="#26a69a"/>
        <!-- 龙鳞装饰 -->
        <ellipse cx="44" cy="44" rx="38" ry="38" fill="none" stroke="#009688" stroke-width="1" opacity="0.3"/>
        <ellipse cx="44" cy="44" rx="34" ry="34" fill="none" stroke="#26a69a" stroke-width="1" opacity="0.2"/>
        <ellipse cx="44" cy="44" rx="30" ry="30" fill="none" stroke="#4db6ac" stroke-width="1" opacity="0.1"/>
        <!-- 龙鳞点缀 -->
        <circle cx="44" cy="28" r="3" fill="#009688" opacity="0.6"/>
        <circle cx="36" cy="32" r="2" fill="#26a69a" opacity="0.6"/>
        <circle cx="52" cy="32" r="2" fill="#26a69a" opacity="0.6"/>
        <circle cx="40" cy="40" r="2" fill="#4db6ac" opacity="0.6"/>
        <circle cx="48" cy="40" r="2" fill="#4db6ac" opacity="0.6"/>
        <!-- 能量环 -->
        <ellipse cx="44" cy="44" rx="36" ry="36" fill="none" stroke="#009688" stroke-width="2" opacity="0.6"/>
        <!-- 脸型+表情 -->
        <ellipse cx="44" cy="54" rx="20" ry="16" fill="#e0f2f1"/>
        <ellipse cx="36" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="52" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="36" cy="52" rx="3.5" ry="6" fill="#009688"/>
        <ellipse cx="52" cy="52" rx="3.5" ry="6" fill="#009688"/>
        <ellipse cx="36" cy="50" rx="1.8" ry="3" fill="#00695c"/>
        <ellipse cx="52" cy="50" rx="1.8" ry="3" fill="#00695c"/>
        <ellipse cx="44" cy="58" rx="1" ry="1.5" fill="#009688"/>
        ${smile ? '<path d="M38 64 Q44 68 50 64" stroke="#009688" stroke-width="2" fill="none"/>' : '<ellipse cx="44" cy="65" rx="3" ry="1" fill="#009688"/>'}
        <!-- 龙爪装饰 -->
        <path d="M16 60 L20 64 L24 60" stroke="#009688" stroke-width="2" fill="none"/>
        <path d="M72 60 L68 64 L64 60" stroke="#009688" stroke-width="2" fill="none"/>
        <!-- 龙息效果 -->
        <ellipse cx="44" cy="70" rx="8" ry="3" fill="#26a69a" opacity="0.4">
          <animate attributeName="opacity" values="0.4;0.8;0.4" dur="2s" repeatCount="indefinite"/>
        </ellipse>
      </svg>`;
    case 5: // Lv.5 宇宙主宰 - 神秘宇宙元素
      return `<svg width="88" height="88" viewBox="0 0 88 88">
        <defs>
          <linearGradient id="cosmic-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fffde7"/>
            <stop offset="100%" stop-color="#fff9c4"/>
          </linearGradient>
          <radialGradient id="star-gradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#fff"/>
            <stop offset="100%" stop-color="#ffd700"/>
          </radialGradient>
          <filter id="cosmic-glow">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge>
              <feMergeNode in="blur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        <circle cx="44" cy="44" r="40" fill="url(#cosmic-gradient)" stroke="#ffd700" stroke-width="5" filter="url(#cosmic-glow)"/>
        <!-- 多重光环 -->
        <ellipse cx="44" cy="44" rx="38" ry="38" fill="none" stroke="#ffd700" stroke-width="2" opacity="0.8"/>
        <ellipse cx="44" cy="44" rx="34" ry="34" fill="none" stroke="#ffed4e" stroke-width="1.5" opacity="0.6"/>
        <ellipse cx="44" cy="44" rx="30" ry="30" fill="none" stroke="#fff59d" stroke-width="1" opacity="0.4"/>
        <!-- 宇宙王冠 -->
        <ellipse cx="44" cy="16" rx="18" ry="8" fill="#fff" stroke="#ffd700" stroke-width="2.5"/>
        <polygon points="44,0 50,16 38,16" fill="#ffd700" stroke="#fffde7" stroke-width="1.5"/>
        <polygon points="44,2 48,14 40,14" fill="#ffed4e"/>
        <!-- 多眼系统 -->
        <ellipse cx="34" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="54" cy="50" rx="6" ry="9" fill="#fff"/>
        <ellipse cx="44" cy="40" rx="4" ry="6" fill="#ffd700"/>
        <ellipse cx="34" cy="52" rx="3.5" ry="6" fill="#ffd700"/>
        <ellipse cx="54" cy="52" rx="3.5" ry="6" fill="#ffd700"/>
        <ellipse cx="34" cy="50" rx="1.8" ry="3" fill="#000"/>
        <ellipse cx="54" cy="50" rx="1.8" ry="3" fill="#000"/>
        <ellipse cx="44" cy="40" rx="1.2" ry="2" fill="#000"/>
        <ellipse cx="44" cy="58" rx="1" ry="1.5" fill="#ffd700"/>
        ${smile ? '<path d="M38 64 Q44 68 50 64" stroke="#ffd700" stroke-width="2" fill="none"/>' : '<ellipse cx="44" cy="65" rx="3" ry="1" fill="#ffd700"/>'}
        <!-- 宇宙星星 -->
        <circle cx="20" cy="20" r="2" fill="url(#star-gradient)">
          <animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite"/>
        </circle>
        <circle cx="68" cy="24" r="1.5" fill="url(#star-gradient)">
          <animate attributeName="opacity" values="0.8;1;0.8" dur="2.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="60" cy="70" r="1.5" fill="url(#star-gradient)">
          <animate attributeName="opacity" values="0.8;1;0.8" dur="1.8s" repeatCount="indefinite"/>
        </circle>
        <circle cx="24" cy="68" r="1.5" fill="url(#star-gradient)">
          <animate attributeName="opacity" values="0.8;1;0.8" dur="2.2s" repeatCount="indefinite"/>
        </circle>
        <!-- 能量漩涡 -->
        <ellipse cx="44" cy="44" rx="25" ry="25" fill="none" stroke="#ffd700" stroke-width="1" opacity="0.3">
          <animateTransform attributeName="transform" type="rotate" values="0 44 44;360 44 44" dur="8s" repeatCount="indefinite"/>
        </ellipse>
        <ellipse cx="44" cy="44" rx="20" ry="20" fill="none" stroke="#ffed4e" stroke-width="1" opacity="0.2">
          <animateTransform attributeName="transform" type="rotate" values="360 44 44;0 44 44" dur="6s" repeatCount="indefinite"/>
        </ellipse>
      </svg>`;
    default:
      return '';
  }
}


onMounted(() => {
  fetchConfig();
  // 页面加载时同步能量和等级
  const s = loadGuardianState();
  energy.value = s.energy;
  guardianLevel.value = s.level;
});


function getNavAvatarSVG(type) {
  switch (type) {
    case 'connection':
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#e3f2fd"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#00bcd4"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#00bcd4"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#2196f3"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#2196f3"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#2196f3"/>
        <path d="M15 28 Q19 32 23 28" stroke="#2196f3" stroke-width="1.5" fill="none"/>
      </svg>`;
    case 'local-backup':
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#fffde7"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#ffd54f"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#ffd54f"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#ffb300"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#ffb300"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#ffb300"/>
        <path d="M15 28 Q19 32 23 28" stroke="#ffb300" stroke-width="1.5" fill="none"/>
      </svg>`;
    case 'remote-backup':
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#e3f2fd"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#4dd0e1"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#4dd0e1"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#00bcd4"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#00bcd4"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#00bcd4"/>
        <path d="M15 28 Q19 32 23 28" stroke="#00bcd4" stroke-width="1.5" fill="none"/>
      </svg>`;
    case 'backup-config':
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#f3e5f5"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#ba68c8"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#ba68c8"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#ba68c8"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#ba68c8"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#ba68c8"/>
        <path d="M15 28 Q19 32 23 28" stroke="#ba68c8" stroke-width="1.5" fill="none"/>
      </svg>`;
    case 'restore':
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#e0f2f1"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#66bb6a"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#66bb6a"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#43a047"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#43a047"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#43a047"/>
        <path d="M15 28 Q19 32 23 28" stroke="#43a047" stroke-width="1.5" fill="none"/>
      </svg>`;
    case 'cleanup': // 系统设置分区Q版头像
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#fff3e0"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#ffb300"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#ffb300"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#ff9800"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#ff9800"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#ff9800"/>
        <rect x="16" y="28" width="6" height="3" rx="1.5" fill="#ffb300"/>
        <rect x="22" y="28" width="6" height="3" rx="1.5" fill="#ffb300"/>
        <ellipse cx="19" cy="32" rx="2.2" ry="1.2" fill="#ffb300"/>
        <ellipse cx="19" cy="34" rx="2.2" ry="0.7" fill="#ffb300"/>
        <ellipse cx="19" cy="36" rx="2.2" ry="0.5" fill="#ff9800"/>
      </svg>`;
    case 'declaration': // 插件说明分区Q版头像
      return `<svg width="38" height="38" viewBox="0 0 38 38">
        <ellipse cx="19" cy="22" rx="15" ry="13" fill="#e3f2fd"/>
        <ellipse cx="11" cy="14" rx="3.5" ry="6" fill="#90caf9"/>
        <ellipse cx="27" cy="14" rx="3.5" ry="6" fill="#90caf9"/>
        <ellipse cx="19" cy="22" rx="8" ry="8" fill="#fff"/>
        <ellipse cx="15" cy="22" rx="2" ry="3" fill="#1976d2"/>
        <ellipse cx="23" cy="22" rx="2" ry="3" fill="#1976d2"/>
        <ellipse cx="15" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="23" cy="22" rx="0.7" ry="1.2" fill="#fff" opacity="0.7"/>
        <ellipse cx="19" cy="28" rx="2.2" ry="1.2" fill="#1976d2"/>
        <circle cx="19" cy="32" r="2" fill="#90caf9"/>
        <rect x="17" y="34" width="4" height="2" rx="1" fill="#90caf9"/>
      </svg>`;
    default:
      return '';
  }
}


ref(false);

// 新增：切换清理系统日志开关后立即生效
watch(() => config.enable_log_cleanup, async (val, oldVal) => {
  if (val === oldVal) return;
  try {
    await props.api.post('plugin/ProxmoxVEBackup/save_config', { enable_log_cleanup: val });
    // 可选：emit 事件通知父组件刷新状态
    emit && emit('refreshStatus');
    if (typeof $snackbar !== 'undefined') {
      $snackbar.success('清理系统日志开关已生效');
    }
  } catch (e) {
    if (typeof $snackbar !== 'undefined') {
      $snackbar.error('保存清理系统日志开关失败');
    }
  }
});

return (_ctx, _cache) => {
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_VCronField = _resolveComponent("VCronField");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_btn = _resolveComponent("v-btn");

  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createElementVNode("div", _hoisted_1, [
      _createElementVNode("div", _hoisted_2, [
        _createVNode(_component_v_progress_circular, {
          value: energyPercent.value,
          size: 100,
          width: 12,
          color: energyGradient.value,
          class: "energy-bar energy-bar-glow"
        }, null, 8, ["value", "color"]),
        _createElementVNode("div", {
          class: _normalizeClass(["q-guardian-avatar", { 'levelup-anim': avatarLevelup.value }]),
          onMouseenter: _cache[0] || (_cache[0] = $event => (avatarSmile.value = true)),
          onMouseleave: _cache[1] || (_cache[1] = $event => (avatarSmile.value = false)),
          onClick: _cache[2] || (_cache[2] = $event => (showBlessing()))
        }, [
          _createElementVNode("span", {
            innerHTML: getGuardianSVG(guardianLevel.value, avatarSmile.value)
          }, null, 8, _hoisted_3)
        ], 34),
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            color: "amber",
            size: "20"
          }, {
            default: _withCtx(() => _cache[48] || (_cache[48] = [
              _createTextVNode("mdi-crown")
            ])),
            _: 1
          }),
          _createTextVNode(" Lv." + _toDisplayString(guardianLevel.value), 1)
        ]),
        _createVNode(_Transition, { name: "fade" }, {
          default: _withCtx(() => [
            (showBlessingBubble.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_5, [
                  (blessingType.value==='blessing')
                    ? (_openBlock(), _createBlock(_component_v_icon, {
                        key: 0,
                        color: "primary",
                        size: "18"
                      }, {
                        default: _withCtx(() => _cache[49] || (_cache[49] = [
                          _createTextVNode("mdi-emoticon-happy")
                        ])),
                        _: 1
                      }))
                    : (blessingType.value==='energy')
                      ? (_openBlock(), _createBlock(_component_v_icon, {
                          key: 1,
                          color: "yellow",
                          size: "18"
                        }, {
                          default: _withCtx(() => _cache[50] || (_cache[50] = [
                            _createTextVNode("mdi-flash")
                          ])),
                          _: 1
                        }))
                      : (blessingType.value==='levelup')
                        ? (_openBlock(), _createBlock(_component_v_icon, {
                            key: 2,
                            color: "amber",
                            size: "18"
                          }, {
                            default: _withCtx(() => _cache[51] || (_cache[51] = [
                              _createTextVNode("mdi-star")
                            ])),
                            _: 1
                          }))
                        : _createCommentVNode("", true),
                  _createTextVNode(" " + _toDisplayString(currentBlessing.value), 1)
                ]))
              : _createCommentVNode("", true)
          ]),
          _: 1
        })
      ]),
      _cache[52] || (_cache[52] = _createElementVNode("div", { class: "plugin-title" }, "PVE虚拟机守护神 - 备份插件", -1))
    ]),
    _createElementVNode("div", _hoisted_6, [
      _createElementVNode("div", _hoisted_7, [
        _createVNode(_component_v_icon, {
          class: "mr-2",
          color: "primary"
        }, {
          default: _withCtx(() => _cache[53] || (_cache[53] = [
            _createTextVNode("mdi-tune")
          ])),
          _: 1
        }),
        _cache[54] || (_cache[54] = _createTextVNode(" 基本设置 "))
      ]),
      _createVNode(_component_v_row, { dense: "" }, {
        default: _withCtx(() => [
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_switch, {
                modelValue: config.enabled,
                "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.enabled) = $event)),
                label: "启用插件",
                color: "success",
                "prepend-icon": "mdi-power",
                class: "tight-switch"
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          }),
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_switch, {
                modelValue: config.notify,
                "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.notify) = $event)),
                label: "发送通知",
                color: "info",
                "prepend-icon": "mdi-bell",
                class: "tight-switch"
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          }),
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_switch, {
                modelValue: config.onlyonce,
                "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.onlyonce) = $event)),
                label: "立即运行一次",
                color: "primary",
                "prepend-icon": "mdi-play",
                class: "tight-switch"
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createVNode(_component_v_row, { dense: "" }, {
        default: _withCtx(() => [
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_text_field, {
                modelValue: config.retry_count,
                "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.retry_count) = $event)),
                modelModifiers: { number: true },
                label: "失败重试次数",
                type: "number",
                min: "0",
                "prepend-inner-icon": "mdi-refresh",
                hint: "建议设置为0",
                "persistent-hint": "",
                dense: ""
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          }),
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_text_field, {
                modelValue: config.retry_interval,
                "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.retry_interval) = $event)),
                modelModifiers: { number: true },
                label: "重试间隔(秒)",
                type: "number",
                min: "1",
                "prepend-inner-icon": "mdi-timer",
                dense: ""
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          }),
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_VCronField, {
                modelValue: config.cron,
                "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.cron) = $event)),
                label: "执行周期",
                hint: "标准cron表达式，如0 3 * * * 表示每天凌晨3点",
                "persistent-hint": "",
                density: "compact"
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          }),
          _createVNode(_component_v_col, {
            cols: "12",
            md: "3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_select, {
                modelValue: config.notification_message_type,
                "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.notification_message_type) = $event)),
                items: messageTypeOptions,
                label: "消息类型",
                "prepend-inner-icon": "mdi-message-alert",
                dense: ""
              }, null, 8, ["modelValue"])
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      (!config.pve_host)
        ? (_openBlock(), _createBlock(_component_v_alert, {
            key: 0,
            type: "warning",
            class: "mt-2 mb-0",
            dense: "",
            border: "left",
            color: "warning"
          }, {
            default: _withCtx(() => _cache[55] || (_cache[55] = [
              _createTextVNode(" 未设置PVE主机地址，插件将无法正常连接！ ")
            ])),
            _: 1
          }))
        : _createCommentVNode("", true)
    ]),
    _createElementVNode("div", _hoisted_8, [
      (_openBlock(), _createElementBlock(_Fragment, null, _renderList(nodes, (node) => {
        return _createElementVNode("div", {
          key: node.value,
          class: _normalizeClass(["crystal-btn", { active: activeNode.value === node.value }]),
          onClick: $event => (activeNode.value = node.value)
        }, [
          _createElementVNode("div", _hoisted_10, [
            _createElementVNode("div", {
              class: "crystal-avatar",
              innerHTML: getNavAvatarSVG(node.value)
            }, null, 8, _hoisted_11),
            (_openBlock(), _createElementBlock("svg", _hoisted_12, [
              _cache[56] || (_cache[56] = _createStaticVNode("<defs data-v-e3be71a9><radialGradient id=\"crystal-gradient\" cx=\"50%\" cy=\"50%\" r=\"50%\" data-v-e3be71a9><stop offset=\"0%\" stop-color=\"#fff\" stop-opacity=\"0.95\" data-v-e3be71a9></stop><stop offset=\"60%\" stop-color=\"#b2ebf2\" stop-opacity=\"0.7\" data-v-e3be71a9></stop><stop offset=\"100%\" stop-color=\"#00eaff\" stop-opacity=\"0.45\" data-v-e3be71a9></stop></radialGradient></defs><circle cx=\"50\" cy=\"50\" r=\"44\" fill=\"url(#crystal-gradient)\" data-v-e3be71a9></circle><ellipse cx=\"38\" cy=\"32\" rx=\"16\" ry=\"7\" fill=\"#fff\" opacity=\"0.35\" data-v-e3be71a9></ellipse>", 3)),
              _createElementVNode("g", null, [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(node.particleCount, (n) => {
                  return (_openBlock(), _createElementBlock("circle", {
                    key: n,
                    cx: 50 + 28 * Math.cos((n*360/node.particleCount-90 + (activeNode.value === node.value ? 20 : 0))*Math.PI/180),
                    cy: 50 + 28 * Math.sin((n*360/node.particleCount-90 + (activeNode.value === node.value ? 20 : 0))*Math.PI/180),
                    r: "2.5",
                    fill: node.particleColor,
                    opacity: "0.85"
                  }, [
                    _createElementVNode("animate", {
                      attributeName: "r",
                      values: "2.5;4;2.5",
                      dur: "1.2s",
                      begin: (n*node.particleDelayBase)+'s',
                      repeatCount: "indefinite"
                    }, null, 8, _hoisted_14)
                  ], 8, _hoisted_13))
                }), 128))
              ])
            ]))
          ]),
          _createElementVNode("div", _hoisted_15, _toDisplayString(node.label), 1)
        ], 10, _hoisted_9)
      }), 64))
    ]),
    _createElementVNode("div", _hoisted_16, [
      (activeNode.value === 'connection')
        ? (_openBlock(), _createElementBlock("div", _hoisted_17, [
            _createVNode(_component_v_row, { dense: "" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_text_field, {
                      modelValue: config.pve_host,
                      "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.pve_host) = $event)),
                      label: "PVE主机地址",
                      "prepend-inner-icon": "mdi-server",
                      dense: ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_text_field, {
                      modelValue: config.ssh_port,
                      "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.ssh_port) = $event)),
                      modelModifiers: { number: true },
                      label: "SSH端口",
                      type: "number",
                      min: "0",
                      "prepend-inner-icon": "mdi-numeric",
                      dense: ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_row, { dense: "" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_text_field, {
                      modelValue: config.ssh_username,
                      "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.ssh_username) = $event)),
                      label: "SSH用户名",
                      "prepend-inner-icon": "mdi-account",
                      hint: "通常使用root用户以确保有足够权限",
                      "persistent-hint": "",
                      dense: ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_text_field, {
                      modelValue: config.ssh_password,
                      "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.ssh_password) = $event)),
                      label: "SSH密码",
                      type: showSshPassword.value?"text":"password",
                      "append-inner-icon": showSshPassword.value?"mdi-eye-off":"mdi-eye",
                      "onClick:appendInner": _cache[14] || (_cache[14] = $event => (showSshPassword.value=!showSshPassword.value)),
                      "prepend-inner-icon": "mdi-key",
                      dense: ""
                    }, null, 8, ["modelValue", "type", "append-inner-icon"])
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
                    _createVNode(_component_v_text_field, {
                      modelValue: config.ssh_key_file,
                      "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.ssh_key_file) = $event)),
                      label: "SSH私钥文件路径",
                      "prepend-inner-icon": "mdi-file-key",
                      dense: ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_divider, { class: "my-4" }),
            _createElementVNode("div", _hoisted_18, [
              _createVNode(_component_v_icon, {
                class: "mr-1",
                color: "info",
                size: "18"
              }, {
                default: _withCtx(() => _cache[57] || (_cache[57] = [
                  _createTextVNode("mdi-refresh")
                ])),
                _: 1
              }),
              _cache[58] || (_cache[58] = _createTextVNode(" 状态页轮询设置 "))
            ]),
            _createVNode(_component_v_alert, {
              type: "warning",
              dense: "",
              class: "mb-3",
              border: "left"
            }, {
              default: _withCtx(() => _cache[59] || (_cache[59] = [
                _createElementVNode("span", { style: {"font-size":"0.875rem"} }, "轮询间隔设置太低会增加CPU使用率和API请求频率，建议使用默认值或更长间隔。", -1)
              ])),
              _: 1
            }),
            _createVNode(_component_v_row, { dense: "" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_select, {
                      modelValue: config.status_poll_interval,
                      "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((config.status_poll_interval) = $event)),
                      items: pollIntervalOptions,
                      label: "状态轮询间隔",
                      "prepend-inner-icon": "mdi-clock-outline",
                      hint: "状态页轮询PVE主机状态和插件状态的时间间隔",
                      "persistent-hint": "",
                      dense: ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_col, {
                  cols: "12",
                  md: "6"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_select, {
                      modelValue: config.container_poll_interval,
                      "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((config.container_poll_interval) = $event)),
                      items: pollIntervalOptions,
                      label: "容器状态轮询间隔",
                      "prepend-inner-icon": "mdi-docker",
                      hint: "状态页轮询容器状态的时间间隔",
                      "persistent-hint": "",
                      dense: ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]))
        : (activeNode.value === 'local-backup')
          ? (_openBlock(), _createElementBlock("div", _hoisted_19, [
              _createVNode(_component_v_row, { dense: "" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_switch, {
                        modelValue: config.enable_local_backup,
                        "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((config.enable_local_backup) = $event)),
                        label: "启用本地备份",
                        color: "primary",
                        "prepend-icon": "mdi-folder",
                        class: "tight-switch",
                        onChange: _cache[19] || (_cache[19] = $event => (onFeatureSwitch('enable_local_backup', $event)))
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.backup_path,
                        "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((config.backup_path) = $event)),
                        label: "备份文件存储路径",
                        "prepend-inner-icon": "mdi-folder-open",
                        dense: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.keep_backup_num,
                        "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((config.keep_backup_num) = $event)),
                        modelModifiers: { number: true },
                        label: "本地备份保留数量",
                        type: "number",
                        min: "0",
                        "prepend-inner-icon": "mdi-counter",
                        hint: "设置为0或留空表示保留全部备份",
                        "persistent-hint": "",
                        dense: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_divider, { class: "my-2" }),
              _createVNode(_component_v_row, { dense: "" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "3"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_switch, {
                        modelValue: config.enable_webdav,
                        "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((config.enable_webdav) = $event)),
                        label: "启用WebDAV备份",
                        color: "info",
                        "prepend-icon": "mdi-cloud-upload",
                        class: "tight-switch",
                        onChange: _cache[23] || (_cache[23] = $event => (onFeatureSwitch('enable_webdav', $event)))
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "9"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.webdav_url,
                        "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => ((config.webdav_url) = $event)),
                        label: "WebDAV服务器地址",
                        "prepend-inner-icon": "mdi-cloud",
                        dense: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_row, { dense: "" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.webdav_username,
                        "onUpdate:modelValue": _cache[25] || (_cache[25] = $event => ((config.webdav_username) = $event)),
                        label: "WebDAV用户名",
                        "prepend-inner-icon": "mdi-account",
                        dense: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "6"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.webdav_password,
                        "onUpdate:modelValue": _cache[26] || (_cache[26] = $event => ((config.webdav_password) = $event)),
                        label: "WebDAV密码",
                        type: showWebdavPassword.value?"text":"password",
                        "append-inner-icon": showWebdavPassword.value?"mdi-eye-off":"mdi-eye",
                        "onClick:appendInner": _cache[27] || (_cache[27] = $event => (showWebdavPassword.value=!showWebdavPassword.value)),
                        "prepend-inner-icon": "mdi-lock",
                        dense: ""
                      }, null, 8, ["modelValue", "type", "append-inner-icon"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_row, { dense: "" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "7"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.webdav_path,
                        "onUpdate:modelValue": _cache[28] || (_cache[28] = $event => ((config.webdav_path) = $event)),
                        label: "WebDAV备份路径",
                        "prepend-inner-icon": "mdi-folder-network",
                        dense: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_col, {
                    cols: "12",
                    md: "5"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_text_field, {
                        modelValue: config.webdav_keep_backup_num,
                        "onUpdate:modelValue": _cache[29] || (_cache[29] = $event => ((config.webdav_keep_backup_num) = $event)),
                        modelModifiers: { number: true },
                        label: "WebDAV备份保留数量",
                        type: "number",
                        min: "0",
                        "prepend-inner-icon": "mdi-counter",
                        hint: "设置为0或留空表示保留全部备份",
                        "persistent-hint": "",
                        dense: ""
                      }, null, 8, ["modelValue"])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              })
            ]))
          : (activeNode.value === 'backup-config')
            ? (_openBlock(), _createElementBlock("div", _hoisted_20, [
                _createElementVNode("div", _hoisted_21, [
                  _createElementVNode("div", _hoisted_22, [
                    _createVNode(_component_v_switch, {
                      modelValue: config.auto_delete_after_download,
                      "onUpdate:modelValue": _cache[30] || (_cache[30] = $event => ((config.auto_delete_after_download) = $event)),
                      label: "下载后自动删除PVE备份",
                      color: "error",
                      "prepend-icon": "mdi-delete-forever",
                      class: "tight-switch"
                    }, null, 8, ["modelValue"])
                  ]),
                  _createElementVNode("div", _hoisted_23, [
                    _createVNode(_component_v_switch, {
                      modelValue: config.download_all_backups,
                      "onUpdate:modelValue": _cache[31] || (_cache[31] = $event => ((config.download_all_backups) = $event)),
                      label: "下载所有备份文件（多VM时）",
                      color: "info",
                      "prepend-icon": "mdi-download-multiple",
                      class: "tight-switch"
                    }, null, 8, ["modelValue"])
                  ]),
                  _cache[60] || (_cache[60] = _createElementVNode("div", { class: "switch-flex-item" }, null, -1))
                ]),
                _createElementVNode("div", _hoisted_24, [
                  _createElementVNode("div", _hoisted_25, [
                    _createVNode(_component_v_switch, {
                      modelValue: config.enable_restore,
                      "onUpdate:modelValue": _cache[32] || (_cache[32] = $event => ((config.enable_restore) = $event)),
                      label: "启用恢复系统",
                      color: "primary",
                      "prepend-icon": "mdi-restore",
                      class: "tight-switch"
                    }, null, 8, ["modelValue"])
                  ]),
                  _createElementVNode("div", _hoisted_26, [
                    _createVNode(_component_v_switch, {
                      modelValue: config.restore_force,
                      "onUpdate:modelValue": _cache[33] || (_cache[33] = $event => ((config.restore_force) = $event)),
                      label: "强制恢复容器",
                      color: "error",
                      "prepend-icon": "mdi-alert-circle",
                      class: "tight-switch"
                    }, null, 8, ["modelValue"])
                  ]),
                  _createElementVNode("div", _hoisted_27, [
                    _createVNode(_component_v_switch, {
                      modelValue: config.restore_skip_existing,
                      "onUpdate:modelValue": _cache[34] || (_cache[34] = $event => ((config.restore_skip_existing) = $event)),
                      label: "跳过已存在的VM",
                      color: "warning",
                      "prepend-icon": "mdi-skip-next",
                      class: "tight-switch"
                    }, null, 8, ["modelValue"])
                  ])
                ]),
                _createVNode(_component_v_row, { dense: "" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.storage_name,
                          "onUpdate:modelValue": _cache[35] || (_cache[35] = $event => ((config.storage_name) = $event)),
                          label: "存储名称",
                          "prepend-inner-icon": "mdi-database",
                          dense: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: config.backup_vmid,
                          "onUpdate:modelValue": _cache[36] || (_cache[36] = $event => ((config.backup_vmid) = $event)),
                          label: "要备份的容器ID",
                          "prepend-inner-icon": "mdi-numeric",
                          dense: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: config.backup_mode,
                          "onUpdate:modelValue": _cache[37] || (_cache[37] = $event => ((config.backup_mode) = $event)),
                          items: backupModeOptions,
                          label: "备份模式",
                          "prepend-inner-icon": "mdi-camera-timer",
                          dense: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_row, { dense: "" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: config.compress_mode,
                          "onUpdate:modelValue": _cache[38] || (_cache[38] = $event => ((config.compress_mode) = $event)),
                          items: compressModeOptions,
                          label: "压缩模式",
                          "prepend-inner-icon": "mdi-zip-box",
                          dense: ""
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]))
            : (activeNode.value === 'cleanup')
              ? (_openBlock(), _createElementBlock("div", _hoisted_28, [
                  _createElementVNode("div", _hoisted_29, [
                    _createVNode(_component_v_icon, {
                      size: "18",
                      color: "warning",
                      class: "mr-2"
                    }, {
                      default: _withCtx(() => _cache[61] || (_cache[61] = [
                        _createTextVNode("mdi-alert")
                      ])),
                      _: 1
                    }),
                    _cache[62] || (_cache[62] = _createElementVNode("span", { style: {"font-size":"1.08em"} }, "本分区所有操作将直接作用于PVE主机系统，部分操作不可逆，请务必谨慎操作并提前做好备份！", -1))
                  ]),
                  _createVNode(_component_v_row, { dense: "" }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_30, [
                        _createVNode(_component_v_switch, {
                          modelValue: config.auto_cleanup_tmp,
                          "onUpdate:modelValue": _cache[39] || (_cache[39] = $event => ((config.auto_cleanup_tmp) = $event)),
                          label: "启用临时空间",
                          color: "warning",
                          "prepend-icon": "mdi-delete-sweep"
                        }, null, 8, ["modelValue"]),
                        _createVNode(_component_v_switch, {
                          modelValue: config.enable_log_cleanup,
                          "onUpdate:modelValue": _cache[40] || (_cache[40] = $event => ((config.enable_log_cleanup) = $event)),
                          label: "启用系统日志",
                          color: "info",
                          "prepend-icon": "mdi-file-document-multiple"
                        }, null, 8, ["modelValue"]),
                        _createVNode(_component_v_switch, {
                          modelValue: config.cleanup_template_images,
                          "onUpdate:modelValue": _cache[41] || (_cache[41] = $event => ((config.cleanup_template_images) = $event)),
                          label: "启用镜像模板",
                          color: "primary",
                          "prepend-icon": "mdi-cube-outline",
                          class: "tight-switch"
                        }, null, 8, ["modelValue"])
                      ])
                    ]),
                    _: 1
                  }),
                  _createVNode(_component_v_row, {
                    dense: "",
                    class: "mt-4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.log_journal_days,
                            "onUpdate:modelValue": _cache[42] || (_cache[42] = $event => ((config.log_journal_days) = $event)),
                            modelModifiers: { number: true },
                            disabled: !config.enable_log_cleanup,
                            label: "journalctl保留天数",
                            type: "number",
                            min: "0",
                            "prepend-inner-icon": "mdi-calendar-clock",
                            hint: "仅清理早于N天的systemd日志，留空或0为全部清理",
                            "persistent-hint": "",
                            dense: ""
                          }, null, 8, ["modelValue", "disabled"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.log_vzdump_keep,
                            "onUpdate:modelValue": _cache[43] || (_cache[43] = $event => ((config.log_vzdump_keep) = $event)),
                            modelModifiers: { number: true },
                            disabled: !config.enable_log_cleanup,
                            label: "/var/log/vzdump保留最新N个",
                            type: "number",
                            min: "0",
                            "prepend-inner-icon": "mdi-file-document",
                            hint: "0为全部清理",
                            "persistent-hint": "",
                            dense: ""
                          }, null, 8, ["modelValue", "disabled"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.log_pve_keep,
                            "onUpdate:modelValue": _cache[44] || (_cache[44] = $event => ((config.log_pve_keep) = $event)),
                            modelModifiers: { number: true },
                            disabled: !config.enable_log_cleanup,
                            label: "/var/log/pve保留最新N个",
                            type: "number",
                            min: "0",
                            "prepend-inner-icon": "mdi-file-document",
                            hint: "0为全部清理",
                            "persistent-hint": "",
                            dense: ""
                          }, null, 8, ["modelValue", "disabled"])
                        ]),
                        _: 1
                      }),
                      _createVNode(_component_v_col, {
                        cols: "12",
                        md: "3"
                      }, {
                        default: _withCtx(() => [
                          _createVNode(_component_v_text_field, {
                            modelValue: config.log_dpkg_keep,
                            "onUpdate:modelValue": _cache[45] || (_cache[45] = $event => ((config.log_dpkg_keep) = $event)),
                            modelModifiers: { number: true },
                            disabled: !config.enable_log_cleanup,
                            label: "/var/log/dpkg.log保留最新N个",
                            type: "number",
                            min: "0",
                            "prepend-inner-icon": "mdi-file-document",
                            hint: "0为全部清理",
                            "persistent-hint": "",
                            dense: ""
                          }, null, 8, ["modelValue", "disabled"])
                        ]),
                        _: 1
                      })
                    ]),
                    _: 1
                  }),
                  _createElementVNode("ul", _hoisted_31, [
                    _createElementVNode("li", null, [
                      _createVNode(_component_v_icon, {
                        size: "16",
                        color: "warning",
                        class: "dot-icon"
                      }, {
                        default: _withCtx(() => _cache[63] || (_cache[63] = [
                          _createTextVNode("mdi-checkbox-blank-circle")
                        ])),
                        _: 1
                      }),
                      _cache[64] || (_cache[64] = _createTextVNode(" 临时空间功能会删除系统 /var/lib/vz/dump/ 下所有以 .tmp 结尾的文件和目录（含临时备份缓存）。 "))
                    ]),
                    _createElementVNode("li", null, [
                      _createVNode(_component_v_icon, {
                        size: "16",
                        color: "info",
                        class: "dot-icon"
                      }, {
                        default: _withCtx(() => _cache[65] || (_cache[65] = [
                          _createTextVNode("mdi-checkbox-blank-circle")
                        ])),
                        _: 1
                      }),
                      _cache[66] || (_cache[66] = _createTextVNode(" 系统日志功能清理不可逆，请谨慎操作。journalctl 支持按天保留，其它日志只能保留最新N个或全部清理。 "))
                    ]),
                    _createElementVNode("li", null, [
                      _createVNode(_component_v_icon, {
                        size: "16",
                        color: "primary",
                        class: "dot-icon"
                      }, {
                        default: _withCtx(() => _cache[67] || (_cache[67] = [
                          _createTextVNode("mdi-checkbox-blank-circle")
                        ])),
                        _: 1
                      }),
                      _cache[68] || (_cache[68] = _createTextVNode(" 镜像模板功能启用后，可在状态页管理ISO镜像和CT模板。关闭后相关操作将被禁用。 "))
                    ])
                  ])
                ]))
              : (activeNode.value === 'declaration')
                ? (_openBlock(), _createElementBlock("div", _hoisted_32, [
                    _createElementVNode("div", _hoisted_33, [
                      _createVNode(_component_v_icon, {
                        class: "mr-2",
                        color: "info"
                      }, {
                        default: _withCtx(() => _cache[69] || (_cache[69] = [
                          _createTextVNode("mdi-information-outline")
                        ])),
                        _: 1
                      }),
                      _cache[70] || (_cache[70] = _createTextVNode(" 插件说明 "))
                    ]),
                    _cache[82] || (_cache[82] = _createElementVNode("div", { class: "declaration-section" }, [
                      _createElementVNode("div", { class: "declaration-text" }, [
                        _createTextVNode(" 欢迎使用 "),
                        _createElementVNode("b", null, "PVE虚拟机守护神 - 备份插件"),
                        _createTextVNode("！本插件旨在为你的PVE环境提供便捷、安全的备份与恢复体验。 ")
                      ])
                    ], -1)),
                    _createElementVNode("div", _hoisted_34, [
                      _createElementVNode("div", _hoisted_35, [
                        _createVNode(_component_v_icon, {
                          size: "20",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[71] || (_cache[71] = [
                            _createTextVNode("mdi-message-text")
                          ])),
                          _: 1
                        }),
                        _cache[72] || (_cache[72] = _createTextVNode(" 消息交互指令 "))
                      ]),
                      _cache[75] || (_cache[75] = _createStaticVNode("<div class=\"command-cards\" data-v-e3be71a9><div class=\"command-card\" data-v-e3be71a9><div class=\"command-icon\" data-v-e3be71a9>📊</div><div class=\"command-content\" data-v-e3be71a9><div class=\"command-title\" data-v-e3be71a9>/pve状态</div><div class=\"command-desc\" data-v-e3be71a9>查看PVE主机状态信息，包括CPU、内存、磁盘等实时数据</div></div></div><div class=\"command-card\" data-v-e3be71a9><div class=\"command-icon\" data-v-e3be71a9>📦</div><div class=\"command-content\" data-v-e3be71a9><div class=\"command-title\" data-v-e3be71a9>/pve容器</div><div class=\"command-desc\" data-v-e3be71a9>查看所有容器/虚拟机的运行状态和详细信息</div></div></div><div class=\"command-card\" data-v-e3be71a9><div class=\"command-icon\" data-v-e3be71a9>📚</div><div class=\"command-content\" data-v-e3be71a9><div class=\"command-title\" data-v-e3be71a9>/pve帮助</div><div class=\"command-desc\" data-v-e3be71a9>显示插件帮助信息，查看所有可用指令</div></div></div></div>", 1)),
                      _createElementVNode("div", _hoisted_36, [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          color: "info",
                          class: "mr-1"
                        }, {
                          default: _withCtx(() => _cache[73] || (_cache[73] = [
                            _createTextVNode("mdi-information")
                          ])),
                          _: 1
                        }),
                        _cache[74] || (_cache[74] = _createElementVNode("span", null, "在消息渠道（微信、Telegram等）中发送上述指令即可使用交互功能", -1))
                      ])
                    ]),
                    _createElementVNode("div", _hoisted_37, [
                      _createElementVNode("div", _hoisted_38, [
                        _createVNode(_component_v_icon, {
                          size: "20",
                          color: "warning",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[76] || (_cache[76] = [
                            _createTextVNode("mdi-alert-circle-outline")
                          ])),
                          _: 1
                        }),
                        _cache[77] || (_cache[77] = _createTextVNode(" 重要须知 "))
                      ]),
                      _cache[78] || (_cache[78] = _createElementVNode("ul", { class: "declaration-list" }, [
                        _createElementVNode("li", null, "数据仅本地存储，远程备份只上传到你指定的服务器，如有顾虑请勿使用本插件。"),
                        _createElementVNode("li", null, "插件作者不对因使用本插件造成的任何数据丢失、损坏或其他后果负责。"),
                        _createElementVNode("li", null, "使用本插件即表示您已知悉并同意以上说明。")
                      ], -1))
                    ]),
                    _createElementVNode("div", _hoisted_39, [
                      _createElementVNode("div", _hoisted_40, [
                        _createVNode(_component_v_icon, {
                          size: "20",
                          color: "primary",
                          class: "mr-2"
                        }, {
                          default: _withCtx(() => _cache[79] || (_cache[79] = [
                            _createTextVNode("mdi-lightbulb-on-outline")
                          ])),
                          _: 1
                        }),
                        _cache[80] || (_cache[80] = _createTextVNode(" 使用方法 "))
                      ]),
                      _cache[81] || (_cache[81] = _createElementVNode("ol", { class: "declaration-list ordered" }, [
                        _createElementVNode("li", null, "插件的所有主要操作（如备份、恢复、清理）都在\"状态页\"进行。"),
                        _createElementVNode("li", null, "各项功能（如自动备份、WebDAV远程备份、恢复、系统设置）需在本页相应分区启用并保存后，才能在状态页正常使用。"),
                        _createElementVNode("li", null, "修改配置后请务必点击\"保存\"，否则新设置不会生效。"),
                        _createElementVNode("li", null, "如遇按钮无法点击或功能不可用，请检查相关功能是否已在本页启用。"),
                        _createElementVNode("li", null, "欢迎提交Issue和Pull Request来帮助改进插件。")
                      ], -1))
                    ])
                  ]))
                : _createCommentVNode("", true),
      _createElementVNode("div", _hoisted_41, [
        _createElementVNode("div", _hoisted_42, [
          _createVNode(_component_v_btn, {
            class: "glow-btn glow-btn-blue",
            size: "small",
            "prepend-icon": "mdi-view-dashboard",
            onClick: _cache[46] || (_cache[46] = $event => (emit('switch')))
          }, {
            default: _withCtx(() => _cache[83] || (_cache[83] = [
              _createTextVNode("状态页")
            ])),
            _: 1
          })
        ]),
        _createElementVNode("div", _hoisted_43, [
          _createVNode(_component_v_btn, {
            class: "glow-btn glow-btn-orange",
            size: "small",
            "prepend-icon": "mdi-restore",
            onClick: resetConfig
          }, {
            default: _withCtx(() => _cache[84] || (_cache[84] = [
              _createTextVNode("重置")
            ])),
            _: 1
          }),
          _createVNode(_component_v_btn, {
            class: "glow-btn glow-btn-green",
            size: "small",
            "prepend-icon": "mdi-content-save",
            loading: saving.value,
            onClick: saveConfig
          }, {
            default: _withCtx(() => _cache[85] || (_cache[85] = [
              _createTextVNode("保存")
            ])),
            _: 1
          }, 8, ["loading"]),
          _createVNode(_component_v_btn, {
            class: "glow-btn glow-btn-pink",
            size: "small",
            "prepend-icon": "mdi-close",
            onClick: _cache[47] || (_cache[47] = $event => (emit('close')))
          }, {
            default: _withCtx(() => _cache[86] || (_cache[86] = [
              _createTextVNode("关闭")
            ])),
            _: 1
          })
        ])
      ])
    ]),
    _cache[87] || (_cache[87] = _createElementVNode("svg", {
      width: "0",
      height: "0"
    }, [
      _createElementVNode("defs", null, [
        _createElementVNode("linearGradient", {
          id: "badge-gradient",
          x1: "0",
          y1: "0",
          x2: "1",
          y2: "1"
        }, [
          _createElementVNode("stop", {
            offset: "0%",
            "stop-color": "#e0f7fa"
          }),
          _createElementVNode("stop", {
            offset: "100%",
            "stop-color": "#b2ebf2"
          })
        ])
      ])
    ], -1))
  ], 64))
}
}

};
const ConfigComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-e3be71a9"]]);

export { ConfigComponent as default };
