"""
配置加载模块
负责加载和更新插件配置
"""
from pathlib import Path
from typing import Optional
from app.log import logger


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化配置加载器
        :param plugin_instance: OpenWrtBackup插件实例
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
        
        # OpenWrt连接配置
        self.plugin._openwrt_host = str(saved_config.get("openwrt_host", ""))
        self.plugin._openwrt_username = str(saved_config.get("openwrt_username", "root"))
        self.plugin._openwrt_password = str(saved_config.get("openwrt_password", ""))
        
        # 本地备份配置
        self.plugin._enable_local_backup = bool(saved_config.get("enable_local_backup", True))
        configured_backup_path = str(saved_config.get("backup_path", "")).strip()
        if not configured_backup_path:
            self.plugin._backup_path = str(self.plugin.get_data_path())
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

