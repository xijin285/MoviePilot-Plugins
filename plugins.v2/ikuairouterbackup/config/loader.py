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
        :param plugin_instance: IkuaiRouterBackup插件实例
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
        self.plugin._retry_count = int(saved_config.get("retry_count", 3))
        self.plugin._retry_interval = int(saved_config.get("retry_interval", 60))
        self.plugin._notification_style = int(saved_config.get("notification_style", 0))

        # 处理ikuai_url，保留原始值用于显示，处理后的值用于后端请求
        self.plugin._original_ikuai_url = str(saved_config.get("ikuai_url", "")).strip()
        self.plugin._ikuai_url = self.plugin._get_processed_ikuai_url(self.plugin._original_ikuai_url)

        self.plugin._ikuai_username = str(saved_config.get("ikuai_username", "admin"))
        self.plugin._ikuai_password = str(saved_config.get("ikuai_password", ""))
        self.plugin._enable_local_backup = bool(saved_config.get("enable_local_backup", True))
        
        # 备份路径配置
        configured_backup_path = str(saved_config.get("backup_path", "")).strip()
        if not configured_backup_path:
            self.plugin._backup_path = str(self.plugin.get_data_path() / "actual_backups")
            logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self.plugin._backup_path}")
        else:
            self.plugin._backup_path = configured_backup_path
        self.plugin._keep_backup_num = int(saved_config.get("keep_backup_num", 7))
        
        # WebDAV配置
        self.plugin._enable_webdav = bool(saved_config.get("enable_webdav", False))
        self.plugin._webdav_url = str(saved_config.get("webdav_url", ""))
        self.plugin._webdav_username = str(saved_config.get("webdav_username", ""))
        self.plugin._webdav_password = str(saved_config.get("webdav_password", ""))
        self.plugin._webdav_path = str(saved_config.get("webdav_path", ""))
        self.plugin._webdav_keep_backup_num = int(saved_config.get("webdav_keep_backup_num", 7))
        self.plugin._clear_history = bool(saved_config.get("clear_history", False))
        self.plugin._delete_after_backup = bool(saved_config.get("delete_after_backup", False))
        
        # 恢复配置
        self.plugin._enable_restore = bool(saved_config.get("enable_restore", False))
        self.plugin._restore_force = bool(saved_config.get("restore_force", False))
        self.plugin._restore_file = str(saved_config.get("restore_file", ""))
        self.plugin._restore_now = bool(saved_config.get("restore_now", False))
        
        # IP分组配置
        self.plugin._enable_ip_group = bool(saved_config.get("enable_ip_group", False))
        self.plugin._ip_group_province = str(saved_config.get("ip_group_province", ""))
        self.plugin._ip_group_city = str(saved_config.get("ip_group_city", ""))
        self.plugin._ip_group_isp = str(saved_config.get("ip_group_isp", ""))
        self.plugin._ip_group_prefix = str(saved_config.get("ip_group_prefix", ""))
        self.plugin._ip_group_address_pool = bool(saved_config.get("ip_group_address_pool", False))
        self.plugin._ip_group_sync_now = bool(saved_config.get("ip_group_sync_now", False))
        
        # 创建备份目录
        self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """确保备份目录存在"""
        try:
            Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建实际备份目录 {self.plugin._backup_path} 失败: {e}")

