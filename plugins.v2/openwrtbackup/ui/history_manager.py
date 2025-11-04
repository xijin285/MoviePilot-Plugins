"""
历史记录管理模块
负责备份历史记录的加载、保存和管理
"""
from typing import Any, List, Dict
from app.log import logger


class HistoryManager:
    """历史记录管理器类"""
    
    def __init__(self, plugin_instance, max_history_entries: int = 100):
        """
        初始化历史记录管理器
        :param plugin_instance: OpenWrtBackup插件实例
        :param max_history_entries: 最大历史记录数量
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.max_history_entries = max_history_entries
    
    def load_backup_history(self) -> List[Dict[str, Any]]:
        """加载备份历史记录"""
        history = self.plugin.get_data('backup_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history
    
    def save_backup_history_entry(self, entry: Dict[str, Any]):
        """保存单条备份历史记录"""
        history = self.load_backup_history()
        history.insert(0, entry)
        if len(history) > self.max_history_entries:
            history = history[:self.max_history_entries]
        
        self.plugin.save_data('backup_history', history)
        logger.info(f"{self.plugin_name} 已保存备份历史，当前共 {len(history)} 条记录。")

