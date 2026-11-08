"""
配置管理模块
负责处理配置的哈希计算、更新和初始化检查
"""
import hashlib
import json
from typing import Optional, Dict
from app.log import logger


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化配置管理器
        :param plugin_instance: ProxmoxVEBackup插件实例
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
        special_operations = {'clear_history', 'restore_now'}
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
                'enabled', 'notify', 'onlyonce', 'retry_count', 'retry_interval', 'notification_message_type',
                'pve_host', 'ssh_port', 'ssh_username', 'ssh_password', 'ssh_key_file',
                'enable_local_backup', 'backup_path', 'keep_backup_num',
                'enable_webdav', 'webdav_url', 'webdav_username', 'webdav_password', 'webdav_path', 'webdav_keep_backup_num',
                'storage_name', 'backup_vmid', 'backup_mode', 'compress_mode', 'auto_delete_after_download', 'download_all_backups',
                'enable_restore', 'restore_force', 'restore_skip_existing', 'restore_storage', 'restore_vmid', 'restore_now', 'restore_file',
                'clear_history',
                'auto_cleanup_tmp',
                'cron'
            }
            for key in critical_keys:
                if key in config:
                    critical_config[key] = config[key]
            if 'auto_cleanup_tmp' not in critical_config:
                critical_config['auto_cleanup_tmp'] = True
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
            "notification_message_type": self.plugin._notification_message_type,
            
            # SSH配置
            "pve_host": self.plugin._pve_host,
            "ssh_port": self.plugin._ssh_port,
            "ssh_username": self.plugin._ssh_username,
            "ssh_password": self.plugin._ssh_password,
            "ssh_key_file": self.plugin._ssh_key_file,
            
            # 备份配置
            "storage_name": self.plugin._storage_name,
            "backup_vmid": self.plugin._backup_vmid,
            "enable_local_backup": self.plugin._enable_local_backup,
            "backup_path": self.plugin._backup_path,
            "keep_backup_num": self.plugin._keep_backup_num,
            "backup_mode": self.plugin._backup_mode,
            "compress_mode": self.plugin._compress_mode,
            "auto_delete_after_download": self.plugin._auto_delete_after_download,
            "download_all_backups": self.plugin._download_all_backups,
            
            # WebDAV配置
            "enable_webdav": self.plugin._enable_webdav,
            "webdav_url": self.plugin._webdav_url,
            "webdav_username": self.plugin._webdav_username,
            "webdav_password": self.plugin._webdav_password,
            "webdav_path": self.plugin._webdav_path,
            "webdav_keep_backup_num": self.plugin._webdav_keep_backup_num,
            "clear_history": self.plugin._clear_history,
            
            # 恢复配置
            "enable_restore": self.plugin._enable_restore,
            "restore_storage": self.plugin._restore_storage,
            "restore_vmid": self.plugin._restore_vmid,
            "restore_force": self.plugin._restore_force,
            "restore_skip_existing": self.plugin._restore_skip_existing,
            "restore_file": self.plugin._restore_file,
            "restore_now": self.plugin._restore_now,
            "auto_cleanup_tmp": (self.plugin.get_config() or {}).get("auto_cleanup_tmp", True),
            
            # 新增系统日志清理配置
            "enable_log_cleanup": getattr(self.plugin, "_enable_log_cleanup", False),
            
            # 状态页轮询配置（单位：毫秒）
            "status_poll_interval": self.plugin.get_config().get("status_poll_interval", 30000) if self.plugin.get_config() else 30000,
            "container_poll_interval": self.plugin.get_config().get("container_poll_interval", 30000) if self.plugin.get_config() else 30000,
            "log_journal_days": getattr(self.plugin, "_log_journal_days", 7),
            "log_vzdump_keep": getattr(self.plugin, "_log_vzdump_keep", 7),
            "log_pve_keep": getattr(self.plugin, "_log_pve_keep", 7),
            "log_dpkg_keep": getattr(self.plugin, "_log_dpkg_keep", 7),
            "cleanup_template_images": self.plugin._cleanup_template_images,
        })
        
        # 保存配置哈希
        if self.plugin._last_config_hash:
            self.plugin.save_data('last_config_hash', self.plugin._last_config_hash)

