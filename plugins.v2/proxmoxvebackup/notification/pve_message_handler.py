"""
PVE消息处理模块 - 处理微信等消息渠道的命令交互
完全独立的PVE插件消息处理
"""
from datetime import datetime
from typing import Optional, Dict, Any
from ..pve.client import get_pve_status, get_container_status, get_qemu_status

# 延迟导入logger，避免循环导入
pve_logger = None

def get_pve_logger():
    """获取logger实例"""
    global pve_logger
    if pve_logger is None:
        try:
            from app.log import logger as app_logger
            pve_logger = app_logger
        except ImportError:
            import logging
            pve_logger = logging.getLogger(__name__)
    return pve_logger


class PVEMessageHandler:
    """PVE消息处理器类 - 完全独立，专属于PVE插件"""
    
    def __init__(self, pve_plugin_instance):
        """
        初始化PVE消息处理器
        :param pve_plugin_instance: ProxmoxVEBackup插件实例
        """
        self.pve_plugin = pve_plugin_instance
        self.pve_plugin_name = pve_plugin_instance.plugin_name
    
    def pve_process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理用户通过消息渠道发送的消息（PVE专属）
        
        :param message: 消息字典，包含 text, title, userid, username 等字段
        :return: 响应字典，包含 title 和 text 字段，或 None 表示不处理
        """
        try:
            # 提取消息内容
            text = message.get("text", "").strip()
            title = message.get("title", "")
            userid = message.get("userid", "")
            username = message.get("username", "")
            
            get_pve_logger().info(f"{self.pve_plugin_name} 处理PVE消息: '{text}', userid: {userid}")
            
            if not text:
                get_pve_logger().debug(f"{self.pve_plugin_name} PVE消息内容为空，不处理")
                return None
            
            # 严格检查：必须是"/pve"开头（双重验证）
            if not text.startswith("/pve"):
                get_pve_logger().debug(f"{self.pve_plugin_name} 收到非PVE命令，跳过: {text}")
                return None
            
            # 处理带空格或斜杠变体的命令（如"/ pve帮助" -> "/pve帮助"）
            # 移除命令中的空格，统一格式
            normalized_text = text.replace(" ", "").replace("　", "")  # 移除普通空格和全角空格
            
            # 严格匹配：只处理已注册的PVE命令（只支持三个命令）
            # 帮助命令
            if normalized_text == "/pve帮助" or normalized_text == "/pvehelp":
                get_pve_logger().info(f"{self.pve_plugin_name} 匹配到PVE帮助命令")
                return self._pve_get_help_message()
            
            # 状态查询命令
            if normalized_text == "/pve状态":
                get_pve_logger().info(f"{self.pve_plugin_name} 匹配到PVE状态命令")
                return self._pve_get_pve_status()
            
            # 容器状态命令
            if normalized_text == "/pve容器":
                get_pve_logger().info(f"{self.pve_plugin_name} 匹配到PVE容器命令")
                return self._pve_get_container_status()
            
            # 如果以"/pve"开头但不是有效命令，返回帮助信息
            get_pve_logger().info(f"{self.pve_plugin_name} 未知的PVE命令: {text}")
            return {
                "title": f"❓ {self.pve_plugin_name}",
                "text": f"未知命令: {text}\n\n发送 '/pve帮助' 查看可用命令。"
            }
            
        except Exception as e:
            get_pve_logger().error(f"{self.pve_plugin_name} 处理PVE消息时发生错误: {e}")
            return {
                "title": f"❌ {self.pve_plugin_name}",
                "text": f"处理消息时发生错误: {str(e)}"
            }
    
    def _pve_get_help_message(self) -> Dict[str, Any]:
        """获取PVE帮助信息 - 优化样式"""
        title = f"📚 {self.pve_plugin_name} 帮助"
        
        help_text = f"""━━━━━━━━━━━━━━━

🔹 /pve状态 - 查看PVE主机状态信息
🔹 /pve容器 - 查看容器/虚拟机状态
🔹 /pve帮助 - 显示帮助信息
━━━━━━━━━━━━━━━
📦 版本: {self.pve_plugin.plugin_version}
👤 作者: {self.pve_plugin.plugin_author}"""
        
        return {
            "title": title,
            "text": help_text
        }
    
    def _pve_get_pve_status(self) -> Dict[str, Any]:
        """获取PVE主机状态 - 使用缓存优化性能"""
        try:
            pve_plugin = self.pve_plugin
            if not pve_plugin._pve_host or not pve_plugin._ssh_username or (not pve_plugin._ssh_password and not pve_plugin._ssh_key_file):
                return {
                    "title": f"⚠️ {self.pve_plugin_name}",
                    "text": "❌ PVE配置不完整：请先配置PVE主机地址和SSH认证信息。\n\n请在插件配置页面填写完整的PVE连接信息。"
                }
            
            # 使用缓存机制优化性能
            cache_key = "pve_status"
            status = None
            
            # 检查缓存（使用Redis缓存，自动处理过期）
            if hasattr(pve_plugin, '_pve_status_cache') and cache_key in pve_plugin._pve_status_cache:
                get_pve_logger().debug(f"{self.pve_plugin_name} 使用缓存数据: PVE状态")
                status = pve_plugin._pve_status_cache[cache_key]
            else:
                # 缓存未命中，从PVE获取新数据
                get_pve_logger().debug(f"{self.pve_plugin_name} 缓存未命中，从PVE获取新数据")
                status = get_pve_status(
                    pve_plugin._pve_host,
                    pve_plugin._ssh_port,
                    pve_plugin._ssh_username,
                    pve_plugin._ssh_password,
                    pve_plugin._ssh_key_file
                )
                
                # 更新缓存
                if hasattr(pve_plugin, '_pve_status_cache'):
                    pve_plugin._pve_status_cache[cache_key] = status
                    get_pve_logger().debug(f"{self.pve_plugin_name} 已将PVE状态存入缓存")
            
            if not status.get("online"):
                error = status.get("error", "未知错误")
                return {
                    "title": f"❌ {self.pve_plugin_name}",
                    "text": f"❌ PVE主机连接失败\n\n错误信息：{error}\n\n请检查：\n• 主机地址是否正确\n• SSH端口是否开放\n• 认证信息是否正确"
                }
            
            # 格式化状态信息 - 按用户要求的样式设计
            message = "━━━━━━━━━━━━━━━\n"
            message += "📡 主机信息\n"
            message += f"   主机：{status.get('hostname', 'N/A')} ({status.get('ip', 'N/A')})\n"
            message += f"   地址：{pve_plugin._pve_host}\n"
            message += f"   版本：{status.get('pve_version', 'N/A')}\n"
            message += f"   内核：{status.get('kernel', 'N/A')}\n"
            
            # CPU信息
            cpu_usage = status.get('cpu_usage')
            cpu_cores = status.get('cpu_cores', 'N/A')
            cpu_model = status.get('cpu_model', 'N/A')
            cpu_temp = status.get('cpu_temp')
            if cpu_model:
                cpu_model = cpu_model[:45]  # 截断过长的CPU型号
            message += "💻 CPU 信息\n"
            message += f"   型号：{cpu_model}\n"
            message += f"   核心数：{cpu_cores}\n"
            if cpu_usage is not None:
                cpu_emoji = "🟢" if cpu_usage < 50 else "🟡" if cpu_usage < 80 else "🔴"
                message += f"   使用率：{cpu_emoji} {cpu_usage:.1f}%\n"
            if cpu_temp is not None:
                temp_emoji = "🟢" if cpu_temp < 60 else "🟡" if cpu_temp < 80 else "🔴"
                message += f"   温度：{temp_emoji} {cpu_temp:.1f}°C\n"
            
            # 负载信息
            load_avg = status.get('load_avg')
            if load_avg:
                message += f"   负载：{', '.join(load_avg)}\n"
            
            # 内存信息
            mem_usage = status.get('mem_usage')
            mem_total = status.get('mem_total')
            mem_used = status.get('mem_used')
            if mem_total:
                mem_gb = mem_total / 1024
                mem_used_gb = mem_used / 1024 if mem_used else 0
                if mem_usage is not None:
                    mem_emoji = "🟢" if mem_usage < 70 else "🟡" if mem_usage < 90 else "🔴"
                    message += "💾 内存信息\n"
                    message += f"   使用率：{mem_emoji} {mem_usage:.1f}%\n"
                    message += f"   已用：{mem_used_gb:.1f} GB / {mem_gb:.1f} GB\n"
            
            # 交换分区信息
            swap_usage = status.get('swap_usage')
            swap_total = status.get('swap_total')
            swap_used = status.get('swap_used')
            if swap_total and swap_total > 0:
                swap_gb = swap_total / 1024
                swap_used_gb = swap_used / 1024 if swap_used else 0
                if swap_usage is not None:
                    message += f"   交换：{swap_usage:.1f}% ({swap_used_gb:.1f} GB / {swap_gb:.1f} GB)\n"
            
            # 磁盘信息
            disk_usage = status.get('disk_usage')
            disk_total = status.get('disk_total')
            disk_used = status.get('disk_used')
            disk_temp = status.get('disk_temp')
            if disk_total:
                disk_gb = disk_total / 1024
                disk_used_gb = disk_used / 1024 if disk_used else 0
                if disk_usage is not None:
                    disk_emoji = "🟢" if disk_usage < 70 else "🟡" if disk_usage < 90 else "🔴"
                    message += "💿 磁盘信息\n"
                    message += f"   使用率：{disk_emoji} {disk_usage:.1f}%\n"
                    message += f"   已用：{disk_used_gb:.1f} GB / {disk_gb:.1f} GB\n"
                if disk_temp is not None:
                    temp_emoji = "🟢" if disk_temp < 50 else "🟡" if disk_temp < 60 else "🔴"
                    message += f"   温度：{temp_emoji} {disk_temp}°C\n"
            
            message += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"🖥️ {self.pve_plugin_name} PVE主机状态",
                "text": message
            }
            
        except Exception as e:
            get_pve_logger().error(f"{self.pve_plugin_name} 获取PVE状态失败: {e}")
            return {
                "title": f"❌ {self.pve_plugin_name}",
                "text": f"获取PVE主机状态失败: {str(e)}"
            }
    
    def _pve_get_container_status(self) -> Dict[str, Any]:
        """获取容器/虚拟机状态 - 使用缓存优化性能"""
        try:
            pve_plugin = self.pve_plugin
            if not pve_plugin._pve_host or not pve_plugin._ssh_username or (not pve_plugin._ssh_password and not pve_plugin._ssh_key_file):
                return {
                    "title": f"⚠️ {self.pve_plugin_name}",
                    "text": "❌ PVE配置不完整：请先配置PVE主机地址和SSH认证信息。\n\n请在插件配置页面填写完整的PVE连接信息。"
                }
            
            # 使用缓存机制优化性能
            cache_key = "container_status"
            all_vms = None
            
            # 检查缓存（使用Redis缓存，自动处理过期）
            if hasattr(pve_plugin, '_container_status_cache') and cache_key in pve_plugin._container_status_cache:
                get_pve_logger().debug(f"{self.pve_plugin_name} 使用缓存数据: 容器状态")
                all_vms = pve_plugin._container_status_cache[cache_key]
            else:
                # 缓存未命中，从PVE获取新数据
                get_pve_logger().debug(f"{self.pve_plugin_name} 缓存未命中，从PVE获取新数据")
                
                # 获取所有虚拟机
                qemu_list = get_qemu_status(
                    pve_plugin._pve_host,
                    pve_plugin._ssh_port,
                    pve_plugin._ssh_username,
                    pve_plugin._ssh_password,
                    pve_plugin._ssh_key_file
                )
                
                # 获取所有容器
                lxc_list = get_container_status(
                    pve_plugin._pve_host,
                    pve_plugin._ssh_port,
                    pve_plugin._ssh_username,
                    pve_plugin._ssh_password,
                    pve_plugin._ssh_key_file
                )
                
                all_vms = qemu_list + lxc_list
                
                # 更新缓存
                if hasattr(pve_plugin, '_container_status_cache'):
                    pve_plugin._container_status_cache[cache_key] = all_vms
                    get_pve_logger().debug(f"{self.pve_plugin_name} 已将容器状态存入缓存")
            
            if not all_vms:
                return {
                    "title": f"📦 {self.pve_plugin_name} 容器状态",
                    "text": "📭 当前没有虚拟机或容器"
                }
            
            # 统计信息
            total = len(all_vms)
            running = sum(1 for vm in all_vms if vm.get('status', '').lower() == 'running')
            stopped = total - running
            
            message = "━━━━━━━━━━━━━━━\n"
            
            # 按状态分组显示
            running_vms = [vm for vm in all_vms if vm.get('status', '').lower() == 'running']
            stopped_vms = [vm for vm in all_vms if vm.get('status', '').lower() != 'running']
            
            # 运行中的
            if running_vms:
                message += "🟢 运行中\n"
                for vm in sorted(running_vms, key=lambda x: int(x.get('vmid', 0))):
                    vmid = vm.get('vmid', 'N/A')
                    name = vm.get('displayName') or vm.get('name', 'N/A')
                    vmtype = 'QEMU' if vm.get('type') == 'qemu' else 'LXC'
                    cpu = vm.get('cpu', 'N/A')
                    mem = vm.get('mem', 'N/A')
                    uptime = vm.get('uptime', 0)
                    
                    # 格式化运行时间
                    uptime_str = "未知"
                    if uptime and isinstance(uptime, (int, float)) and uptime > 0:
                        days = int(uptime // 86400)
                        hours = int((uptime % 86400) // 3600)
                        minutes = int((uptime % 3600) // 60)
                        if days > 0:
                            uptime_str = f"{days}天{hours}小时"
                        elif hours > 0:
                            uptime_str = f"{hours}小时{minutes}分钟"
                        else:
                            uptime_str = f"{minutes}分钟"
                    
                    message += f"  [{vmtype}] {vmid} - {name}\n"
                    message += f"    CPU: {cpu}  |  内存: {mem}  |  运行时间: {uptime_str}\n"
            
            # 已停止的
            if stopped_vms:
                message += "🔴 已停止\n"
                for vm in sorted(stopped_vms, key=lambda x: int(x.get('vmid', 0))):
                    vmid = vm.get('vmid', 'N/A')
                    name = vm.get('displayName') or vm.get('name', 'N/A')
                    vmtype = 'QEMU' if vm.get('type') == 'qemu' else 'LXC'
                    status = vm.get('status', 'unknown')
                    message += f"  [{vmtype}] {vmid} - {name} ({status})\n"
            
            message += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"📦 {self.pve_plugin_name} 容器状态",
                "text": message
            }
            
        except Exception as e:
            get_pve_logger().error(f"{self.pve_plugin_name} 获取容器状态失败: {e}")
            return {
                "title": f"❌ {self.pve_plugin_name}",
                "text": f"获取容器/虚拟机状态失败: {str(e)}"
            }

