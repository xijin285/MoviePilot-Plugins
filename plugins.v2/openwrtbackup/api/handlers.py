"""API处理模块"""
from typing import Any, Dict
from app.log import logger


class APIHandler:
    """API处理器类"""
    
    def __init__(self, plugin_instance):
        """初始化API处理器"""
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def backup(self, onlyonce: bool = False):
        """API备份接口"""
        try:
            self.plugin.run_backup_job()
            return {"success": True, "message": "备份任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动备份任务失败: {str(e)}"}

