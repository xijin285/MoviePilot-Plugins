"""
通知服务模块
负责发送插件通知消息
"""
from datetime import datetime
from typing import Optional
from app.log import logger
from app.schemas import NotificationType


class NotificationService:
    """通知服务类"""
    
    def __init__(self, plugin_instance):
        """
        初始化通知服务
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def send_notification(self, success: bool, message: str = "", filename: Optional[str] = None, 
                         notify: bool = True):
        """发送通知"""
        if not notify:
            return
        
        title = f"🛠️ {self.plugin_name} "
        title += "成功" if success else "失败"
        status_emoji = "✅" if success else "❌"
        
        # 通知样式 - 缩短分割线适配手机显示
        divider = "━━━━━━━━━━━━━"
        status_prefix = "📌"
        router_prefix = "🌐"
        file_prefix = "📁"
        info_prefix = "ℹ️"
        congrats = "\n🎉 备份任务已顺利完成！"
        error_msg = "\n⚠️ 备份失败，请检查日志了解详情。"
        
        # 构建通知内容
        text_content = f"{divider}\n"
        
        text_content += f"{status_prefix} 状态：{status_emoji} {'备份成功' if success else '备份失败'}\n"
        text_content += f"{router_prefix} 路由：{self.plugin._openwrt_host}\n"
        if filename:
            text_content += f"{file_prefix} 文件：{filename}\n"
        if message and message.strip() != "备份成功" and message.strip() != "备份失败":
            text_content += f"{info_prefix} 详情：{message.strip()}\n"
        
        # 添加底部分隔线和时间戳
        text_content += f"{divider}\n"
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 根据成功/失败添加不同信息
        if success:
            text_content += congrats
        else:
            text_content += error_msg
        
        try:
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.debug(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}")

