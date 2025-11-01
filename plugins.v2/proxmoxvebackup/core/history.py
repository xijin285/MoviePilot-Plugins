"""
历史记录管理模块
负责备份和恢复历史记录的加载、保存和清理
"""
from typing import List, Dict, Any, Optional
from app.log import logger


class HistoryHandler:
    """历史记录处理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化历史记录处理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.max_backup_history_entries = plugin_instance._max_history_entries
        self.max_restore_history_entries = plugin_instance._max_restore_history_entries
    
    def load_backup_history(self) -> List[Dict[str, Any]]:
        """
        加载备份历史记录
        
        :return: 备份历史记录列表
        """
        history = self.plugin.get_data('backup_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history
    
    def save_backup_history_entry(self, entry: Dict[str, Any]):
        """
        保存单条备份历史记录
        
        :param entry: 备份历史记录条目
        """
        try:
            # 加载现有历史记录
            history = self.load_backup_history()
            
            # 添加新记录到开头
            history.insert(0, entry)
            
            # 如果超过最大记录数，删除旧记录
            if len(history) > self.max_backup_history_entries:
                history = history[:self.max_backup_history_entries]
            
            # 保存更新后的历史记录
            self.plugin.save_data('backup_history', history)
            logger.debug(f"{self.plugin_name} 已保存备份历史记录")
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存备份历史记录失败: {str(e)}")
    
    def load_restore_history(self) -> List[Dict[str, Any]]:
        """
        加载恢复历史记录
        
        :return: 恢复历史记录列表
        """
        history = self.plugin.get_data('restore_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 恢复历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history
    
    def save_restore_history_entry(self, entry: Dict[str, Any]):
        """
        保存单条恢复历史记录
        
        :param entry: 恢复历史记录条目
        """
        try:
            # 加载现有历史记录
            history = self.load_restore_history()
            
            # 添加新记录到开头
            history.insert(0, entry)
            
            # 如果超过最大记录数，删除旧记录
            if len(history) > self.max_restore_history_entries:
                history = history[:self.max_restore_history_entries]
            
            # 保存更新后的历史记录
            self.plugin.save_data('restore_history', history)
            logger.debug(f"{self.plugin_name} 已保存恢复历史记录")
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存恢复历史记录失败: {str(e)}")
    
    def clear_all_history(self):
        """
        清理所有历史记录
        包括备份历史和恢复历史
        """
        try:
            self.plugin.save_data('backup_history', [])
            self.plugin.save_data('restore_history', [])
            logger.info(f"{self.plugin_name} 已清理所有历史记录")
            
            # 发送通知（如果启用）
            if self.plugin._notify and hasattr(self.plugin, '_notification_handler') and self.plugin._notification_handler:
                self.plugin._notification_handler.send_backup_notification(
                    success=True,
                    message="已成功清理所有备份和恢复历史记录",
                    is_clear_history=True,
                    backup_details={}
                )
        except Exception as e:
            error_msg = f"清理历史记录失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            
            # 发送失败通知（如果启用）
            if self.plugin._notify and hasattr(self.plugin, '_notification_handler') and self.plugin._notification_handler:
                self.plugin._notification_handler.send_backup_notification(
                    success=False,
                    message=error_msg,
                    is_clear_history=True,
                    backup_details={}
                )

