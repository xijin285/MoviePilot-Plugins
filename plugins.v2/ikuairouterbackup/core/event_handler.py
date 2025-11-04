"""
事件处理模块
负责处理插件事件（如消息渠道命令等）
"""
from app.log import logger
from app.core.event import eventmanager, Event
from app.schemas.types import EventType
from app.schemas import NotificationType
import time


class EventHandler:
    """事件处理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化事件处理器

        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        # 用于防止重复处理同一个事件
        self._processed_events = set()
        self._event_cache_ttl = 5  # 5秒内的重复事件将被忽略
    
    def _is_our_command(self, event_data: dict) -> bool:
        """
        严格检查事件是否属于我们的插件命令

        """
        # 严格检查1：命令字符串必须以"/爱快"开头
        cmd = event_data.get("cmd", "").strip()
        if not cmd.startswith("/爱快"):
            logger.debug(f"{self.plugin_name} 命令不匹配（必须以'/爱快'开头）: cmd={cmd}")
            return False
        
        # 严格检查2：category必须是"爱快路由"
        category = event_data.get("category", "")
        if category and category != "爱快路由":
            logger.debug(f"{self.plugin_name} 类别不匹配（必须是'爱快路由'）: category={category}")
            return False
        
        # 严格检查3：action必须是我们的有效动作之一
        data = event_data.get("data", {})
        if isinstance(data, dict):
            action = data.get("action", "")
            if action:
                valid_actions = ["help", "status", "line", "list", "history", "backup"]
                if action not in valid_actions:
                    logger.debug(f"{self.plugin_name} action不匹配（无效的action）: action={action}")
                    return False
        
        # 所有检查通过
        logger.debug(f"{self.plugin_name} 确认是我们的命令: cmd={cmd}, category={category}")
        return True
    
    def _is_duplicate_event(self, event: Event) -> bool:
        """        
        使用事件的关键信息生成唯一标识，防止重复处理
        """
        current_time = time.time()
        
        # 清理过期的缓存（超过TTL的缓存项）
        if hasattr(self, '_event_cache_time'):
            if current_time - self._event_cache_time > self._event_cache_ttl:
                self._processed_events.clear()
                self._event_cache_time = current_time
        
        if not hasattr(self, '_event_cache_time'):
            self._event_cache_time = current_time
        
        # 生成事件的唯一标识
        event_id = None
        
        # 优先使用事件对象的内置ID
        if hasattr(event, 'event_id'):
            event_id = event.event_id
        elif hasattr(event, 'id'):
            event_id = event.id
        
        # 如果没有内置ID，从事件数据中提取关键信息生成唯一标识
        if not event_id:
            try:
                event_data = None
                if hasattr(event, 'event_data'):
                    event_data = event.event_data
                elif hasattr(event, 'data'):
                    event_data = event.data
                elif isinstance(event, dict):
                    event_data = event
                
                if event_data:
                    # 使用命令、用户ID、时间戳等信息生成唯一标识
                    cmd = event_data.get("cmd", "")
                    userid = event_data.get("user") or event_data.get("userid") or event_data.get("user_id") or ""
                    action = event_data.get("action", "")
                    # 生成唯一标识（结合命令、用户和动作）
                    # 使用更细粒度的时间戳（毫秒级）来避免冲突
                    event_key = f"{cmd}|{userid}|{action}|{current_time:.6f}"
                    event_id = hash(event_key)
                    logger.debug(f"{self.plugin_name} 生成事件ID: key={event_key}, id={event_id}")
                else:
                    # 如果无法获取事件数据，使用事件字符串的哈希
                    event_id = hash(str(event))
            except Exception as e:
                logger.debug(f"{self.plugin_name} 生成事件ID时出错: {e}")
                event_id = hash(str(event))
        
        # 检查是否已处理过
        if event_id in self._processed_events:
            logger.debug(f"{self.plugin_name} 检测到重复事件，忽略: event_id={event_id}")
            return True
        
        # 记录已处理的事件
        self._processed_events.add(event_id)
        logger.debug(f"{self.plugin_name} 记录新事件: event_id={event_id}")
        return False
    
    def handle_ikuai_command(self, event: Event):
        """
        处理爱快相关命令（通过事件系统）
        """
        if not event:
            logger.debug(f"{self.plugin_name} 事件为空")
            return
        
        # 检查是否是重复事件
        if self._is_duplicate_event(event):
            logger.info(f"{self.plugin_name} 检测到重复事件，跳过处理")
            return
        
        # 尝试多种方式获取事件数据
        event_data = None
        if hasattr(event, 'event_data'):
            event_data = event.event_data
        elif hasattr(event, 'data'):
            event_data = event.data
        elif isinstance(event, dict):
            event_data = event
        
        if not event_data:
            logger.debug(f"{self.plugin_name} 事件数据为空，事件类型: {type(event)}, 事件内容: {event}")
            return
        
        action = event_data.get("action") or (event_data.get("data", {}) or {}).get("action")
        if not action:
            logger.debug(f"{self.plugin_name} 事件中没有action字段")
            return
        
        if action not in ["help", "status", "line", "list", "history", "backup"]:
            logger.debug(f"{self.plugin_name} 未知的action: {action}")
            return
        
        logger.info(f"{self.plugin_name} 处理命令事件: action={action}, event_data keys={list(event_data.keys())}")
        
        try:
            # 注意：cmd字段可能在事件数据中不存在，因为我们已经在主函数中通过action验证过了
            # 所以这里不需要再次检查cmd，直接处理即可
            cmd = event_data.get("cmd", "").strip()
            if cmd and not cmd.startswith("/爱快"):
                # 只有当cmd存在且不是爱快命令时才警告
                logger.warning(f"{self.plugin_name} 事件处理中发现非爱快命令，这不应该发生: cmd={cmd}, action={action}")
                return
            
            # 使用消息处理器处理命令
            if not self.plugin._message_handler:
                error_msg = "❌ 插件消息处理器未初始化，请重新加载插件"
                logger.error(f"{self.plugin_name} {error_msg}")
                try:
                    self.plugin.post_message(
                        channel=event_data.get("channel"),
                        title=error_msg,
                        userid=event_data.get("user")
                    )
                except Exception as e:
                    logger.error(f"{self.plugin_name} 发送错误消息失败: {e}")
                return
            
            result = None
            if action == "help":
                logger.info(f"{self.plugin_name} 执行帮助命令")
                result = self.plugin._message_handler._get_help_message()
            elif action == "status":
                logger.info(f"{self.plugin_name} 执行状态命令")
                result = self.plugin._message_handler._get_system_status()
            elif action == "line":
                logger.info(f"{self.plugin_name} 执行线路命令")
                result = self.plugin._message_handler._get_line_status()
            elif action == "list":
                logger.info(f"{self.plugin_name} 执行列表命令")
                result = self.plugin._message_handler._get_backup_list()
            elif action == "history":
                logger.info(f"{self.plugin_name} 执行历史命令")
                result = self.plugin._message_handler._get_backup_history()
            elif action == "backup":
                logger.info(f"{self.plugin_name} 执行备份命令")
                result = self.plugin._message_handler._trigger_backup()
            else:
                logger.warning(f"{self.plugin_name} 未知的action: {action}")
                result = {
                    "title": f"❓ {self.plugin_name}",
                    "text": f"未知命令: {cmd}\n\n发送 '/爱快帮助' 查看可用命令。"
                }
            
            # 发送回复消息
            if result:
                # result是字典格式 {title, text}
                title = result.get("title", f"{self.plugin_name}")
                text_content = result.get("text", "")
                
                # 关键修复：对于帮助消息，确保title中明确包含插件名称，避免与其他插件混淆
                if action == "help":
                    # 确保title中明确标识是爱快插件
                    if self.plugin_name not in title:
                        title = f"{self.plugin_name} - {title}"
                
                channel = event_data.get("channel")
                userid = event_data.get("user")
                
                logger.info(f"{self.plugin_name} 准备发送回复消息: action={action}, title={title}, userid={userid}, text长度={len(text_content) if text_content else 0}")

                # 发送消息
                try:
                    if userid:
                        # 有userid时，回复给用户
                        self.plugin.post_message(
                            channel=channel,
                            title=title,
                            text=text_content,
                            userid=userid
                        )
                        logger.info(f"{self.plugin_name} ✅ 成功发送回复消息给用户 {userid}: {title}")
                    else:
                        # 没有userid时，作为普通通知发送（群聊）
                        self.plugin.post_message(
                            title=title,
                            text=text_content
                        )
                        logger.info(f"{self.plugin_name} ✅ 成功发送回复消息（无userid）: {title}")
                except Exception as msg_e:
                    logger.error(f"{self.plugin_name} ❌ 发送回复消息失败: {msg_e}", exc_info=True)
            else:
                logger.warning(f"{self.plugin_name} ⚠️ 命令处理返回空结果: action={action}, cmd={cmd}")
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 处理命令事件失败: {str(e)}", exc_info=True)
            error_msg = f"❌ 执行命令时发生错误: {str(e)}"
            try:
                event_data = None
                if event:
                    event_data = event.event_data if hasattr(event, 'event_data') else event.data
                if event_data:
                    self.plugin.post_message(
                        channel=event_data.get("channel"),
                        title=error_msg,
                        userid=event_data.get("user")
                    )
            except Exception as msg_e:
                logger.error(f"{self.plugin_name} 发送错误消息失败: {msg_e}")

