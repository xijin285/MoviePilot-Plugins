"""
事件处理模块
负责处理插件事件（如微信命令等）
"""
from app.log import logger


class EventHandler:
    """事件处理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化事件处理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def handle_pve_command(self, event):
        """
        处理PVE相关命令（通过事件系统）
        """
        if not event:
            return
        
        event_data = event.event_data
        if not event_data:
            return
        
        action = event_data.get("action")
        if action not in ["pve_status", "container_status", "help"]:
            return
        
        try:
            # 检查SSH配置
            if not self.plugin._pve_host:
                error_msg = "❌ PVE主机未配置，请在插件配置中设置SSH连接信息"
                logger.warning(f"{self.plugin_name} {error_msg}")
                self.plugin.post_message(
                    channel=event_data.get("channel"),
                    title=error_msg,
                    userid=event_data.get("user")
                )
                return
            
            # 使用消息处理器处理命令
            if not self.plugin._message_handler:
                error_msg = "❌ 插件消息处理器未初始化，请重新加载插件"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin.post_message(
                    channel=event_data.get("channel"),
                    title=error_msg,
                    userid=event_data.get("user")
                )
                return
            
            # 根据action获取消息内容
            result = None
            if action == "pve_status":
                result = self.plugin._message_handler.format_pve_status_message()
            elif action == "container_status":
                result = self.plugin._message_handler.format_container_status_message()
            elif action == "help":
                result = self.plugin._message_handler.format_help_message()
            
            if result:
                self.plugin.post_message(
                    channel=event_data.get("channel"),
                    title=f"{self.plugin_name}",
                    text=result,
                    userid=event_data.get("user")
                )
            else:
                logger.warning(f"{self.plugin_name} 命令处理返回空结果: action={action}")
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 处理命令事件失败: {str(e)}", exc_info=True)
            error_msg = f"❌ 执行命令时发生错误: {str(e)}"
            self.plugin.post_message(
                channel=event_data.get("channel") if event_data else None,
                title=error_msg,
                userid=event_data.get("user") if event_data else None
            )

