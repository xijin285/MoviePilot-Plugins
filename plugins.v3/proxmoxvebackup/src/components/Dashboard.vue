<template>
  <div class="pve-dash pa-2">
    <div class="d-flex align-center mb-1">
      <v-icon size="18" color="primary" class="mr-2">mdi-server</v-icon>
      <span class="text-subtitle-2 font-weight-bold">PVE 守护神</span>
      <v-spacer />
      <span class="text-caption text-medium-emphasis">{{ updatedAt }}</span>
      <v-btn icon variant="text" size="x-small" :loading="loading" @click="load">
        <v-icon size="16">mdi-refresh</v-icon>
      </v-btn>
    </div>

    <div v-if="error" class="text-error text-caption d-flex align-center py-2">
      <v-icon size="small" color="error" class="mr-1">mdi-alert-circle-outline</v-icon>
      {{ error }}
    </div>

    <template v-else>
      <div class="d-flex flex-wrap ga-1 mb-2">
        <v-chip size="x-small" variant="tonal" :color="status.enabled ? 'success' : 'grey'">
          {{ status.enabled ? '已启用' : '已禁用' }}
        </v-chip>
        <v-chip size="x-small" variant="tonal" color="info" prepend-icon="mdi-archive">
          {{ backupCount }} 个备份
        </v-chip>
        <v-chip
          v-if="status.backup_activity && status.backup_activity !== '空闲'"
          size="x-small"
          variant="tonal"
          color="warning"
          prepend-icon="mdi-database-arrow-up"
        >
          {{ status.backup_activity }}
        </v-chip>
        <v-chip
          v-if="status.restore_activity && status.restore_activity !== '空闲'"
          size="x-small"
          variant="tonal"
          color="warning"
          prepend-icon="mdi-database-arrow-down"
        >
          {{ status.restore_activity }}
        </v-chip>
      </div>

      <div class="text-caption d-flex align-center">
        <v-icon size="14" class="mr-1 text-medium-emphasis">mdi-lan-connect</v-icon>
        <span class="text-medium-emphasis">主机</span>
        <span class="ml-1 font-weight-medium">{{ status.pve_host || '未配置' }}</span>
      </div>
      <div v-if="status.next_run_time" class="text-caption d-flex align-center mt-1">
        <v-icon size="14" class="mr-1 text-medium-emphasis">mdi-timer-outline</v-icon>
        <span class="text-medium-emphasis">下次备份</span>
        <span class="ml-1 font-weight-medium">{{ status.next_run_time }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'ProxmoxVEBackup' },
})

const loading = ref(false)
const error = ref('')
const updatedAt = ref('')
const backupCount = ref(0)
const status = reactive({
  enabled: false,
  pve_host: '',
  backup_activity: '空闲',
  restore_activity: '空闲',
  next_run_time: '',
})

let timer = null

const statusApi = computed(() => `plugin/${props.pluginId}/status`)
const filesApi = computed(() => `plugin/${props.pluginId}/available_backups`)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await props.api.get(statusApi.value)
    if (data && !data.error) {
      Object.assign(status, data)
      updatedAt.value = new Date().toLocaleTimeString()
    } else {
      error.value = '获取状态失败'
    }
  } catch (e) {
    error.value = '获取状态失败'
  }
  try {
    const files = await props.api.get(filesApi.value)
    backupCount.value = Array.isArray(files) ? files.length : 0
  } catch (e) {
    backupCount.value = 0
  } finally {
    loading.value = false
  }
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
.pve-dash {
  height: 100%;
  width: 100%;
}
</style>
