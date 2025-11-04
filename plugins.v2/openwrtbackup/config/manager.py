"""
配置管理模块
负责更新和保存插件配置
"""


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化配置管理器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
    
    def update_config(self):
        """更新插件配置"""
        self.plugin.update_config({
            "enabled": self.plugin._enabled,
            "notify": self.plugin._notify,
            "cron": self.plugin._cron,
            "onlyonce": self.plugin._onlyonce,
            "retry_count": self.plugin._retry_count,
            "retry_interval": self.plugin._retry_interval,
            "openwrt_host": self.plugin._openwrt_host,
            "openwrt_username": self.plugin._openwrt_username,
            "openwrt_password": self.plugin._openwrt_password,
            "enable_local_backup": self.plugin._enable_local_backup,
            "backup_path": self.plugin._backup_path,
            "keep_backup_num": self.plugin._keep_backup_num,
            "enable_webdav": self.plugin._enable_webdav,
            "webdav_url": self.plugin._webdav_url,
            "webdav_username": self.plugin._webdav_username,
            "webdav_password": self.plugin._webdav_password,
            "webdav_path": self.plugin._webdav_path,
            "webdav_keep_backup_num": self.plugin._webdav_keep_backup_num,
        })

