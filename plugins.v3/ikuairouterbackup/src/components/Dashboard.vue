<template>
  <div class="dashboard-wrap pa-2">
    <template v-if="status.ok">
      <!-- 负载 -->
      <div class="d-flex align-center ga-3 mb-2">
        <v-icon size="18" color="primary">mdi-router-network</v-icon>
        <span class="text-subtitle-2 font-weight-bold">
          {{ status.hostname || '爱快路由' }}
        </span>
        <v-chip v-if="status.version" size="x-small" variant="tonal" class="text-caption">
          {{ status.version }}
        </v-chip>
        <v-spacer />
        <span class="text-caption text-medium-emphasis">{{ updatedAt }}</span>
      </div>
      <v-row dense>
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis d-flex justify-space-between">
            <span>CPU</span><span class="font-weight-bold" :class="cpuColor + '--text'">{{ status.cpu_usage }}%</span>
          </div>
          <v-progress-linear :model-value="status.cpu_usage" :color="cpuColor" height="8" rounded />
        </v-col>
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis d-flex justify-space-between">
            <span>内存</span><span class="font-weight-bold" :class="memColor + '--text'">{{ status.mem_usage }}%</span>
          </div>
          <v-progress-linear :model-value="status.mem_usage" :color="memColor" height="8" rounded />
        </v-col>
      </v-row>
      <!-- 流量 -->
      <div class="d-flex flex-wrap ga-3 mt-3">
        <v-chip size="small" variant="tonal" color="info" prepend-icon="mdi-arrow-up">
          ↑ {{ fmtSpeed(status.upload_speed) }}
        </v-chip>
        <v-chip size="small" variant="tonal" color="success" prepend-icon="mdi-arrow-down">
          ↓ {{ fmtSpeed(status.download_speed) }}
        </v-chip>
        <v-chip v-if="backupActivity && backupActivity !== '空闲'" size="small" variant="tonal" color="warning" prepend-icon="mdi-content-save-cog">
          {{ backupActivity }}
        </v-chip>
      </div>
    </template>
    <template v-else>
      <div class="d-flex align-center ga-2 py-4">
        <v-icon color="error" size="20">mdi-alert-circle-outline</v-icon>
        <span class="text-body-2">{{ status.error || '无法连接爱快路由' }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'IkuaiRouterBackup' },
})

const status = reactive({ ok: false, error: '' })
const backupActivity = ref('')
const updatedAt = ref('')
let timer = null

const cpuColor = computed(() => {
  const v = status.cpu_usage || 0
  return v < 50 ? 'success' : v < 80 ? 'warning' : 'error'
})
const memColor = computed(() => {
  const v = status.mem_usage || 0
  return v < 50 ? 'success' : v < 80 ? 'warning' : 'error'
})

const fmtSpeed = (bps) => {
  const v = Number(bps) || 0
  if (v >= 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024).toFixed(2) + ' GB/s'
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(1) + ' MB/s'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' KB/s'
  return v + ' B/s'
}

const load = async () => {
  try {
    const data = await props.api.get(`plugin/${props.pluginId}/status`)
    if (data) Object.assign(status, data)
    updatedAt.value = new Date().toLocaleTimeString()
  } catch (e) {
    status.ok = false
    status.error = '获取状态失败'
  }
  try {
    const hist = await props.api.get(`plugin/${props.pluginId}/histories`)
    backupActivity.value = hist?.backup_activity || '空闲'
  } catch (e) { /* 静默 */ }
}

onMounted(() => {
  load()
  timer = setInterval(load, 30000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.dashboard-wrap {
  min-height: 96px;
}
</style>
