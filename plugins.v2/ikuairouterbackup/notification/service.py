"""通知模块"""
from typing import Optional
from datetime import datetime
from app.log import logger
from app.schemas import NotificationType


class NotificationManager:
    """通知管理器类"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def send_backup_notification(self, success: bool, message: str = "", filename: Optional[str] = None, 
                                  notification_style: int = 0, notify: bool = True):
        """发送备份通知"""
        if not notify:
            return
        
        title = f"🛠️ {self.plugin_name} "
        title += "成功" if success else "失败"
        status_emoji = "✅" if success else "❌"
        
        # 默认样式
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
        status_prefix = "📣"
        router_prefix = "🔗"
        file_prefix = "📄"
        info_prefix = "📋"
        congrats = "\n✨ 备份已成功完成！"
        error_msg = "\n❗ 备份失败，请检查配置和连接！"
        
        # 失败时的特殊处理 - 添加额外的警告指示
        if not success:
            divider_failure = "❌" + divider[1:-1] + "❌"
            text_content = f"{divider_failure}\n"
        else:
            text_content = f"{divider}\n"
            
        text_content += f"{status_prefix} 状态：{status_emoji} {'备份成功' if success else '备份失败'}\n\n"
        text_content += f"{router_prefix} 路由：{self.plugin._original_ikuai_url}\n"
        if filename:
            text_content += f"{file_prefix} 文件：{filename}\n"
        if message:
            text_content += f"{info_prefix} 详情：{message.strip()}\n"
        
        # 添加底部分隔线和时间戳
        if not success:
            text_content += f"\n{divider_failure}\n"
        else:
            text_content += f"\n{divider}\n"
            
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 根据成功/失败添加不同信息
        if success:
            text_content += congrats
        else:
            text_content += error_msg
        
        try:
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}")
    
    def send_restore_notification(self, success: bool, message: str = "", filename: str = "",
                                   notification_style: int = 0, notify: bool = True):
        """发送恢复通知"""
        if not notify:
            return
        
        title = f"🛠️ {self.plugin_name} "
        title += "恢复" + ("成功" if success else "失败")
        status_emoji = "✅" if success else "❌"
        
        # 默认样式
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
        status_prefix = "📣"
        router_prefix = "🔗"
        file_prefix = "📄"
        info_prefix = "📋"
        congrats = "\n✨ 恢复已成功完成！"
        error_msg = "\n❗ 恢复失败，请检查配置和连接！"
        
        # 失败时的特殊处理 - 添加额外的警告指示
        if not success:
            divider_failure = "❌" + divider[1:-1] + "❌"
            text_content = f"{divider_failure}\n"
        else:
            text_content = f"{divider}\n"
            
        text_content += f"{status_prefix} 状态：{status_emoji} {'恢复成功' if success else '恢复失败'}\n\n"
        text_content += f"{router_prefix} 路由：{self.plugin._original_ikuai_url}\n"
        if filename:
            text_content += f"{file_prefix} 文件：{filename}\n"
        if message:
            text_content += f"{info_prefix} 详情：{message.strip()}\n"
        
        # 添加底部分隔线和时间戳
        if not success:
            text_content += f"\n{divider_failure}\n"
        else:
            text_content += f"\n{divider}\n"
            
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 根据成功/失败添加不同信息
        if success:
            text_content += congrats
        else:
            text_content += error_msg
        
        try:
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送恢复通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送恢复通知失败: {e}")
    
    def send_clear_history_notification(self, success: bool, message: str, 
                                         notification_style: int = 0, notify: bool = True):
        """发送清理历史记录通知"""
        if not notify:
            return
        
        title = f"🛠️ {self.plugin_name} 清理历史记录"
        status_emoji = "✅" if success else "❌"
        
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
        text_content = f"{divider}\n"
        text_content += f"📣 状态：{status_emoji} {'清理成功' if success else '清理失败'}\n\n"
        if message:
            text_content += f"📋 详情：{message.strip()}\n"
        text_content += f"\n{divider}\n"
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送清理历史记录通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送清理历史记录通知失败: {e}")

