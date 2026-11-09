<template>
  <!-- 顶部主视觉：Q版守护神头像+能量槽圆环+等级徽章+祝福语气泡 -->
  <div class="guardian-visual">
    <div class="q-guardian-avatar-wrapper">
      <v-progress-circular :value="energyPercent" :size="100" :width="12" :color="energyGradient" class="energy-bar energy-bar-glow" />
      <div class="q-guardian-avatar" :class="{ 'levelup-anim': avatarLevelup }" @mouseenter="avatarSmile = true" @mouseleave="avatarSmile = false" @click="showBlessing()">
        <span v-html="getGuardianSVG(guardianLevel, avatarSmile)"></span>
      </div>
      <!-- 等级徽章移到wrapper层级，避免被裁剪 -->
      <div class="guardian-level">
        <v-icon color="amber" size="20">mdi-crown</v-icon>
        Lv.{{ guardianLevel }}
      </div>
      <!-- 祝福语气泡移到wrapper下，避免被裁剪 -->
      <transition name="fade">
        <div v-if="showBlessingBubble" class="blessing-bubble">
          <v-icon v-if="blessingType==='blessing'" color="primary" size="18">mdi-emoticon-happy</v-icon>
          <v-icon v-else-if="blessingType==='energy'" color="yellow" size="18">mdi-flash</v-icon>
          <v-icon v-else-if="blessingType==='levelup'" color="amber" size="18">mdi-star</v-icon>
          {{ currentBlessing }}
        </div>
      </transition>
    </div>
    <div class="plugin-title">PVE 守护神 - 备份插件</div>
  </div>

  <!-- 基本设置：玻璃拟态/发光卡片 -->
  <div class="glass-card base-settings">
    <div class="section-title">
      <v-icon class="mr-2" color="primary">mdi-tune</v-icon>
      基本设置
    </div>
    <v-row dense>
      <v-col cols="12" md="3">
        <v-switch v-model="config.enabled" label="启用插件" color="success" prepend-icon="mdi-power" class="tight-switch" />
      </v-col>
      <v-col cols="12" md="3">
        <v-switch v-model="config.notify" label="发送通知" color="info" prepend-icon="mdi-bell" class="tight-switch" />
      </v-col>
      <v-col cols="12" md="3">
        <v-switch v-model="config.onlyonce" label="立即运行一次" color="primary" prepend-icon="mdi-play" class="tight-switch" />
      </v-col>
    </v-row>
    <v-row dense>
      <v-col cols="12" md="3">
        <v-text-field v-model.number="config.retry_count" label="失败重试次数" type="number" min="0" prepend-inner-icon="mdi-refresh" hint="建议设置为0" persistent-hint dense />
      </v-col>
      <v-col cols="12" md="3">
        <v-text-field v-model.number="config.retry_interval" label="重试间隔(秒)" type="number" min="1" prepend-inner-icon="mdi-timer" dense />
      </v-col>
      <!-- 新增：可视化cron表达式选择器 -->
      <v-col cols="12" md="3">
        <VCronField
          v-model="config.cron"
          label="执行周期"
          hint="标准cron表达式，如0 3 * * * 表示每天凌晨3点"
          persistent-hint
          density="compact"
        />
      </v-col>
      <v-col cols='12' md='3'><v-select v-model='config.notification_message_type' :items='messageTypeOptions' label='消息类型' prepend-inner-icon='mdi-message-alert' dense /></v-col>
    </v-row>
    <v-alert v-if="!config.pve_host" type="warning" class="mt-2 mb-0" dense border="left" color="warning">
      未设置PVE主机地址，插件将无法正常连接！
    </v-alert>
  </div>

  <!-- 悬浮水晶球导航按钮 -->
  <div class="nav-bar-crystal">
    <div
      v-for="node in nodes"
      :key="node.value"
      class="crystal-btn"
      :class="{ active: activeNode === node.value }"
      @click="activeNode = node.value"
    >
      <div class="crystal-inner">
        <!-- Q版头像SVG（每个按钮不同level） -->
        <div class="crystal-avatar" v-html="getNavAvatarSVG(node.value)"></div>
        <!-- 水晶球SVG -->
        <svg class="crystal-ball" viewBox="0 0 100 100">
          <defs>
            <radialGradient id="crystal-gradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="#fff" stop-opacity="0.95"/>
              <stop offset="60%" stop-color="#b2ebf2" stop-opacity="0.7"/>
              <stop offset="100%" stop-color="#00eaff" stop-opacity="0.45"/>
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="44" fill="url(#crystal-gradient)"/>
          <!-- 高光 -->
          <ellipse cx="38" cy="32" rx="16" ry="7" fill="#fff" opacity="0.35"/>
          <!-- 粒子动画：每个按钮不同颜色/数量/延迟 -->
          <g>
            <circle v-for="n in node.particleCount" :key="n"
              :cx="50 + 28 * Math.cos((n*360/node.particleCount-90 + (activeNode === node.value ? 20 : 0))*Math.PI/180)"
              :cy="50 + 28 * Math.sin((n*360/node.particleCount-90 + (activeNode === node.value ? 20 : 0))*Math.PI/180)"
              r="2.5" :fill="node.particleColor" opacity="0.85">
              <animate attributeName="r" values="2.5;4;2.5" dur="1.2s" :begin="(n*node.particleDelayBase)+'s'" repeatCount="indefinite"/>
            </circle>
          </g>
        </svg>
      </div>
      <div class="crystal-label">{{ node.label }}</div>
    </div>
  </div>

  <!-- 内容区：玻璃拟态/发光卡片，节点切换用v-if渲染内容 -->
  <div class="glass-card content-area">
    <div v-if="activeNode === 'connection'">
      <v-row dense>
        <v-col cols='12' md='6'><v-text-field v-model='config.pve_host' label='PVE主机地址' prepend-inner-icon='mdi-server' dense /></v-col>
        <v-col cols='12' md='6'><v-text-field v-model.number='config.ssh_port' label='SSH端口' type='number' min='0' prepend-inner-icon='mdi-numeric' dense /></v-col>
      </v-row>
      <v-row dense>
        <v-col cols='12' md='6'><v-text-field v-model='config.ssh_username' label='SSH用户名' prepend-inner-icon='mdi-account' hint='通常使用root用户以确保有足够权限' persistent-hint dense /></v-col>
        <v-col cols='12' md='6'><v-text-field v-model='config.ssh_password' label='SSH密码' :type='showSshPassword?"text":"password"' :append-inner-icon='showSshPassword?"mdi-eye-off":"mdi-eye"' @click:append-inner='showSshPassword=!showSshPassword' prepend-inner-icon='mdi-key' dense /></v-col>
      </v-row>
      <v-row dense>
        <v-col cols='12'><v-text-field v-model='config.ssh_key_file' label='SSH私钥文件路径' prepend-inner-icon='mdi-file-key' dense /></v-col>
      </v-row>
      
      <!-- 状态页轮询配置 -->
      <v-divider class="my-4"></v-divider>
      <div class="section-subtitle mb-2">
        <v-icon class="mr-1" color="info" size="18">mdi-refresh</v-icon>
        状态页轮询设置
      </div>
      <v-alert type="warning" dense class="mb-3" border="left">
        <span style="font-size:0.875rem;">轮询间隔设置太低会增加CPU使用率和API请求频率，建议使用默认值或更长间隔。</span>
      </v-alert>
      <v-row dense>
        <v-col cols='12' md='6'>
          <v-select 
            v-model='config.status_poll_interval' 
            :items='pollIntervalOptions' 
            label='状态轮询间隔' 
            prepend-inner-icon='mdi-clock-outline'
            hint='状态页轮询PVE主机状态和插件状态的时间间隔'
            persistent-hint
            dense 
          />
        </v-col>
        <v-col cols='12' md='6'>
          <v-select 
            v-model='config.container_poll_interval' 
            :items='pollIntervalOptions' 
            label='容器状态轮询间隔' 
            prepend-inner-icon='mdi-docker'
            hint='状态页轮询容器状态的时间间隔'
            persistent-hint
            dense 
          />
        </v-col>
      </v-row>
    </div>
    <div v-else-if="activeNode === 'local-backup'">
      <!-- 备份存储（本地磁盘 / MP 存储网盘，可多目标同时备份） -->
      <v-row dense>
        <v-col cols='12' md='4'><v-switch v-model='config.storage_backup_enable' label='备份存储（本地磁盘 / MP 存储）' color='success' prepend-icon='mdi-database-outline' class='tight-switch' /></v-col>
      </v-row>
      <template v-if="config.storage_backup_enable">
        <v-row v-for="(t, idx) in config.storage_targets" :key="'ptarget-' + idx" dense align="center">
          <v-col cols='12' md='3'>
            <v-select v-model='t.type' :items='storageOptions' label='选择存储' dense hide-details no-data-text='未找到可用存储'
              @update:model-value='v => onTargetTypeChange(t, v)' />
          </v-col>
          <v-col cols='12' md='5'>
            <v-text-field v-model='t.path' :label="t.type === 'local' ? '备份路径（默认本地备份目录）' : '远端目录'" prepend-inner-icon='mdi-folder-network' dense hide-details>
              <template #append-inner>
                <v-icon icon='mdi-folder-open' size='18' color='primary' style='cursor:pointer' title='浏览目录' @click='openDirPicker(idx)' />
              </template>
            </v-text-field>
          </v-col>
          <v-col cols='12' md='3'><v-text-field v-model.number='t.keep_backup_num' label='备份保留数量' type='number' min='0' dense hide-details /></v-col>
          <v-col cols='12' md='1' class="text-center">
            <v-btn icon='mdi-trash-can-outline' variant='text' color='error' size='small' :disabled='config.storage_targets.length <= 1' title='删除该目标' @click='config.storage_targets.splice(idx, 1)' />
          </v-col>
        </v-row>
        <v-row dense>
          <v-col cols='12' class="d-flex align-center flex-wrap ga-2">
            <v-btn size='small' variant='tonal' color='primary' prepend-icon='mdi-plus' @click='addStorageTarget'>添加备份目标</v-btn>
            <span class='text-caption text-medium-emphasis'>可同时添加多个存储目标，备份时同时保存到所有目标；备份保留数量为 0 表示保留全部</span>
          </v-col>
        </v-row>
      </template>
      <v-divider class="my-2" />
      <v-row dense>
        <v-col cols='12' md='3'><v-switch v-model='config.enable_webdav' label='启用WebDAV备份' color='info' prepend-icon='mdi-cloud-upload' class='tight-switch' @change="onFeatureSwitch('enable_webdav', $event)" /></v-col>
        <v-col cols='12' md='9'><v-text-field v-model='config.webdav_url' label='WebDAV服务器地址' prepend-inner-icon='mdi-cloud' dense /></v-col>
      </v-row>
      <v-row dense>
        <v-col cols='12' md='6'><v-text-field v-model='config.webdav_username' label='WebDAV用户名' prepend-inner-icon='mdi-account' dense /></v-col>
        <v-col cols='12' md='6'><v-text-field v-model='config.webdav_password' label='WebDAV密码' :type='showWebdavPassword?"text":"password"' :append-inner-icon='showWebdavPassword?"mdi-eye-off":"mdi-eye"' @click:append-inner='showWebdavPassword=!showWebdavPassword' prepend-inner-icon='mdi-lock' dense /></v-col>
      </v-row>
      <v-row dense>
        <v-col cols='12' md='7'><v-text-field v-model='config.webdav_path' label='WebDAV备份路径' prepend-inner-icon='mdi-folder-network' dense /></v-col>
        <v-col cols='12' md='5'><v-text-field v-model.number='config.webdav_keep_backup_num' label='WebDAV备份保留数量' type='number' min='0' prepend-inner-icon='mdi-counter' hint='设置为0或留空表示保留全部备份' persistent-hint dense /></v-col>
      </v-row>
    </div>
    <div v-else-if="activeNode === 'backup-config'">
      <div class="switch-flex-row backup-options" style="margin-bottom:8px;">
        <div class="switch-flex-item">
          <v-switch v-model="config.auto_delete_after_download" label="下载后自动删除PVE备份" color="error" prepend-icon="mdi-delete-forever" class="tight-switch" />
        </div>
        <div class="switch-flex-item">
          <v-switch v-model="config.download_all_backups" label="下载所有备份文件（多VM时）" color="info" prepend-icon="mdi-download-multiple" class="tight-switch" />
        </div>
        <div class="switch-flex-item"></div>
      </div>
      <div class="switch-flex-row" style="margin-bottom:18px;">
        <div class="switch-flex-item">
          <v-switch v-model="config.enable_restore" label="启用恢复系统" color="primary" prepend-icon="mdi-restore" class="tight-switch" />
        </div>
        <div class="switch-flex-item">
          <v-switch v-model="config.restore_force" label="强制恢复容器" color="error" prepend-icon="mdi-alert-circle" class="tight-switch" />
        </div>
        <div class="switch-flex-item">
          <v-switch v-model="config.restore_skip_existing" label="跳过已存在的VM" color="warning" prepend-icon="mdi-skip-next" class="tight-switch" />
        </div>
      </div>
      <v-row dense>
        <v-col cols='12' md='4'><v-text-field v-model='config.storage_name' label='存储名称' prepend-inner-icon='mdi-database' dense /></v-col>
        <v-col cols='12' md='4'><v-text-field v-model='config.backup_vmid' label='要备份的容器ID' prepend-inner-icon='mdi-numeric' dense /></v-col>
        <v-col cols='12' md='4'><v-select v-model='config.backup_mode' :items='backupModeOptions' label='备份模式' prepend-inner-icon='mdi-camera-timer' dense /></v-col>
      </v-row>
      <v-row dense>
        <v-col cols='12' md='4'><v-select v-model='config.compress_mode' :items='compressModeOptions' label='压缩模式' prepend-inner-icon='mdi-zip-box' dense /></v-col>
      </v-row>
    </div>
    <div v-else-if="activeNode === 'cleanup'">
      <div class="risk-warning mb-4">
        <v-icon size="18" color="warning" class="mr-2">mdi-alert</v-icon>
        <span style="font-size:1.08em;">本分区所有操作将直接作用于PVE主机系统，部分操作不可逆，请务必谨慎操作并提前做好备份！</span>
      </div>
      <v-row dense>
        <div class="cleanup-switch-row">
          <v-switch
            v-model="config.auto_cleanup_tmp"
            label="启用临时空间"
            color="warning"
            prepend-icon="mdi-delete-sweep"
          />
          <v-switch
            v-model="config.enable_log_cleanup"
            label="启用系统日志"
            color="info"
            prepend-icon="mdi-file-document-multiple"
          />
          <v-switch
            v-model="config.cleanup_template_images"
            label="启用镜像模板"
            color="primary"
            prepend-icon="mdi-cube-outline"
            class="tight-switch"
          />
        </div>
      </v-row>
      <v-row dense class="mt-4">
        <v-col cols="12" md="3">
          <v-text-field v-model.number="config.log_journal_days" :disabled="!config.enable_log_cleanup" label="journalctl保留天数" type="number" min="0" prepend-inner-icon="mdi-calendar-clock" hint="仅清理早于N天的systemd日志，留空或0为全部清理" persistent-hint dense />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field v-model.number="config.log_vzdump_keep" :disabled="!config.enable_log_cleanup" label="/var/log/vzdump保留最新N个" type="number" min="0" prepend-inner-icon="mdi-file-document" hint="0为全部清理" persistent-hint dense />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field v-model.number="config.log_pve_keep" :disabled="!config.enable_log_cleanup" label="/var/log/pve保留最新N个" type="number" min="0" prepend-inner-icon="mdi-file-document" hint="0为全部清理" persistent-hint dense />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field v-model.number="config.log_dpkg_keep" :disabled="!config.enable_log_cleanup" label="/var/log/dpkg.log保留最新N个" type="number" min="0" prepend-inner-icon="mdi-file-document" hint="0为全部清理" persistent-hint dense />
        </v-col>
      </v-row>
      <!-- 功能说明区块 -->
      <ul class="feature-list">
        <li>
          <v-icon size="16" color="warning" class="dot-icon">mdi-checkbox-blank-circle</v-icon>
          临时空间功能会删除系统 /var/lib/vz/dump/ 下所有以 .tmp 结尾的文件和目录（含临时备份缓存）。
        </li>
        <li>
          <v-icon size="16" color="info" class="dot-icon">mdi-checkbox-blank-circle</v-icon>
          系统日志功能清理不可逆，请谨慎操作。journalctl 支持按天保留，其它日志只能保留最新N个或全部清理。
        </li>
        <li>
          <v-icon size="16" color="primary" class="dot-icon">mdi-checkbox-blank-circle</v-icon>
          镜像模板功能启用后，可在状态页管理ISO镜像和CT模板。关闭后相关操作将被禁用。
        </li>
      </ul>
    </div>
    <div v-else-if="activeNode === 'declaration'">
      <div class="section-title">
        <v-icon class="mr-2" color="info">mdi-information-outline</v-icon>
        插件说明
      </div>
      
      <!-- 欢迎信息 -->
      <div class="declaration-section">
        <div class="declaration-text">
          欢迎使用 <b>PVE 守护神 - 备份插件</b>！本插件旨在为你的PVE环境提供便捷、安全的备份与恢复体验。
        </div>
      </div>

      <!-- 交互指令说明 -->
      <div class="declaration-section command-section">
        <div class="declaration-subtitle">
          <v-icon size="20" color="primary" class="mr-2">mdi-message-text</v-icon>
          消息交互指令
        </div>
        <div class="command-cards">
          <div class="command-card">
            <div class="command-icon">📊</div>
            <div class="command-content">
              <div class="command-title">/pve状态</div>
              <div class="command-desc">查看PVE主机状态信息，包括CPU、内存、磁盘等实时数据</div>
            </div>
          </div>
          <div class="command-card">
            <div class="command-icon">📦</div>
            <div class="command-content">
              <div class="command-title">/pve容器</div>
              <div class="command-desc">查看所有容器/虚拟机的运行状态和详细信息</div>
            </div>
          </div>
          <div class="command-card">
            <div class="command-icon">📚</div>
            <div class="command-content">
              <div class="command-title">/pve帮助</div>
              <div class="command-desc">显示插件帮助信息，查看所有可用指令</div>
            </div>
          </div>
        </div>
        <div class="command-hint">
          <v-icon size="16" color="info" class="mr-1">mdi-information</v-icon>
          <span>在消息渠道（微信、Telegram等）中发送上述指令即可使用交互功能</span>
        </div>
      </div>

      <!-- 重要须知 -->
      <div class="declaration-section warning-section">
        <div class="declaration-subtitle">
          <v-icon size="20" color="warning" class="mr-2">mdi-alert-circle-outline</v-icon>
          重要须知
        </div>
        <ul class="declaration-list">
          <li>数据仅本地存储，远程备份只上传到你指定的服务器，如有顾虑请勿使用本插件。</li>
          <li>插件作者不对因使用本插件造成的任何数据丢失、损坏或其他后果负责。</li>
          <li>使用本插件即表示您已知悉并同意以上说明。</li>
        </ul>
      </div>

      <!-- 使用方法 -->
      <div class="declaration-section">
        <div class="declaration-subtitle">
          <v-icon size="20" color="primary" class="mr-2">mdi-lightbulb-on-outline</v-icon>
          使用方法
        </div>
        <ol class="declaration-list ordered">
          <li>插件的所有主要操作（如备份、恢复、清理）都在"状态页"进行。</li>
          <li>各项功能（如自动备份、WebDAV远程备份、恢复、系统设置）需在本页相应分区启用并保存后，才能在状态页正常使用。</li>
          <li>修改配置后请务必点击"保存"，否则新设置不会生效。</li>
          <li>如遇按钮无法点击或功能不可用，请检查相关功能是否已在本页启用。</li>
          <li>欢迎提交Issue和Pull Request来帮助改进插件。</li>
        </ol>
      </div>
    </div>
    <!-- 全局底部按钮组，所有分区都可见，顺序：状态页、重置、保存、关闭 -->
    <div class="action-btns">
      <div class="left-btns">
        <v-btn class="glow-btn glow-btn-blue" size="small" prepend-icon="mdi-view-dashboard" @click="emit('switch')">状态页</v-btn>
      </div>
      <div class="right-btns">
        <v-btn class="glow-btn glow-btn-orange" size="small" prepend-icon="mdi-restore" @click="resetConfig">重置</v-btn>
        <v-btn class="glow-btn glow-btn-green" size="small" prepend-icon="mdi-content-save" :loading="saving" @click="saveConfig">保存</v-btn>
        <v-btn class="glow-btn glow-btn-pink" size="small" prepend-icon="mdi-close" @click="emit('close')">关闭</v-btn>
      </div>
    </div>
  </div>
  <!-- 目录浏览对话框（本地磁盘 / MP 存储） -->
  <v-dialog v-model="dirPicker.show" max-width="500">
    <v-card>
      <v-card-title class="text-subtitle-1 d-flex align-center flex-wrap ga-2">
        <v-icon size="18">mdi-folder-open</v-icon>选择目录
        <v-chip v-if="dirPicker.storage && dirPicker.storage !== 'local'" size="x-small" variant="tonal" color="deep-purple">{{ dirPicker.storageName || dirPicker.storage }}</v-chip>
        <v-spacer />
        <v-text-field v-model="dirPicker.input" density="compact" variant="outlined" hide-details
          style="max-width: 230px" placeholder="直接输入路径后回车" @keyup.enter="browseTo(dirPicker.input)" />
      </v-card-title>
      <v-card-text style="max-height: 360px; overflow-y: auto">
        <div v-if="dirPicker.loading" class="text-center py-4"><v-progress-circular indeterminate size="24" /></div>
        <template v-else>
          <v-list v-if="dirPicker.dirs.length" density="compact" class="py-0">
            <v-list-item v-if="dirPicker.parent" prepend-icon="mdi-arrow-up" title="..（上级目录）" @click="browseTo(dirPicker.parent)" />
            <v-list-item v-for="d in dirPicker.dirs" :key="d" :title="d" prepend-icon="mdi-folder-outline" @click="browseTo(dirJoin(d))" />
          </v-list>
          <div v-else class="text-caption text-medium-emphasis text-center py-4">此目录没有子目录</div>
        </template>
      </v-card-text>
      <v-card-actions>
        <span class="text-caption text-medium-emphasis text-truncate">{{ dirPicker.path }}</span>
        <v-spacer />
        <v-btn variant="text" @click="dirPicker.show = false">取消</v-btn>
        <v-btn color="primary" variant="tonal" @click="chooseCurrent">选择此目录</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <!-- 徽章渐变定义 -->
  <svg width="0" height="0">
    <defs>
      <linearGradient id="badge-gradient" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#e0f7fa"/>
        <stop offset="100%" stop-color="#b2ebf2"/>
      </linearGradient>
    </defs>
  </svg>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
onMounted(() => {
  document.body.classList.add('theme-light');
});
const props = defineProps({ api: { type: [Object, Function], required: true } });
const emit = defineEmits(['switch', 'close', 'save']);

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
  enable_local_backup: false,
  backup_path: '/config/plugins/ProxmoxVEBackup/actual_backups',
  keep_backup_num: 0,
  enable_webdav: false,
  webdav_url: '',
  webdav_username: '',
  webdav_password: '',
  webdav_path: '',
  webdav_keep_backup_num: 0,
  // 备份存储（本地磁盘 / MP 存储网盘，可多目标）
  storage_backup_enable: true,
  storage_targets: [{ type: 'local', path: '', keep_backup_num: 0 }],
  mp_storages: [],
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

// ===== MP 存储备份 =====
const storageOptions = computed(() => [
  { title: '本地磁盘', value: 'local' },
  ...(config.mp_storages || []).map(s => ({ title: s.name || s.type, value: s.type })),
]);

function addStorageTarget() {
  if (!Array.isArray(config.storage_targets)) config.storage_targets = [];
  // 新增行默认本地磁盘，预填之前的本地备份路径
  config.storage_targets.push({ type: 'local', path: String(config.backup_path || ''), keep_backup_num: 0 });
}

// 切换目标存储类型：从本地切到网盘时清掉本地路径残留
function onTargetTypeChange(t, v) {
  if (v !== 'local' && t.path === String(config.backup_path || '')) {
    t.path = '';
  }
}

// 目录浏览（本地磁盘 / MP 存储）
const dirPicker = reactive({
  show: false, loading: false, targetIdx: 0,
  storage: 'local', storageName: '',
  path: '', input: '', parent: '', dirs: [],
});

function pickerStorage() {
  const t = config.storage_targets?.[dirPicker.targetIdx] || {};
  return t.type === 'local' || !t.type ? 'local' : t.type;
}

function openDirPicker(idx = 0) {
  dirPicker.targetIdx = idx;
  const t = config.storage_targets?.[idx] || {};
  dirPicker.storage = t.type === 'local' || !t.type ? 'local' : t.type;
  dirPicker.storageName = (config.mp_storages || []).find(s => s.type === dirPicker.storage)?.name || dirPicker.storage;
  dirPicker.show = true;
  browseTo(t.path || (dirPicker.storage === 'local' ? config.backup_path || '' : '/'));
}

async function browseTo(path) {
  dirPicker.loading = true;
  try {
    const data = await props.api.get('plugin/ProxmoxVEBackup/list_dir', {
      params: { path: path || '', storage: dirPicker.storage },
    });
    if (data?.ok) {
      dirPicker.path = data.path;
      dirPicker.input = data.path;
      dirPicker.parent = data.parent || '';
      dirPicker.dirs = data.dirs || [];
    } else {
      dirPicker.dirs = [];
      dirPicker.parent = '';
      if (data?.error) error.value = data.error;
    }
  } catch (e) {
    /* 静默 */
  } finally {
    dirPicker.loading = false;
  }
}

function dirJoin(name) {
  const base = (dirPicker.path || '').replace(/[\\/]+$/, '');
  const sep = dirPicker.storage === 'local' && base && !base.includes('/') ? '\\' : '/';
  return base ? `${base}${sep}${name}` : `/${name}`;
}

function chooseCurrent() {
  const t = config.storage_targets?.[dirPicker.targetIdx];
  if (t) t.path = dirPicker.path;
  dirPicker.show = false;
}

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
      // 备份存储目标：确保是数组且至少有一行（本地行默认预填之前的备份路径）
      if (!Array.isArray(config.storage_targets) || !config.storage_targets.length) {
        config.storage_targets = [{ type: 'local', path: String(config.backup_path || ''), keep_backup_num: 0 }];
      }
      // 旧版「启用本地备份」配置迁移：转为存储目标中的本地磁盘行
      if (!config.storage_backup_enable && config.enable_local_backup) {
        config.storage_backup_enable = true;
        config.storage_targets = [{ type: 'local', path: String(config.backup_path || ''), keep_backup_num: Number(config.keep_backup_num) || 0 }];
      }
      if (!Array.isArray(config.mp_storages)) config.mp_storages = [];
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
      backup_path: String(config.backup_path || ''),
      enable_webdav: Boolean(config.enable_webdav),
      webdav_url: String(config.webdav_url || ''),
      webdav_username: String(config.webdav_username || ''),
      webdav_password: String(config.webdav_password || ''),
      webdav_path: String(config.webdav_path || ''),
      webdav_keep_backup_num: Number(config.webdav_keep_backup_num) || 0,
      storage_backup_enable: Boolean(config.storage_backup_enable),
      storage_targets: (Array.isArray(config.storage_targets) ? config.storage_targets : []).map(t => ({
        type: String(t.type || ''),
        path: String(t.path || ''),
        keep_backup_num: Number(t.keep_backup_num) || 0,
      })),
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
    enable_local_backup: false,
    backup_path: '/config/plugins/ProxmoxVEBackup/actual_backups',
    keep_backup_num: 0,
    enable_webdav: false,
    webdav_url: '',
    webdav_username: '',
    webdav_password: '',
    webdav_path: '',
    webdav_keep_backup_num: 0,
    storage_backup_enable: true,
    storage_targets: [{ type: 'local', path: '', keep_backup_num: 0 }],
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


const cleanupLoading = ref(false)
function cleanupTmp() {
  cleanupLoading.value = true
  props.api.get('plugin/ProxmoxVEBackup/status')
    .then(status => {
      if (status.backup_activity && status.backup_activity !== '空闲') {
        $snackbar.error('当前有备份任务进行中，请稍后再清理临时空间');
        cleanupLoading.value = false;
        return;
      }
      props.api.post('plugin/ProxmoxVEBackup/cleanup_tmp')
        .then(res => {
          $snackbar.success(res.msg || '清理完成')
        })
        .catch(e => {
          $snackbar.error(e?.msg || '清理失败')
        })
        .finally(() => {
          cleanupLoading.value = false
        })
    })
    .catch(() => {
      $snackbar.error('获取备份状态失败，无法判断是否可清理');
      cleanupLoading.value = false;
    })
}

// 说明：「启用系统日志」等开关随页面底部「保存」按钮统一持久化。
// 之前此处的自动保存 watch 会在 MP 保存后刷新配置时再次触发，形成保存死循环，已移除。
</script>

<style scoped>
body {
  background: linear-gradient(135deg, #23272f 0%, #181c23 100%);
}
.theme-light {
  --card-bg: #f7f8fa;
}
.theme-dark {
  --card-bg: #23272f;
}
/* 适配浅色主题 */
.theme-light .glass-card {
  /* background: rgba(255, 255, 255, 0.97); 删除纯白背景 */
  border: 2px solid #42a5f5;
  box-shadow: 0 8px 32px 0 #90caf9cc, 0 2px 12px 0 #1976d244;
  /* color: #1a237e; 删除字体颜色，交给主题自动适配 */
  backdrop-filter: blur(10px);
}
.glass-card {
  border-radius: 18px;
  margin-bottom: 32px;
  padding: 24px 32px 16px 32px;
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  transition: all 0.3s ease;
}
.glass-card:hover {
  box-shadow: 0 3px 6px rgba(var(--v-border-color), 0.1) !important;
}
.theme-light .plugin-title {
  color: #1976d2;
  text-shadow: 0 2px 8px #90caf944;
}
.theme-light .section-title {
  color: #1976d2;
  text-shadow: 0 2px 8px #90caf944;
}
.theme-light .glow-btn {
  background: linear-gradient(90deg, #90caf9 0%, #1976d2 100%);
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #90caf955;
}
.theme-light .glow-btn:hover {
  box-shadow: 0 4px 32px 0 #1976d2cc;
  background: linear-gradient(90deg, #1976d2 0%, #90caf9 100%);
}
.guardian-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
  margin-top: 40px;
}
.energy-ring {
  position: relative;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: radial-gradient(circle at 60% 40%, #3f51b5 60%, #23272f 100%);
  box-shadow: 0 0 32px 4px #00eaff55, 0 0 0 8px #23272f;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  transition: box-shadow 0.4s;
}
.energy-ring.enabled {
  box-shadow: 0 0 48px 8px #00eaffcc, 0 0 0 8px #23272f;
  animation: ring-glow 2s infinite alternate;
}
@keyframes ring-glow {
  0% { box-shadow: 0 0 48px 8px #00eaffcc, 0 0 0 8px #23272f; }
  100% { box-shadow: 0 0 80px 16px #00eaffcc, 0 0 0 8px #23272f; }
}
.plugin-status {
  display: none;
}
.plugin-title {
  font-size: 1.3rem;
  font-weight: bold;
  color: #fff;
  margin-top: 16px;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px #00eaff44;
}
.base-settings {
  max-width: 900px;
  margin: 0 auto 32px auto;
  border: 2px solid #00eaff77;
  box-shadow: 0 0 32px 0 #00eaff33;
}
.section-title {
  font-weight: bold;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  color: #00eaff;
  margin-bottom: 8px;
  letter-spacing: 1px;
}
.section-subtitle {
  font-weight: 600;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  color: inherit;
  opacity: 0.85;
  margin-bottom: 8px;
  letter-spacing: 1px;
}
.guardian-nodes {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 36px;
  margin-bottom: 32px;
}
.node-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  border-radius: 50%;
  background: linear-gradient(135deg, #23272f 60%, #00eaff22 100%);
  box-shadow: 0 2px 12px 0 #00eaff22;
  padding: 18px 10px 10px 10px;
  transition: box-shadow 0.3s, background 0.3s;
  border: 2px solid transparent;
}
.node-btn.active {
  background: linear-gradient(135deg, #00eaff55 60%, #23272f 100%);
  box-shadow: 0 0 32px 0 #00eaff99;
  border: 2px solid #00eaff;
}
.node-btn:hover {
  box-shadow: 0 0 32px 0 #00eaff77;
  background: linear-gradient(135deg, #00eaff33 60%, #23272f 100%);
}
.node-label {
  margin-top: 6px;
  font-size: 0.95rem;
  color: #90caf9;
  text-shadow: 0 1px 4px #00eaff33;
}
.content-area {
  max-width: 900px;
  margin: 0 auto 32px auto;
  min-height: 220px;
  border: 2px solid #00eaff44;
  box-shadow: 0 0 32px 0 #00eaff22;
  padding-bottom: 24px;
}
.action-btns {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  margin-top: 24px;
}
.left-btns {
  display: flex;
  align-items: center;
}
.right-btns {
  display: flex;
  align-items: center;
  gap: 18px;
}
.glow-btn {
  border-radius: 10px;
  font-weight: 500;
  min-width: 90px;
  background: linear-gradient(90deg, #00eaff 0%, #3f51b5 100%);
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #00eaff55;
  transition: box-shadow 0.3s, background 0.3s;
}
.glow-btn:hover {
  box-shadow: 0 4px 32px 0 #00eaffcc;
  background: linear-gradient(90deg, #3f51b5 0%, #00eaff 100%);
}
.tight-switch {
  margin-bottom: -8px;
  margin-top: -8px;
}
.v-alert {
  font-size: 0.95rem;
}
.q-guardian-avatar-wrapper {
  position: relative;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.energy-bar {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 1;
  pointer-events: none;
}
.energy-bar-glow .v-progress-circular__overlay {
  filter: drop-shadow(0 0 16px #00eaffcc);
}
.energy-bar-glow .v-progress-circular__underlay {
  filter: blur(1px);
}
.energy-bar-glow .v-progress-circular__content {
  display: none;
}
.energy-bar-glow .v-progress-circular__overlay {
  stroke-linecap: round !important;
}
.q-guardian-avatar {
  position: relative;
  width: 88px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: filter 0.2s;
  z-index: 2;
  border-radius: 50%;
  overflow: hidden;
  background: #fff;
}
.q-guardian-avatar:hover {
  filter: brightness(1.1) drop-shadow(0 0 8px #00eaff88);
}
.energy-value {
  display: none;
}
.guardian-level {
  position: absolute;
  right: -18px;
  top: 8px;
  background: #fff8;
  border-radius: 10px;
  padding: 2px 8px 2px 4px;
  font-size: 0.95rem;
  color: #ffb300;
  display: flex;
  align-items: center;
  gap: 2px;
  box-shadow: 0 2px 8px #ffd70033;
  z-index: 3;
}
.blessing-bubble {
  position: absolute;
  left: 100%;
  top: 18px;
  background: #fff;
  color: #2196f3;
  border-radius: 16px;
  padding: 6px 16px;
  font-size: 1rem;
  box-shadow: 0 2px 24px 4px #00eaff88, 0 2px 12px #00eaff33;
  white-space: nowrap;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 6px;
  animation: bubble-bounce-glow 0.5s;
}
@keyframes bubble-bounce-glow {
  0% { transform: scale(0.7) translateY(0); opacity: 0; box-shadow: 0 2px 0 0 #00eaff00; }
  40% { transform: scale(1.15) translateY(-12px); opacity: 1; box-shadow: 0 2px 32px 8px #00eaffcc; }
  60% { transform: scale(0.95) translateY(4px); box-shadow: 0 2px 24px 4px #00eaff88; }
  100% { transform: scale(1) translateY(0); opacity: 1; box-shadow: 0 2px 24px 4px #00eaff88; }
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.q-guardian-avatar.levelup-anim {
  animation: levelup-pop 0.8s, levelup-glow 0.8s;
  box-shadow: 0 0 32px 16px #ffd700cc;
  border-radius: 50%;
}
@keyframes levelup-pop {
  0% { transform: scale(1); }
  30% { transform: scale(1.25) rotate(-8deg);}
  60% { transform: scale(1.15) rotate(8deg);}
  100% { transform: scale(1) rotate(0);}
}
@keyframes levelup-glow {
  0% { box-shadow: 0 0 0 0 #ffd70000; }
  50% { box-shadow: 0 0 48px 24px #ffd700cc; }
  100% { box-shadow: 0 0 32px 16px #ffd700cc; }
}
.node-icon-anim {
  transition: transform 0.18s, filter 0.18s;
}
.node-btn:hover .node-icon-anim {
  transform: scale(1.18) rotate(-8deg);
  filter: drop-shadow(0 0 8px #00eaffcc);
}
.node-btn:active .node-icon-anim {
  transform: scale(0.95) rotate(8deg);
  filter: drop-shadow(0 0 16px #00eaff);
}
.theme-light .plugin-page {
  background: rgba(255,255,255,0.92);
  border: 2px solid #42a5f5;
  box-shadow: 0 8px 32px 0 #90caf9cc, 0 2px 12px 0 #1976d244;
  border-radius: 24px;
  padding: 32px 0 24px 0;
  margin: 32px auto 0 auto;
  max-width: 900px;
  position: relative;
}
.theme-light .plugin-page .guardian-visual {
  margin-bottom: 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #42a5f5;
  box-shadow: 0 4px 16px 0 #90caf922;
}
.cron-field-glass-card {
  background: rgba(40, 50, 70, 0.75);
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 #00eaff22;
  border: 1.5px solid #00eaff33;
  padding: 10px 14px 8px 14px;
  margin-bottom: 2px;
}
.theme-light .cron-field-glass-card {
  background: rgba(255,255,255,0.97);
  border: 1.5px solid #42a5f5;
  box-shadow: 0 2px 12px 0 #90caf922;
}
.cron-expression-input {
  margin-top: 8px;
}
/* Q版导航按钮动画 */
.nav-bar-q {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 28px;
  margin: 32px 0 24px 0;
  flex-wrap: wrap;
}
.nav-btn-q {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: linear-gradient(145deg, #e3f2fd 60%, #b3e5fc 100%);
  box-shadow: 0 4px 24px 0 #90caf9aa, 0 1.5px 8px 0 #0002;
  border: 2.5px solid #b3e5fc;
  position: relative;
  cursor: pointer;
  transition: 
    box-shadow 0.28s cubic-bezier(.4,2,.6,1),
    background 0.28s,
    border 0.28s,
    transform 0.18s;
  user-select: none;
  overflow: visible;
}
.nav-btn-q.active {
  background: linear-gradient(145deg, #fffde7 60%, #aeefff 100%);
  border: 2.5px solid #00eaff;
  box-shadow: 0 0 32px 8px #00eaffcc, 0 2px 12px 0 #ffd70044;
  transform: scale(1.10);
}
.nav-btn-q.active .nav-icon-q {
  animation: q-bounce 0.6s cubic-bezier(.4,2,.6,1), q-glow 2.2s infinite;
}
@keyframes q-bounce {
  0%   { transform: translateY(0) scale(1);}
  20%  { transform: translateY(-12%) scale(1.12);}
  40%  { transform: translateY(0) scale(0.96);}
  60%  { transform: translateY(-6%) scale(1.06);}
  80%  { transform: translateY(0) scale(1);}
  100% { transform: translateY(0) scale(1);}
}
@keyframes q-glow {
  0%, 100% { filter: drop-shadow(0 0 8px #00eaff66);}
  50%      { filter: drop-shadow(0 0 24px #00eaffcc);}
}
.nav-btn-q:hover .nav-icon-q {
  animation: q-shake 0.5s;
}
@keyframes q-shake {
  0%,100% { transform: rotate(0);}
  20%     { transform: rotate(-8deg);}
  40%     { transform: rotate(6deg);}
  60%     { transform: rotate(-4deg);}
  80%     { transform: rotate(2deg);}
}
.nav-icon-q {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin-bottom: 6px;
  filter: drop-shadow(0 0 8px #00eaff33);
  transition: filter 0.18s;
}
.nav-label-q {
  font-size: 1.08rem;
  font-family: 'ZCOOL KuaiLe', 'Inter', 'PingFang SC', 'HarmonyOS Sans', Arial, sans-serif;
  font-weight: 600;
  color: #00bcd4;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px #00eaff33;
  transition: color 0.22s, text-shadow 0.22s;
}
.nav-btn-q.active .nav-label-q {
  color: #ffb300;
  text-shadow: 0 2px 8px #ffd70077;
}
@keyframes q-blink {
  0%, 90%, 100% { transform: scaleY(1);}
  92%, 96%     { transform: scaleY(0.2);}
}
.nav-btn-q.active .q-eye {
  transform-origin: center;
  animation: q-blink 2.2s infinite;
  transition: transform 0.2s;
}
@media (max-width: 900px) {
  .nav-bar-q {
    gap: 12px;
  }
  .nav-btn-q {
    width: 64px;
    height: 64px;
  }
  .nav-icon-q {
    width: 32px;
    height: 32px;
  }
}
@media (max-width: 600px) {
  .nav-bar-q {
    gap: 6px;
    flex-wrap: wrap;
    justify-content: flex-start;
  }
  .nav-btn-q {
    width: 44vw;
    height: 44vw;
    min-width: 56px;
    min-height: 56px;
    margin-bottom: 6px;
  }
  .nav-label-q {
    font-size: 0.98rem;
  }
  /* 新增：底部action-btns按钮组手机端竖排适配 */
  .action-btns {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .action-btns .glow-btn {
    width: 100%;
    min-width: 0;
    margin: 0;
  }
  .left-btns, .right-btns {
    display: contents;
    gap: 0;
  }
  .action-btns .glow-btn {
    width: 100%;
    min-width: 0;
    margin: 0;
  }
}

/* Q版头像徽章型导航按钮 */
.nav-bar-badge {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 32px;
  margin: 32px 0 24px 0;
  flex-wrap: wrap;
}
.badge-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 110px;
  cursor: pointer;
  user-select: none;
  margin: 0 12px;
  transition: transform 0.18s;
}
.badge-inner {
  position: relative;
  width: 100px;
  height: 100px;
  margin-bottom: 8px;
}
.badge-ring {
  position: absolute;
  left: 0; top: 0;
  width: 100px; height: 100px;
  z-index: 1;
}
.badge-ring circle {
  fill: none;
  stroke: url(#badge-gradient);
  stroke-width: 8;
  filter: drop-shadow(0 0 16px #aeeaff88);
  transition: stroke 0.2s, filter 0.2s;
}
.badge-btn.active .badge-ring circle,
.ring-animate {
  stroke: #ffd700;
  filter: drop-shadow(0 0 32px #ffe066cc);
  animation: ring-glow 1.6s infinite alternate;
}
@keyframes ring-glow {
  0% { filter: drop-shadow(0 0 16px #ffe066cc);}
  100% { filter: drop-shadow(0 0 32px #ffd700cc);}
}
.badge-avatar {
  position: absolute;
  left: 10px; top: 10px;
  width: 80px; height: 80px;
  z-index: 2;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 12px #00eaff33;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter 0.18s;
}
.badge-btn.active .badge-avatar {
  filter: brightness(1.1) drop-shadow(0 0 12px #ffd70088);
}
.badge-label {
  margin-top: 2px;
  font-size: 1.08rem;
  font-family: 'ZCOOL KuaiLe', 'PingFang SC', sans-serif;
  font-weight: 600;
  color: #00bcd4;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px #00eaff33;
  transition: color 0.22s, text-shadow 0.22s;
  text-align: center;
}
.badge-btn.active .badge-label {
  color: #ffb300;
  text-shadow: 0 2px 8px #ffd70077;
}
.badge-btn:active {
  transform: scale(0.96);
}
.badge-btn.active {
  transform: scale(1.08);
  z-index: 2;
}
@media (max-width: 900px) {
  .nav-bar-badge {
    gap: 12px;
  }
  .badge-btn {
    width: 80px;
  }
  .badge-inner {
    width: 72px; height: 72px;
  }
  .badge-ring {
    width: 72px; height: 72px;
  }
  .badge-avatar {
    left: 6px; top: 6px; width: 60px; height: 60px;
  }
  .badge-label {
    font-size: 0.98rem;
  }
}

.nav-bar-crystal {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 36px; /* 更舒适宽松的间距 */
  margin: 32px 0 24px 0;
  flex-wrap: wrap;
}
.crystal-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 90px;
  cursor: pointer;
  user-select: none;
  margin: 0 16px;
  transition: transform 0.18s;
}
.crystal-inner {
  position: relative;
  width: 100px;
  height: 100px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.crystal-ball {
  width: 100px;
  height: 100px;
  z-index: 1;
  transition: filter 0.22s;
}
.crystal-btn.active .crystal-ball {
  animation: crystal-rotate 2.2s linear infinite;
}
@keyframes crystal-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.crystal-avatar {
  position: absolute;
  left: 10px; top: 10px;
  width: 80px; height: 80px;
  z-index: 2;
  border-radius: 50%;
  background: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter 0.18s;
  pointer-events: none;
}
.crystal-btn.active .crystal-avatar {
  filter: brightness(1.1) drop-shadow(0 0 12px #ffd70088);
}
.crystal-label {
  margin-top: 2px;
  font-size: 1.08rem;
  font-family: 'ZCOOL KuaiLe', 'PingFang SC', sans-serif;
  font-weight: 600;
  color: #00bcd4;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px #00eaff33;
  transition: color 0.22s, text-shadow 0.22s;
  text-align: center;
}
.crystal-btn.active .crystal-label {
  color: #ffb300;
  text-shadow: 0 2px 8px #ffd70077;
}
.crystal-btn:active {
  transform: scale(0.96);
}
.crystal-btn.active {
  transform: scale(1.08);
  z-index: 2;
}
.crystal-btn:hover .crystal-inner {
  animation: crystal-float 1.2s infinite alternate;
}
@keyframes crystal-float {
  0% { transform: translateY(0); }
  100% { transform: translateY(-10px); }
}
@media (max-width: 900px) {
  .nav-bar-crystal {
    gap: 16px; /* 移动端更松散的间距 */
  }
  .crystal-btn {
    width: 72px; /* 移动端更舒适的宽度 */
    margin: 0 4px; /* 移动端更舒适的外边距 */
  }
  .crystal-inner {
    width: 56px; height: 56px; /* 保持比例缩小 */
  }
  .crystal-ball {
    width: 56px; height: 56px;
  }
  .crystal-avatar {
    left: 3px; top: 3px; width: 48px; height: 48px;
  }
  .crystal-label {
    font-size: 0.98rem;
  }
}

.glow-btn-blue {
  background: linear-gradient(90deg, #2196f3 0%, #3f51b5 100%) !important;
}
.glow-btn-orange {
  background: linear-gradient(90deg, #ff9800 0%, #ff5722 100%) !important;
}
.glow-btn-green {
  background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%) !important;
}
.glow-btn-pink {
  background: linear-gradient(90deg, #ff6a88 0%, #ff99ac 100%) !important;
}
@media (max-width: 600px) {
  .action-btns {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .action-btns .glow-btn {
    width: 100%;
    min-width: 0;
    margin: 0;
  }
}

/* 在 style scoped 末尾添加系列点点图标样式 */
.feature-list {
  margin: 12px 0 0 0;
  padding-left: 0;
  color: #666;
  font-size: 0.98em;
  line-height: 1.8;
  list-style: none;
}
.feature-list li {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 2px;
}
.dot-icon {
  margin-top: 3px;
  flex-shrink: 0;
}
.cleanup-switch-row {
  display: flex;
  gap: 32px;
  align-items: center;
}
@media (max-width: 600px) {
  .cleanup-switch-row {
    flex-direction: column;
    gap: 12px;
  }
}
.section-avatar {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
  margin-top: -8px;
}
.section-avatar svg {
  width: 64px;
  height: 64px;
  display: block;
}

.risk-warning {
  display: flex;
  align-items: center;
  color: #ff9800;
  background: none;
  padding: 0;
  border: none;
}

.backup-switch-row {
  display: flex;
  gap: 32px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.switch-flex-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 24px;
}
.switch-flex-item {
  flex: 1 1 0;
  min-width: 0;
}
@media (max-width: 600px) {
  .backup-options {
    flex-direction: column !important;
    gap: 8px !important;
  }
  .backup-options .switch-flex-item {
    width: 100% !important;
    min-width: 0 !important;
    margin-bottom: 4px;
  }
}
@media (max-width: 600px) {
  .backup-options .option-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 0;
    gap: 8px;
  }
  .backup-options .option-row .v-icon {
    margin-right: 8px;
  }
  .backup-options .option-row span {
    flex: 1;
    font-size: 1.05em;
  }
}
@media (max-width: 600px) {
  .backup-options .switch-flex-item {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 4px 0;
  }
  .backup-options .v-icon {
    margin-right: 8px;
    flex-shrink: 0;
  }
  .backup-options .v-input__control {
    margin-left: auto;
  }
  .backup-options .v-label {
    flex: 1;
    min-width: 0;
  }
}
@media (max-width: 600px) {
  .mobile-hide-title {
    display: none !important;
  }
  .mobile-only-options {
    display: block;
    margin-bottom: 12px;
  }
  .mobile-option-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0;
  }
  .mobile-option-row .v-icon {
    margin-right: 8px;
    flex-shrink: 0;
  }
  .mobile-option-row .v-input__control {
    margin-left: auto;
  }
  .mobile-option-row span {
    flex: 1;
    min-width: 0;
  }
}
@media (min-width: 601px) {
  .mobile-only-options {
    display: none !important;
  }
}
@media (max-width: 600px) {
  .switch-flex-row {
    flex-direction: column !important;
    gap: 8px !important;
  }
}

/* 插件说明区域样式 */
.declaration-section {
  margin-bottom: 24px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 234, 255, 0.2);
}

.theme-light .declaration-section {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.declaration-text {
  font-size: 1.1em;
  line-height: 1.8;
  color: #2196f3;
  padding: 8px 0;
}

.theme-light .declaration-text {
  color: #1976d2;
}

.declaration-subtitle {
  font-size: 1.15em;
  font-weight: 600;
  color: #00eaff;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.theme-light .declaration-subtitle {
  color: #1976d2;
}

.declaration-list {
  margin: 12px 0;
  padding-left: 24px;
  line-height: 1.8;
  color: #90caf9;
}

.theme-light .declaration-list {
  color: #424242;
}

.declaration-list.ordered {
  list-style-type: decimal;
}

.declaration-list li {
  margin-bottom: 8px;
}

/* 指令说明卡片样式 */
.command-section {
  background: linear-gradient(135deg, rgba(0, 234, 255, 0.1) 0%, rgba(63, 81, 181, 0.1) 100%);
  border: 2px solid rgba(0, 234, 255, 0.3);
}

.theme-light .command-section {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.08) 0%, rgba(144, 202, 249, 0.08) 100%);
  border: 2px solid rgba(33, 150, 243, 0.3);
}

.command-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin: 16px 0;
}

.command-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(0, 234, 255, 0.08);
  border-radius: 10px;
  border: 1px solid rgba(0, 234, 255, 0.2);
  transition: all 0.3s ease;
}

.theme-light .command-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.command-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 234, 255, 0.2);
  border-color: rgba(0, 234, 255, 0.4);
}

.theme-light .command-card:hover {
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.2);
  border-color: rgba(33, 150, 243, 0.4);
}

.command-icon {
  font-size: 2rem;
  line-height: 1;
  flex-shrink: 0;
}

.command-content {
  flex: 1;
}

.command-title {
  font-size: 1.1em;
  font-weight: 600;
  color: #00eaff;
  margin-bottom: 6px;
  font-family: 'Courier New', monospace;
  letter-spacing: 0.5px;
}

.theme-light .command-title {
  color: #1976d2;
}

.command-desc {
  font-size: 0.95em;
  color: #90caf9;
  line-height: 1.6;
}

.theme-light .command-desc {
  color: #616161;
}

.command-hint {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(0, 234, 255, 0.1);
  border-radius: 8px;
  margin-top: 12px;
  font-size: 0.95em;
  color: #90caf9;
  border-left: 3px solid #00eaff;
}

.theme-light .command-hint {
  background: rgba(33, 150, 243, 0.08);
  color: #616161;
  border-left-color: #1976d2;
}

.warning-section {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(255, 87, 34, 0.1) 100%);
  border: 2px solid rgba(255, 152, 0, 0.3);
}

.theme-light .warning-section {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.08) 0%, rgba(255, 87, 34, 0.08) 100%);
  border: 2px solid rgba(255, 152, 0, 0.3);
}

.warning-section .declaration-subtitle {
  color: #ff9800;
}

.theme-light .warning-section .declaration-subtitle {
  color: #f57c00;
}

.warning-section .declaration-list {
  color: #ffb74d;
}

.theme-light .warning-section .declaration-list {
  color: #424242;
}

@media (max-width: 768px) {
  .command-cards {
    grid-template-columns: 1fr;
  }
  
  .declaration-section {
    padding: 12px;
  }
  
  .command-card {
    padding: 12px;
  }
}
</style>