"""表单构建器模块 - LuckyHelper风格UI设计"""
from typing import Tuple, Dict, Any
from app.log import logger


class FormBuilder:
    """表单构建器类"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def build_form(self) -> Tuple[list, dict]:
        """构建配置表单"""
        
        from app.core.config import settings
        version = getattr(settings, "VERSION_FLAG", "v1")
        cron_field_component = "VCronField" if version == "v2" else "VTextField"
        
        # 构建表单结构
        form_structure = [
            {
                'component': 'VForm',
                'content': [
                    # 基础设置卡片
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
                                    'style': 'background: linear-gradient(135deg, #a8edea 0%, #fbc2eb 100%); color: white; border-radius: 12px 12px 0 0;'
                                },
                                'content': [
                                    {'component': 'VIcon', 'props': {'class': 'mr-3', 'size': '28'}, 'text': 'mdi-cog'},
                                    {'component': 'span', 'props': {'style': 'font-size: 18px; font-weight: 600; letter-spacing: 0.5px;'}, 'text': '基础设置'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-5'},
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-4'},
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 3}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'enabled',
                                                    'label': '启用插件',
                                                    'color': 'primary',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 3}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'notify',
                                                    'label': '发送通知', 
                                                    'color': 'info',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 3}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'clear_history',
                                                    'label': '清理历史记录',
                                                    'color': 'info',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 3}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'onlyonce',
                                                    'label': '立即运行一次', 
                                                    'color': 'success',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                                }}
                                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-2'},
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'ikuai_url',
                                                    'label': '爱快路由地址',
                                                    'placeholder': 'http(s)://ip:port',
                                                    'prepend-inner-icon': 'mdi-server-network',
                                                    'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'ikuai_username',
                                                    'label': '用户名',
                                                    'placeholder': '默认为 admin',
                                                    'prepend-inner-icon': 'mdi-account',
                                                    'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'ikuai_password',
                                                    'label': '密码',
                                                    'type': 'password',
                                                    'placeholder': '请输入密码',
                                                    'prepend-inner-icon': 'mdi-lock',
                                                    'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]}
                                        ]
                                    },
                                                {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-2'},
                                                    'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                                {'component': cron_field_component, 'props': {
                                                                        'model': 'cron',
                                                                        'label': '执行周期',
                                                    'placeholder': '0 3 * * *',
                                                    'prepend-inner-icon': 'mdi-clock-outline',
                                                    'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'retry_count',
                                                    'label': '最大重试次数',
                                                    'type': 'number',
                                                    'placeholder': '默认3',
                                                    'prepend-inner-icon': 'mdi-repeat',
                                                    'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'retry_interval',
                                                    'label': '重试间隔(秒)',
                                                    'type': 'number',
                                                    'placeholder': '默认60',
                                                    'prepend-inner-icon': 'mdi-clock-outline',
                                                                        'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                                    }}
                                                                ]}
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # 备份目录设置卡片
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
                                    'style': 'background: linear-gradient(135deg, #c2e9fb 0%, #a1c4fd 100%); color: white; border-radius: 12px 12px 0 0;'
                                },
                                'content': [
                                    {'component': 'VIcon', 'props': {'class': 'mr-3', 'size': '28'}, 'text': 'mdi-folder-multiple'},
                                    {'component': 'span', 'props': {'style': 'font-size: 18px; font-weight: 600; letter-spacing: 0.5px;'}, 'text': '备份目录'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-5'},
                                'content': [
                                    # 本地备份设置
                                    {
                                        'component': 'div',
                                        'props': {
                                            'class': 'mb-6'
                                        },
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {
                                                    'class': 'd-flex align-center mb-4',
                                                    'style': 'padding-bottom: 12px; border-bottom: 1px solid rgba(0,0,0,0.08);'
                                                },
                                                'content': [
                                                    {'component': 'span', 'props': {'style': 'font-size: 14px; font-weight: 500; color: #666; letter-spacing: 0.3px;'}, 'text': '本地备份'}
                                                ]
                                            },
                                    {
                                        'component': 'VRow',
                                                'props': {'class': 'mb-3'},
                                        'content': [
                                                    {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 6}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'enable_local_backup',
                                                    'label': '启用本地备份', 
                                                    'color': 'primary',
                                                            'hide-details': True,
                                                            'density': 'comfortable'
                                                }}
                                            ]},
                                                    {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 6}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'delete_after_backup', 
                                                    'label': '备份后删除路由器上的文件', 
                                                    'color': 'warning',
                                                            'hide-details': True,
                                                            'density': 'comfortable'
                                                }}
                                            ]}
                                        ]
                                    },
                                            {
                                                'component': 'VRow',
                                                'props': {'class': 'mb-3'},
                                                'content': [
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                    {'component': 'VTextField', 'props': {
                                        'model': 'backup_path',
                                                            'label': '本地备份保存路径',
                                                            'placeholder': '如未映射默认即可',
                                        'prepend-inner-icon': 'mdi-folder',
                                        'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                                        }}
                                                    ]},
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                    {'component': 'VTextField', 'props': {
                                        'model': 'keep_backup_num',
                                        'label': '本地备份保留数量', 
                                        'type': 'number',
                                                            'placeholder': '最大保留备份数，默认7份',
                                        'prepend-inner-icon': 'mdi-counter',
                                        'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                                        }}
                                                    ]}
                                                ]
                                            }
                                        ]
                                    },
                                    # WebDAV远程备份设置
                                    {
                                        'component': 'div',
                                        'props': {
                                            'class': 'mb-0'
                                        },
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {
                                                    'class': 'd-flex align-center mb-4',
                                                    'style': 'padding-top: 12px; padding-bottom: 12px; border-bottom: 1px solid rgba(0,0,0,0.08);'
                                                },
                                                'content': [
                                                    {'component': 'span', 'props': {'style': 'font-size: 14px; font-weight: 500; color: #666; letter-spacing: 0.3px;'}, 'text': 'WebDAV远程备份'}
                                                ]
                                            },
                                            {
                                                'component': 'VRow',
                                                'props': {'class': 'mb-3'},
                                                'content': [
                                                    {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 6}, 'content': [
                                    {'component': 'VSwitch', 'props': {
                                        'model': 'enable_webdav', 
                                                            'label': '启用WebDAV远程备份',
                                        'color': 'primary',
                                                            'hide-details': True,
                                                            'density': 'comfortable'
                                                        }}
                                                    ]},
                                                    {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 6}, 'content': [
                                    {'component': 'VTextField', 'props': {
                                        'model': 'webdav_keep_backup_num', 
                                        'label': 'WebDAV备份保留数量', 
                                        'type': 'number', 
                                        'placeholder': '例如: 7', 
                                        'prepend-inner-icon': 'mdi-counter',
                                        'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                    }}
                                                    ]}
                                            ]
                                },
                                                {
                                                'component': 'VRow',
                                                'props': {'class': 'mb-3'},
                                                    'content': [
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'webdav_url', 
                        'label': 'WebDAV服务器地址', 
                        'placeholder': '例如: https://dav.example.com', 
                        'prepend-inner-icon': 'mdi-cloud',
                                                                'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                                        }}
                                                    ]},
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                        {'component': 'VTextField', 'props': {
                                                            'model': 'webdav_path',
                                                            'label': 'WebDAV备份子目录',
                                                            'placeholder': '如/backups/ikuai',
                                                            'prepend-inner-icon': 'mdi-folder-network',
                                                            'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                                        }}
                                                    ]}
                                                ]
                                            },
                                            {
                                                'component': 'VRow',
                                                'content': [
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'webdav_username', 
                                                            'label': 'WebDAV登录名',
                                                            'placeholder': '请输入WebDAV登录名',
                        'prepend-inner-icon': 'mdi-account-key',
                                                                'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                                        }}
                                                    ]},
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'webdav_password', 
                        'label': 'WebDAV密码', 
                        'type': 'password', 
                                        'placeholder': '请输入WebDAV密码', 
                        'prepend-inner-icon': 'mdi-lock-check',
                                                                'variant': 'outlined',
                                                            'density': 'comfortable',
                                                            'hide-details': True
                                                        }}
                                                    ]}
                                                ]
                                            }
                                        ]
                                    }
                        ]
                                                }
                                            ]
                                },
                    # 恢复设置卡片
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
                                    'style': 'background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: white; border-radius: 12px 12px 0 0;'
                                },
                                'content': [
                                    {'component': 'VIcon', 'props': {'class': 'mr-3', 'size': '28'}, 'text': 'mdi-restore'},
                                    {'component': 'span', 'props': {'style': 'font-size: 18px; font-weight: 600; letter-spacing: 0.5px;'}, 'text': '恢复设置'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-5'},
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-4'},
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                {'component': 'VSwitch', 'props': {
                                    'model': 'enable_restore', 
                                    'label': '启用恢复功能', 
                                                    'color': 'primary',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                }}
                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                {'component': 'VSwitch', 'props': {
                                    'model': 'restore_force', 
                                                    'label': '强制恢复（覆盖现有配置）', 
                                                    'color': 'error',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                }}
                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                {'component': 'VSwitch', 'props': {
                                    'model': 'restore_now', 
                                    'label': '立即恢复', 
                                                    'color': 'success',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                }}
                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12}, 'content': [
                    {'component': 'VSelect', 'props': {
                        'model': 'restore_file',
                                        'label': '选择要恢复的备份文件',
                        'items': [
                            {'title': f"{backup['filename']} ({backup['source']})", 'value': f"{backup['source']}|{backup['filename']}"}
                            for backup in self.plugin._get_available_backups()
                        ],
                                        'placeholder': '请选择一个备份文件',
                        'prepend-inner-icon': 'mdi-file-find',
                        'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                            }}
                                            ]}
                                ]
                            }
                                                    ]
                                                }
                                            ]
                                },
                    # IP分组设置卡片
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
                                    'style': 'background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%); color: white; border-radius: 12px 12px 0 0;'
                                },
                                'content': [
                                    {'component': 'VIcon', 'props': {'class': 'mr-3', 'size': '28'}, 'text': 'mdi-network'},
                                    {'component': 'span', 'props': {'style': 'font-size: 18px; font-weight: 600; letter-spacing: 0.5px;'}, 'text': 'IP分组设置'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-5'},
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-4'},
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                {'component': 'VSwitch', 'props': {
                                    'model': 'enable_ip_group', 
                                                    'label': '启用IP分组功能', 
                                                    'color': 'primary',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                }}
                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                {'component': 'VSwitch', 'props': {
                                    'model': 'ip_group_address_pool', 
                                    'label': '绑定地址池', 
                                                    'color': 'info',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                }}
                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'sm': 6, 'md': 4}, 'content': [
                                {'component': 'VSwitch', 'props': {
                                    'model': 'ip_group_sync_now', 
                                                    'label': '立即同步IP分组', 
                                                    'color': 'success',
                                                    'hide-details': True,
                                                    'density': 'comfortable'
                                }}
                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-4'},
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12}, 'content': [
                    {'component': 'VAlert', 'props': {
                        'type': 'warning',
                        'variant': 'tonal',
                                        'text': '警告：由于爱快限制，IP分组无法自动覆盖删除，如需重新同步请先手动删除现有分组。',
                                                    'border': 'start',
                                                    'border-color': 'warning',
                                                    'icon': 'mdi-alert',
                                                    'elevation': 0,
                                                    'rounded': 'lg',
                                                    'density': 'compact'
                                                }}
                                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mb-2'},
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'ip_group_province', 
                        'label': '省份', 
                        'placeholder': '例如: 北京', 
                        'prepend-inner-icon': 'mdi-map-marker',
                                                                        'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'ip_group_city', 
                        'label': '城市', 
                        'placeholder': '例如: 北京', 
                        'prepend-inner-icon': 'mdi-city',
                                                                        'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'ip_group_isp', 
                        'label': '运营商', 
                        'placeholder': '例如: 电信', 
                        'prepend-inner-icon': 'mdi-network',
                                                                        'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12}, 'content': [
                    {'component': 'VTextField', 'props': {
                        'model': 'ip_group_prefix', 
                        'label': '分组前缀', 
                                        'placeholder': '留空则使用"省份_城市_运营商"格式', 
                        'prepend-inner-icon': 'mdi-tag',
                                                                        'variant': 'outlined',
                                                    'density': 'comfortable',
                                                    'hide-details': True
                                                }}
                                            ]}
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # 使用说明卡片
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
                                    {'component': 'VIcon', 'props': {'class': 'mr-3', 'size': '28'}, 'text': 'mdi-information'},
                                    {'component': 'span', 'props': {'style': 'font-size: 18px; font-weight: 600; letter-spacing: 0.5px;'}, 'text': '使用说明'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'props': {'class': 'pa-5'},
                                'content': [
                                    {
                                        'component': 'div',
                                        'props': {'class': 'mb-4'},
                                        'content': [
                                            {
                                                'component': 'div',
                                                'props': {'class': 'd-flex align-center mb-2'},
                                                'content': [
                                                    {'component': 'VIcon', 'props': {'class': 'mr-2', 'color': 'primary'}, 'text': 'mdi-chat'},
                                                    {'component': 'span', 'props': {'class': 'text-h6', 'style': 'color: #667eea;'}, 'text': '交互指令'}
                                                ]
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8 mb-3'},
                                                'text': '在消息渠道中发送以下命令来操作插件：'
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8 mb-2'},
                                                'text': '• /爱快状态 - 查看系统状态'
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8 mb-2'},
                                                'text': '• /爱快线路 - 查看线路监控状态'
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8 mb-2'},
                                                'text': '• /爱快列表 - 查看备份文件列表'
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8 mb-2'},
                                                'text': '• /爱快历史 - 查看备份历史记录'
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8 mb-2'},
                                                'text': '• /爱快备份 - 立即执行备份任务'
                                            },
                                            {
                                                'component': 'div',
                                                'props': {'class': 'ml-8'},
                                                'text': '• /爱快帮助 - 显示帮助信息'
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

        # 默认值
        default_values = {
            "enabled": self.plugin._enabled,
            "notify": self.plugin._notify,
            "cron": self.plugin._cron,
            "onlyonce": self.plugin._onlyonce,
            "retry_count": self.plugin._retry_count,
            "retry_interval": self.plugin._retry_interval,
            "ikuai_url": self.plugin._original_ikuai_url,
            "ikuai_username": self.plugin._ikuai_username,
            "ikuai_password": self.plugin._ikuai_password,
            "enable_local_backup": self.plugin._enable_local_backup,
            "backup_path": self.plugin._backup_path,
            "keep_backup_num": self.plugin._keep_backup_num,
            "notification_style": self.plugin._notification_style,
            "enable_webdav": self.plugin._enable_webdav,
            "webdav_url": self.plugin._webdav_url,
            "webdav_username": self.plugin._webdav_username,
            "webdav_password": self.plugin._webdav_password,
            "webdav_path": self.plugin._webdav_path,
            "webdav_keep_backup_num": self.plugin._webdav_keep_backup_num,
            "clear_history": self.plugin._clear_history,
            "delete_after_backup": self.plugin._delete_after_backup,
            "enable_restore": self.plugin._enable_restore,
            "restore_force": self.plugin._restore_force,
            "restore_file": self.plugin._restore_file,
            "restore_now": self.plugin._restore_now,
            "enable_ip_group": self.plugin._enable_ip_group,
            "ip_group_province": self.plugin._ip_group_province,
            "ip_group_city": self.plugin._ip_group_city,
            "ip_group_isp": self.plugin._ip_group_isp,
            "ip_group_prefix": self.plugin._ip_group_prefix,
            "ip_group_address_pool": self.plugin._ip_group_address_pool,
            "ip_group_sync_now": self.plugin._ip_group_sync_now,
        }

        return form_structure, default_values
