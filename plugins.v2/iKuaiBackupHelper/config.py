# 配置管理模块 - config.py
import json
import os

class ConfigManager:
    CONFIG_FILE = "ikuai_backup_config.json"
    
    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self._get_default_config()
        return self._get_default_config()
        
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "ikuai_url": "http://192.168.1.1",
            "username": "admin",
            "password": "",
            "backup_interval": "0 2 * * *",  # 每天凌晨2点
            "max_backups": 7,
            "save_path": "./backups",
            "notify_enabled": False,
            "notify_type": "synology",
            "notify_url": ""
        }
        
    def save_config(self):
        """保存配置文件"""
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
