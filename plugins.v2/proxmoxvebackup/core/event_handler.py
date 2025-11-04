"""
事件处理模块
负责处理插件事件（如消息渠道命令等）
"""
from app.log import logger
from app.core.event import eventmanager, Event
from app.schemas.types import EventType
import time


class EventHandler:
    """事件处理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化事件处理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        # 用于防止重复处理同一个事件
        self._processed_events = set()
        self._event_cache_ttl = 5  # 5秒内的重复事件将被忽略
        
        # 不再需要构建action映射，完全依赖category和cmd标识
    
    def _is_our_command(self, event_data: dict) -> bool:
        """
        严格检查事件是否属于PVE插件的命令
        完全独立，不依赖任何可能与其他插件共享的逻辑
        """
        # PVE插件独有的action列表（这些action只属于PVE插件）
        pve_only_actions = ["pve_status", "container_status"]
        
        # 获取action
        action = event_data.get("action", "")
        if not action:
            data = event_data.get("data", {})
            if isinstance(data, dict):
                action = data.get("action", "")
        
        # 第一步：如果action是PVE独有的，直接确认是我们的命令
        if action in pve_only_actions:
            logger.debug(f"{self.plugin_name} 通过PVE独有action确认是我们的命令: action={action}")
            return True
        
        # 第二步：优先检查 category（最可靠的标识）
        category = event_data.get("category", "")
        if category:
            if category == "PVE":
                # category明确是PVE，确认是我们的命令
                logger.debug(f"{self.plugin_name} 通过category确认是我们的命令: category={category}")
                return True
            else:
                # category存在但不是PVE，直接拒绝
                logger.debug(f"{self.plugin_name} category不匹配（必须是'PVE'）: category={category}")
                return False
        
        # 第三步：如果没有category，必须通过cmd检查
        # 尝试多种方式获取cmd
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
            logger.debug(f"{self.plugin_name} 没有category且cmd为空，且action不是PVE独有的，拒绝处理: action={action}")
            return False
        
        # 检查cmd是否以"/pve"开头
        if not cmd.startswith("/pve"):
            logger.debug(f"{self.plugin_name} cmd不匹配（必须以'/pve'开头）: cmd={cmd}")
            return False
        
        # cmd以"/pve"开头，确认是我们的命令
        logger.debug(f"{self.plugin_name} 通过cmd确认是我们的命令: cmd={cmd}")
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
    
    def handle_pve_command(self, event: Event):
        """
        处理PVE相关命令（通过事件系统）
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
        
        # 尝试从事件对象本身获取cmd和category（可能在事件的其他属性中）
        # 检查事件对象的所有属性
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
        
        # 获取action用于判断
        action = event_data.get("action") or (event_data.get("data", {}) or {}).get("action", "")
        
        # PVE插件独有的action列表（这些action只属于PVE插件）
        pve_only_actions = ["pve_status", "container_status"]
        
        # 如果action是PVE独有的，即使没有category和cmd，也确认是我们的命令
        if action in pve_only_actions:
            logger.debug(f"{self.plugin_name} 通过PVE独有action确认是我们的命令: action={action}")
            # 不需要提前返回，继续处理
        elif not event_data.get('category') and not event_data.get('cmd'):
            # 对于非PVE独有的action（如help），如果没有category和cmd，拒绝处理
            logger.debug(f"{self.plugin_name} 事件数据中没有category和cmd，且action不是PVE独有的，拒绝处理: action={action}, keys={list(event_data.keys())}")
            return  # 直接返回，不处理
        
        # 关键修复：在开始处理前，先检查是否是我们的命令
        logger.debug(f"{self.plugin_name} 收到事件: cmd={event_data.get('cmd', 'N/A')}, category={event_data.get('category', 'N/A')}, action={event_data.get('action', 'N/A')}, keys={list(event_data.keys())}")
        
        if not self._is_our_command(event_data):
            logger.debug(f"{self.plugin_name} ❌ 不是我们的命令，跳过处理: cmd={event_data.get('cmd', 'N/A')}, category={event_data.get('category', 'N/A')}")
            return
        
        action = event_data.get("action") or (event_data.get("data", {}) or {}).get("action")
        if not action:
            logger.debug(f"{self.plugin_name} 事件中没有action字段")
            return
        
        # 兼容处理：将 status 映射到 pve_status
        if action == "status":
            action = "pve_status"
            logger.debug(f"{self.plugin_name} 将 action 'status' 映射为 'pve_status'")
        
        if action not in ["pve_status", "container_status", "help"]:
            logger.debug(f"{self.plugin_name} 未知的action: {action}")
            return
        
        logger.info(f"{self.plugin_name} 处理命令事件: action={action}, event_data keys={list(event_data.keys())}")
        
        try:
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
            elif action == "pve_status":
                logger.info(f"{self.plugin_name} 执行状态命令")
                result = self.plugin._message_handler._get_pve_status()
            elif action == "container_status":
                logger.info(f"{self.plugin_name} 执行容器命令")
                result = self.plugin._message_handler._get_container_status()
            else:
                logger.warning(f"{self.plugin_name} 未知的action: {action}")
                cmd = event_data.get("cmd", "")
                result = {
                    "title": f"❓ {self.plugin_name}",
                    "text": f"未知命令: {cmd}\n\n发送 '/pve帮助' 查看可用命令。"
                }
            
            # 发送回复消息
            if result:
                # result是字典格式 {title, text}
                title = result.get("title", f"{self.plugin_name}")
                text_content = result.get("text", "")
                
                # 关键修复：对于帮助消息，确保title中明确包含插件名称
                if action == "help":
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
                logger.warning(f"{self.plugin_name} ⚠️ 命令处理返回空结果: action={action}")
                
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

