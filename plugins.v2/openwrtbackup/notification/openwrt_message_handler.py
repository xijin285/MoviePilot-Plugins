"""
OpenWrt消息处理模块 - 处理微信等消息渠道的命令交互
完全独立的OpenWrt插件消息处理
"""
from datetime import datetime
from typing import Optional, Dict, Any

# 延迟导入logger，避免循环导入
openwrt_logger = None

def get_openwrt_logger():
    """获取logger实例"""
    global openwrt_logger
    if openwrt_logger is None:
        try:
            from app.log import logger as app_logger
            openwrt_logger = app_logger
        except ImportError:
            import logging
            openwrt_logger = logging.getLogger(__name__)
    return openwrt_logger


class OpenWrtMessageHandler:
    """OpenWrt消息处理器类 - 完全独立，专属于OpenWrt插件"""
    
    def __init__(self, openwrt_plugin_instance):
        """
        初始化OpenWrt消息处理器
        :param openwrt_plugin_instance: OpenWrtBackup插件实例
        """
        self.openwrt_plugin = openwrt_plugin_instance
        self.openwrt_plugin_name = openwrt_plugin_instance.plugin_name
    
    def _get_help_message(self) -> Dict[str, Any]:
        """获取OpenWrt帮助信息"""
        title = f"📚 {self.openwrt_plugin_name} 帮助"
        
        help_text = f"""━━━━━━━━━━━━━━━

🔹 /op状态 - 系统状态
🔹 /op流量 - 网络流量
🔹 /op备份 - 立即备份
🔹 /op帮助 - 显示帮助
━━━━━━━━━━━━━━━
📦 版本: {self.openwrt_plugin.plugin_version}
👤 作者: {self.openwrt_plugin.plugin_author}"""
        
        return {
            "title": title,
            "text": help_text
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            from ..openwrt.status import OpenWrtStatus
            
            if not self.openwrt_plugin._openwrt_host or not self.openwrt_plugin._openwrt_username or not self.openwrt_plugin._openwrt_password:
                return {
                    "title": f"⚠️ {self.openwrt_plugin_name}",
                    "text": "❌ 配置不完整：地址、用户名或密码未设置。\n\n请在插件配置页面填写完整的OpenWrt路由器信息。"
                }
            
            status = OpenWrtStatus(self.openwrt_plugin)
            system_info = status.get_system_status()
            
            if not system_info:
                return {
                    "title": f"⚠️ {self.openwrt_plugin_name}",
                    "text": "❌ 无法获取系统信息\n\n请检查：\n• 路由器地址是否正确\n• 网络连接是否正常\n• 用户名密码是否正确"
                }
            
            # 格式化系统信息
            cpu_usage = system_info.get("cpu_usage", 0)
            mem_usage = system_info.get("memory_usage", 0)
            mem_total = system_info.get("memory_total", 0)
            mem_used = system_info.get("memory_used", 0)
            uptime = system_info.get("uptime", "N/A")
            temperature = system_info.get("temperature", "N/A")
            load_5min = system_info.get("load_5min", "N/A")
            version = system_info.get("version", "N/A")
            architecture = system_info.get("architecture", "N/A")
            
            # 格式化内存
            def format_bytes(bytes_value):
                if bytes_value < 1024:
                    return f"{bytes_value} B"
                elif bytes_value < 1024 * 1024:
                    return f"{bytes_value / 1024:.2f} KB"
                elif bytes_value < 1024 * 1024 * 1024:
                    return f"{bytes_value / (1024 * 1024):.2f} MB"
                else:
                    return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"
            
            mem_total_bytes = mem_total * 1024 * 1024
            mem_used_bytes = mem_used * 1024 * 1024
            
            # 确定状态颜色
            cpu_status = "🟢" if cpu_usage < 50 else "🟡" if cpu_usage < 80 else "🔴"
            mem_status = "🟢" if mem_usage < 50 else "🟡" if mem_usage < 80 else "🔴"
            
            message = "━━━━━━━━━━━━━━━\n"
            message += "📊 系统状态\n"
            message += f"🖥️ CPU {cpu_status} {cpu_usage:.1f}%\n"
            message += f"💾 内存 {mem_status} {mem_usage:.1f}%\n"
            message += f"   {format_bytes(mem_used_bytes)} / {format_bytes(mem_total_bytes)}\n"
            message += f"🌡️ 温度 {temperature}\n"
            message += f"⚡ 负载 {load_5min}\n"
            message += f"⏱️ 运行 {uptime}\n"
            message += f"📦 版本 {version}\n"
            message += f"🔧 架构 {architecture}\n"
            message += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"📊 {self.openwrt_plugin_name} 系统状态",
                "text": message
            }
            
        except Exception as e:
            get_openwrt_logger().error(f"{self.openwrt_plugin_name} 获取系统状态失败: {e}")
            return {
                "title": f"❌ {self.openwrt_plugin_name}",
                "text": f"获取系统状态失败: {str(e)}"
            }
    
    def _get_traffic_status(self) -> Dict[str, Any]:
        """获取网络流量状态"""
        try:
            from ..openwrt.status import OpenWrtStatus
            
            if not self.openwrt_plugin._openwrt_host or not self.openwrt_plugin._openwrt_username or not self.openwrt_plugin._openwrt_password:
                return {
                    "title": f"⚠️ {self.openwrt_plugin_name}",
                    "text": "❌ 配置不完整：地址、用户名或密码未设置。"
                }
            
            status = OpenWrtStatus(self.openwrt_plugin)
            traffic_info = status.get_traffic_stats()
            
            if not traffic_info:
                return {
                    "title": f"⚠️ {self.openwrt_plugin_name}",
                    "text": "❌ 无法获取网络流量信息"
                }
            
            # 格式化流量信息
            message = "━━━━━━━━━━━━━━━\n"
            message += "📈 网络流量\n"
            traffic_text = ""
            
            for idx, traffic in enumerate(traffic_info[:10], 1):  # 最多显示10个接口
                interface = traffic.get('interface', 'N/A')
                rx_mb = traffic.get('rx_mb', 0)
                tx_mb = traffic.get('tx_mb', 0)
                rx_packets = traffic.get('rx_packets', 0)
                tx_packets = traffic.get('tx_packets', 0)
                
                traffic_text += f"{idx}. {interface}\n"
                traffic_text += f"   ⬇️ {rx_mb} MB ({rx_packets} 包)\n"
                traffic_text += f"   ⬆️ {tx_mb} MB ({tx_packets} 包)\n\n"
            
            if len(traffic_info) > 10:
                traffic_text += f"（仅显示前10个接口，共{len(traffic_info)}个）"
            else:
                traffic_text = traffic_text.rstrip()
            
            message += traffic_text
            message += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "title": f"📈 {self.openwrt_plugin_name} 网络流量",
                "text": message
            }
            
        except Exception as e:
            get_openwrt_logger().error(f"{self.openwrt_plugin_name} 获取网络流量失败: {e}")
            return {
                "title": f"❌ {self.openwrt_plugin_name}",
                "text": f"获取网络流量失败: {str(e)}"
            }
    
    def _trigger_backup(self) -> Dict[str, Any]:
        """触发立即备份"""
        try:
            # 检查是否已启用
            if not self.openwrt_plugin._enabled:
                return {
                    "title": f"⚠️ {self.openwrt_plugin_name}",
                    "text": "❌ 插件未启用\n\n请在插件配置页面启用插件。"
                }
            
            # 检查配置
            if not self.openwrt_plugin._openwrt_host or not self.openwrt_plugin._openwrt_username or not self.openwrt_plugin._openwrt_password:
                return {
                    "title": f"⚠️ {self.openwrt_plugin_name}",
                    "text": "❌ 配置不完整：地址、用户名或密码未设置。"
                }
            
            # 检查是否有任务正在运行
            if self.openwrt_plugin._lock and self.openwrt_plugin._lock.locked():
                return {
                    "title": f"⏳ {self.openwrt_plugin_name}",
                    "text": "⏳ 备份任务正在进行中，请稍候...\n\n完成后会自动通知您。"
                }
            
            # 触发备份任务
            # 这里需要异步执行，避免阻塞消息回复
            import threading
            backup_thread = threading.Thread(target=self.openwrt_plugin.run_backup_job)
            backup_thread.daemon = True
            backup_thread.start()
            
            return {
                "title": f"🚀 {self.openwrt_plugin_name}",
                "text": "✅ 备份任务已启动\n\n备份完成后会自动通知您结果。"
            }
            
        except Exception as e:
            get_openwrt_logger().error(f"{self.openwrt_plugin_name} 触发备份失败: {e}")
            return {
                "title": f"❌ {self.openwrt_plugin_name}",
                "text": f"触发备份失败: {str(e)}"
            }

