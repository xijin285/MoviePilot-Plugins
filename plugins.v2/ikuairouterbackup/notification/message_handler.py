"""消息渠道交互处理器模块"""
from typing import Optional, Dict, Any
from app.log import logger


class MessageHandler:
    """消息渠道交互处理器类"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理用户通过消息渠道发送的消息"""
        try:
            # 提取消息内容
            text = message.get("text", "").strip()
            title = message.get("title", "")
            userid = message.get("userid", "")
            username = message.get("username", "")
            
            logger.info(f"{self.plugin_name} 处理消息: '{text}', userid: {userid}")
            
            if not text:
                logger.debug(f"{self.plugin_name} 消息内容为空，不处理")
                return None
            
            # 再次严格检查：必须是"/爱快"开头（双重验证）
            if not text.startswith("/爱快"):
                logger.warning(f"{self.plugin_name} 收到非爱快命令，这不应该发生: {text}")
                return None
            
            # 处理带空格或斜杠变体的命令（如"/ 爱快帮助" -> "/爱快帮助"）
            # 移除命令中的空格，统一格式
            normalized_text = text.replace(" ", "").replace("　", "")  # 移除普通空格和全角空格
            
            # 严格匹配：只处理已注册的爱快命令，不处理通用关键词
            # 帮助命令
            if normalized_text.startswith("/爱快帮助"):
                logger.info(f"{self.plugin_name} 匹配到帮助命令")
                return self._get_help_message()
            
            # 状态查询命令
            if normalized_text.startswith("/爱快状态"):
                logger.info(f"{self.plugin_name} 匹配到状态命令")
                return self._get_system_status()
            
            # 线路状态命令
            if normalized_text.startswith("/爱快线路"):
                logger.info(f"{self.plugin_name} 匹配到线路命令")
                return self._get_line_status()
            
            # 备份列表命令
            if normalized_text.startswith("/爱快列表"):
                logger.info(f"{self.plugin_name} 匹配到列表命令")
                return self._get_backup_list()
            
            # 备份历史命令
            if normalized_text.startswith("/爱快历史"):
                logger.info(f"{self.plugin_name} 匹配到历史命令")
                return self._get_backup_history()
            
            # 立即备份命令
            if normalized_text.startswith("/爱快备份"):
                logger.info(f"{self.plugin_name} 匹配到备份命令")
                return self._trigger_backup()
            
            # 如果以"/爱快"开头但不是有效命令，返回帮助信息
            logger.info(f"{self.plugin_name} 未知的爱快命令: {text}")
            return {
                "title": f"❓ {self.plugin_name}",
                "text": f"未知命令: {text}\n\n发送 '/爱快帮助' 查看可用命令。"
            }
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 处理消息时发生错误: {e}")
            return {
                "title": f"❌ {self.plugin_name}",
                "text": f"处理消息时发生错误: {str(e)}"
            }
    
    def _get_help_message(self) -> Dict[str, Any]:
        """获取帮助信息"""
        title = f"📚 {self.plugin_name} 帮助"
        
        help_text = f"""/爱快状态 - 系统状态
/爱快线路 - 线路监控
/爱快列表 - 备份列表
/爱快历史 - 历史记录
/爱快备份 - 立即备份
/爱快帮助 - 显示帮助

版本: {self.plugin.plugin_version} | 作者: {self.plugin.plugin_author}"""
        
        return {
            "title": title,
            "text": help_text
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            from ..ikuai.client import IkuaiClient
            
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。\n\n请在插件配置页面填写完整的爱快路由器信息。"
                }
            
            client = IkuaiClient(
                url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password,
                plugin_name=self.plugin_name
            )
            
            if not client.login():
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 无法连接到爱快路由器\n\n请检查：\n• 路由器地址是否正确\n• 网络连接是否正常\n• 用户名密码是否正确"
                }
            
            system_info = client.get_system_info()
            
            if not system_info:
                return {
                    "title": f"⚠️ {self.plugin_name}",
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
            
            status_text = f"""🖥️ CPU {cpu_status} {cpu_usage:.1f}%  💾 内存 {mem_status} {mem_usage:.1f}%
👥 设备 {online_users}台  🔗 连接 {connect_num}个
⬆️ {format_speed(upload_speed)}  ⬇️ {format_speed(download_speed)}
⏱️ {uptime_str}
📌 {version}"""
            
            return {
                "title": f"📊 {self.plugin_name} 系统状态",
                "text": status_text
            }
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取系统状态失败: {e}")
            return {
                "title": f"❌ {self.plugin_name}",
                "text": f"获取系统状态失败: {str(e)}"
            }
    
    def _get_line_status(self) -> Dict[str, Any]:
        """获取线路状态"""
        try:
            from ..ikuai.client import IkuaiClient
            
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。"
                }
            
            client = IkuaiClient(
                url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password,
                plugin_name=self.plugin_name
            )
            
            if not client.login():
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 无法连接到爱快路由器"
                }
            
            interface_info = client.get_interface_info()
            
            if not interface_info:
                return {
                    "title": f"⚠️ {self.plugin_name}",
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
            
            return {
                "title": f"🌐 {self.plugin_name} 线路状态",
                "text": lines_text
            }
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取线路状态失败: {e}")
            return {
                "title": f"❌ {self.plugin_name}",
                "text": f"获取线路状态失败: {str(e)}"
            }
    
    def _get_backup_list(self) -> Dict[str, Any]:
        """获取备份列表"""
        try:
            from ..ikuai.client import IkuaiClient
            
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。"
                }
            
            client = IkuaiClient(
                url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password,
                plugin_name=self.plugin_name
            )
            
            if not client.login():
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 无法连接到爱快路由器"
                }
            
            backup_list = client.get_backup_list()
            
            if backup_list is None:
                return {
                    "title": f"❌ {self.plugin_name}",
                    "text": "❌ 无法获取备份列表"
                }
            
            if not backup_list:
                return {
                    "title": f"📁 {self.plugin_name} 备份列表",
                    "text": "📭 当前没有备份文件"
                }
            
            # 格式化备份列表
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
            
            return {
                "title": f"📁 {self.plugin_name} 备份列表",
                "text": list_text
            }
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取备份列表失败: {e}")
            return {
                "title": f"❌ {self.plugin_name}",
                "text": f"获取备份列表失败: {str(e)}"
            }
    
    def _get_backup_history(self) -> Dict[str, Any]:
        """获取备份历史"""
        try:
            history = self.plugin._load_backup_history()
            
            if not history:
                return {
                    "title": f"📜 {self.plugin_name} 备份历史",
                    "text": "📭 当前没有备份历史记录"
                }
            
            # 格式化历史记录
            history_text = f"📜 备份历史记录\n\n"
            
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
            
            return {
                "title": f"📜 {self.plugin_name} 备份历史",
                "text": history_text
            }
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取备份历史失败: {e}")
            return {
                "title": f"❌ {self.plugin_name}",
                "text": f"获取备份历史失败: {str(e)}"
            }
    
    def _trigger_backup(self) -> Dict[str, Any]:
        """触发立即备份"""
        try:
            # 检查是否已启用
            if not self.plugin._enabled:
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 插件未启用\n\n请在插件配置页面启用插件。"
                }
            
            # 检查配置
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {
                    "title": f"⚠️ {self.plugin_name}",
                    "text": "❌ 配置不完整：URL、用户名或密码未设置。"
                }
            
            # 检查是否有任务正在运行
            if self.plugin._lock and self.plugin._lock.locked():
                return {
                    "title": f"⏳ {self.plugin_name}",
                    "text": "⏳ 备份任务正在进行中，请稍候...\n\n完成后会自动通知您。"
                }
            
            # 触发备份任务
            # 这里需要异步执行，避免阻塞消息回复
            import threading
            backup_thread = threading.Thread(target=self.plugin.run_backup_job)
            backup_thread.daemon = True
            backup_thread.start()
            
            return {
                "title": f"🚀 {self.plugin_name}",
                "text": "✅ 备份任务已启动\n\n备份完成后会自动通知您结果。\n\n💡 提示：可以发送 'history' 查看备份历史记录。"
            }
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 触发备份失败: {e}")
            return {
                "title": f"❌ {self.plugin_name}",
                "text": f"触发备份失败: {str(e)}"
            }

