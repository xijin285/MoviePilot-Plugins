"""页面构建器模块"""
from typing import Any, List, Dict
from datetime import datetime
from app.log import logger


class PageBuilder:
    """页面构建器类"""
    
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
    
    def build_page(self) -> List[dict]:
        """构建状态页面 - 精简设计"""
        # --- 获取爱快数据 ---
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
        
        # === 精简优雅的现代化风格 ===
        
        # 1. 爱快路由器状态卡片 - 简洁美观设计
        if ikuai_status.get("status") == "success":
            ikuai_dashboard_card = {
            'component': 'VCard',
            'props': {'variant': 'outlined', 'class': 'mb-4'},
            'content': [
                {
                    'component': 'VCardTitle',
                    'props': {'class': 'd-flex align-center justify-space-between flex-wrap'},
                    'content': [
                        {
                            'component': 'span',
                            'props': {'class': 'text-h6'},
                            'text': '📊 系统概况'
                        },
                        {
                            'component': 'span',
                            'props': {
                                'class': 'text-caption ml-2',
                                'style': 'color: #ff9800; font-size: 11px; font-weight: 500;'
                            },
                            'text': '⚠️ 提示: 本界面数据可能存在延迟，最终数据请以爱快控制台为准'
                        }
                    ]
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
                                        'props': {'cols': '12', 'sm': '6', 'md': '6'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-3'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-2'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '🖥️'},
                                                            {'component': 'span', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': 'CPU'},
                                                            {'component': 'VSpacer'},
                                                            {'component': 'span', 'props': {'class': 'text-h6 font-weight-bold'}, 'text': f'{cpu_usage:.1f}%'}
                                                        ]
                                                    },
                                                    {
                                                        'component': 'VProgressLinear',
                                                        'props': {
                                                            'model-value': cpu_usage,
                                                            'color': cpu_color,
                                                            'height': '8',
                                                            'rounded': True
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '6'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-3'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-2'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '💾'},
                                                            {'component': 'span', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': '内存'},
                                                            {'component': 'VSpacer'},
                                                            {'component': 'span', 'props': {'class': 'text-h6 font-weight-bold'}, 'text': f'{mem_usage:.1f}%'}
                                                        ]
                                                    },
                                                    {
                                                        'component': 'VProgressLinear',
                                                        'props': {
                                                            'model-value': mem_usage,
                                                            'color': mem_color,
                                                            'height': '8',
                                                            'rounded': True
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '6'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-3'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-2'},
                                                        'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '👥'},
                                                            {'component': 'span', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': '在线设备'},
                                                            {'component': 'VSpacer'},
                                                            {'component': 'span', 'props': {'class': 'text-h6 font-weight-bold'}, 'text': str(online_users)}
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': '12', 'sm': '6', 'md': '6'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'pa-3'},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {'class': 'd-flex align-center mb-2'},
                            'content': [
                                                            {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '🔗'},
                                                            {'component': 'span', 'props': {'class': 'text-body-1 font-weight-bold'}, 'text': '网络连接'},
                                {'component': 'VSpacer'},
                                                            {'component': 'span', 'props': {'class': 'text-h6 font-weight-bold'}, 'text': str(connect_num)}
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                'component': 'VDivider',
                                'props': {'class': 'my-3'}
                            },
                            {
                                'component': 'VRow',
                                'props': {'justify': 'space-between', 'align': 'center'},
                                'content': [
                                    {
                                        'component': 'VCol',
                                        'props': {'cols': 'auto'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'd-flex align-center pa-2'},
                                                'content': [
                                                    {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '⏱️'},
                                                    {'component': 'div', 'content': [
                                                        {'component': 'div', 'props': {'class': 'text-body-2 font-weight-bold'}, 'text': format_uptime(uptime)},
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
                                                'props': {'class': 'd-flex align-center pa-2'},
                                                'content': [
                                                    {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '⬆️'},
                                                    {'component': 'div', 'content': [
                                                        {'component': 'div', 'props': {'class': 'text-body-2 font-weight-bold'}, 'text': format_speed(upload_speed)},
                                                        {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '上传速度'}
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
                                                'props': {'class': 'd-flex align-center pa-2'},
                                                'content': [
                                                    {'component': 'span', 'props': {'class': 'mr-2'}, 'text': '⬇️'},
                                                    {'component': 'div', 'content': [
                                                        {'component': 'div', 'props': {'class': 'text-body-2 font-weight-bold'}, 'text': format_speed(download_speed)},
                                                        {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '下载速度'}
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
        elif self.plugin._ikuai_url:
            ikuai_dashboard_card = {
                'component': 'VAlert',
                'props': {
                    'type': 'warning',
                    'variant': 'tonal',
                    'text': f'⚠️ 无法获取爱快路由器状态: {ikuai_status.get("message", "未知错误")}',
                    'class': 'mb-4'
                }
            }
        
        # 2. 接口信息卡片 - 使用iface_check显示所有线路（包含adsl子接口）
        interface_card = None
        if interface_info:
            iface_check = interface_info.get("iface_check", [])
            iface_stream = interface_info.get("iface_stream", [])
            snapshoot_lan = interface_info.get("snapshoot_lan", [])
            # 创建流量映射
            stream_map = {line.get("interface"): line for line in iface_stream}
            interface_rows = []
            # WAN接口（包含adsl等子接口）
            for line in iface_check:
                line_name = line.get("interface", "")
                line_ip = line.get("ip_addr", "未配置")
                line_gateway = line.get("gateway", "")
                line_status = line.get("errmsg", "")
                line_result = line.get("result", "")
                parent = line.get("parent_interface", "")
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
                connect_count = stream_info.get("connect_num", "--")
                # 确定接口类型显示
                if line_name.startswith("adsl") or line_name.startswith("pppoe"):
                    iface_type = "子线路"
                    sub_line_colors = {
                        "adsl1": "purple",
                        "adsl2": "success",
                        "adsl3": "warning",
                        "adsl4": "error",
                        "adsl5": "info",
                        "pppoe1": "purple",
                        "pppoe2": "success",
                        "pppoe3": "warning",
                        "pppoe4": "error",
                        "pppoe5": "info"
                    }
                    chip_color = sub_line_colors.get(line_name.lower(), "secondary")
                elif line_name.startswith("wan"):
                    iface_type = "WAN"
                    chip_color = "primary"
                else:
                    iface_type = "其他"
                    chip_color = "default"
                interface_rows.append({
                    'component': 'tr',
                    'content': [
                        {'component': 'td', 'content': [
                            {'component': 'VChip', 'props': {'color': chip_color, 'size': 'small', 'variant': 'outlined'}, 'text': line_name}
                        ]},
                        {'component': 'td', 'text': iface_type},
                        {'component': 'td', 'text': line_ip if line_ip != "未配置" else "--"},
                        {'component': 'td', 'text': line_gateway if line_gateway else "--"},
                        {'component': 'td', 'content': [
                            {'component': 'VChip', 'props': {'color': status_color, 'size': 'small'}, 'text': status_text}
                        ]},
                        {'component': 'td', 'text': line_status if line_result == "success" else ""},
                        {'component': 'td', 'text': str(connect_count)},
                        {'component': 'td', 'text': format_speed(upload_speed)},
                        {'component': 'td', 'text': format_speed(download_speed)},
                    ]
                })
            # LAN接口
            for lan in snapshoot_lan:
                lan_name = lan.get("interface", "")
                lan_ip = lan.get("ip_addr", "未配置")
                stream_info = stream_map.get(lan_name, {})
                upload_speed = stream_info.get("upload", 0)
                download_speed = stream_info.get("download", 0)
                connect_count = connect_num if connect_num > 0 else "--"
                interface_rows.append({
                    'component': 'tr',
                    'content': [
                        {'component': 'td', 'content': [
                            {'component': 'VChip', 'props': {'color': 'info', 'size': 'small', 'variant': 'outlined'}, 'text': lan_name}
                        ]},
                        {'component': 'td', 'text': 'LAN'},
                        {'component': 'td', 'text': lan_ip if lan_ip != "未配置" else "--"},
                        {'component': 'td', 'text': lan_ip if lan_ip != "未配置" else "--"},
                        {'component': 'td', 'content': [
                            {'component': 'VChip', 'props': {'color': 'success', 'size': 'small'}, 'text': '已启用'}
                        ]},
                        {'component': 'td', 'text': '线路检测成功'},
                        {'component': 'td', 'text': str(connect_count)},
                        {'component': 'td', 'text': format_speed(upload_speed)},
                        {'component': 'td', 'text': format_speed(download_speed)},
                    ]
                })
            # 友好提示：无详细线路数据时，显示兼容提示卡片
            if not (iface_check or snapshoot_lan):
                interface_card = {
                    'component': 'VCard',
                    'props': {'variant': 'outlined', 'class': 'mb-4'},
                    'content': [
                        {
                            'component': 'VCardTitle',
                            'props': {'class': 'text-h6'},
                            'text': '🌐 线路监控'
                        },
                        {
                            'component': 'VCardText',
                            'content': [
                                {
                                    'component': 'VAlert',
                                    'props': {
                                        'type': 'info',
                                        'variant': 'tonal',
                                        'text': '当前路由器版本不支持详细线路状态监控，仅可显示基础接口信息。',
                                        'class': 'mb-2'
                                    }
                                }
                            ]
                        }
                    ]
                }
            elif interface_rows:
                interface_card = {
                    'component': 'VCard',
                    'props': {'variant': 'outlined', 'class': 'mb-4'},
                    'content': [
                        {
                            'component': 'VCardTitle',
                            'props': {'class': 'text-h6'},
                            'text': '🌐 线路监控'
                        },
                        {
                            'component': 'VCardText',
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
                                                        {'component': 'th', 'text': '线路'},
                                                        {'component': 'th', 'text': '类型'},
                                                        {'component': 'th', 'text': 'IP地址'},
                                                        {'component': 'th', 'text': '网关'},
                                                        {'component': 'th', 'text': '连接状态'},
                                                        {'component': 'th', 'text': '线路状态'},
                                                        {'component': 'th', 'text': '连接数'},
                                                        {'component': 'th', 'text': '上传'},
                                                        {'component': 'th', 'text': '下载'}
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

        # 构建返回列表
        result = []
        if 'ikuai_dashboard_card' in locals():
            result.append(ikuai_dashboard_card)
        if interface_card:
            result.append(interface_card)
        
        # 如果状态页为空，添加错误提示卡片
        if not result:
            error_message = ikuai_status.get("message", "未知错误")
            error_card = {
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mb-4'},
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {'class': 'text-h6 text-error'},
                        'text': '⚠️ 状态获取失败'
                    },
                    {
                        'component': 'VCardText',
                        'text': error_message
                    }
                ]
            }
            result.append(error_card)
        
        return result