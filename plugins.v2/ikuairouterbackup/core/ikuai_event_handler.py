"""
爱快事件处理模块
完全独立的爱快插件事件处理，不与其他插件共享任何逻辑
"""
from app.log import logger
from app.core.event import eventmanager, Event
from app.schemas.types import EventType
from app.schemas import NotificationType
import time


class IkuaiEventHandler:
    """爱快事件处理器类 - 完全独立，专属于爱快插件"""
    
    def __init__(self, ikuai_plugin_instance):
        """
        初始化爱快事件处理器
        :param ikuai_plugin_instance: IkuaiRouterBackup插件实例
        """
        self.ikuai_plugin = ikuai_plugin_instance
        self.ikuai_plugin_name = ikuai_plugin_instance.plugin_name
        # 用于防止重复处理同一个事件
        self._ikuai_processed_events = set()
        self._ikuai_event_cache_ttl = 5  # 5秒内的重复事件将被忽略
    
    def _ikuai_is_our_command(self, event_data: dict) -> bool:
        """
        严格检查事件是否属于爱快插件的命令
        """
        # 爱快插件独有的action列表（这些action只属于爱快插件）
        ikuai_only_actions = ["ikuai_help", "ikuai_status", "ikuai_line", "ikuai_list", "ikuai_history", "ikuai_backup"]
        
        # 获取action
        action = event_data.get("action", "")
        if not action:
            data = event_data.get("data", {})
            if isinstance(data, dict):
                action = data.get("action", "")
        
        # 第一步：如果action是爱快独有的，直接确认是我们的命令
        if action in ikuai_only_actions:
            logger.debug(f"{self.ikuai_plugin_name} 通过爱快独有action确认是我们的命令: action={action}")
            return True
        
        # 第二步：优先检查 category（最可靠的标识）
        category = event_data.get("category", "")
        if category:
            if category == "爱快路由":
                logger.debug(f"{self.ikuai_plugin_name} 通过category确认是我们的命令: category={category}")
                return True
            else:
                logger.debug(f"{self.ikuai_plugin_name} category不匹配（必须是'爱快路由'）: category={category}")
                return False
        else:
            # 第三步：如果没有category，必须通过cmd检查
            cmd = event_data.get("cmd", "") or event_data.get("command", "") or ""
            if isinstance(cmd, str):
                cmd = cmd.strip()
            else:
                cmd = str(cmd).strip() if cmd else ""
            
            if not cmd:
                data = event_data.get("data", {})
                if isinstance(data, dict):
                    cmd = data.get("cmd", "") or data.get("command", "") or ""
                    if isinstance(cmd, str):
                        cmd = cmd.strip()
            
            if not cmd:
                # 如果没有cmd且action不是爱快独有的，直接拒绝
                logger.debug(f"{self.ikuai_plugin_name} 没有category且cmd为空，且action不是爱快独有的，拒绝处理: action={action}")
                return False
            
            if not cmd.startswith("/爱快"):
                logger.debug(f"{self.ikuai_plugin_name} cmd不匹配（必须以'/爱快'开头）: cmd={cmd}")
                return False
        
        logger.debug(f"{self.ikuai_plugin_name} 通过cmd确认是我们的命令: cmd={cmd}")
        return True
    
    def _ikuai_is_duplicate_event(self, event: Event) -> bool:
        """
        检查事件是否已被处理过（防止重复处理）
        """
        current_time = time.time()
        
        # 定期清理过期的事件缓存
        if hasattr(self, '_ikuai_event_cache_time'):
            if current_time - self._ikuai_event_cache_time > self._ikuai_event_cache_ttl:
                self._ikuai_processed_events.clear()
                self._ikuai_event_cache_time = current_time
        if not hasattr(self, '_ikuai_event_cache_time'):
            self._ikuai_event_cache_time = current_time
        
        # 尝试从事件中提取唯一标识
        event_data = None
        if hasattr(event, 'event_data'):
            event_data = event.event_data
        elif hasattr(event, 'data'):
            event_data = event.data
        elif isinstance(event, dict):
            event_data = event
        
        event_key = None
        if event_data:
            cmd = event_data.get("cmd", "") or event_data.get("command", "") or ""
            userid = event_data.get("user") or event_data.get("userid") or event_data.get("user_id") or ""
            action = event_data.get("action", "") or (event_data.get("data", {}) or {}).get("action", "")
            event_key = f"ikuai_{cmd}|{userid}|{action}|{int(current_time)}"
        else:
            if hasattr(event, 'event_id'):
                event_key = f"ikuai_event_{event.event_id}"
            elif hasattr(event, 'id'):
                event_key = f"ikuai_event_{event.id}"
            else:
                event_key = f"ikuai_unknown_{hash(str(event))}"
        
        if event_key in self._ikuai_processed_events:
            return True
        
        self._ikuai_processed_events.add(event_key)
        logger.debug(f"{self.ikuai_plugin_name} 记录新爱快事件: key={event_key}")
        return False
    
    def handle_ikuai_command(self, event: Event):
        """
        处理爱快插件命令事件
        
        :param event: 事件对象
        """
        if not event:
            return
        
        # 检查是否是重复事件
        if self._ikuai_is_duplicate_event(event):
            return
        
        # 提取事件数据
        event_data = None
        if hasattr(event, 'event_data'):
            event_data = event.event_data
        elif hasattr(event, 'data'):
            event_data = event.data
        elif isinstance(event, dict):
            event_data = event
        
        if not event_data:
            logger.debug(f"{self.ikuai_plugin_name} 爱快事件数据为空，事件类型: {type(event)}")
            return
        
        # 尝试从事件对象本身获取cmd和category（如果event_data中没有）
        event_cmd = None
        event_category = None
        if hasattr(event, 'cmd'):
            event_cmd = event.cmd
        if hasattr(event, 'category'):
            event_category = event.category
        if hasattr(event, 'command'):
            event_cmd = event.command
        if hasattr(event, 'command_info'):
            cmd_info = event.command_info
            if isinstance(cmd_info, dict):
                event_cmd = cmd_info.get('cmd') or event_cmd
                event_category = cmd_info.get('category') or event_category
        
        if hasattr(event, '__dict__'):
            event_dict = event.__dict__
            if 'cmd' in event_dict and not event_cmd:
                event_cmd = event_dict['cmd']
            if 'category' in event_dict and not event_category:
                event_category = event_dict['category']
            if 'command_info' in event_dict and not event_cmd:
                cmd_info = event_dict['command_info']
                if isinstance(cmd_info, dict):
                    event_cmd = cmd_info.get('cmd') or event_cmd
                    event_category = cmd_info.get('category') or event_category
        
        # 将事件对象中的cmd和category添加到event_data中（如果不存在）
        if event_cmd and 'cmd' not in event_data:
            event_data['cmd'] = event_cmd
        if event_category and 'category' not in event_data:
            event_data['category'] = event_category
        
        # 爱快插件独有的action列表（这些action只属于爱快插件）
        ikuai_only_actions = ["ikuai_help", "ikuai_status", "ikuai_line", "ikuai_list", "ikuai_history", "ikuai_backup"]
        
        # 获取action用于判断
        action = event_data.get("action", "")
        if not action:
            data = event_data.get("data", {})
            if isinstance(data, dict):
                action = data.get("action", "")
        
        # 如果action是爱快独有的，直接确认是我们的命令（无需检查category和cmd）
        if action in ikuai_only_actions:
            logger.debug(f"{self.ikuai_plugin_name} 通过爱快独有action确认是我们的命令: action={action}")
        else:
            # 不是爱快独有的action，通过 _ikuai_is_our_command 进一步检查（兼容旧数据）
            if not self._ikuai_is_our_command(event_data):
                return
        
        if not action:
            logger.debug(f"{self.ikuai_plugin_name} 爱快事件中没有action字段")
            return
        
        logger.info(f"{self.ikuai_plugin_name} 处理爱快命令事件: action={action}, event_data keys={list(event_data.keys())}")
        
        try:
            # 使用爱快消息处理器处理命令
            if not self.ikuai_plugin._ikuai_message_handler:
                error_msg = "❌ 爱快插件消息处理器未初始化，请重新加载插件"
                logger.error(f"{self.ikuai_plugin_name} {error_msg}")
                try:
                    # 只使用 mtype=NotificationType.Plugin，不传 userid 和 channel 以确保只出现在"插件推送"分类
                    self.ikuai_plugin.post_message(
                        mtype=NotificationType.Plugin,
                        title=error_msg
                    )
                except Exception as e:
                    logger.error(f"{self.ikuai_plugin_name} 发送错误消息失败: {e}")
                return
            
            result = None
            if action == "ikuai_help":
                logger.info(f"{self.ikuai_plugin_name} 执行爱快帮助命令")
                result = self.ikuai_plugin._ikuai_message_handler._ikuai_get_help_message()
            elif action == "ikuai_status":
                logger.info(f"{self.ikuai_plugin_name} 执行爱快状态命令")
                result = self.ikuai_plugin._ikuai_message_handler._ikuai_get_system_status()
            elif action == "ikuai_line":
                logger.info(f"{self.ikuai_plugin_name} 执行爱快线路命令")
                result = self.ikuai_plugin._ikuai_message_handler._ikuai_get_line_status()
            elif action == "ikuai_list":
                logger.info(f"{self.ikuai_plugin_name} 执行爱快列表命令")
                result = self.ikuai_plugin._ikuai_message_handler._ikuai_get_backup_list()
            elif action == "ikuai_history":
                logger.info(f"{self.ikuai_plugin_name} 执行爱快历史命令")
                result = self.ikuai_plugin._ikuai_message_handler._ikuai_get_backup_history()
            elif action == "ikuai_backup":
                logger.info(f"{self.ikuai_plugin_name} 执行爱快备份命令")
                result = self.ikuai_plugin._ikuai_message_handler._ikuai_trigger_backup()
            else:
                # 理论上不应该到达这里，因为action已经在前面验证过了
                logger.warning(f"{self.ikuai_plugin_name} 未处理的爱快action: {action}")
                cmd = event_data.get("cmd", "")
                result = {
                    "title": f"❓ {self.ikuai_plugin_name}",
                    "text": f"未知命令: {cmd}\n\n发送 '/爱快帮助' 查看可用命令。"
                }
            
            # 发送回复消息
            if result:
                title = result.get("title", f"{self.ikuai_plugin_name}")
                text_content = result.get("text", "")
                userid = event_data.get("user")
                
                logger.info(f"{self.ikuai_plugin_name} 准备发送爱快回复消息: action={action}, title={title}, userid={userid}, text长度={len(text_content) if text_content else 0}")
                
                # 发送消息 - 只使用 mtype=NotificationType.Plugin，不传 userid 和 channel
                # 注意：传递 userid 会导致消息分发到所有通知渠道，所以交互式回复也不传 userid
                # 这样所有消息都只出现在"插件推送"分类中
                try:
                    # 统一不传递 userid 和 channel，只传递 mtype=NotificationType.Plugin
                    # 消息会出现在"插件推送"分类，用户可以在该分类中查看所有交互回复
                    self.ikuai_plugin.post_message(
                        mtype=NotificationType.Plugin,
                        title=title,
                        text=text_content
                    )
                    if userid:
                        logger.info(f"{self.ikuai_plugin_name} ✅ 成功发送爱快回复消息（用户 {userid}，仅在插件推送分类）: {title}")
                    else:
                        logger.info(f"{self.ikuai_plugin_name} ✅ 成功发送爱快回复消息（无userid）: {title}")
                except Exception as msg_e:
                    logger.error(f"{self.ikuai_plugin_name} ❌ 发送爱快回复消息失败: {msg_e}", exc_info=True)
            else:
                logger.warning(f"{self.ikuai_plugin_name} ⚠️ 爱快命令处理返回空结果: action={action}")
                
        except Exception as e:
            logger.error(f"{self.ikuai_plugin_name} 处理爱快命令事件失败: {str(e)}", exc_info=True)
            error_msg = f"❌ 执行爱快命令时发生错误: {str(e)}"
            try:
                # 只使用 mtype=NotificationType.Plugin，不传 userid 和 channel 以确保只出现在"插件推送"分类
                self.ikuai_plugin.post_message(
                    mtype=NotificationType.Plugin,
                    title=error_msg
                )
            except Exception as msg_e:
                logger.error(f"{self.ikuai_plugin_name} 发送错误消息失败: {msg_e}")

