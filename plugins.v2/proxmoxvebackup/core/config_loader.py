"""
配置加载模块
负责加载和更新插件配置
"""
import threading
from pathlib import Path
from typing import Optional
from app.log import logger


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化配置加载器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def load_config(self, saved_config: Optional[dict] = None):
        """从保存的配置中加载所有配置项"""
        if not saved_config:
            return
        
        # 基本配置
        self.plugin._enabled = bool(saved_config.get("enabled", False))
        self.plugin._cron = str(saved_config.get("cron", "0 3 * * *"))
        self.plugin._onlyonce = bool(saved_config.get("onlyonce", False))
        self.plugin._notify = bool(saved_config.get("notify", False))
        self.plugin._retry_count = int(saved_config.get("retry_count", 0))
        self.plugin._retry_interval = int(saved_config.get("retry_interval", 60))
        self.plugin._notification_message_type = str(saved_config.get("notification_message_type", "Plugin"))
        
        # SSH配置
        self.plugin._pve_host = str(saved_config.get("pve_host", ""))
        self.plugin._ssh_port = int(saved_config.get("ssh_port", 22))
        self.plugin._ssh_username = str(saved_config.get("ssh_username", "root"))
        self.plugin._ssh_password = str(saved_config.get("ssh_password", ""))
        self.plugin._ssh_key_file = str(saved_config.get("ssh_key_file", ""))
        
        # 备份配置
        self.plugin._storage_name = str(saved_config.get("storage_name", "local"))
        self.plugin._enable_local_backup = bool(saved_config.get("enable_local_backup", True))
        self.plugin._backup_mode = str(saved_config.get("backup_mode", "snapshot"))
        self.plugin._compress_mode = str(saved_config.get("compress_mode", "zstd"))
        self.plugin._backup_vmid = str(saved_config.get("backup_vmid", ""))
        self.plugin._auto_delete_after_download = bool(saved_config.get("auto_delete_after_download", False))
        self.plugin._download_all_backups = bool(saved_config.get("download_all_backups", True))
        
        # 备份路径配置
        configured_backup_path = str(saved_config.get("backup_path", "")).strip()
        if not configured_backup_path:
            self.plugin._backup_path = str(self.plugin.get_data_path() / "actual_backups")
            logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self.plugin._backup_path}")
        else:
            self.plugin._backup_path = configured_backup_path
        
        self.plugin._keep_backup_num = int(saved_config.get("keep_backup_num", 5))
        
        # WebDAV配置
        self.plugin._enable_webdav = bool(saved_config.get("enable_webdav", False))
        self.plugin._webdav_url = str(saved_config.get("webdav_url", ""))
        self.plugin._webdav_username = str(saved_config.get("webdav_username", ""))
        self.plugin._webdav_password = str(saved_config.get("webdav_password", ""))
        self.plugin._webdav_path = str(saved_config.get("webdav_path", ""))
        self.plugin._webdav_keep_backup_num = int(saved_config.get("webdav_keep_backup_num", 7))
        self.plugin._clear_history = bool(saved_config.get("clear_history", False))
        
        # 恢复配置
        self.plugin._enable_restore = bool(saved_config.get("enable_restore", False))
        self.plugin._restore_storage = str(saved_config.get("restore_storage", "local"))
        self.plugin._restore_vmid = str(saved_config.get("restore_vmid", ""))
        self.plugin._restore_force = bool(saved_config.get("restore_force", False))
        self.plugin._restore_skip_existing = bool(saved_config.get("restore_skip_existing", True))
        self.plugin._restore_file = str(saved_config.get("restore_file", ""))
        self.plugin._restore_now = bool(saved_config.get("restore_now", False))
        
        # 其他配置
        self.plugin.auto_cleanup_tmp = saved_config.get("auto_cleanup_tmp", True)
        
        # 系统日志清理配置
        self.plugin._enable_log_cleanup = bool(saved_config.get("enable_log_cleanup", False))
        self.plugin._log_journal_days = int(saved_config.get("log_journal_days", 0))
        self.plugin._log_vzdump_keep = int(saved_config.get("log_vzdump_keep", 0))
        self.plugin._log_pve_keep = int(saved_config.get("log_pve_keep", 0))
        self.plugin._log_dpkg_keep = int(saved_config.get("log_dpkg_keep", 0))
        self.plugin._cleanup_template_images = bool(saved_config.get("cleanup_template_images", False))
    
    def apply_config_updates(self, config: Optional[dict] = None):
        """应用新配置更新"""
        if not config:
            return
        
        for k, v in config.items():
            if k == "cron":
                self.plugin._cron = str(v)
            if hasattr(self.plugin, f"_{k}"):
                setattr(self.plugin, f"_{k}", v)
            # 新增：支持 auto_cleanup_tmp
            if k == "auto_cleanup_tmp":
                self.plugin.auto_cleanup_tmp = bool(v)
            if k == "enable_log_cleanup":
                self.plugin._enable_log_cleanup = bool(v)
            if k == "log_journal_days":
                self.plugin._log_journal_days = int(v)
            if k == "log_vzdump_keep":
                self.plugin._log_vzdump_keep = int(v)
            if k == "log_pve_keep":
                self.plugin._log_pve_keep = int(v)
            if k == "log_dpkg_keep":
                self.plugin._log_dpkg_keep = int(v)
            if k == "cleanup_template_images":
                self.plugin._cleanup_template_images = bool(v)
        
        # 保存轮询配置等不需要实例属性的配置字段
        # 这些字段直接保存到配置字典中，不存储为实例属性
        poll_config_fields = {"status_poll_interval", "container_poll_interval"}
        poll_config_updated = False
        if any(k in poll_config_fields for k in config.keys()):
            # 获取当前完整配置并更新轮询字段
            current_config = self.plugin.get_config() or {}
            for field in poll_config_fields:
                if field in config:
                    current_config[field] = int(config[field])
                    poll_config_updated = True
            # 先保存轮询配置到配置字典
            if poll_config_updated:
                self.plugin.update_config(current_config)
        
        if self.plugin._config_manager:
            # update_config 会保存完整配置，包括轮询配置
            self.plugin._config_manager.update_config()
    
    def process_special_actions(self):
        """处理特殊操作（清理历史/立即恢复）"""
        # 处理清理历史
        if self.plugin._clear_history:
            if self.plugin._history_handler:
                self.plugin._history_handler.clear_all_history()
            self.plugin._clear_history = False
            if self.plugin._config_manager:
                self.plugin._config_manager.update_config()
        
        # 处理立即恢复
        if self.plugin._restore_now and self.plugin._restore_file:
            try:
                source, filename = self.plugin._restore_file.split('|', 1)
                threading.Thread(target=self.plugin._restore_executor.run_restore_job, args=(filename, source)).start()
                logger.info(f"{self.plugin_name} 已触发恢复任务，文件: {filename}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 触发恢复任务失败: {e}")
            finally:
                self.plugin._restore_now = False
                self.plugin._restore_file = ""
                if self.plugin._config_manager:
                    self.plugin._config_manager.update_config()
    
    def ensure_backup_directory(self):
        """确保备份目录存在"""
        try:
            Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建实际备份目录 {self.plugin._backup_path} 失败: {e}")

