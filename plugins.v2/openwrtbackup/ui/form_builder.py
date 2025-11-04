"""
表单构建模块
负责构建插件配置表单
"""
from typing import Tuple, List, Dict, Any


class FormBuilder:
    """表单构建器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化表单构建器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
    
    def build_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """构建配置表单"""
        default_backup_location_desc = "插件数据目录下的 actual_backups 子目录"
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '⚙️ 基础设置'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 3, 'sm': 3, 'md': 3, 'lg': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件', 'color': 'primary', 'prepend-icon': 'mdi-power'}}]},
                                            {'component': 'VCol', 'props': {'cols': 3, 'sm': 3, 'md': 3, 'lg': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '发送通知', 'color': 'info', 'prepend-icon': 'mdi-bell'}}]},
                                            {'component': 'VCol', 'props': {'cols': 3, 'sm': 3, 'md': 3, 'lg': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'onlyonce', 'label': '立即运行一次', 'color': 'success', 'prepend-icon': 'mdi-play'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_host', 'label': 'OpenWrt地址', 'placeholder': '例如: 192.168.1.1', 'prepend-inner-icon': 'mdi-router-network'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VCronField', 'props': {'model': 'cron', 'label': '执行周期', 'prepend-inner-icon': 'mdi-clock-outline'}}]}
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_username', 'label': '用户名', 'placeholder': '默认为 root', 'prepend-inner-icon': 'mdi-account'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_password', 'label': '密码', 'type': 'password', 'placeholder': '请输入密码', 'prepend-inner-icon': 'mdi-lock'}}]},
                                        ],
                                    },
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '📦 备份设置'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enable_local_backup', 'label': '启用本地备份', 'color': 'primary', 'prepend-icon': 'mdi-folder-home'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 8}, 'content': [{'component': 'VTextField', 'props': {'model': 'backup_path', 'label': '备份文件存储路径', 'placeholder': f'默认为{default_backup_location_desc}', 'prepend-inner-icon': 'mdi-folder'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'keep_backup_num', 'label': '备份保留数量', 'type': 'number', 'placeholder': '例如: 7', 'prepend-inner-icon': 'mdi-counter'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_count', 'label': '最大重试次数', 'type': 'number', 'placeholder': '3', 'prepend-inner-icon': 'mdi-refresh'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_interval', 'label': '重试间隔(秒)', 'type': 'number', 'placeholder': '60', 'prepend-inner-icon': 'mdi-timer'}}]},
                                        ],
                                    },
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '☁️ WebDAV远程备份设置'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enable_webdav', 'label': '启用WebDAV远程备份', 'color': 'primary', 'prepend-icon': 'mdi-cloud-sync'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 8}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_url', 'label': 'WebDAV服务器地址', 'placeholder': '例如: https://dav.example.com', 'prepend-inner-icon': 'mdi-cloud'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_username', 'label': 'WebDAV用户名', 'placeholder': '请输入WebDAV用户名', 'prepend-inner-icon': 'mdi-account-key'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_password', 'label': 'WebDAV密码', 'type': 'password', 'placeholder': '请输入WebDAV密码', 'prepend-inner-icon': 'mdi-lock-check'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_path', 'label': 'WebDAV备份路径', 'placeholder': '例如: /backups/openwrt', 'prepend-inner-icon': 'mdi-folder-network'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_keep_backup_num', 'label': 'WebDAV备份保留数量', 'type': 'number', 'placeholder': '例如: 7', 'prepend-inner-icon': 'mdi-counter'}}]},
                                        ],
                                    },
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VCard',
                        'props': {
                            'variant': 'outlined',
                            'class': 'mb-4',
                            'style': 'border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);'
                        },
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {
                                    'class': 'd-flex align-center pa-4',
                                    'style': 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px 12px 0 0;'
                                },
                                'content': [
                                    {'component': 'VIcon', 'props': {'class': 'mr-3', 'size': '28'}, 'text': 'mdi-message-text'},
                                    {'component': 'span', 'props': {'style': 'font-size: 18px; font-weight: 600; letter-spacing: 0.5px;'}, 'text': '消息交互指令'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-5'},
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-3'},
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'sm': 6, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {
                                                            'class': 'pa-3',
                                                            'style': 'background: rgba(102, 126, 234, 0.08); border-radius: 10px; border: 1px solid rgba(102, 126, 234, 0.2); transition: all 0.3s ease; cursor: pointer;'
                                                        },
                                                        'content': [
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-size: 2rem;'}, 'text': '📊'},
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-family: "Courier New", monospace; font-size: 1.1em; font-weight: 600; color: #667eea; letter-spacing: 0.5px;'}, 'text': '/op状态'},
                                                            {'component': 'div', 'props': {'class': 'text-center text-caption', 'style': 'color: #616161; line-height: 1.6;'}, 'text': '查看OpenWrt路由器系统状态，包括CPU、内存、温度等实时数据'}
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'sm': 6, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {
                                                            'class': 'pa-3',
                                                            'style': 'background: rgba(102, 126, 234, 0.08); border-radius: 10px; border: 1px solid rgba(102, 126, 234, 0.2); transition: all 0.3s ease; cursor: pointer;'
                                                        },
                                                        'content': [
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-size: 2rem;'}, 'text': '📈'},
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-family: "Courier New", monospace; font-size: 1.1em; font-weight: 600; color: #667eea; letter-spacing: 0.5px;'}, 'text': '/op流量'},
                                                            {'component': 'div', 'props': {'class': 'text-center text-caption', 'style': 'color: #616161; line-height: 1.6;'}, 'text': '查看OpenWrt路由器网络流量统计，包括各接口的上下行流量和包数'}
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'sm': 6, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {
                                                            'class': 'pa-3',
                                                            'style': 'background: rgba(102, 126, 234, 0.08); border-radius: 10px; border: 1px solid rgba(102, 126, 234, 0.2); transition: all 0.3s ease; cursor: pointer;'
                                                        },
                                                        'content': [
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-size: 2rem;'}, 'text': '🚀'},
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-family: "Courier New", monospace; font-size: 1.1em; font-weight: 600; color: #667eea; letter-spacing: 0.5px;'}, 'text': '/op备份'},
                                                            {'component': 'div', 'props': {'class': 'text-center text-caption', 'style': 'color: #616161; line-height: 1.6;'}, 'text': '立即执行备份任务，备份完成后会自动通知结果'}
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'sm': 6, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'div',
                                                        'props': {
                                                            'class': 'pa-3',
                                                            'style': 'background: rgba(102, 126, 234, 0.08); border-radius: 10px; border: 1px solid rgba(102, 126, 234, 0.2); transition: all 0.3s ease; cursor: pointer;'
                                                        },
                                                        'content': [
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-size: 2rem;'}, 'text': '📚'},
                                                            {'component': 'div', 'props': {'class': 'text-center mb-2', 'style': 'font-family: "Courier New", monospace; font-size: 1.1em; font-weight: 600; color: #667eea; letter-spacing: 0.5px;'}, 'text': '/op帮助'},
                                                            {'component': 'div', 'props': {'class': 'text-center text-caption', 'style': 'color: #616161; line-height: 1.6;'}, 'text': '显示插件帮助信息，查看所有可用指令'}
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'div',
                                        'props': {
                                            'class': 'd-flex align-center pa-3 mt-3',
                                            'style': 'background: rgba(102, 126, 234, 0.1); border-radius: 8px; border-left: 3px solid #667eea;'
                                        },
                                        'content': [
                                            {'component': 'VIcon', 'props': {'class': 'mr-2', 'size': '16', 'color': 'info'}, 'text': 'mdi-information'},
                                            {'component': 'span', 'props': {'class': 'text-caption', 'style': 'color: #616161;'}, 'text': '在消息渠道（微信、Telegram等）中发送上述指令即可使用交互功能'}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False, "notify": False, "cron": "0 3 * * *", "onlyonce": False,
            "retry_count": 3, "retry_interval": 60, "openwrt_host": "",
            "openwrt_username": "root", "openwrt_password": "",
            "enable_local_backup": True, "backup_path": "", "keep_backup_num": 7,
            "enable_webdav": False, "webdav_url": "", "webdav_username": "",
            "webdav_password": "", "webdav_path": "", "webdav_keep_backup_num": 7
        }

