"""仪表盘构建器模块"""
from typing import Any, List, Dict
from app.log import logger


class DashboardBuilder:
    """仪表盘构建器类"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def _get_ikuai_status(self) -> Dict[str, Any]:
        """获取爱快路由器状态信息"""
        try:
            auth_mode = (getattr(self.plugin, '_ikuai_auth_mode', 'auto') or 'auto').lower()
            api_token = (getattr(self.plugin, '_ikuai_api_token', '') or '').strip()
            has_url = bool(self.plugin._ikuai_url)
            has_password = bool(self.plugin._ikuai_password)
            # token 模式：URL + 令牌即可支撑状态/控制面；密码仅下载备份需要
            if auth_mode == "token":
                if not has_url or not api_token:
                    return {"status": "error", "message": "请先配置爱快路由器基本信息（URL、用户名、密码）"}
            elif not has_url or not has_password:
                return {"status": "error", "message": "请先配置爱快路由器基本信息（URL、用户名、密码）"}

            from ..ikuai.client import IkuaiClient
            client = IkuaiClient(
                url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password,
                plugin_name=self.plugin_name,
                auth_mode=auth_mode,
                api_token=api_token
            )
            
            # 尝试登录
            if not client.login():
                return {"status": "error", "message": "无法连接到爱快路由器"}
            
            # 获取系统信息和接口信息
            system_info = client.get_system_info()
            interface_info = client.get_interface_info()
            
            if not system_info:
                return {"status": "error", "message": "无法获取系统信息"}
            
            return {
                "status": "success",
                "system": system_info,
                "interface": interface_info
            }
        except Exception as e:
            logger.error(f"获取爱快状态失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def build_dashboard(self, **kwargs) -> tuple:
        """构建仪表盘 - 返回 (cols, attrs, elements)"""
        # 仪表盘列配置
        cols = {
            "cols": 12, 
            "md": 12
        }
        
        # 仪表盘属性配置：刷新间隔30秒，显示边框
        attrs = {
            "refresh": 30, 
            "border": False
        }
        
        # 获取爱快数据
        ikuai_status = self._get_ikuai_status()
        
        # 格式化函数
        def format_speed(bytes_per_sec):
            """格式化速度显示"""
            if bytes_per_sec < 1024:
                return f"{bytes_per_sec} B/s"
            elif bytes_per_sec < 1024 * 1024:
                return f"{bytes_per_sec / 1024:.2f} KB/s"
            else:
                return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
        
        def format_uptime(seconds):
            """格式化运行时间"""
            if not seconds:
                return "N/A"
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            minutes = (seconds % 3600) // 60
            return f"{days}天{hours}小时{minutes}分钟" if days > 0 else f"{hours}小时{minutes}分钟"
        
        # 提取爱快数据
        system_info = ikuai_status.get("system", {}) if ikuai_status.get("status") == "success" else {}
        interface_info = ikuai_status.get("interface", {}) if ikuai_status.get("status") == "success" else {}
        
        cpu_usage = system_info.get("cpu_usage", 0)
        mem_usage = system_info.get("mem_usage", 0)
        uptime = system_info.get("uptime", 0)
        online_users = system_info.get("online_users", 0)
        connect_num = system_info.get("connect_num", 0)
        upload_speed = system_info.get("upload_speed", 0)
        download_speed = system_info.get("download_speed", 0)
        
        # 确定颜色
        cpu_color = "success" if cpu_usage < 50 else "warning" if cpu_usage < 80 else "error"
        mem_color = "success" if mem_usage < 50 else "warning" if mem_usage < 80 else "error"
        
        # 构建仪表盘元素列表
        elements = []
        
        # 1. 系统概况卡片
        if ikuai_status.get("status") == "success":
            system_card = {
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mb-3'},
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {'class': 'text-h6'},
                        'text': '📊 系统概况'
                    },
                    {
                        'component': 'VDivider',
                        'props': {'class': 'my-2'}
                    },
                    {
                        'component': 'VCardText',
                        'content': [
                            {
                                'component': 'VRow',
                                'content': [
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '3'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-2'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-2'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '🖥️'},
                                                            {'component': 'span', 'props': {'class': 'text-body-2'}, 'text': 'CPU'},
                                                            {'component': 'VSpacer'},
                                                            {'component': 'span', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': f'{cpu_usage:.1f}%'}
                                                        ]
                                                    },
                                                    {
                                                        'component': 'VProgressLinear',
                                                        'props': {
                                                            'model-value': cpu_usage,
                                                            'color': cpu_color,
                                                            'height': '6',
                                                            'rounded': True
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '3'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-2'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-2'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '💾'},
                                                            {'component': 'span', 'props': {'class': 'text-body-2'}, 'text': '内存'},
                                                            {'component': 'VSpacer'},
                                                            {'component': 'span', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': f'{mem_usage:.1f}%'}
                                                        ]
                                                    },
                                                    {
                                                        'component': 'VProgressLinear',
                                                        'props': {
                                                            'model-value': mem_usage,
                                                            'color': mem_color,
                                                            'height': '6',
                                                            'rounded': True
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '3'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-2'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-1'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '👥'},
                                                            {'component': 'span', 'props': {'class': 'text-body-2'}, 'text': '在线设备'}
                                                        ]
                                                    },
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'text-h6 font-weight-bold'}, 
                                                        'text': str(online_users)
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '3'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-2'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-1'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '🔗'},
                                                            {'component': 'span', 'props': {'class': 'text-body-2'}, 'text': '连接数'}
                                                        ]
                                                    },
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'text-h6 font-weight-bold'}, 
                                                        'text': str(connect_num)
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                'component': 'VDivider',
                                'props': {'class': 'my-2'}
                            },
                            {
                                'component': 'VRow',
                                'props': {'justify': 'space-between'},
                                'content': [
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': 'auto'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'd-flex align-center pa-1'},
                                                'content': [
                                                    {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '⏱️'},
                                                    {'component': 'div', 'content': [
                                                        {'component': 'div', 'props': {'class': 'text-caption font-weight-bold'}, 'text': format_uptime(uptime)},
                                                        {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '运行时间'}
                                                    ]}
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': 'auto'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'd-flex align-center pa-1'},
                                                'content': [
                                                    {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '⬆️'},
                                                    {'component': 'div', 'content': [
                                                        {'component': 'div', 'props': {'class': 'text-caption font-weight-bold'}, 'text': format_speed(upload_speed)},
                                                        {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '上传'}
                                                    ]}
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': 'auto'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'd-flex align-center pa-1'},
                                                'content': [
                                                    {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '⬇️'},
                                                    {'component': 'div', 'content': [
                                                        {'component': 'div', 'props': {'class': 'text-caption font-weight-bold'}, 'text': format_speed(download_speed)},
                                                        {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '下载'}
                                                    ]}
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            elements.append(system_card)
        elif self.plugin._ikuai_url:
            # 如果配置了URL但连接失败，显示错误提示
            error_card = {
                'component': 'VAlert',
                'props': {
                    'type': 'warning',
                    'variant': 'tonal',
                    'text': f'⚠️ 无法获取爱快路由器状态: {ikuai_status.get("message", "未知错误")}',
                    'class': 'mb-3'
                }
            }
            elements.append(error_card)
        
        # 2. 线路监控卡片（精简版，适合仪表盘）
        interface_info_card = None
        if interface_info:
            iface_check = interface_info.get("iface_check", [])
            iface_stream = interface_info.get("iface_stream", [])
            snapshoot_lan = interface_info.get("snapshoot_lan", [])
            
            # 创建流量映射
            stream_map = {line.get("interface"): line for line in iface_stream}
            
            if iface_check or snapshoot_lan:
                interface_rows = []
                
                # 处理WAN接口（包含adsl等子接口）
                for line in iface_check[:3]:  # 最多显示3条WAN线路
                    line_name = line.get("interface", "")
                    line_ip = line.get("ip_addr", "未配置")
                    line_result = line.get("result", "")
                    
                    # 确定接口类型
                    if line_name.startswith("adsl") or line_name.startswith("pppoe"):
                        iface_type = "子线路"
                    elif line_name.startswith("wan"):
                        iface_type = "WAN"
                    else:
                        iface_type = "其他"
                    
                    # 判断连接状态
                    if line_result == "success":
                        status_color = "success"
                        status_text = "已连接"
                    else:
                        status_color = "error"
                        status_text = "未连接"
                    
                    # 获取流量统计
                    stream_info = stream_map.get(line_name, {})
                    upload_speed = stream_info.get("upload", 0)
                    download_speed = stream_info.get("download", 0)
                    
                    interface_rows.append({
                        'component': 'tr',
                        'content': [
                            {'component': 'td', 'content': [
                                {'component': 'VChip', 'props': {'color': 'primary', 'size': 'x-small', 'variant': 'outlined'}, 'text': line_name}
                            ]},
                            {'component': 'td', 'text': iface_type},
                            {'component': 'td', 'text': line_ip if line_ip != "未配置" else "--"},
                            {'component': 'td', 'content': [
                                {'component': 'VChip', 'props': {'color': status_color, 'size': 'x-small'}, 'text': status_text}
                            ]},
                            {'component': 'td', 'text': format_speed(upload_speed)},
                            {'component': 'td', 'text': format_speed(download_speed)},
                        ]
                    })
                
                # 处理LAN接口（最多显示2条）
                for lan in snapshoot_lan[:2]:
                    lan_name = lan.get("interface", "")
                    lan_ip = lan.get("ip_addr", "未配置")
                    
                    # 获取流量统计
                    stream_info = stream_map.get(lan_name, {})
                    upload_speed = stream_info.get("upload", 0)
                    download_speed = stream_info.get("download", 0)
                    
                    interface_rows.append({
                        'component': 'tr',
                        'content': [
                            {'component': 'td', 'content': [
                                {'component': 'VChip', 'props': {'color': 'info', 'size': 'x-small', 'variant': 'outlined'}, 'text': lan_name}
                            ]},
                            {'component': 'td', 'text': 'LAN'},
                            {'component': 'td', 'text': lan_ip if lan_ip != "未配置" else "--"},
                            {'component': 'td', 'content': [
                                {'component': 'VChip', 'props': {'color': 'success', 'size': 'x-small'}, 'text': '已启用'}
                            ]},
                            {'component': 'td', 'text': format_speed(upload_speed)},
                            {'component': 'td', 'text': format_speed(download_speed)},
                        ]
                    })
                
                if interface_rows:
                    interface_info_card = {
                        'component': 'VCard',
                        'props': {'variant': 'outlined'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '🌐 线路监控'
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-2'},
                                'content': [
                                    {
                                        'component': 'VTable',
                                        'props': {'hover': True, 'density': 'compact'},
                                        'content': [
                                            {
                                                'component': 'thead',
                                                'content': [
                                                    {
                                                        'component': 'tr',
                                                        'content': [
                                                            {'component': 'th', 'props': {'class': 'text-caption'}, 'text': '线路'},
                                                            {'component': 'th', 'props': {'class': 'text-caption'}, 'text': '类型'},
                                                            {'component': 'th', 'props': {'class': 'text-caption'}, 'text': 'IP地址'},
                                                            {'component': 'th', 'props': {'class': 'text-caption'}, 'text': '状态'},
                                                            {'component': 'th', 'props': {'class': 'text-caption'}, 'text': '上传'},
                                                            {'component': 'th', 'props': {'class': 'text-caption'}, 'text': '下载'}
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'tbody',
                                                'content': interface_rows
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
        
        if interface_info_card:
            elements.append(interface_info_card)
        
        return cols, attrs, elements

