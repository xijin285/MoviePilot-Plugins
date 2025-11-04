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
                                 is_clear_history: bool = False, backup_details: Optional[Dict[str, Any]] = None,
                                 notify: bool = True):
        """
        发送备份通知
        
        :param success: 是否成功
        :param message: 消息内容
        :param filename: 文件名
        :param is_clear_history: 是否为清理历史记录操作
        :param backup_details: 备份详情
        :param notify: 是否发送通知
        """
        if not notify or not self.plugin._notify:
            return
        
        try:
            title = f"🛠️ {self.plugin_name} "
            if is_clear_history:
                title += "清理历史记录"
            else:
                title += "成功" if success else "失败"
            
            status_emoji = "✅" if success else "❌"
            
            # 默认样式
            divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
            status_prefix = "📣"
            host_prefix = "🔗"
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
            
            if is_clear_history:
                text_content += f"{status_prefix} 状态：{status_emoji} {'清理成功' if success else '清理失败'}\n\n"
                if message:
                    text_content += f"{info_prefix} 详情：{message.strip()}\n"
            else:
                text_content += f"{status_prefix} 状态：{status_emoji} {'备份成功' if success else '备份失败'}\n\n"
                text_content += f"{host_prefix} 主机：{self.plugin._pve_host or '-'}\n"
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
                if not is_clear_history:
                    text_content += congrats
            else:
                text_content += error_msg
            
            # 强制使用插件推送渠道
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}")
    
    def send_restore_notification(self, success: bool, message: str = "", filename: str = "", 
                                  target_vmid: Optional[str] = None, is_clear_history: bool = False,
                                  notify: bool = True):
        """
        发送恢复通知
        
        :param success: 是否成功
        :param message: 消息内容
        :param filename: 文件名
        :param target_vmid: 目标VMID
        :param is_clear_history: 是否为清理历史记录操作
        :param notify: 是否发送通知
        """
        if not notify or not self.plugin._notify:
            return
        
        title = f"🛠️ {self.plugin_name} "
        if is_clear_history:
            title += "清理恢复历史记录"
        else:
            title += "恢复" + ("成功" if success else "失败")
        
        status_emoji = "✅" if success else "❌"
        
        # 默认样式
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
        status_prefix = "📣"
        host_prefix = "🔗"
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
        text_content += f"{host_prefix} 主机：{self.plugin._pve_host or '-'}\n"
        if filename:
            text_content += f"{file_prefix} 文件：{filename}\n"
        if target_vmid:
            text_content += f"🎯 目标VMID：{target_vmid}\n"
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
            # 强制使用插件推送渠道
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送恢复通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送恢复通知失败: {e}")
    
    def send_clear_history_notification(self, success: bool, message: str, 
                                         notify: bool = True):
        """
        发送清理历史记录通知
        
        :param success: 是否成功
        :param message: 消息内容
        :param notify: 是否发送通知
        """
        if not notify or not self.plugin._notify:
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
            # 强制使用插件推送渠道
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送清理历史记录通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送清理历史记录通知失败: {e}")

