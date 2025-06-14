import hashlib
import json
import os
import re
import time
import threading
from datetime import datetime, timedelta
from typing import Any, List, Dict, Tuple, Optional
from urllib.parse import urljoin, quote, urlparse
from pathlib import Path

import pytz
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType

class ProxmoxVEBackup(_PluginBase):
    # 插件名称
    plugin_name = "ProxmoxVE备份助手"
    # 插件描述
    plugin_desc = "测试版本"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/proxmox.webp"
    # 插件版本
    plugin_version = "99999.99999.99999"
    # 插件作者
    plugin_author = "M.Jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "proxmox_backup_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _max_history_entries: int = 100 # Max number of history entries to keep

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 60
    _notification_style: int = 1
    
    _proxmox_url: str = ""
    _proxmox_token_id: str = ""
    _proxmox_token_secret: str = ""
    _proxmox_node: str = "pve"
    _enable_local_backup: bool = True  # 本地备份开关
    _backup_path: str = ""
    _keep_backup_num: int = 7
    _backup_vmid: str = ""  # 要备份的容器ID，逗号分隔
    _storage_name: str = "local"  # 新增：存储名称

    # WebDAV配置属性
    _enable_webdav: bool = False
    _webdav_url: str = ""
    _webdav_username: str = ""
    _webdav_password: str = ""
    _webdav_path: str = ""
    _webdav_keep_backup_num: int = 7
    _clear_history: bool = False  # 清理历史记录开关

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        self.stop_service()
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._cron = str(config.get("cron", "0 3 * * *"))
            self._onlyonce = bool(config.get("onlyonce", False))
            self._notify = bool(config.get("notify", False))
            self._retry_count = int(config.get("retry_count", 3))
            self._retry_interval = int(config.get("retry_interval", 60))
            self._notification_style = int(config.get("notification_style", 1))
            self._proxmox_url = str(config.get("proxmox_url", "")).rstrip('/')
            self._proxmox_token_id = str(config.get("proxmox_token_id", ""))
            self._proxmox_token_secret = str(config.get("proxmox_token_secret", ""))
            self._proxmox_node = str(config.get("proxmox_node", "pve"))
            self._storage_name = str(config.get("storage_name", "local"))  # 新增
            self._enable_local_backup = bool(config.get("enable_local_backup", True))
            configured_backup_path = str(config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(self.get_data_path() / "actual_backups")
                logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self._backup_path}")
            else:
                self._backup_path = configured_backup_path
            self._keep_backup_num = int(config.get("keep_backup_num", 7))
            self._backup_vmid = str(config.get("backup_vmid", ""))
            self._enable_webdav = bool(config.get("enable_webdav", False))
            self._webdav_url = str(config.get("webdav_url", ""))
            self._webdav_username = str(config.get("webdav_username", ""))
            self._webdav_password = str(config.get("webdav_password", ""))
            self._webdav_path = str(config.get("webdav_path", ""))
            self._webdav_keep_backup_num = int(config.get("webdav_keep_backup_num", 7))
            self._clear_history = bool(config.get("clear_history", False))  # 新增：清理历史记录开关
            self.__update_config()

            # 处理清理历史记录请求
            if self._clear_history:
                self._clear_backup_history()
                self._clear_history = False
                self.__update_config()

        try:
            Path(self._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
             logger.error(f"{self.plugin_name} 创建实际备份目录 {self._backup_path} 失败: {e}")

        if self._enabled or self._onlyonce:
            if self._onlyonce:
                try:
                    if not self._scheduler or not self._scheduler.running:
                         self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    job_name = f"{self.plugin_name}服务_onlyonce"
                    if self._scheduler.get_job(job_name):
                        self._scheduler.remove_job(job_name)
                    logger.info(f"{self.plugin_name} 服务启动，立即运行一次")
                    self._scheduler.add_job(func=self.run_backup_job, trigger='date',
                                         run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                         name=job_name, id=job_name)
                    self._onlyonce = False
                    self.__update_config()
                    if self._scheduler and not self._scheduler.running:
                        self._scheduler.print_jobs()
                        self._scheduler.start()
                except Exception as e:
                    logger.error(f"启动一次性 {self.plugin_name} 任务失败: {str(e)}")
    
    def _load_backup_history(self) -> List[Dict[str, Any]]:
        history = self.get_data('backup_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history

    def _save_backup_history_entry(self, entry: Dict[str, Any]):
        history = self._load_backup_history()
        history.insert(0, entry)
        if len(history) > self._max_history_entries:
            history = history[:self._max_history_entries]
        
        self.save_data('backup_history', history)
        logger.info(f"{self.plugin_name} 已保存备份历史，当前共 {len(history)} 条记录。")

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "proxmox_url": self._proxmox_url,
            "proxmox_token_id": self._proxmox_token_id,
            "proxmox_token_secret": self._proxmox_token_secret,
            "proxmox_node": self._proxmox_node,
            "storage_name": self._storage_name,  # 新增
            "backup_vmid": self._backup_vmid,
            "enable_local_backup": self._enable_local_backup,  # 新增：本地备份开关
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
            "notification_style": self._notification_style,
            "enable_webdav": self._enable_webdav,
            "webdav_url": self._webdav_url,
            "webdav_username": self._webdav_username,
            "webdav_password": self._webdav_password,
            "webdav_path": self._webdav_path,
            "webdav_keep_backup_num": self._webdav_keep_backup_num,
            "clear_history": self._clear_history,  # 新增：清理历史记录开关
        })

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        if self._enabled and self._cron:
            try:
                if str(self._cron).strip().count(" ") == 4:
                    return [{
                        "id": "ProxmoxVEBackupService",
                        "name": f"{self.plugin_name}定时服务",
                        "trigger": CronTrigger.from_crontab(self._cron, timezone=settings.TZ),
                        "func": self.run_backup_job,
                        "kwargs": {}
                    }]
                else:
                    logger.error(f"{self.plugin_name} cron表达式格式错误: {self._cron}")
                    return []
            except Exception as err:
                logger.error(f"{self.plugin_name} 定时任务配置错误：{str(err)}")
                return []
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
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
                                    # 开关行保持不变
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件', 'color': 'primary', 'prepend-icon': 'mdi-power'}}]},
                                            {'component': 'VCol', 'props': {'cols': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '发送通知', 'color': 'info', 'prepend-inner-icon': 'mdi-bell'}}]},
                                            {'component': 'VCol', 'props': {'cols': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'onlyonce', 'label': '立即运行一次', 'color': 'success', 'prepend-inner-icon': 'mdi-play'}}]},
                                            {'component': 'VCol', 'props': {'cols': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'clear_history', 'label': '清理历史记录', 'color': 'warning', 'prepend-inner-icon': 'mdi-delete-sweep'}}]},
                                        ],
                                    },
                                    # 第一行：ProxmoxVE地址 | 执行周期
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'proxmox_url',
                                                    'label': 'ProxmoxVE地址',
                                                    'placeholder': '例如: https://10.0.0.1:8006',
                                                    'prepend-inner-icon': 'mdi-server'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VCronField', 'props': {
                                                    'model': 'cron',
                                                    'label': '执行周期',
                                                    'prepend-inner-icon': 'mdi-clock-outline'
                                                }}
                                            ]}
                                        ]
                                    },
                                    # 第二行：存储名称 | 节点名称
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'storage_name',
                                                    'label': '存储名称',
                                                    'placeholder': '如 local、PVE，默认为 local',
                                                    'prepend-inner-icon': 'mdi-database'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'proxmox_node',
                                                    'label': '节点名称',
                                                    'placeholder': '默认为 pve',
                                                    'prepend-inner-icon': 'mdi-server-network'
                                                }}
                                            ]}
                                        ]
                                    },
                                    # 第三行：API Token ID | API Token Secret
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'proxmox_token_id',
                                                    'label': 'API Token ID',
                                                    'placeholder': '例如: root@pam!backup',
                                                    'prepend-inner-icon': 'mdi-key-variant'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'proxmox_token_secret',
                                                    'label': 'API Token Secret',
                                                    'type': 'password',
                                                    'placeholder': '请输入Token密钥',
                                                    'prepend-inner-icon': 'mdi-key'
                                                }}
                                            ]},
                                            # 指引用户查看API Token获取方法
                                            {'component': 'VCol', 'props': {'cols': 12}, 'content': [
                                                {'component': 'VAlert', 'props': {
                                                    'type': 'info',
                                                    'variant': 'tonal',
                                                    'class': 'mb-2'
                                                },
                                                'content': [
                                                    {'component': 'VRow', 'props': {'no-gutters': True, 'align': 'center'}, 'content': [
                                                        {'component': 'VCol', 'props': {'cols': 'auto'}, 'content': [
                                                            {'component': 'VListItemSubtitle', 'text': '🔑 如何获取 API Token？请点击本插件目录下的 '}
                                                        ]},
                                                        {'component': 'VCol', 'props': {'cols': 'auto'}, 'content': [
                                                            {'component': 'VBtn', 'props': {
                                                                'variant': 'text',
                                                                'size': 'small',
                                                                'color': 'primary',
                                                                'href': 'https://github.com/xijin285/MoviePilot-Plugins/blob/main/plugins.v2/proxmoxvebackup/README.md',
                                                                'target': '_blank'
                                                            }, 'text': 'README.md查看'}
                                                        ]}
                                                    ]}
                                                ]}
                                            ]}
                                        ]
                                    },
                                    # 第四行：要备份的容器ID | 通知样式
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'backup_vmid',
                                                    'label': '要备份的容器ID',
                                                    'placeholder': '多个ID用英文逗号分隔，如102,103，留空则备份全部',
                                                    'prepend-inner-icon': 'mdi-numeric'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VSelect', 'props': {
                                                    'model': 'notification_style',
                                                    'label': '通知样式',
                                                    'items': [
                                                        {'title': '简洁', 'value': 1},
                                                        {'title': '详细', 'value': 2},
                                                        {'title': '箭头风格', 'value': 3},
                                                        {'title': '波浪风格', 'value': 4},
                                                        {'title': '科技风格', 'value': 5},
                                                    ],
                                                    'prepend-inner-icon': 'mdi-message-text'
                                                }}
                                            ]}
                                        ]
                                    },
                                ]
                            }
                        ]
                    },
                    # 本地备份设置卡片
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '💾 本地备份设置'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enable_local_backup', 'label': '启用本地备份', 'color': 'primary', 'prepend-icon': 'mdi-folder'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 8}, 'content': [{'component': 'VTextField', 'props': {'model': 'backup_path', 'label': '备份文件存储路径', 'placeholder': '留空则使用默认路径', 'prepend-inner-icon': 'mdi-folder-open'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'keep_backup_num', 'label': '本地备份保留数量', 'type': 'number', 'placeholder': '例如: 7', 'prepend-inner-icon': 'mdi-counter'}}]},
                                        ],
                                    },
                                ]
                            }
                        ]
                    },
                    # WebDAV远程备份设置卡片
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
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enable_webdav', 'label': '启用WebDAV备份', 'color': 'primary', 'prepend-icon': 'mdi-cloud-upload'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 12}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_url', 'label': 'WebDAV服务器地址', 'placeholder': '例如: https://dav.jianguoyun.com/dav/', 'prepend-inner-icon': 'mdi-cloud'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_username', 'label': 'WebDAV用户名', 'placeholder': '请输入用户名', 'prepend-inner-icon': 'mdi-account'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_password', 'label': 'WebDAV密码', 'type': 'password', 'placeholder': '请输入密码', 'prepend-inner-icon': 'mdi-lock'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 8}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_path', 'label': 'WebDAV备份路径', 'placeholder': '例如: /backups/proxmox', 'prepend-inner-icon': 'mdi-folder-network'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_keep_backup_num', 'label': 'WebDAV备份保留数量', 'type': 'number', 'placeholder': '例如: 7', 'prepend-inner-icon': 'mdi-counter'}}]},
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
                                'text': '📖 插件使用说明'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    # 基础使用说明
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'class': 'mb-2'
                                        },
                                        'content': [
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemTitle', 'text': '🌟 【基础使用说明】'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ① 填写 ProxmoxVE 地址（含端口号，默认8006）'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ② 节点名称默认为 pve（如有多个节点请填写实际名称）'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ③ 存储名称默认为 local（如有自定义请填写实际名称）'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ④ 备份文件存储路径可留空（默认为 actual_backups 子目录）'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ⑤ 设置执行周期（例如：每天凌晨3点执行 0 3 * * *）'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ⑥ 设置本地/云端备份保留数量（旧备份将自动删除）'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ⑦ 可选开启通知，支持多种通知样式'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ⑧ WebDAV远程备份支持坚果云、NextCloud等'}]},
                                            {'component': 'VListItem', 'content': [{'component': 'VListItemSubtitle', 'text': ' ⑨ 启用插件并保存，备份文件以 .tar.gz / .tar.zst 等格式保存'}]},
                                        ]
                                    },
                                    # 关键注意事项高亮
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'warning',
                                            'variant': 'tonal',
                                            'class': 'mb-2',
                                            'text': (
                                                '⚠️ 注意事项：\n\n'
                                                '- Token 权限不足会导致认证失败或部分功能不可用。\n\n'
                                                '- 建议为备份助手单独创建 Token，避免泄露主账户密码。\n\n'
                                                '- 如遇"权限不足"或"认证失败"，请检查 Token 权限和 ID/Secret 填写是否正确。'
                                            )
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "notify": False,
            "cron": "0 3 * * *",
            "onlyonce": False,
            "retry_count": 3,
            "retry_interval": 60,
            "proxmox_url": "",
            "proxmox_token_id": "",
            "proxmox_token_secret": "",
            "proxmox_node": "pve",
            "storage_name": "local",  # 新增
            "backup_vmid": "",
            "enable_local_backup": True,
            "backup_path": "",
            "keep_backup_num": 7,
            "notification_style": 1,
            "enable_webdav": False,
            "webdav_url": "",
            "webdav_username": "",
            "webdav_password": "",
            "webdav_path": "",
            "webdav_keep_backup_num": 7,
            "clear_history": False
        }

    def get_page(self) -> List[dict]:
        history_data = self._load_backup_history()
        
        if not history_data:
            return [
                {
                    'component': 'VAlert',
                    'props': {
                        'type': 'info',
                        'variant': 'tonal',
                        'text': '暂无备份历史记录。当有备份操作后，历史将在此处显示。',
                        'class': 'mb-2'
                    }
                }
            ]
            
        history_rows = []
        for item in history_data:
            timestamp_str = datetime.fromtimestamp(item.get("timestamp", 0)).strftime('%Y-%m-%d %H:%M:%S') if item.get("timestamp") else "N/A"
            status_success = item.get("success", False)
            status_text = "成功" if status_success else "失败"
            status_color = "success" if status_success else "error"
            filename_str = item.get("filename", "N/A")
            message_str = item.get("message", "")

            history_rows.append({
                'component': 'tr',
                'content': [
                    {'component': 'td', 'props': {'class': 'text-caption'}, 'text': timestamp_str},
                    {'component': 'td', 'content': [
                        {'component': 'VChip', 'props': {'color': status_color, 'size': 'small', 'variant': 'outlined'}, 'text': status_text}
                    ]},
                    {'component': 'td', 'text': filename_str},
                    {'component': 'td', 'text': message_str},
                ]
            })

        return [
            {
                "component": "VCard",
                "props": {"variant": "outlined", "class": "mb-4"},
                "content": [
                    {
                        "component": "VCardTitle",
                        "props": {"class": "text-h6"},
                        "text": "📊 ProxmoxVE备份历史"
                    },
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                "component": "VTable",
                                "props": {
                                    "hover": True,
                                    "density": "compact"
                                },
                                "content": [
                                    {
                                        'component': 'thead',
                                        'content': [
                                            {
                                                'component': 'tr',
                                                'content': [
                                                    {'component': 'th', 'text': '时间'},
                                                    {'component': 'th', 'text': '状态'},
                                                    {'component': 'th', 'text': '备份文件名 (.bak)'},
                                                    {'component': 'th', 'text': '消息'}
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'tbody',
                                        'content': history_rows
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    def stop_service(self):
        try:
            if self._scheduler:
                job_name = f"{self.plugin_name}服务_onlyonce"
                if self._scheduler.get_job(job_name):
                    self._scheduler.remove_job(job_name)
                if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                    logger.info(f"等待 {self.plugin_name} 当前任务执行完成...")
                    acquired = self._lock.acquire(timeout=300)
                    if acquired: self._lock.release()
                    else: logger.warning(f"{self.plugin_name} 等待任务超时。")
                if hasattr(self._scheduler, 'remove_all_jobs') and not self._scheduler.get_jobs(jobstore='default'):
                     pass
                elif hasattr(self._scheduler, 'remove_all_jobs'):
                    self._scheduler.remove_all_jobs()
                if hasattr(self._scheduler, 'running') and self._scheduler.running:
                    if not self._scheduler.get_jobs():
                         self._scheduler.shutdown(wait=False)
                         self._scheduler = None
                logger.info(f"{self.plugin_name} 服务已停止或已无任务。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 退出插件失败：{str(e)}")

    def run_backup_job(self):
        if not self._lock: self._lock = threading.Lock()
        if not self._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有任务正在执行，本次调度跳过！")
            return
            
        history_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": None,
            "message": "任务开始"
        }
            
        try:
            self._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            if not self._proxmox_url or not self._proxmox_token_id or not self._proxmox_token_secret:
                error_msg = "配置不完整：URL、Token ID或Token Secret未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return

            if not self._backup_path:
                error_msg = "备份路径未配置且无法设置默认路径。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return

            try:
                Path(self._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"创建本地备份目录 {self._backup_path} 失败: {e}"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            
            for i in range(self._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self._retry_count +1} 次备份尝试...")
                current_try_success, current_try_error_msg, current_try_downloaded_file = self._perform_backup_once()
                
                if current_try_success:
                    success_final = True
                    downloaded_file_final = current_try_downloaded_file
                    error_msg_final = None
                    logger.info(f"{self.plugin_name} 第{i+1}次尝试成功。备份文件: {downloaded_file_final}")
                    break 
                else:
                    error_msg_final = current_try_error_msg
                    logger.warning(f"{self.plugin_name} 第{i+1}次备份尝试失败: {error_msg_final}")
                    if i < self._retry_count:
                        logger.info(f"{self._retry_interval}秒后重试...")
                        time.sleep(self._retry_interval)
                    else:
                        logger.error(f"{self.plugin_name} 所有 {self._retry_count +1} 次尝试均失败。最后错误: {error_msg_final}")
            
            history_entry["success"] = success_final
            history_entry["filename"] = downloaded_file_final
            history_entry["message"] = "备份成功" if success_final else f"备份失败: {error_msg_final}"
            
            self._send_notification(success=success_final, message=history_entry["message"], filename=downloaded_file_final)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
            history_entry["message"] = f"任务执行主流程出错: {str(e)}"
            self._send_notification(success=False, message=history_entry["message"])
        finally:
            self._running = False
            self._save_backup_history_entry(history_entry)
            if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                try: self._lock.release()
                except RuntimeError: pass
            logger.info(f"{self.plugin_name} 任务执行完成。")

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行一次备份操作
        :return: (是否成功, 错误消息, 备份文件名)
        """
        # 准备会话
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        session.headers.update({"User-Agent": browser_user_agent})
        
        # 获取认证令牌
        auth_token = self._login_proxmox(session)
        if not auth_token:
            return False, "登录ProxmoxVE失败，无法获取认证令牌", None
        
        # 设置认证头
        session.headers.update({"Authorization": f"PVEAPIToken={self._proxmox_token_id}={self._proxmox_token_secret}"})
        
        # 生成本地备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_display_and_saved_filename = f"proxmox_backup_{timestamp}.tar.gz"
        
        # 确保备份目录存在
        try:
            Path(self._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_msg = f"创建备份目录失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None
            
        local_filepath = os.path.join(self._backup_path, local_display_and_saved_filename)
        
        # 创建备份
        success, error_msg = self._create_backup_on_proxmox(session)
        if not success:
            return False, error_msg, None
            
        # 下载备份文件
        success, error_msg, downloaded_file = self._download_backup_file(session)
        if not success:
            return False, error_msg, None
            
        # 清理旧的备份文件
        self._cleanup_old_backups()
        
        # 如果启用了WebDAV，上传到WebDAV
        if self._enable_webdav and self._webdav_url:
            webdav_success, webdav_error = self._upload_to_webdav(local_filepath, local_display_and_saved_filename)
            if not webdav_success:
                logger.error(f"{self.plugin_name} WebDAV上传失败: {webdav_error}")
                # 继续执行，不影响主流程
                
            # 清理WebDAV上的旧备份
            self._cleanup_webdav_backups()
            
        return True, None, downloaded_file

    def _login_proxmox(self, session: requests.Session) -> Optional[str]:
        """
        登录到ProxmoxVE并获取认证令牌（API Token方式）
        :param session: requests会话对象
        :return: 认证令牌或None(如果失败)
        """
        if not self._proxmox_token_id or not self._proxmox_token_secret:
            logger.error(f"{self.plugin_name} API Token未配置")
            return None
        session.headers.update({
            'Authorization': f'PVEAPIToken={self._proxmox_token_id}={self._proxmox_token_secret}'
        })
        try:
            test_url = urljoin(self._proxmox_url, "/api2/json/access/ticket")
            response = session.get(test_url, verify=False, timeout=10)
            if response.status_code == 200:
                logger.info(f"{self.plugin_name} API Token认证成功")
                return "TOKEN_AUTH"
            else:
                logger.error(f"{self.plugin_name} API Token认证失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"{self.plugin_name} API Token验证失败: {str(e)}")
            return None

    def _create_backup_on_proxmox(self, session: requests.Session) -> Tuple[bool, Optional[str]]:
        """
        在ProxmoxVE上创建备份
        :param session: requests会话对象
        :return: (是否成功, 错误消息)
        """
        backup_url = urljoin(self._proxmox_url, f"/api2/json/nodes/{self._proxmox_node}/vzdump")
        backup_params = {
            "compress": "gzip",  # 使用gzip压缩
            "mode": "snapshot",  # 使用快照模式
            "remove": "0",  # 不删除旧备份
        }
        # 新增：如果指定了容器ID，则只备份这些，否则备份全部
        if self._backup_vmid.strip():
            backup_params["vmid"] = self._backup_vmid.strip()
        else:
            backup_params["all"] = "1"
        try:
            logger.info(f"{self.plugin_name} 尝试在 {self._proxmox_url} 创建新备份... (参数: {backup_params})")
            response = session.post(backup_url, params=backup_params, verify=False)
            response.raise_for_status()
            result = response.json()
            if result.get("data"):
                return True, None
            else:
                error_msg = "创建备份失败: 服务器返回空数据"
                logger.error(f"{self.plugin_name} {error_msg}")
                return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"创建备份请求失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg
        except json.JSONDecodeError as e:
            error_msg = f"解析创建备份响应失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg
            
    def _download_backup_file(self, session: requests.Session, local_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        从ProxmoxVE下载最新的备份文件
        :param session: requests会话对象
        :param local_filepath: 本地保存路径（已废弃，自动用真实文件名）
        :return: (是否成功, 错误消息, 真实文件名)
        """
        # 获取本地存储内容
        list_url = urljoin(self._proxmox_url, f"/api2/json/nodes/{self._proxmox_node}/storage/{self._storage_name}/content")
        try:
            logger.info(f"{self.plugin_name} 尝试获取本地存储备份文件列表...")
            response = session.get(list_url, verify=False)
            response.raise_for_status()
            result = response.json()
            if not result.get("data"):
                error_msg = "获取本地存储内容失败: 服务器返回空数据"
                logger.error(f"{self.plugin_name} {error_msg}")
                return False, error_msg, None
            # 过滤出vzdump备份文件（支持tar.gz、tar.lzo、tar.zst等）
            backup_files = [
                f for f in result["data"]
                if f.get("content") == "backup" and f.get("volid") and (
                    f.get("volid").endswith(".tar.gz") or f.get("volid").endswith(".tar.lzo") or f.get("volid").endswith(".tar.zst")
                )
            ]
            if not backup_files:
                error_msg = "未找到可下载的vzdump备份文件"
                logger.error(f"{self.plugin_name} {error_msg}")
                return False, error_msg, None
            # 按ctime排序，取最新
            latest_backup = sorted(backup_files, key=lambda x: x.get("ctime", 0), reverse=True)[0]
            backup_volid = latest_backup.get("volid")
            backup_name = latest_backup.get("name") or backup_volid.split(':')[-1]
            if not backup_volid or not backup_name:
                error_msg = "无法获取最新备份文件的volid或文件名"
                logger.error(f"{self.plugin_name} {error_msg}")
                return False, error_msg, None
            # 下载备份文件
            download_url = urljoin(self._proxmox_url, f"/api2/json/nodes/{self._proxmox_node}/storage/{self._storage_name}/content/{backup_volid}")
            logger.info(f"{self.plugin_name} 开始下载备份文件: {backup_name}")
            local_filepath_real = os.path.join(self._backup_path, backup_name)
            # 新增：自动创建所有父目录
            os.makedirs(os.path.dirname(local_filepath_real), exist_ok=True)
            with session.get(download_url, verify=False, stream=True) as response:
                response.raise_for_status()
                with open(local_filepath_real, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return True, None, backup_name
        except requests.exceptions.RequestException as e:
            error_msg = f"下载备份文件失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None
        except (json.JSONDecodeError, KeyError) as e:
            error_msg = f"解析本地存储内容失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None
        except IOError as e:
            error_msg = f"保存备份文件失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None

    def _cleanup_old_backups(self):
        if not self._backup_path or self._keep_backup_num <= 0: return
        try:
            logger.info(f"{self.plugin_name} 开始清理本地备份目录: {self._backup_path}, 保留数量: {self._keep_backup_num} (仅处理 .bak 文件)")
            backup_dir = Path(self._backup_path)
            if not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 本地备份目录 {self._backup_path} 不存在，无需清理。")
                return

            files = []
            for f_path_obj in backup_dir.iterdir():
                if f_path_obj.is_file() and f_path_obj.suffix.lower() == ".bak":
                    try:
                        match = re.search(r'(\d{4}\d{2}\d{2}[_]?\d{2}\d{2}\d{2})', f_path_obj.stem)
                        file_time = None
                        if match:
                            time_str = match.group(1).replace('_','')
                            try:
                                file_time = datetime.strptime(time_str, '%Y%m%d%H%M%S').timestamp()
                            except ValueError:
                                pass 
                        if file_time is None:
                           file_time = f_path_obj.stat().st_mtime
                        files.append({'path': f_path_obj, 'name': f_path_obj.name, 'time': file_time})
                    except Exception as e:
                        logger.error(f"{self.plugin_name} 处理文件 {f_path_obj.name} 时出错: {e}")
                        try:
                            files.append({'path': f_path_obj, 'name': f_path_obj.name, 'time': f_path_obj.stat().st_mtime})
                        except Exception as stat_e:
                            logger.error(f"{self.plugin_name} 无法获取文件状态 {f_path_obj.name}: {stat_e}")

            files.sort(key=lambda x: x['time'], reverse=True)
            
            if len(files) > self._keep_backup_num:
                files_to_delete = files[self._keep_backup_num:]
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个旧 .bak 备份文件需要删除。")
                for f_info in files_to_delete:
                    try:
                        f_info['path'].unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {f_info['name']}")
                    except OSError as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {f_info['name']} 失败: {e}")
            else:
                logger.info(f"{self.plugin_name} 当前 .bak 备份数量 ({len(files)}) 未超过保留限制 ({self._keep_backup_num})，无需清理。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时发生错误: {e}")

    def _create_webdav_directories(self, auth, base_url: str, path: str) -> Tuple[bool, Optional[str]]:
        """递归创建WebDAV目录"""
        try:
            import requests
            from urllib.parse import urljoin

            # 分割路径
            path_parts = [p for p in path.split('/') if p]
            current_path = base_url.rstrip('/')

            # 逐级创建目录
            for part in path_parts:
                current_path = urljoin(current_path + '/', part)
                
                # 检查当前目录是否存在
                check_response = requests.request(
                    'PROPFIND',
                    current_path,
                    auth=auth,
                    headers={
                        'Depth': '0',
                        'User-Agent': 'MoviePilot/1.0',
                        'Connection': 'keep-alive'
                    },
                    timeout=10,
                    verify=False
                )

                if check_response.status_code == 404:
                    # 目录不存在，创建它
                    logger.info(f"{self.plugin_name} 创建WebDAV目录: {current_path}")
                    mkdir_response = requests.request(
                        'MKCOL',
                        current_path,
                        auth=auth,
                        headers={
                            'User-Agent': 'MoviePilot/1.0',
                            'Connection': 'keep-alive'
                        },
                        timeout=10,
                        verify=False
                    )
                    
                    if mkdir_response.status_code not in [200, 201, 204]:
                        return False, f"创建WebDAV目录失败 {current_path}, 状态码: {mkdir_response.status_code}, 响应: {mkdir_response.text}"
                elif check_response.status_code not in [200, 207]:
                    return False, f"检查WebDAV目录失败 {current_path}, 状态码: {check_response.status_code}, 响应: {check_response.text}"

            return True, None
        except Exception as e:
            return False, f"创建WebDAV目录时发生错误: {str(e)}"

    def _upload_to_webdav(self, local_file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
        """上传文件到WebDAV服务器"""
        if not self._enable_webdav or not self._webdav_url:
            return False, "WebDAV未启用或URL未配置"

        try:
            import requests
            from urllib.parse import urljoin, urlparse
            import base64
            from requests.auth import HTTPBasicAuth, HTTPDigestAuth
            import socket

            # 验证WebDAV URL格式
            parsed_url = urlparse(self._webdav_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return False, f"WebDAV URL格式无效: {self._webdav_url}"

            # 检查服务器连接
            try:
                host = parsed_url.netloc.split(':')[0]
                port = int(parsed_url.port or (443 if parsed_url.scheme == 'https' else 80))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                if result != 0:
                    return False, f"无法连接到WebDAV服务器 {host}:{port}，请检查服务器地址和端口是否正确"
            except Exception as e:
                return False, f"检查WebDAV服务器连接时出错: {str(e)}"

            # 构建WebDAV基础URL
            base_url = self._webdav_url.rstrip('/')
            webdav_path = self._webdav_path.lstrip('/')
            upload_url = urljoin(base_url + '/', f"{webdav_path}/{filename}")

            # 准备认证信息
            auth_methods = [
                HTTPBasicAuth(self._webdav_username, self._webdav_password),
                HTTPDigestAuth(self._webdav_username, self._webdav_password),
                (self._webdav_username, self._webdav_password)
            ]

            # 首先尝试检查目录是否存在
            auth_success = False
            last_error = None
            successful_auth = None

            for auth in auth_methods:
                try:
                    logger.info(f"{self.plugin_name} 尝试使用认证方式 {type(auth).__name__} 连接WebDAV服务器...")
                    
                    # 测试连接
                    test_response = requests.request(
                        'PROPFIND',
                        base_url,
                        auth=auth,
                        headers={
                            'Depth': '0',
                            'User-Agent': 'MoviePilot/1.0',
                            'Accept': '*/*',
                            'Connection': 'keep-alive'
                        },
                        timeout=10,
                        verify=False
                    )

                    if test_response.status_code in [200, 207]:
                        logger.info(f"{self.plugin_name} WebDAV认证成功，使用认证方式: {type(auth).__name__}")
                        auth_success = True
                        successful_auth = auth
                        break
                    elif test_response.status_code == 401:
                        last_error = f"认证失败，状态码: 401, 响应: {test_response.text}"
                        continue
                    else:
                        last_error = f"检查WebDAV服务器失败，状态码: {test_response.status_code}, 响应: {test_response.text}"
                        continue

                except requests.exceptions.RequestException as e:
                    last_error = f"连接WebDAV服务器失败: {str(e)}"
                    continue

            if not auth_success:
                return False, f"所有认证方式均失败。最后错误: {last_error}"

            # 创建目录结构
            if webdav_path:
                create_success, create_error = self._create_webdav_directories(successful_auth, base_url, webdav_path)
                if not create_success:
                    return False, create_error

            # 读取文件内容
            try:
                with open(local_file_path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                return False, f"读取本地文件失败: {str(e)}"

            # 准备上传请求
            headers = {
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(len(file_content)),
                'User-Agent': 'MoviePilot/1.0',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }

            # 发送PUT请求上传文件
            try:
                response = requests.put(
                    upload_url,
                    data=file_content,
                    auth=successful_auth,
                    headers=headers,
                    timeout=30,
                    verify=False
                )

                if response.status_code in [200, 201, 204]:
                    logger.info(f"{self.plugin_name} 成功上传文件到WebDAV: {upload_url}")
                    return True, None
                else:
                    error_msg = f"WebDAV上传失败，状态码: {response.status_code}, 响应: {response.text}"
                    if response.status_code == 401:
                        error_msg += "\n可能原因：\n1. 用户名或密码错误\n2. 服务器要求特定的认证方式\n3. 认证信息格式不正确"
                    elif response.status_code == 403:
                        error_msg += "\n可能原因：\n1. 用户没有写入权限\n2. 服务器禁止PUT请求\n3. 认证信息不正确"
                    elif response.status_code == 404:
                        error_msg += "\n可能原因：目标路径不存在"
                    elif response.status_code == 507:
                        error_msg += "\n可能原因：服务器存储空间不足"
                    logger.error(f"{self.plugin_name} {error_msg}")
                    return False, error_msg

            except requests.exceptions.Timeout:
                return False, "WebDAV上传请求超时"
            except requests.exceptions.ConnectionError:
                return False, "无法连接到WebDAV服务器，请检查网络连接和服务器地址"
            except requests.exceptions.RequestException as e:
                return False, f"WebDAV上传请求失败: {str(e)}"

        except Exception as e:
            error_msg = f"WebDAV上传过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

    def _cleanup_webdav_backups(self):
        """清理WebDAV上的旧备份文件"""
        if not self._enable_webdav or not self._webdav_url or self._webdav_keep_backup_num <= 0:
            return

        try:
            import requests
            from urllib.parse import urljoin, quote, urlparse
            from xml.etree import ElementTree

            # 规范化 WebDAV URL
            parsed_url = urlparse(self._webdav_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            webdav_path = self._webdav_path.strip('/')
            
            # 构建完整的WebDAV URL
            full_webdav_url = f"{base_url}/dav/{webdav_path}"
            
            # 发送PROPFIND请求获取文件列表
            headers = {
                'Depth': '1',
                'Content-Type': 'application/xml',
                'Accept': '*/*',
                'User-Agent': 'MoviePilot/1.0'
            }
            
            response = requests.request(
                'PROPFIND',
                full_webdav_url,
                auth=(self._webdav_username, self._webdav_password),
                headers=headers,
                timeout=30,
                verify=False
            )

            if response.status_code != 207:
                logger.error(f"{self.plugin_name} 获取WebDAV文件列表失败，状态码: {response.status_code}")
                return

            # 解析XML响应
            try:
                root = ElementTree.fromstring(response.content)
            except ElementTree.ParseError as e:
                logger.error(f"{self.plugin_name} 解析WebDAV响应XML失败: {str(e)}")
                return

            files = []

            # 遍历所有文件
            for response in root.findall('.//{DAV:}response'):
                href = response.find('.//{DAV:}href')
                if href is None or not href.text:
                    continue

                file_path = href.text
                # 只处理.bak文件
                if not file_path.lower().endswith('.bak'):
                    continue

                # 获取文件修改时间
                propstat = response.find('.//{DAV:}propstat')
                if propstat is None:
                    continue

                prop = propstat.find('.//{DAV:}prop')
                if prop is None:
                    continue

                getlastmodified = prop.find('.//{DAV:}getlastmodified')
                if getlastmodified is None:
                    continue

                try:
                    # 解析时间字符串
                    from email.utils import parsedate_to_datetime
                    file_time = parsedate_to_datetime(getlastmodified.text).timestamp()
                    files.append({
                        'path': file_path,
                        'time': file_time
                    })
                except Exception as e:
                    logger.error(f"{self.plugin_name} 解析WebDAV文件时间失败: {e}")
                    # 如果无法解析时间，使用当前时间
                    files.append({
                        'path': file_path,
                        'time': time.time()
                    })

            # 按时间排序
            files.sort(key=lambda x: x['time'], reverse=True)

            # 删除超出保留数量的旧文件
            if len(files) > self._webdav_keep_backup_num:
                files_to_delete = files[self._webdav_keep_backup_num:]
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个WebDAV旧备份文件需要删除")

                for file_info in files_to_delete:
                    try:
                        # 从href中提取文件名
                        file_path = file_info['path']
                        if file_path.startswith('/'):
                            file_path = file_path[1:]
                        if file_path.startswith('dav/'):
                            file_path = file_path[4:]
                            
                        # 构建源文件的完整URL
                        source_url = f"{base_url}/dav/{file_path}"
                        filename = os.path.basename(file_path)

                        # 删除文件
                        delete_response = requests.delete(
                            source_url,
                            auth=(self._webdav_username, self._webdav_password),
                            headers=headers,
                            timeout=30,
                            verify=False
                        )

                        if delete_response.status_code in [200, 201, 204, 404]:  # 404意味着文件已经不存在
                            logger.info(f"{self.plugin_name} 成功删除WebDAV旧备份文件: {filename}")
                        else:
                            logger.error(f"{self.plugin_name} 删除文件失败: {filename}, 状态码: {delete_response.status_code}")

                    except Exception as e:
                        logger.error(f"{self.plugin_name} 处理WebDAV文件时发生错误: {str(e)}")

        except Exception as e:
            logger.error(f"{self.plugin_name} 清理WebDAV旧备份文件时发生错误: {str(e)}")

    def _clear_backup_history(self):
        """清理备份历史记录"""
        try:
            self.save_data('backup_history', [])
            logger.info(f"{self.plugin_name} 已清理所有备份历史记录")
            if self._notify:
                self._send_notification(
                    success=True,
                    message="已成功清理所有备份历史记录",
                    is_clear_history=True
                )
        except Exception as e:
            error_msg = f"清理备份历史记录失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            if self._notify:
                self._send_notification(
                    success=False,
                    message=error_msg,
                    is_clear_history=True
                )

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None, is_clear_history: bool = False):
        if not self._notify: return
        title = f"🛠️ {self.plugin_name} "
        if is_clear_history:
            title += "清理历史记录"
        else:
            title += "成功" if success else "失败"
        status_emoji = "✅" if success else "❌"
        
        # 根据选择的通知样式设置分隔符和风格
        if self._notification_style == 1:
            # 简约星线
            divider = "★━━━━━━━━━━━━━━━━━━━━━━━★"
            status_prefix = "📌"
            router_prefix = "🌐"
            file_prefix = "📁"
            info_prefix = "ℹ️"
            congrats = "\n🎉 备份任务已顺利完成！"
            error_msg = "\n⚠️ 备份失败，请检查日志了解详情。"
        elif self._notification_style == 2:
            # 方块花边
            divider = "■□■□■□■□■□■□■□■□■□■□■□■□■"
            status_prefix = "🔰"
            router_prefix = "🔹"
            file_prefix = "📂"
            info_prefix = "📝"
            congrats = "\n🎊 太棒了！备份成功保存！"
            error_msg = "\n🚨 警告：备份过程中出现错误！"
        elif self._notification_style == 3:
            # 箭头主题
            divider = "➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤"
            status_prefix = "🔔"
            router_prefix = "📡"
            file_prefix = "💾"
            info_prefix = "📢"
            congrats = "\n🏆 备份任务圆满完成！"
            error_msg = "\n🔥 错误：备份未能完成！"
        elif self._notification_style == 4:
            # 波浪边框
            divider = "≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈"
            status_prefix = "🌊"
            router_prefix = "🌍"
            file_prefix = "📦"
            info_prefix = "💫"
            congrats = "\n🌟 备份任务完美收官！"
            error_msg = "\n💥 备份任务遇到波折！"
        elif self._notification_style == 5:
            # 科技风格
            divider = "▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣"
            status_prefix = "⚡"
            router_prefix = "🔌"
            file_prefix = "💿"
            info_prefix = "📊"
            congrats = "\n🚀 系统备份成功完成！"
            error_msg = "\n⚠️ 系统备份出现异常！"
        else:
            # 默认样式
            divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
            status_prefix = "📣"
            router_prefix = "🔗"
            file_prefix = "📄"
            info_prefix = "📋"
            congrats = "\n✨ 备份已成功完成！"
            error_msg = "\n❗ 备份失败，请检查配置和连接！"
        
        # 失败时的特殊处理 - 添加额外的警告指示
        if not success:
            divider_failure = "❌" + divider[1:-1] + "❌"
            text_content = f"{divider_failure}\n"
        else:
            text_content = f"{divider}\n"
            
        text_content += f"{status_prefix} 状态：{status_emoji} {'备份成功' if success else '备份失败'}\n\n"
        text_content += f"{router_prefix} 路由：{self._proxmox_url}\n"
        if filename:
            text_content += f"{file_prefix} 文件：{filename}\n"
        if message:
            text_content += f"{info_prefix} 详情：{message.strip()}\n"
        
        # 添加底部分隔线和时间戳
        if not success:
            text_content += f"\n{divider_failure}\n"
        else:
            text_content += f"\n{divider}\n"
            
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 根据成功/失败添加不同信息
        if success:
            text_content += congrats
        else:
            text_content += error_msg
        
        try:
            self.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}")