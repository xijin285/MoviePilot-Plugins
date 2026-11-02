"""
爱快消息处理模块 - 处理微信等消息渠道的命令交互
完全独立的爱快插件消息处理
"""
from datetime import datetime
from typing import Optional, Dict, Any

# 延迟导入logger，避免循环导入
ikuai_logger = None

def get_ikuai_logger():
    """获取logger实例"""
    global ikuai_logger
    if ikuai_logger is None:
        try:
            from app.log import logger as app_logger
            ikuai_logger = app_logger
        except ImportError:
            import logging
            ikuai_logger = logging.getLogger(__name__)
    return ikuai_logger


class IkuaiMessageHandler:
    """爱快消息处理器类 - 完全独立，专属于爱快插件"""
    
    def __init__(self, ikuai_plugin_instance):
        """
        初始化爱快消息处理器
        :param ikuai_plugin_instance: IkuaiRouterBackup插件实例
        """
        self.ikuai_plugin = ikuai_plugin_instance
        self.ikuai_plugin_name = ikuai_plugin_instance.plugin_name
    
    def ikuai_process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理用户通过消息渠道发送的消息（爱快专属）
        
        :param message: 消息字典，包含 text, title, userid, username 等字段
        :return: 响应字典，包含 title 和 text 字段，或 None 表示不处理
        """
        try:
            # 提取消息内容
            text = message.get("text", "").strip()
            title = message.get("title", "")
            userid = message.get("userid", "")
            username = message.get("username", "")
            
            get_ikuai_logger().info(f"{self.ikuai_plugin_name} 处理爱快消息: '{text}', userid: {userid}")
            
            if not text:
                get_ikuai_logger().debug(f"{self.ikuai_plugin_name} 爱快消息内容为空，不处理")
                return None
            
            # 严格检查：必须是"/ikuai"开头（双重验证）
            if not text.startswith("/ikuai"):
                get_ikuai_logger().debug(f"{self.ikuai_plugin_name} 收到非爱快命令，跳过: {text}")
                return None
            
            # 处理带空格或斜杠变体的命令（如"/ ikuai_help" -> "/ikuai_help"）
            # 移除命令中的空格，统一格式
            normalized_text = text.replace(" ", "").replace("　", "")  # 移除普通空格和全角空格
            
            # 严格匹配：只处理已注册的爱快命令
            if normalized_text == "/ikuai_help":
                get_ikuai_logger().info(f"{self.ikuai_plugin_name} 匹配到爱快帮助命令")
                return self._ikuai_get_help_message()
            
            if normalized_text == "/ikuai_status":
                get_ikuai_logger().info(f"{self.ikuai_plugin_name} 匹配到爱快状态命令")
                return self._ikuai_get_system_status()
            
            if normalized_text == "/ikuai_line":
                get_ikuai_logger().info(f"{self.ikuai_plugin_name} 匹配到爱快线路命令")
                return self._ikuai_get_line_status()
            
            if normalized_text == "/ikuai_list":
                get_ikuai_logger().info(f"{self.ikuai_plugin_name} 匹配到爱快列表命令")
                return self._ikuai_get_backup_list()
            
            if normalized_text == "/ikuai_history":
                get_ikuai_logger().info(f"{self.ikuai_plugin_name} 匹配到爱快历史命令")
                return self._ikuai_get_backup_history()
            
            if normalized_text == "/ikuai_backup":
                get_ikuai_logger().info(f"{self.ikuai_plugin_name} 匹配到爱快备份命令")
                return self._ikuai_trigger_backup()
            
            # 如果以"/ikuai"开头但不是有效命令，返回帮助信息
            get_ikuai_logger().info(f"{self.ikuai_plugin_name} 未知的爱快命令: {text}")
            return {
                "title": f"❓ {self.ikuai_plugin_name}",
                "text": f"未知命令: {text}\n\n发送 '/ikuai_help' 查看可用命令。"
            }
            
        except Exception as e:
            get_ikuai_logger().error(f"{self.ikuai_plugin_name} 处理爱快消息时发生错误: {e}")
            return {
                "title": f"❌ {self.ikuai_plugin_name}",
                "text": f"处理消息时发生错误: {str(e)}"
            }
    
    def _ikuai_get_help_message(self) -> Dict[str, Any]:
        """获取爱快帮助信息 - 优化样式"""
        title = f"📚 {self.ikuai_plugin_name} 帮助"
        
        help_text = f"""━━━━━━━━━━━━━━━

🔹 /ikuai_status - 系统状态
🔹 /ikuai_line - 线路监控
🔹 /ikuai_list - 备份列表
🔹 /ikuai_history - 历史记录
🔹 /ikuai_backup - 立即备份
🔹 /ikuai_help - 显示帮助
━━━━━━━━━━━━━━━
📦 版本: {self.ikuai_plugin.plugin_version}
👤 作者: {self.ikuai_plugin.plugin_author}"""
        
        return {
            "title": title,
            "text": help_text
        }
    
    def _ikuai_get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            from ..ikuai.client import IkuaiClient
            
            if not self.ikuai_plugin._ikuai_url or not self.ikuai_plugin._ikuai_username or not self.ikuai_plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。\n\n请在插件配置页面填写完整的爱快路由器信息。"
                }
            
            client = IkuaiClient(
                url=self.ikuai_plugin._ikuai_url,
                username=self.ikuai_plugin._ikuai_username,
                password=self.ikuai_plugin._ikuai_password,
                plugin_name=self.ikuai_plugin_name,
                auth_mode=getattr(self.ikuai_plugin, '_ikuai_auth_mode', 'auto'),
                api_token=getattr(self.ikuai_plugin, '_ikuai_api_token', '')
            )
            
            if not client.login():
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 无法连接到爱快路由器\n\n请检查：\n• 路由器地址是否正确\n• 网络连接是否正常\n• 用户名密码是否正确"
                }
            
            system_info = client.get_system_info()
            
            if not system_info:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 无法获取系统信息"
                }
            
            # 格式化系统信息
            cpu_usage = system_info.get("cpu_usage", 0)
            mem_usage = system_info.get("mem_usage", 0)
            uptime = system_info.get("uptime", 0)
            online_users = system_info.get("online_users", 0)
            connect_num = system_info.get("connect_num", 0)
            upload_speed = system_info.get("upload_speed", 0)
            download_speed = system_info.get("download_speed", 0)
            version = system_info.get("version", "未知")
            
            # 格式化运行时间
            days = uptime // 86400
            hours = (uptime % 86400) // 3600
            minutes = (uptime % 3600) // 60
            uptime_str = f"{days}天{hours}小时{minutes}分钟" if days > 0 else f"{hours}小时{minutes}分钟"
            
            # 格式化速度
            def format_speed(bytes_per_sec):
                if bytes_per_sec < 1024:
                    return f"{bytes_per_sec} B/s"
                elif bytes_per_sec < 1024 * 1024:
                    return f"{bytes_per_sec / 1024:.2f} KB/s"
                else:
                    return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
            
            # 确定状态颜色
            cpu_status = "🟢" if cpu_usage < 50 else "🟡" if cpu_usage < 80 else "🔴"
            mem_status = "🟢" if mem_usage < 50 else "🟡" if mem_usage < 80 else "🔴"
            
            message = "━━━━━━━━━━━━━━━\n"
            message += "📊 系统状态\n"
            message += f"🖥️ CPU {cpu_status} {cpu_usage:.1f}%\n"
            message += f"💾 内存 {mem_status} {mem_usage:.1f}%\n"
            message += f"👥 设备 {online_users}台\n"
            message += f"🔗 连接 {connect_num}个\n"
            message += f"⬆️ {format_speed(upload_speed)}\n"
            message += f"⬇️ {format_speed(download_speed)}\n"
            message += f"⏱️ {uptime_str}\n"
            message += f"📌 {version}\n"
            message += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"📊 {self.ikuai_plugin_name} 系统状态",
                "text": message
            }
            
        except Exception as e:
            get_ikuai_logger().error(f"{self.ikuai_plugin_name} 获取系统状态失败: {e}")
            return {
                "title": f"❌ {self.ikuai_plugin_name}",
                "text": f"获取系统状态失败: {str(e)}"
            }
    
    def _ikuai_get_line_status(self) -> Dict[str, Any]:
        """获取线路状态"""
        try:
            from ..ikuai.client import IkuaiClient
            
            if not self.ikuai_plugin._ikuai_url or not self.ikuai_plugin._ikuai_username or not self.ikuai_plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。"
                }
            
            client = IkuaiClient(
                url=self.ikuai_plugin._ikuai_url,
                username=self.ikuai_plugin._ikuai_username,
                password=self.ikuai_plugin._ikuai_password,
                plugin_name=self.ikuai_plugin_name,
                auth_mode=getattr(self.ikuai_plugin, '_ikuai_auth_mode', 'auto'),
                api_token=getattr(self.ikuai_plugin, '_ikuai_api_token', '')
            )
            
            if not client.login():
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 无法连接到爱快路由器"
                }
            
            interface_info = client.get_interface_info()
            
            if not interface_info:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 无法获取线路信息"
                }
            
            # 格式化线路信息
            iface_check = interface_info.get("iface_check", [])
            iface_stream = interface_info.get("iface_stream", [])
            snapshoot_lan = interface_info.get("snapshoot_lan", [])
            
            # 创建流量映射
            stream_map = {line.get("interface"): line for line in iface_stream}
            
            def format_speed(bytes_per_sec):
                if bytes_per_sec < 1024:
                    return f"{bytes_per_sec} B/s"
                elif bytes_per_sec < 1024 * 1024:
                    return f"{bytes_per_sec / 1024:.2f} KB/s"
                else:
                    return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
            
            message = "━━━━━━━━━━━━━━━\n"
            message += "🌐 线路状态\n"
            lines_text = ""
            
            # WAN线路
            if iface_check:
                for line in iface_check[:5]:  # 最多显示5条
                    line_name = line.get("interface", "")
                    line_result = line.get("result", "")
                    status_emoji = "✅" if line_result == "success" else "❌"
                    
                    # 判断线路类型
                    if line_name.startswith("adsl") or line_name.startswith("pppoe"):
                        line_type = "ADSL"
                    elif line_name.startswith("wan"):
                        line_type = "WAN"
                    else:
                        line_type = "其他"
                    
                    stream_info = stream_map.get(line_name, {})
                    upload_speed = stream_info.get("upload", 0)
                    download_speed = stream_info.get("download", 0)
                    lines_text += f"{status_emoji}{line_name:<8}[{line_type:<6}]⬆️{format_speed(upload_speed):>8} ⬇️{format_speed(download_speed):>8}\n"
            
            # LAN线路
            if snapshoot_lan:
                for lan in snapshoot_lan[:3]:  # 最多显示3条
                    lan_name = lan.get("interface", "")
                    stream_info = stream_map.get(lan_name, {})
                    upload_speed = stream_info.get("upload", 0)
                    download_speed = stream_info.get("download", 0)
                    lines_text += f"✅{lan_name:<8}[LAN   ]⬆️{format_speed(upload_speed):>8} ⬇️{format_speed(download_speed):>8}\n"
            
            # 移除末尾的换行
            if lines_text.endswith("\n"):
                lines_text = lines_text.rstrip("\n")
            
            message += lines_text
            message += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"🌐 {self.ikuai_plugin_name} 线路状态",
                "text": message
            }
            
        except Exception as e:
            get_ikuai_logger().error(f"{self.ikuai_plugin_name} 获取线路状态失败: {e}")
            return {
                "title": f"❌ {self.ikuai_plugin_name}",
                "text": f"获取线路状态失败: {str(e)}"
            }
    
    def _ikuai_get_backup_list(self) -> Dict[str, Any]:
        """获取备份列表"""
        try:
            from ..ikuai.client import IkuaiClient
            
            if not self.ikuai_plugin._ikuai_url or not self.ikuai_plugin._ikuai_username or not self.ikuai_plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。"
                }
            
            client = IkuaiClient(
                url=self.ikuai_plugin._ikuai_url,
                username=self.ikuai_plugin._ikuai_username,
                password=self.ikuai_plugin._ikuai_password,
                plugin_name=self.ikuai_plugin_name,
                auth_mode=getattr(self.ikuai_plugin, '_ikuai_auth_mode', 'auto'),
                api_token=getattr(self.ikuai_plugin, '_ikuai_api_token', '')
            )
            
            if not client.login():
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 无法连接到爱快路由器"
                }
            
            backup_list = client.get_backup_list()
            
            if backup_list is None:
                return {
                    "title": f"❌ {self.ikuai_plugin_name}",
                    "text": "❌ 无法获取备份列表"
                }
            
            if not backup_list:
                return {
                    "title": f"📁 {self.ikuai_plugin_name} 备份列表",
                    "text": "📭 当前没有备份文件"
                }
            
            # 格式化备份列表
            message = "━━━━━━━━━━━━━━━\n"
            message += "📁 备份列表\n"
            list_text = ""
            
            for idx, backup in enumerate(backup_list[:10], 1):  # 最多显示10条
                filename = backup.get("name") or backup.get("filename", "未知")
                date = backup.get("date", "")
                
                list_text += f"{idx}. {filename}\n"
                if date:
                    list_text += f"   {date}\n"
            
            if len(backup_list) > 10:
                list_text += f"（仅显示前10条，共{len(backup_list)}条）"
            else:
                list_text = list_text.rstrip()
            
            message += list_text
            message += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"📁 {self.ikuai_plugin_name} 备份列表",
                "text": message
            }
            
        except Exception as e:
            get_ikuai_logger().error(f"{self.ikuai_plugin_name} 获取备份列表失败: {e}")
            return {
                "title": f"❌ {self.ikuai_plugin_name}",
                "text": f"获取备份列表失败: {str(e)}"
            }
    
    def _ikuai_get_backup_history(self) -> Dict[str, Any]:
        """获取备份历史"""
        try:
            history = self.ikuai_plugin._load_backup_history()
            
            if not history:
                return {
                    "title": f"📜 {self.ikuai_plugin_name} 备份历史",
                    "text": "📭 当前没有备份历史记录"
                }
            
            # 格式化历史记录
            message = "━━━━━━━━━━━━━━━\n"
            message += "📜 备份历史记录\n\n"
            history_text = ""
            
            for idx, entry in enumerate(history[-10:], 1):  # 显示最近10条
                timestamp = entry.get("timestamp", "未知")
                status = entry.get("status", "未知")
                filename = entry.get("filename", "未知")
                source = entry.get("source", "未知")
                
                status_emoji = "✅" if status == "success" else "❌"
                
                history_text += f"{idx}. {status_emoji} {timestamp}\n"
                history_text += f"   状态: {status}\n"
                history_text += f"   文件: {filename}\n"
                history_text += f"   来源: {source}\n\n"
            
            if len(history) > 10:
                history_text += f"（仅显示最近10条，共{len(history)}条）"
            else:
                history_text = history_text.rstrip()
            
            message += history_text
            message += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"📜 {self.ikuai_plugin_name} 备份历史",
                "text": message
            }
            
        except Exception as e:
            get_ikuai_logger().error(f"{self.ikuai_plugin_name} 获取备份历史失败: {e}")
            return {
                "title": f"❌ {self.ikuai_plugin_name}",
                "text": f"获取备份历史失败: {str(e)}"
            }
    
    def _ikuai_trigger_backup(self) -> Dict[str, Any]:
        """触发立即备份"""
        try:
            # 检查是否已启用
            if not self.ikuai_plugin._enabled:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 插件未启用\n\n请在插件配置页面启用插件。"
                }
            
            # 检查配置
            if not self.ikuai_plugin._ikuai_url or not self.ikuai_plugin._ikuai_username or not self.ikuai_plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.ikuai_plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。"
                }
            
            # 检查是否有任务正在运行
            if self.ikuai_plugin._lock and self.ikuai_plugin._lock.locked():
                return {
                    "title": f"⏳ {self.ikuai_plugin_name}",
                    "text": "⏳ 备份任务正在进行中，请稍候...\n\n完成后会自动通知您。"
                }
            
            # 触发备份任务
            # 这里需要异步执行，避免阻塞消息回复
            import threading
            backup_thread = threading.Thread(target=self.ikuai_plugin.run_backup_job)
            backup_thread.daemon = True
            backup_thread.start()
            
            return {
                "title": f"🚀 {self.ikuai_plugin_name}",
                "text": "✅ 备份任务已启动\n\n备份完成后会自动通知您结果。\n\n💡 提示：可以发送 '/ikuai_history' 查看备份历史记录。"
            }
            
        except Exception as e:
            get_ikuai_logger().error(f"{self.ikuai_plugin_name} 触发备份失败: {e}")
            return {
                "title": f"❌ {self.ikuai_plugin_name}",
                "text": f"触发备份失败: {str(e)}"
            }

