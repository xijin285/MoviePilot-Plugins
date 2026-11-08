"""
配置管理模块
负责处理配置的哈希计算和更新
"""
import hashlib
import json
from typing import Optional
from app.log import logger


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化配置管理器
        :param plugin_instance: IkuaiRouterBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def should_skip_reinit(self, config: Optional[dict] = None) -> bool:
        """
        检查是否应该跳过重新初始化
        只有在关键配置发生变更时才重新初始化
        """
        if not config:
            return False
        # 检查特殊操作标志（这些操作需要立即执行）
        special_operations = {'clear_history', 'restore_now', 'ip_group_sync_now'}
        for op in special_operations:
            if op in config and config[op]:
                logger.debug(f"{self.plugin_name} 检测到特殊操作: {op}，需要重新初始化")
                return False
        # 计算当前配置的哈希值
        current_config_hash = self.calculate_config_hash(config)
        # 只有哈希完全一致才跳过，否则都重载
        if self.plugin._last_config_hash == current_config_hash:
            logger.debug(f"{self.plugin_name} 配置哈希未变更，跳过重新初始化 (哈希: {current_config_hash[:8]}...)")
            return True
        # 更新哈希值
        logger.debug(f"{self.plugin_name} 配置哈希已变更，需要重新初始化 (旧哈希: {self.plugin._last_config_hash[:8] if self.plugin._last_config_hash else 'None'}... -> 新哈希: {current_config_hash[:8]}...)")
        self.plugin._last_config_hash = current_config_hash
        return False

    def calculate_config_hash(self, config: dict) -> str:
        """
        计算配置的哈希值，用于检测配置变更
        """
        try:
            # 全量纳入所有前端可配置项，确保每次保存都能生效
            critical_config = {}
            critical_keys = {
                'enabled', 'notify', 'onlyonce', 'retry_count', 'retry_interval', 'notification_style',
                'ikuai_url', 'ikuai_username', 'ikuai_password', 'ikuai_auth_mode', 'ikuai_api_token',
                'storage_backup_enable', 'storage_type', 'storage_path', 'storage_keep_backup_num',
                'storage_targets',
                'enable_webdav', 'webdav_url', 'webdav_username', 'webdav_password', 'webdav_path', 'webdav_keep_backup_num',
                'clear_history', 'delete_after_backup',
                'monitor_enable',
                'skip_unchanged_backup', 'restore_point_enable',
                'load_warn_enable', 'load_cpu_threshold', 'load_mem_threshold', 'load_warn_times',
                'enable_restore', 'restore_force', 'restore_file', 'restore_now',
                'enable_ip_group', 'ip_group_province', 'ip_group_city', 'ip_group_isp', 'ip_group_prefix', 'ip_group_address_pool', 'ip_group_sync_now',
                'cron'
            }
            for key in critical_keys:
                if key in config:
                    critical_config[key] = config[key]
            config_str = json.dumps(critical_config, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(config_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"{self.plugin_name} 计算配置哈希失败: {e}")
            return "error_hash"

    def update_config(self):
        """更新配置到持久化存储"""
        self.plugin.update_config({
            "enabled": self.plugin._enabled,
            "notify": self.plugin._notify,
            "cron": self.plugin._cron,
            "onlyonce": self.plugin._onlyonce,
            "retry_count": self.plugin._retry_count,
            "retry_interval": self.plugin._retry_interval,
            "ikuai_url": self.plugin._original_ikuai_url,
            "ikuai_username": self.plugin._ikuai_username,
            "ikuai_password": self.plugin._ikuai_password,
            "ikuai_auth_mode": self.plugin._ikuai_auth_mode,
            "ikuai_api_token": self.plugin._ikuai_api_token,
            # 统一存储备份目标（多目标）
            "storage_backup_enable": self.plugin._storage_backup_enable,
            "storage_type": self.plugin._storage_type,
            "storage_path": self.plugin._storage_path,
            "storage_keep_backup_num": self.plugin._storage_keep_backup_num,
            "storage_targets": self.plugin._storage_targets or [],
            "notification_style": self.plugin._notification_style,
            "enable_webdav": self.plugin._enable_webdav,
            "webdav_url": self.plugin._webdav_url,
            "webdav_username": self.plugin._webdav_username,
            "webdav_password": self.plugin._webdav_password,
            "webdav_path": self.plugin._webdav_path,
            "webdav_keep_backup_num": self.plugin._webdav_keep_backup_num,
            "clear_history": self.plugin._clear_history,
            "delete_after_backup": self.plugin._delete_after_backup,
            # Vue 仪表盘/侧边栏开关
            "monitor_enable": self.plugin._monitor_enable,
            # 备份增强
            "skip_unchanged_backup": self.plugin._skip_unchanged_backup,
            "restore_point_enable": self.plugin._restore_point_enable,
            # 负载告警
            "load_warn_enable": self.plugin._load_warn_enable,
            "load_cpu_threshold": self.plugin._load_cpu_threshold,
            "load_mem_threshold": self.plugin._load_mem_threshold,
            "load_warn_times": self.plugin._load_warn_times,
            "enable_restore": self.plugin._enable_restore,
            "restore_force": self.plugin._restore_force,
            "restore_file": self.plugin._restore_file,
            "restore_now": self.plugin._restore_now,
            # IP分组配置
            "enable_ip_group": self.plugin._enable_ip_group,
            "ip_group_province": self.plugin._ip_group_province,
            "ip_group_city": self.plugin._ip_group_city,
            "ip_group_isp": self.plugin._ip_group_isp,
            "ip_group_prefix": self.plugin._ip_group_prefix,
            "ip_group_address_pool": self.plugin._ip_group_address_pool,
            "ip_group_sync_now": self.plugin._ip_group_sync_now,
        })

