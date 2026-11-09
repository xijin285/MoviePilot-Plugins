<template>
  <v-card flat class="plugin-page glass-card">
    <!-- 顶部状态条 -->
    <v-card-title class="d-flex align-center flex-wrap ga-3" style="padding: 14px 16px 6px;">
      <v-icon color="primary" size="26">mdi-server</v-icon>
      <span class="text-h6 font-weight-bold">PVE 守护神</span>
      <v-chip :color="status.enabled ? 'success' : 'grey'" size="small" variant="tonal">
        {{ status.enabled ? '已启用' : '未启用' }}
      </v-chip>
      <v-chip v-if="pve.online" size="small" variant="tonal" color="info" class="text-caption">
        PVE {{ pve.pve_version || '' }} · {{ pve.hostname || '' }}
      </v-chip>
      <v-spacer />
      <v-btn size="small" variant="tonal" :loading="refreshing" @click="refreshAll">
        <v-icon size="16" class="mr-1">mdi-refresh</v-icon>刷新
      </v-btn>
      <v-btn size="small" variant="tonal" prepend-icon="mdi-cog" @click="$emit('switch')">配置</v-btn>
      <v-btn icon size="small" variant="text" @click="$emit('close')">
        <v-icon size="22">mdi-close</v-icon>
      </v-btn>
    </v-card-title>

    <v-card-text style="padding: 8px 16px 16px;">
      <v-alert v-if="!status.enabled" type="info" variant="tonal" density="compact" class="mb-3">
        插件尚未启用，请点击右上角「配置」开启后使用。
      </v-alert>
      <v-alert v-else-if="pve.online === false" type="warning" variant="tonal" density="compact" class="mb-3">
        PVE 主机连接失败，请检查配置中的 SSH 连接设置。
      </v-alert>

      <v-row>
        <!-- 运行状态 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined" class="fill-height">
            <v-card-title class="d-flex align-center py-2">
              <v-icon color="primary" size="20" class="mr-2">mdi-clock-check-outline</v-icon>
              <span class="text-subtitle-1">运行状态</span>
            </v-card-title>
            <v-card-text class="pt-0">
              <div class="status-row"><span>定时计划</span><b>{{ status.cron || '未配置' }}</b></div>
              <div class="status-row"><span>下次执行</span><b>{{ status.next_run_time || '待调度' }}</b></div>
              <div class="status-row">
                <span>备份任务</span>
                <v-chip size="x-small" :color="status.backup_activity && status.backup_activity !== '空闲' ? 'warning' : 'success'" variant="tonal">
                  {{ status.backup_activity || '空闲' }}
                </v-chip>
              </div>
              <div class="status-row">
                <span>恢复任务</span>
                <v-chip size="x-small" :color="status.restore_activity && status.restore_activity !== '空闲' ? 'warning' : 'success'" variant="tonal">
                  {{ status.restore_activity || '空闲' }}
                </v-chip>
              </div>
              <div class="status-row"><span>恢复功能</span><b>{{ status.enable_restore ? '已开启' : '已关闭' }}</b></div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- PVE 主机 -->
        <v-col cols="12" md="6">
          <v-card variant="outlined" class="fill-height">
            <v-card-title class="d-flex align-center py-2">
              <v-icon color="teal" size="20" class="mr-2">mdi-cpu-64-bit</v-icon>
              <span class="text-subtitle-1">PVE 主机</span>
            </v-card-title>
            <v-card-text class="pt-0">
              <div class="status-row"><span>连接</span>
                <v-chip size="x-small" :color="pve.online ? 'success' : 'error'" variant="tonal">
                  {{ pve.online ? '在线' : '离线' }}
                </v-chip>
              </div>
              <div class="status-row"><span>主机名</span><b>{{ pve.hostname || '-' }}</b></div>
              <div class="status-row"><span>PVE 版本</span><b>{{ pve.pve_version || '-' }}</b></div>
              <div class="status-row"><span>CPU 使用率</span><b>{{ pve.cpu_usage != null ? pve.cpu_usage + '%' : '-' }}</b></div>
              <div class="status-row"><span>内存使用率</span><b>{{ pve.mem_usage != null ? pve.mem_usage + '%' : '-' }}</b></div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 备份概览 -->
        <v-col cols="12">
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center py-2">
              <v-icon color="amber-darken-2" size="20" class="mr-2">mdi-backup-restore</v-icon>
              <span class="text-subtitle-1">备份概览</span>
              <v-spacer />
              <span class="text-caption text-medium-emphasis">共 {{ backups.length }} 个备份文件</span>
            </v-card-title>
            <v-card-text class="pt-0">
              <v-row dense>
                <v-col v-for="cell in statCells" :key="cell.label" cols="6" sm="3">
                  <div class="stat-cell">
                    <div class="text-caption text-medium-emphasis">{{ cell.label }}</div>
                    <div class="text-h6 font-weight-bold" :class="cell.color">{{ cell.value }}</div>
                  </div>
                </v-col>
              </v-row>
              <div v-if="lastBackup" class="text-caption text-medium-emphasis mt-2">
                最近一次备份：{{ fmtTime(lastBackup.timestamp) }}
                <template v-if="lastBackup.filename"> · {{ lastBackup.filename }}</template>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-alert type="info" variant="tonal" density="compact" class="mt-3">
        完整功能（虚拟机管理、备份下载恢复、主机操作等）已移至左侧导航
        <b>「PVE 守护神」</b>，点击即可使用。
      </v-alert>
    </v-card-text>

    <v-snackbar v-model="snackbar" timeout="2000">已刷新</v-snackbar>
  </v-card>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

const props = defineProps({ api: { type: [Object, Function], required: true } });
defineEmits(['switch', 'close']);

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
</script>

<style scoped>
.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 32px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  font-size: 0.875rem;
}
.status-row:last-child {
  border-bottom: none;
}
.stat-cell {
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(var(--v-theme-primary), 0.06);
}
</style>
