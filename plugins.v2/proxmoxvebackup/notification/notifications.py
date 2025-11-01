"""
通知管理模块
负责处理备份和恢复操作的通知发送
"""
from datetime import datetime
from typing import Optional, Dict, Any
from app.schemas import NotificationType
from app.log import logger


class NotificationHandler:
    """通知处理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化通知处理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def send_backup_notification(self, success: bool, message: str = "", filename: Optional[str] = None, 
                                 is_clear_history: bool = False, backup_details: Optional[Dict[str, Any]] = None):
        """
        发送备份通知（分隔线+emoji+结构化字段+结尾祝贺语，区分单/多容器）
        
        :param success: 是否成功
        :param message: 消息内容
        :param filename: 文件名
        :param is_clear_history: 是否为清理历史记录操作
        :param backup_details: 备份详情
        """
        if not self.plugin._notify:
            return
        
        try:
            # 判断单容器还是多容器
            file_list = []
            if backup_details and "downloaded_files" in backup_details and backup_details["downloaded_files"]:
                file_list = [f["filename"] for f in backup_details["downloaded_files"]]
            is_multi = len(file_list) > 1
            
            # 标题
            status_emoji = "✅" if success else "❌"
            title_emoji = "🛠️"
            
            # 根据操作类型设置不同的标题
            if is_clear_history:
                title = f"{title_emoji} {self.plugin_name} 清理历史记录{'成功' if success else '失败'}"
            elif is_multi:
                title = f"{title_emoji} {self.plugin_name} 多容器备份{'成功' if success else '失败'}"
            else:
                title = f"{title_emoji} {self.plugin_name} 备份{'成功' if success else '失败'}"
            
            divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            # 根据操作类型构建不同的通知内容
            if is_clear_history:
                # 清理历史记录专用格式
                status_str = f"{status_emoji} 清理历史记录{'成功' if success else '失败'}"
                host_str = self.plugin._pve_host or "-"
                detail_str = message.strip() if message else ("历史记录清理完成" if success else "历史记录清理失败")
                end_str = "✨ 历史记录清理完成！" if success else "❗ 历史记录清理失败，请检查日志！"
                
                text_content = (
                    f"{divider}\n"
                    f"📣 状态：{status_str}\n"
                    f"🔗 主机：{host_str}\n"
                    f"📋 详情：{detail_str}\n"
                    f"{divider}\n"
                    f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"{end_str}"
                )
            else:
                # 备份操作格式
                status_str = f"{status_emoji} 备份{'成功' if success else '失败'}"
                host_str = self.plugin._pve_host or "-"
                if is_multi:
                    file_str = "\n".join(file_list)
                elif file_list:
                    file_str = file_list[0]
                else:
                    file_str = "-"
                path_str = "-"
                if backup_details and "downloaded_files" in backup_details and backup_details["downloaded_files"]:
                    details = backup_details["downloaded_files"][0]["details"]
                    if details["local_backup"]["enabled"] and details["local_backup"]["success"]:
                        path_str = details["local_backup"]["path"]
                # 详情
                if is_multi:
                    detail_str = f"共备份 {len(file_list)} 个容器。" + (message.strip() if message else ("备份已成功完成" if success else "备份失败，请检查日志"))
                else:
                    detail_str = message.strip() if message else ("备份已成功完成" if success else "备份失败，请检查日志")
                # 结尾祝贺语
                end_str = "✨ 备份已成功完成！" if success else "❗ 备份失败，请检查日志！"
                
                text_content = (
                    f"{divider}\n"
                    f"📣 状态：{status_str}\n"
                    f"🔗 主机：{host_str}\n"
                    f"📦 备份文件：{file_str}\n"
                    f"📁 路径：{path_str}\n"
                    f"📋 详情：{detail_str}\n"
                    f"{divider}\n"
                    f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"{end_str}"
                )
            
            mtype = getattr(NotificationType, self.plugin._notification_message_type, NotificationType.Plugin)
            self.plugin.post_message(
                title=title,
                text=text_content,
                mtype=mtype
            )
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {str(e)}")
    
    def send_restore_notification(self, success: bool, message: str = "", filename: str = "", 
                                  target_vmid: Optional[str] = None, is_clear_history: bool = False):
        """
        发送恢复通知
        
        :param success: 是否成功
        :param message: 消息内容
        :param filename: 文件名
        :param target_vmid: 目标VMID
        :param is_clear_history: 是否为清理历史记录操作
        """
        if not self.plugin._notify:
            return
        
        title = f"🔄 {self.plugin_name} "
        if is_clear_history:
            title += "清理恢复历史记录"
        else:
            title += f"恢复{'成功' if success else '失败'}"
        status_emoji = "✅" if success else "❌"
        
        # 失败时的特殊处理
        if not success:
            divider_failure = "❌━━━━━━━━━━━━━━━━━━━━━━━━━❌"
            text_content = f"{divider_failure}\n"
        else:
            text_content = f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
        text_content += f"📣 状态：{status_emoji} 恢复{'成功' if success else '失败'}\n\n"
        text_content += f"🔗 路由：{self.plugin._pve_host}\n"
        
        if filename:
            text_content += f"📄 备份文件：{filename}\n"
        
        if target_vmid:
            text_content += f"🎯 目标VMID：{target_vmid}\n"
        
        if message:
            text_content += f"📋 详情：{message.strip()}\n"
        
        # 添加底部分隔线和时间戳
        if not success:
            text_content += f"\n{divider_failure}\n"
        else:
            text_content += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 根据成功/失败添加不同信息
        if success:
            text_content += "\n✨ 恢复已成功完成！"
        else:
            text_content += "\n❗ 恢复失败，请检查配置和连接！"
        
        try:
            mtype = getattr(NotificationType, self.plugin._notification_message_type, NotificationType.Plugin)
            self.plugin.post_message(mtype=mtype, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送恢复通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送恢复通知失败: {e}")

