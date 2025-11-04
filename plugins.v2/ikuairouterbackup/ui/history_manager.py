"""历史记录管理模块"""
from typing import Any, List, Dict
from app.log import logger


class HistoryManager:
    """历史记录管理器类"""
    
    def __init__(self, plugin_instance, max_backup_entries: int = 100, max_restore_entries: int = 50):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.max_backup_entries = max_backup_entries
        self.max_restore_entries = max_restore_entries
    
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
        if len(history) > self.max_backup_entries:
            history = history[:self.max_backup_entries]
        
        self.plugin.save_data('backup_history', history)
        logger.info(f"{self.plugin_name} 已保存备份历史，当前共 {len(history)} 条记录。")
    
    def load_restore_history(self) -> List[Dict[str, Any]]:
        """加载恢复历史记录"""
        history = self.plugin.get_data('restore_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 恢复历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history
    
    def save_restore_history_entry(self, entry: Dict[str, Any]):
        """保存单条恢复历史记录"""
        try:
            # 加载现有历史记录
            history = self.load_restore_history()
            
            # 添加新记录到开头
            history.insert(0, entry)
            
            # 如果超过最大记录数，删除旧记录
            if len(history) > self.max_restore_entries:
                history = history[:self.max_restore_entries]
            
            # 保存更新后的历史记录
            self.plugin.save_data('restore_history', history)
            logger.debug(f"{self.plugin_name} 已保存恢复历史记录")
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存恢复历史记录失败: {str(e)}")
    
    def clear_backup_history(self):
        """清理备份历史记录"""
        try:
            self.plugin.save_data('backup_history', [])
            logger.info(f"{self.plugin_name} 已清理所有备份历史记录")
        except Exception as e:
            error_msg = f"清理备份历史记录失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")

