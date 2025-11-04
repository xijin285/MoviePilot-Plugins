"""
页面构建模块
负责构建插件状态页面
"""
import re
from typing import List, Dict, Optional
from app.log import logger

from ..openwrt.status import OpenWrtStatus


class PageBuilder:
    """页面构建器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化页面构建器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.openwrt_status = OpenWrtStatus(plugin_instance)
    
    def _get_openwrt_data(self) -> Dict:
        """获取OpenWrt路由器数据"""
        data = {
            'system_status': None,
            'traffic_stats': None,
            'plugin_services': None,
            'error': None
        }
        
        # 检查插件是否启用
        if not self.plugin._enabled:
            data['error'] = '插件未启用，请先启用插件以查看状态信息'
            return data
        
        # 检查必要的配置项（任何一个为空都返回错误，不显示数据）
        if not self.plugin._openwrt_host or not self.plugin._openwrt_host.strip():
            data['error'] = '未配置OpenWrt地址，请先配置插件'
            return data
        
        if not self.plugin._openwrt_username or not self.plugin._openwrt_username.strip():
            data['error'] = '未配置OpenWrt用户名，请先配置插件'
            return data
        
        if not self.plugin._openwrt_password or not self.plugin._openwrt_password.strip():
            data['error'] = '未配置OpenWrt密码，请先配置插件'
            return data
        
        try:
            # 获取各项数据（内部会自动处理连接）
            data['system_status'] = self.openwrt_status.get_system_status()
            data['traffic_stats'] = self.openwrt_status.get_traffic_stats()
            data['plugin_services'] = self.openwrt_status.get_plugin_services()
            
        except Exception as e:
            logger.error(f"{self.plugin.plugin_name} 获取OpenWrt数据失败: {e}")
            data['error'] = f'获取数据失败: {str(e)}'
        
        return data
    
    def build_page(self) -> List[dict]:
        """构建状态页面"""
        elements = []
        
        # 获取OpenWrt数据
        openwrt_data = self._get_openwrt_data()
        
        # 1. 错误提示或系统状态卡片
        if openwrt_data.get('error'):
            # 如果有错误，只显示错误提示，不显示任何数据
            elements.append({
                'component': 'VAlert',
                'props': {
                    'type': 'warning' if '未配置' in openwrt_data["error"] or '未启用' in openwrt_data["error"] else 'error',
                    'variant': 'tonal',
                    'text': openwrt_data["error"],
                    'class': 'mb-4'
                }
            })
            # 有错误时直接返回，不显示任何数据卡片
            return elements
        else:
            system_status = openwrt_data.get('system_status', {})
            if system_status:
                cpu_usage = system_status.get('cpu_usage', 0)
                mem_usage = system_status.get('memory_usage', 0)
                mem_total = system_status.get('memory_total', 0)
                mem_used = system_status.get('memory_used', 0)
                
                # 计算系统负载百分比（基于5分钟负载，假设1.0为100%）
                load_5min_str = system_status.get('load_5min', '0')
                try:
                    load_5min = float(load_5min_str)
                    # 假设单核系统，负载1.0为100%，多核系统需要除以核心数，这里简化处理
                    load_percentage = min(load_5min * 100, 100)  # 限制最大100%
                except:
                    load_percentage = 0
                
                # 解析温度并计算百分比
                temperature_str = system_status.get('temperature', 'N/A')
                temp_value = 0
                temp_percentage = 0
                if temperature_str != 'N/A':
                    # 尝试提取温度数值（如 "CPU: 37.3°C"）
                    temp_match = re.search(r'(\d+\.?\d*)', temperature_str)
                    if temp_match:
                        temp_value = float(temp_match.group(1))
                        # 假设正常温度范围0-100°C，100°C为100%
                        temp_percentage = min((temp_value / 100) * 100, 100)
                
                cpu_color = 'success' if cpu_usage < 50 else 'warning' if cpu_usage < 80 else 'error'
                mem_color = 'success' if mem_usage < 50 else 'warning' if mem_usage < 80 else 'error'
                temp_color = 'success' if temp_value < 60 else 'warning' if temp_value < 80 else 'error'
                
                # 构建系统状态卡片内容 - 重新设计的布局
                card_content = [
                    # 第一行：核心性能指标 - CPU和内存（大卡片，各占一半）
                    {
                        'component': 'VRow',
                        'props': {'class': 'mb-3'},
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6, 'class': 'mb-3 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'tonal', 'color': cpu_color, 'elevation': '2', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4'},
                                            'content': [
                                                {
                                                    'component': 'div',
                                                    'props': {'class': 'd-flex align-center justify-space-between mb-3'},
                                                    'content': [
                                                        {'component': 'div', 'props': {'class': 'text-body-1 text-medium-emphasis font-weight-medium'}, 'text': 'CPU使用率'},
                                                        {'component': 'div', 'props': {'class': 'text-h4 font-weight-bold'}, 'text': f"{cpu_usage}%"}
                                                    ]
                                                },
                                                {
                                                    'component': 'VProgressLinear',
                                                    'props': {
                                                        'model-value': cpu_usage,
                                                        'color': cpu_color,
                                                        'height': '10',
                                                        'rounded': True,
                                                        'bg-opacity': '0.2'
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6, 'class': 'mb-3 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'tonal', 'color': mem_color, 'elevation': '2', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4'},
                                            'content': [
                                                {
                                                    'component': 'div',
                                                    'props': {'class': 'd-flex align-center justify-space-between mb-3'},
                                                    'content': [
                                                        {'component': 'div', 'props': {'class': 'text-body-1 text-medium-emphasis font-weight-medium'}, 'text': '内存使用率'},
                                                        {'component': 'div', 'props': {'class': 'text-h4 font-weight-bold'}, 'text': f"{mem_usage}%"}
                                                    ]
                                                },
                                                {
                                                    'component': 'VProgressLinear',
                                                    'props': {
                                                        'model-value': mem_usage,
                                                        'color': mem_color,
                                                        'height': '10',
                                                        'rounded': True,
                                                        'bg-opacity': '0.2'
                                                    }
                                                },
                                                {
                                                    'component': 'div',
                                                    'props': {'class': 'text-caption text-medium-emphasis mt-3'},
                                                    'text': f"已用 {mem_used:,}MB / 总计 {mem_total:,}MB"
                                                }
                                            ]
                                        }
                                    ]
                                }]
                            }
                        ]
                    },
                    # 第二行：系统负载、温度、架构、固件版本（4个等宽卡片）
                    {
                        'component': 'VRow',
                        'props': {'class': 'mb-3'},
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'sm': 6, 'md': 3, 'class': 'mb-2 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'outlined', 'elevation': '1', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4 d-flex flex-column justify-center', 'style': {'min-height': '100px'}},
                                            'content': [
                                                {'component': 'div', 'props': {'class': 'text-caption text-medium-emphasis mb-2'}, 'text': '系统负载'},
                                                {'component': 'div', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': f"{system_status.get('load_1min', 'N/A')} / {system_status.get('load_5min', 'N/A')} / {system_status.get('load_15min', 'N/A')}"}
                                            ]
                                        }
                                    ]
                                }]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'sm': 6, 'md': 3, 'class': 'mb-2 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'outlined', 'elevation': '1', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4 d-flex flex-column justify-center', 'style': {'min-height': '100px'}},
                                            'content': [
                                                {'component': 'div', 'props': {'class': 'text-caption text-medium-emphasis mb-2'}, 'text': '温度'},
                                                {'component': 'div', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': temperature_str}
                                            ]
                                        }
                                    ]
                                }]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'sm': 6, 'md': 3, 'class': 'mb-2 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'outlined', 'elevation': '1', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4'},
                                            'content': [
                                                {'component': 'div', 'props': {'class': 'text-caption text-medium-emphasis mb-2'}, 'text': '架构'},
                                                {'component': 'div', 'props': {'class': 'text-body-2 font-weight-medium'}, 'text': system_status.get('architecture', 'N/A')}
                                            ]
                                        }
                                    ]
                                }]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'sm': 6, 'md': 3, 'class': 'mb-2 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'outlined', 'elevation': '1', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4'},
                                            'content': [
                                                {'component': 'div', 'props': {'class': 'text-caption text-medium-emphasis mb-2'}, 'text': '固件版本'},
                                                {'component': 'div', 'props': {'class': 'text-body-2 font-weight-medium'}, 'text': system_status.get('version', 'N/A')}
                                            ]
                                        }
                                    ]
                                }]
                            }
                        ]
                    },
                    # 第三行：内核版本、运行时间（2个等宽卡片，各占一半）
                    {
                        'component': 'VRow',
                        'props': {'class': 'mb-0'},
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6, 'class': 'mb-2 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'outlined', 'elevation': '1', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4'},
                                            'content': [
                                                {'component': 'div', 'props': {'class': 'text-caption text-medium-emphasis mb-2'}, 'text': '内核版本'},
                                                {'component': 'div', 'props': {'class': 'text-body-1 font-weight-medium'}, 'text': system_status.get('kernel', 'N/A')}
                                            ]
                                        }
                                    ]
                                }]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6, 'class': 'mb-2 mb-md-0'},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'outlined', 'elevation': '1', 'class': 'h-100'},
                                    'content': [
                                        {
                                            'component': 'VCardText',
                                            'props': {'class': 'pa-4'},
                                            'content': [
                                                {'component': 'div', 'props': {'class': 'text-caption text-medium-emphasis mb-2'}, 'text': '运行时间'},
                                                {'component': 'div', 'props': {'class': 'text-body-1 font-weight-medium'}, 'text': system_status.get('uptime', 'N/A')}
                                            ]
                                        }
                                    ]
                                }]
                            }
                        ]
                    }
                ]
                
                elements.append({
                    'component': 'VCard',
                    'props': {'variant': 'outlined', 'class': 'mb-4', 'elevation': '2'},
                    'content': [
                        {
                            'component': 'VCardTitle',
                            'props': {'class': 'text-h6 pa-4 pb-2'},
                            'text': '💻 系统状态'
                        },
                        {
                            'component': 'VCardText',
                            'props': {'class': 'pa-4'},
                            'content': card_content
                        }
                    ]
                })
        
        # 2. 网络流量卡片（按设备显示）
        traffic_stats = openwrt_data.get('traffic_stats', [])
        if traffic_stats:
            traffic_rows = []
            for traffic in traffic_stats:
                device_name = traffic.get('interface', 'N/A')
                mac = traffic.get('mac', '')
                ip = traffic.get('ip', '')
                iface = traffic.get('iface', '')
                
                # 显示设备信息：IP或MAC地址，如果有接口信息也显示
                device_display = device_name
                if iface:
                    device_display = f"{device_name}\n({iface})" if device_name != iface else device_name
                
                traffic_rows.append({
                    'component': 'tr',
                    'content': [
                        {'component': 'td', 'props': {'class': 'text-body-2'}, 'text': device_display},
                        {'component': 'td', 'text': f"{traffic.get('rx_mb', 0)} MB"},
                        {'component': 'td', 'text': f"{traffic.get('rx_packets', 0)}"},
                        {'component': 'td', 'text': f"{traffic.get('tx_mb', 0)} MB"},
                        {'component': 'td', 'text': f"{traffic.get('tx_packets', 0)}"}
                    ]
                })
            
            elements.append({
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mb-4'},
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {'class': 'text-h6'},
                        'text': '📊 网络流量'
                    },
                    {
                        'component': 'VCardText',
                        'content': [{
                            'component': 'VTable',
                            'props': {'hover': True, 'density': 'compact'},
                            'content': [
                                {
                                    'component': 'thead',
                                    'content': [{
                                        'component': 'tr',
                                        'content': [
                                            {'component': 'th', 'text': '设备'},
                                            {'component': 'th', 'text': '下行流量'},
                                            {'component': 'th', 'text': '下行包数'},
                                            {'component': 'th', 'text': '上行流量'},
                                            {'component': 'th', 'text': '上行包数'}
                                        ]
                                    }]
                                },
                                {
                                    'component': 'tbody',
                                    'content': traffic_rows
                                }
                            ]
                        }]
                    }
                ]
            })
        
        # 4. 插件服务状态卡片
        plugin_services = openwrt_data.get('plugin_services', [])
        if plugin_services:
            plugin_rows = []
            for plugin in plugin_services:
                status_color = 'success' if plugin.get('running') else 'error'
                plugin_rows.append({
                    'component': 'tr',
                    'content': [
                        {'component': 'td', 'text': plugin.get('name', 'N/A')},
                        {'component': 'td', 'content': [{
                            'component': 'VChip',
                            'props': {'color': status_color, 'size': 'small', 'variant': 'outlined'},
                            'text': plugin.get('status', 'N/A')
                        }]},
                        {'component': 'td', 'content': [{
                            'component': 'VChip',
                            'props': {'color': 'success' if plugin.get('enabled') else 'default', 'size': 'small', 'variant': 'text'},
                            'text': '已启用' if plugin.get('enabled') else '未启用'
                        }]}
                    ]
                })
            
            elements.append({
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mb-4'},
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {'class': 'text-h6'},
                        'text': '🔌 插件服务'
                    },
                    {
                        'component': 'VCardText',
                        'content': [{
                            'component': 'VTable',
                            'props': {'hover': True, 'density': 'compact'},
                            'content': [
                                {
                                    'component': 'thead',
                                    'content': [{
                                        'component': 'tr',
                                        'content': [
                                            {'component': 'th', 'text': '插件名称'},
                                            {'component': 'th', 'text': '运行状态'},
                                            {'component': 'th', 'text': '启用状态'}
                                        ]
                                    }]
                                },
                                {
                                    'component': 'tbody',
                                    'content': plugin_rows
                                }
                            ]
                        }]
                    }
                ]
            })
        
        return elements if elements else [{
            'component': 'VAlert',
            'props': {
                'type': 'info',
                'variant': 'tonal',
                'text': '请先配置OpenWrt连接信息以查看系统状态。',
                'class': 'mb-2'
            }
        }]
