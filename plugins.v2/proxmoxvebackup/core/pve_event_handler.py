"""
PVE事件处理模块
完全独立的PVE插件事件处理，不与其他插件共享任何逻辑
"""
from app.log import logger
from app.core.event import eventmanager, Event
from app.schemas.types import EventType
from app.schemas import NotificationType
import time


class PVEEventHandler:
    """PVE事件处理器类 - 完全独立，专属于PVE插件"""
    
    def __init__(self, pve_plugin_instance):
        """
        初始化PVE事件处理器
        :param pve_plugin_instance: ProxmoxVEBackup插件实例
        """
        self.pve_plugin = pve_plugin_instance
        self.pve_plugin_name = pve_plugin_instance.plugin_name
        # 用于防止重复处理同一个事件
        self._pve_processed_events = set()
        self._pve_event_cache_ttl = 5  # 5秒内的重复事件将被忽略
    
    def _pve_is_our_command(self, event_data: dict) -> bool:
        """
        严格检查事件是否属于PVE插件的命令
        完全独立，不依赖任何可能与其他插件共享的逻辑
        """
        # PVE插件独有的action列表（这些action只属于PVE插件）
        pve_only_actions = ["pve_status", "container_status", "pve_help"]
        
        # 获取action
        action = event_data.get("action", "")
        if not action:
            data = event_data.get("data", {})
            if isinstance(data, dict):
                action = data.get("action", "")
        
        # 第一步：如果action是PVE独有的，直接确认是我们的命令
        if action in pve_only_actions:
            logger.debug(f"{self.pve_plugin_name} 通过PVE独有action确认是我们的命令: action={action}")
            return True
        
        # 第二步：优先检查 category（最可靠的标识）
        category = event_data.get("category", "")
        if category:
            if category == "PVE":
                # category明确是PVE，确认是我们的命令
                logger.debug(f"{self.pve_plugin_name} 通过category确认是我们的命令: category={category}")
                return True
            else:
                # category存在但不是PVE，直接拒绝
                logger.debug(f"{self.pve_plugin_name} category不匹配（必须是'PVE'）: category={category}")
                return False
        
        # 第三步：如果没有category，必须通过cmd检查
        cmd = event_data.get("cmd", "") or event_data.get("command", "") or ""
        if isinstance(cmd, str):
            cmd = cmd.strip()
        else:
            cmd = str(cmd).strip() if cmd else ""
        
        # 如果cmd为空，尝试从data中获取
        if not cmd:
            data = event_data.get("data", {})
            if isinstance(data, dict):
                cmd = data.get("cmd", "") or data.get("command", "") or ""
                if isinstance(cmd, str):
                    cmd = cmd.strip()
        
        # 如果没有category，cmd必须存在且以"/pve"开头
        if not cmd:
            # 如果cmd和category都为空，且action不是PVE独有的，直接拒绝
            logger.debug(f"{self.pve_plugin_name} 没有category且cmd为空，且action不是PVE独有的，拒绝处理: action={action}")
            return False
        
        # 检查cmd是否以"/pve"开头
        if not cmd.startswith("/pve"):
            logger.debug(f"{self.pve_plugin_name} cmd不匹配（必须以'/pve'开头）: cmd={cmd}")
            return False
        
        # cmd以"/pve"开头，确认是我们的命令
        logger.debug(f"{self.pve_plugin_name} 通过cmd确认是我们的命令: cmd={cmd}")
        return True
    
    def _pve_is_duplicate_event(self, event: Event) -> bool:
        """
        使用事件的关键信息生成唯一标识，防止重复处理
        改进：基于命令+用户+action生成更可靠的唯一标识，而不是依赖可能重复的事件ID
        """
        current_time = time.time()
        
        # 清理过期的缓存（超过TTL的缓存项）
        if hasattr(self, '_pve_event_cache_time'):
            if current_time - self._pve_event_cache_time > self._pve_event_cache_ttl:
                self._pve_processed_events.clear()
                self._pve_event_cache_time = current_time
        
        if not hasattr(self, '_pve_event_cache_time'):
            self._pve_event_cache_time = current_time
        
        # 从事件数据中提取关键信息
        event_data = None
        if hasattr(event, 'event_data'):
            event_data = event.event_data
        elif hasattr(event, 'data'):
            event_data = event.data
        elif isinstance(event, dict):
            event_data = event
        
        # 生成基于命令内容的唯一标识（不依赖可能重复的事件ID）
        event_key = None
        if event_data:
            cmd = event_data.get("cmd", "") or event_data.get("command", "") or ""
            userid = event_data.get("user") or event_data.get("userid") or event_data.get("user_id") or ""
            action = event_data.get("action", "") or (event_data.get("data", {}) or {}).get("action", "")
            # 使用命令+用户+action生成唯一标识（精确到秒，避免毫秒级重复）
            # 这样同一个用户的同一个命令在1秒内只会处理一次
            event_key = f"pve_{cmd}|{userid}|{action}|{int(current_time)}"
        else:
            # 如果无法获取事件数据，尝试使用事件对象的内置ID
            if hasattr(event, 'event_id'):
                event_key = f"pve_event_{event.event_id}"
            elif hasattr(event, 'id'):
                event_key = f"pve_event_{event.id}"
            else:
                event_key = f"pve_unknown_{hash(str(event))}"
        
        # 检查是否已处理过
        if event_key in self._pve_processed_events:
            # 静默返回，不记录日志（重复事件很常见，不需要记录）
            return True
        
        # 记录已处理的事件
        self._pve_processed_events.add(event_key)
        # 只在第一次处理时记录DEBUG日志
        logger.debug(f"{self.pve_plugin_name} 记录新PVE事件: key={event_key}")
        return False
    
    def handle_pve_command(self, event: Event):
        """
        处理PVE相关命令（通过事件系统）
        完全独立的PVE插件命令处理逻辑
        """
        if not event:
            return  # 静默返回，不记录日志
        
        # 优先检查是否是重复事件（在获取事件数据之前就检查，减少开销）
        if self._pve_is_duplicate_event(event):
            return  # 静默返回，不记录日志（重复事件很常见，不需要记录）
        
        # 尝试多种方式获取事件数据
        event_data = None
        if hasattr(event, 'event_data'):
            event_data = event.event_data
        elif hasattr(event, 'data'):
            event_data = event.data
        elif isinstance(event, dict):
            event_data = event
        
        if not event_data:
            logger.debug(f"{self.pve_plugin_name} PVE事件数据为空，事件类型: {type(event)}")
            return
        
        # 尝试从事件对象本身获取cmd和category（可能在事件的其他属性中）
        event_cmd = None
        event_category = None
        
        # 尝试从事件对象的各种可能属性获取
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
        
        # 尝试从事件对象的 __dict__ 获取
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
        
        # 如果从事件对象获取到了cmd或category，合并到event_data中
        if event_cmd and 'cmd' not in event_data:
            event_data['cmd'] = event_cmd
        if event_category and 'category' not in event_data:
            event_data['category'] = event_category
        
        # PVE插件独有的action列表（这些action只属于PVE插件）
        pve_only_actions = ["pve_status", "container_status", "pve_help"]
        
        # 获取action用于判断
        action = event_data.get("action", "")
        if not action:
            data = event_data.get("data", {})
            if isinstance(data, dict):
                action = data.get("action", "")
        
        # 如果action是PVE独有的，直接确认是我们的命令（无需检查category和cmd）
        if action in pve_only_actions:
            logger.debug(f"{self.pve_plugin_name} 通过PVE独有action确认是我们的命令: action={action}")
        else:
            # 不是PVE独有的action，通过 _pve_is_our_command 进一步检查（兼容旧数据）
            if not self._pve_is_our_command(event_data):
                # 不是我们的命令，静默返回（避免日志噪音）
                return
        
        if not action:
            logger.debug(f"{self.pve_plugin_name} PVE事件中没有action字段")
            return
        
        logger.info(f"{self.pve_plugin_name} 处理PVE命令事件: action={action}, event_data keys={list(event_data.keys())}")
        
        try:
            # 使用PVE消息处理器处理命令
            if not self.pve_plugin._pve_message_handler:
                error_msg = "❌ PVE插件消息处理器未初始化，请重新加载插件"
                logger.error(f"{self.pve_plugin_name} {error_msg}")
                try:
                    # 只使用 mtype=NotificationType.Plugin，不传 userid 和 channel 以确保只出现在"插件推送"分类
                    self.pve_plugin.post_message(
                        mtype=NotificationType.Plugin,
                        title=error_msg
                    )
                except Exception as e:
                    logger.error(f"{self.pve_plugin_name} 发送错误消息失败: {e}")
                return
            
            result = None
            if action == "pve_help":
                logger.info(f"{self.pve_plugin_name} 执行PVE帮助命令")
                result = self.pve_plugin._pve_message_handler._pve_get_help_message()
            elif action == "pve_status":
                logger.info(f"{self.pve_plugin_name} 执行PVE状态命令")
                result = self.pve_plugin._pve_message_handler._pve_get_pve_status()
            elif action == "container_status":
                logger.info(f"{self.pve_plugin_name} 执行PVE容器命令")
                result = self.pve_plugin._pve_message_handler._pve_get_container_status()
            else:
                # 理论上不应该到达这里，因为action已经在前面验证过了
                logger.warning(f"{self.pve_plugin_name} 未处理的PVE action: {action}")
                cmd = event_data.get("cmd", "")
                result = {
                    "title": f"❓ {self.pve_plugin_name}",
                    "text": f"未知命令: {cmd}\n\n发送 '/pve_help' 查看可用命令。"
                }
                result = {
                    "title": f"❓ {self.pve_plugin_name}",
                    "text": f"未知命令: {cmd}\n\n发送 '/pve_help' 查看可用命令。"
                }
            
            # 发送回复消息
            if result:
                # result是字典格式 {title, text}
                title = result.get("title", f"{self.pve_plugin_name}")
                text_content = result.get("text", "")
                userid = event_data.get("user")
                
                logger.info(f"{self.pve_plugin_name} 准备发送PVE回复消息: action={action}, title={title}, userid={userid}, text长度={len(text_content) if text_content else 0}")

                # 发送消息 - 只使用 mtype=NotificationType.Plugin，不传 userid 和 channel
                # 注意：传递 userid 会导致消息分发到所有通知渠道，所以交互式回复也不传 userid
                # 这样所有消息都只出现在"插件推送"分类中
                try:
                    # 统一不传递 userid 和 channel，只传递 mtype=NotificationType.Plugin
                    # 消息会出现在"插件推送"分类，用户可以在该分类中查看所有交互回复
                    self.pve_plugin.post_message(
                        mtype=NotificationType.Plugin,
                        title=title,
                        text=text_content
                    )
                    if userid:
                        logger.info(f"{self.pve_plugin_name} ✅ 成功发送PVE回复消息（用户 {userid}，仅在插件推送分类）: {title}")
                    else:
                        logger.info(f"{self.pve_plugin_name} ✅ 成功发送PVE回复消息（无userid）: {title}")
                except Exception as msg_e:
                    logger.error(f"{self.pve_plugin_name} ❌ 发送PVE回复消息失败: {msg_e}", exc_info=True)
            else:
                logger.warning(f"{self.pve_plugin_name} ⚠️ PVE命令处理返回空结果: action={action}")
                
        except Exception as e:
            logger.error(f"{self.pve_plugin_name} 处理PVE命令事件失败: {str(e)}", exc_info=True)
            error_msg = f"❌ 执行PVE命令时发生错误: {str(e)}"
            try:
                # 只使用 mtype=NotificationType.Plugin，不传 userid 和 channel 以确保只出现在"插件推送"分类
                self.pve_plugin.post_message(
                    mtype=NotificationType.Plugin,
                    title=error_msg
                )
            except Exception as msg_e:
                logger.error(f"{self.pve_plugin_name} 发送错误消息失败: {msg_e}")

