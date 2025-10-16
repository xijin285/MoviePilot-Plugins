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

from .ip_group_manager import IPGroupManager

class IkuaiRouterBackup(_PluginBase):
    # 插件名称
    plugin_name = "爱快路由时光机"
    # 插件描述
    plugin_desc = "轻松配置您的爱快路由，让路由管理更简单"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/ikuai.png"
    # 插件版本
    plugin_version = "1.3.1"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "ikuai_backup_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _max_history_entries: int = 100 # Max number of history entries to keep
    _restore_lock: Optional[threading.Lock] = None  # 恢复操作锁
    _max_restore_history_entries: int = 50  # 恢复历史记录最大数量
    _global_task_lock: Optional[threading.Lock] = None  # 全局任务锁，协调备份和恢复任务
    _backup_activity: str = "空闲"  # 备份活动状态
    _restore_activity: str = "空闲"  # 恢复活动状态

    # IP分组配置属性
    _enable_ip_group: bool = False  # 启用IP分组功能
    _ip_group_province: str = ""  # 省份
    _ip_group_city: str = ""  # 城市
    _ip_group_isp: str = ""  # 运营商
    _ip_group_prefix: str = ""  # 分组前缀
    _ip_group_address_pool: bool = False  # 是否绑定地址池
    _ip_group_sync_now: bool = False  # 立即同步开关
    _ip_group_activity: str = "空闲"  # IP分组活动状态

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 60
    _notification_style: int = 0
    
    _ikuai_url: str = ""
    _ikuai_username: str = "admin"
    _ikuai_password: str = ""
    _enable_local_backup: bool = True  # 新增：本地备份开关
    _backup_path: str = ""
    _keep_backup_num: int = 7

    # WebDAV配置属性
    _enable_webdav: bool = False
    _webdav_url: str = ""
    _webdav_username: str = ""
    _webdav_password: str = ""
    _webdav_path: str = ""
    _webdav_keep_backup_num: int = 7
    _clear_history: bool = False  # 新增：清理历史记录开关
    _delete_after_backup: bool = False # 新增：备份后删除路由器文件开关

    # 恢复配置
    _enable_restore: bool = False  # 启用恢复功能
    _restore_force: bool = False  # 强制恢复（覆盖现有配置）
    _restore_file: str = ""  # 要恢复的文件
    _restore_now: bool = False  # 立即恢复开关

    _original_ikuai_url: str = ""

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
            self._notification_style = int(config.get("notification_style", 0))

            # 处理ikuai_url，保留原始值用于显示，处理后的值用于后端请求
            self._original_ikuai_url = str(config.get("ikuai_url", "")).strip()
            self._ikuai_url = self._get_processed_ikuai_url(self._original_ikuai_url)

            self._ikuai_username = str(config.get("ikuai_username", "admin"))
            self._ikuai_password = str(config.get("ikuai_password", ""))
            self._enable_local_backup = bool(config.get("enable_local_backup", True))
            configured_backup_path = str(config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(self.get_data_path() / "actual_backups")
                logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self._backup_path}")
            else:
                self._backup_path = configured_backup_path
            self._keep_backup_num = int(config.get("keep_backup_num", 7))
            self._enable_webdav = bool(config.get("enable_webdav", False))
            self._webdav_url = str(config.get("webdav_url", ""))
            self._webdav_username = str(config.get("webdav_username", ""))
            self._webdav_password = str(config.get("webdav_password", ""))
            self._webdav_path = str(config.get("webdav_path", ""))
            self._webdav_keep_backup_num = int(config.get("webdav_keep_backup_num", 7))
            self._clear_history = bool(config.get("clear_history", False))  # 新增：清理历史记录开关
            self._delete_after_backup = bool(config.get("delete_after_backup", False))
            self._enable_restore = bool(config.get("enable_restore", False))
            self._restore_force = bool(config.get("restore_force", False))
            self._restore_file = str(config.get("restore_file", ""))
            self._restore_now = bool(config.get("restore_now", False))
            
            # IP分组配置
            self._enable_ip_group = bool(config.get("enable_ip_group", False))
            self._ip_group_province = str(config.get("ip_group_province", ""))
            self._ip_group_city = str(config.get("ip_group_city", ""))
            self._ip_group_isp = str(config.get("ip_group_isp", ""))
            self._ip_group_prefix = str(config.get("ip_group_prefix", ""))
            self._ip_group_address_pool = bool(config.get("ip_group_address_pool", False))
            self._ip_group_sync_now = bool(config.get("ip_group_sync_now", False))
            
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
    
        # 处理IP分组同步任务
        if self._ip_group_sync_now:
            try:
                if not self._scheduler or not self._scheduler.running:
                     self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                job_name = f"{self.plugin_name}IP分组同步_onlyonce"
                if self._scheduler.get_job(job_name):
                    self._scheduler.remove_job(job_name)
                logger.info(f"{self.plugin_name} IP分组同步服务启动，立即运行一次")
                self._scheduler.add_job(func=self.run_ip_group_sync_job, trigger='date',
                                     run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                     name=job_name, id=job_name)
                self._ip_group_sync_now = False
                self.__update_config()
                if self._scheduler and not self._scheduler.running:
                    self._scheduler.print_jobs()
                    self._scheduler.start()
            except Exception as e:
                logger.error(f"启动一次性 {self.plugin_name} IP分组同步任务失败: {str(e)}")

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
            "ikuai_url": self._original_ikuai_url,
            "ikuai_username": self._ikuai_username,
            "ikuai_password": self._ikuai_password,
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
            "delete_after_backup": self._delete_after_backup,
            "enable_restore": self._enable_restore,
            "restore_force": self._restore_force,
            "restore_file": self._restore_file,
            "restore_now": self._restore_now,
            # IP分组配置
            "enable_ip_group": self._enable_ip_group,
            "ip_group_province": self._ip_group_province,
            "ip_group_city": self._ip_group_city,
            "ip_group_isp": self._ip_group_isp,
            "ip_group_prefix": self._ip_group_prefix,
            "ip_group_address_pool": self._ip_group_address_pool,
            "ip_group_sync_now": self._ip_group_sync_now,
        })

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """注册插件API"""
        return [
            {
                "path": "/backup",
                "endpoint": self._api_backup,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行备份"
            },
            {
                "path": "/restore",
                "endpoint": self._api_restore_backup,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行恢复"
            },
            {
                "path": "/sync_ip_groups",
                "endpoint": self._api_sync_ip_groups,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "同步IP分组"
            },
            {
                "path": "/get_ip_blocks_info",
                "endpoint": self._api_get_ip_blocks_info,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取IP段信息"
            },
            {
                "path": "/get_available_options",
                "endpoint": self._api_get_available_options,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取可用选项"
            },
            {
                "path": "/get_cities_by_province",
                "endpoint": self._api_get_cities_by_province,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "根据省份获取城市列表"
            },
            {
                "path": "/test_ip_group",
                "endpoint": self._api_test_ip_group,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "测试IP分组创建"
            }
        ]

    def get_service(self) -> List[Dict[str, Any]]:
        if self._enabled and self._cron:
            try:
                if str(self._cron).strip().count(" ") == 4:
                    return [{
                        "id": "IkuaiRouterBackupService",
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
        # 基础设置卡片（独立显示）
        basic_settings_card = {
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
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VSwitch', 'props': {
                                        'model': 'enabled', 
                                        'label': '启用插件', 
                                        'color': 'primary', 
                                        'prepend-icon': 'mdi-power'
                                    }}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VSwitch', 'props': {
                                        'model': 'notify', 
                                        'label': '发送通知', 
                                        'color': 'info', 
                                        'prepend-icon': 'mdi-bell'
                                    }}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VSwitch', 'props': {
                                        'model': 'onlyonce', 
                                        'label': '立即运行一次', 
                                        'color': 'success', 
                                        'prepend-icon': 'mdi-play'
                                    }}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VSwitch', 'props': {
                                        'model': 'clear_history', 
                                        'label': '清理历史记录', 
                                        'color': 'warning', 
                                        'prepend-icon': 'mdi-delete-sweep'
                                    }}
                                ]},
                            ],
                        },
                        {
                            'component': 'VRow',
                            'content': [
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VTextField', 'props': {
                                        'model': 'retry_count', 
                                        'label': '最大重试次数', 
                                        'type': 'number', 
                                        'placeholder': '3', 
                                        'prepend-inner-icon': 'mdi-refresh'
                                    }}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VTextField', 'props': {
                                        'model': 'retry_interval', 
                                        'label': '重试间隔(秒)', 
                                        'type': 'number', 
                                        'placeholder': '60', 
                                        'prepend-inner-icon': 'mdi-timer'
                                    }}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VCronField', 'props': {
                                        'model': 'cron', 
                                        'label': '执行周期', 
                                        'prepend-inner-icon': 'mdi-clock-outline'
                                    }}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [
                                    {'component': 'VSelect', 'props': {
                                        'model': 'notification_style', 
                                        'label': '通知样式', 
                                        'items': [
                                            {'title': '默认样式', 'value': 0},
                                            {'title': '简约星线', 'value': 1}, 
                                            {'title': '方块花边', 'value': 2}, 
                                            {'title': '箭头主题', 'value': 3}, 
                                            {'title': '波浪边框', 'value': 4}, 
                                            {'title': '科技风格', 'value': 5}
                                        ], 
                                        'prepend-inner-icon': 'mdi-palette'
                                    }}
                                ]},
                            ],
                        },
                    ]
                }
            ]
        }

        # 定义选项卡内容
        tabs = {
            'connection': {
                'icon': 'mdi-router-network', 'title': '连接设置', 'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '🔌 爱快路由连接'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ikuai_url', 
                                        'label': '爱快路由地址', 
                                        'placeholder': '例如: http://10.0.0.1', 
                                        'prepend-inner-icon': 'mdi-web'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ikuai_username', 
                                        'label': '用户名', 
                                        'placeholder': '默认为 admin', 
                                        'prepend-inner-icon': 'mdi-account', 
                                        'class': 'mt-4'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ikuai_password', 
                                        'label': '密码', 
                                        'type': 'password', 
                                        'placeholder': '请输入密码', 
                                        'prepend-inner-icon': 'mdi-lock', 
                                        'class': 'mt-4'
                                    }},
                                ]
                            }
                        ]
                    }
                ]
            },
            'webdav': {
                'icon': 'mdi-cloud', 'title': 'WebDAV设置', 'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '☁️ WebDAV远程备份'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {'component': 'VSwitch', 'props': {
                                        'model': 'enable_webdav', 
                                        'label': '启用WebDAV远程备份', 
                                        'color': 'primary'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'webdav_url', 
                                        'label': 'WebDAV服务器地址', 
                                        'placeholder': '例如: https://dav.example.com', 
                                        'prepend-inner-icon': 'mdi-cloud', 
                                        'class': 'mt-4'
                                    }},
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'webdav_username', 
                                                    'label': 'WebDAV用户名', 
                                                    'placeholder': '请输入WebDAV用户名', 
                                                    'prepend-inner-icon': 'mdi-account-key'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'webdav_password', 
                                                    'label': 'WebDAV密码', 
                                                    'type': 'password', 
                                                    'placeholder': '请输入WebDAV密码', 
                                                    'prepend-inner-icon': 'mdi-lock-check'
                                                }}
                                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'webdav_path', 
                                                    'label': 'WebDAV备份路径', 
                                                    'placeholder': '例如: /backups/ikuai', 
                                                    'prepend-inner-icon': 'mdi-folder-network'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VTextField', 'props': {
                                                    'model': 'webdav_keep_backup_num', 
                                                    'label': 'WebDAV备份保留数量', 
                                                    'type': 'number', 
                                                    'placeholder': '例如: 7', 
                                                    'prepend-inner-icon': 'mdi-counter'
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
            'backup': {
                'icon': 'mdi-backup-restore', 'title': '备份设置', 'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '📦 本地备份'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'enable_local_backup', 
                                                    'label': '启用本地备份', 
                                                    'color': 'primary'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'delete_after_backup', 
                                                    'label': '备份后删除路由器上的文件', 
                                                    'color': 'warning'
                                                }}
                                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'warning',
                                            'variant': 'tonal',
                                            'text': '警告：启用此选项将在备份成功后从您的爱快路由器上永久删除该备份文件，请谨慎操作！',
                                            'density': 'compact',
                                            'class': 'mt-2'
                                        }
                                    },
                                    {'component': 'VTextField', 'props': {
                                        'model': 'backup_path', 
                                        'label': '备份文件存储路径', 
                                        'placeholder': '默认为插件数据目录下的 actual_backups 子目录', 
                                        'prepend-inner-icon': 'mdi-folder', 
                                        'class': 'mt-4'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'keep_backup_num', 
                                        'label': '备份保留数量', 
                                        'type': 'number', 
                                        'placeholder': '例如: 7', 
                                        'prepend-inner-icon': 'mdi-counter', 
                                        'class': 'mt-4'
                                    }},
                                ]
                            }
                        ]
                    }
                ]
            },
            'restore': {
                'icon': 'mdi-restore', 'title': '恢复设置', 'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '🔄 恢复功能'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'enable_restore', 
                                                    'label': '启用恢复功能', 
                                                    'color': 'primary'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'restore_force', 
                                                    'label': '强制恢复（覆盖现有配置）', 
                                                    'color': 'error'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'restore_now', 
                                                    'label': '立即恢复', 
                                                    'color': 'success', 
                                                    'prepend-icon': 'mdi-play-circle'
                                                }}
                                            ]}
                                        ]
                                    },
                                    {'component': 'VSelect', 'props': {
                                        'model': 'restore_file',
                                        'label': '选择要恢复的备份文件',
                                        'items': [
                                            {'title': f"{backup['filename']} ({backup['source']})", 'value': f"{backup['source']}|{backup['filename']}"}
                                            for backup in self._get_available_backups()
                                        ],
                                        'placeholder': '请选择一个备份文件',
                                        'prepend-inner-icon': 'mdi-file-find',
                                        'class': 'mt-4'
                                    }},
                                ]
                            }
                        ]
                    }
                ]
            },
            'ip_group': {
                'icon': 'mdi-ip-network', 'title': 'IP分组设置', 'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined', 'class': 'mb-4'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '🌐 IP分组管理'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'enable_ip_group', 
                                                    'label': '启用IP分组功能', 
                                                    'color': 'primary'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'ip_group_address_pool', 
                                                    'label': '绑定地址池', 
                                                    'color': 'info'
                                                }}
                                            ]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [
                                                {'component': 'VSwitch', 'props': {
                                                    'model': 'ip_group_sync_now', 
                                                    'label': '立即同步IP分组', 
                                                    'color': 'success', 
                                                    'prepend-icon': 'mdi-sync'
                                                }}
                                            ]}
                                        ]
                                    },
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'warning',
                                            'variant': 'tonal',
                                            'text': '警告：由于爱快限制，IP分组无法自动覆盖删除，如需重新同步请先手动删除现有分组。',
                                            'density': 'compact',
                                            'class': 'mt-2'
                                        }
                                    },
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ip_group_province', 
                                        'label': '省份', 
                                        'placeholder': '例如: 北京', 
                                        'prepend-inner-icon': 'mdi-map-marker',
                                        'class': 'mt-4'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ip_group_city', 
                                        'label': '城市', 
                                        'placeholder': '例如: 北京', 
                                        'prepend-inner-icon': 'mdi-city',
                                        'class': 'mt-4'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ip_group_isp', 
                                        'label': '运营商', 
                                        'placeholder': '例如: 电信', 
                                        'prepend-inner-icon': 'mdi-network',
                                        'class': 'mt-4'
                                    }},
                                    {'component': 'VTextField', 'props': {
                                        'model': 'ip_group_prefix', 
                                        'label': '分组前缀', 
                                        'placeholder': '留空则使用"省份_城市_运营商"格式', 
                                        'prepend-inner-icon': 'mdi-tag',
                                        'class': 'mt-4'
                                    }},
                                    {
                                        'component': 'VAlert', 'props': {
                                            'type': 'info',
                                            'color': 'info',
                                            'outlined': True,
                                            'dense': True,
                                            'class': 'mt-4'
                                        }, 'content': [
                                            {'component': 'span', 'text': '配置说明参考: '},
                                            {'component': 'a', 'props': {'href': 'https://github.com/xijin285/MoviePilot-Plugins/tree/main/plugins.v2/ikuairouterbackup/README.md', 'target': '_blank', 'style': 'color:#2196f3;text-decoration:underline;'}, 'text': 'README'}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            'help': {
                'icon': 'mdi-help-circle', 'title': '使用说明', 'content': [
                    {
                        'component': 'VCard',
                        'props': {'variant': 'outlined'},
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'props': {'class': 'text-h6'},
                                'text': '📖 使用说明'
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'class': 'mb-2'
                                        },
                                        'content': [
                                            {'component': 'VListItem', 'props': {'prepend-icon': 'mdi-star-circle-outline'}, 'content': [{'component': 'VListItemTitle', 'text': '【基础使用说明】'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '1. 在[连接设置]中填写爱快路由的访问地址、用户名和密码。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '2. 在[备份设置]中配置本地备份参数。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '3. 在[WebDAV设置]中按需配置远程备份。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '4. 在[恢复设置]中可进行系统恢复操作。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '5. 在[基础设置]中设置执行周期、通知等并启用插件。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '6. 点击保存即可。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '7. 备份文件将以.bak后缀保存。'}]},
                                        ]
                                    },
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'warning',
                                            'variant': 'tonal',
                                            'class': 'mb-2'
                                        },
                                        'content': [
                                            {'component': 'VListItem', 'props': {'prepend-icon': 'mdi-alert-circle-outline'}, 'content': [{'component': 'VListItemTitle', 'text': '【注意事项】'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '• 确保爱快路由的Web管理界面可以正常访问。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '• 用户名和密码需要具有备份和恢复权限。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '• 备份文件可能占用较大空间，请确保存储空间充足。'}]},
                                            {'component': 'VListItem', 'props': {'density': 'compact'}, 'content': [{'component': 'VListItemSubtitle', 'text': '"立即运行一次" 会在点击保存后约3秒执行，请留意日志输出。'}]},
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        # 最终表单结构
        form_structure = [
            {
                'component': 'VForm',
                'content': [
                    basic_settings_card,
                    {
                        'component': 'VCard',
                        'props': {'variant': 'flat'},
                        'content': [
                            {
                                'component': 'VTabs',
                                'props': {'v-model': 'tab', 'grow': True},
                                'content': [
                                    {'component': 'VTab', 'props': {'value': key, 'prepend-icon': value['icon']}, 'text': value['title']}
                                    for key, value in tabs.items()
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'VWindow',
                                        'props': {'v-model': 'tab'},
                                        'content': [
                                            {
                                                'component': 'VWindowItem',
                                                'props': {'value': key},
                                                'content': value['content']
                                            }
                                            for key, value in tabs.items()
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
            "tab": "connection",
            "enabled": self._enabled, "notify": self._notify, "cron": self._cron, "onlyonce": self._onlyonce,
            "retry_count": self._retry_count, "retry_interval": self._retry_interval, "ikuai_url": self._original_ikuai_url,
            "ikuai_username": self._ikuai_username, "ikuai_password": self._ikuai_password,
            "enable_local_backup": self._enable_local_backup, "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num, "notification_style": self._notification_style,
            "enable_webdav": self._enable_webdav, "webdav_url": self._webdav_url,
            "webdav_username": self._webdav_username, "webdav_password": self._webdav_password,
            "webdav_path": self._webdav_path, "webdav_keep_backup_num": self._webdav_keep_backup_num,
            "clear_history": self._clear_history,  # 新增：清理历史记录开关
            "delete_after_backup": self._delete_after_backup,
            "enable_restore": self._enable_restore,
            "restore_force": self._restore_force, "restore_file": self._restore_file, "restore_now": self._restore_now,
            # IP分组配置
            "enable_ip_group": self._enable_ip_group,
            "ip_group_province": self._ip_group_province,
            "ip_group_city": self._ip_group_city,
            "ip_group_isp": self._ip_group_isp,
            "ip_group_prefix": self._ip_group_prefix,
            "ip_group_address_pool": self._ip_group_address_pool,
            "ip_group_sync_now": self._ip_group_sync_now,
        }

        return form_structure, default_values

    def get_page(self) -> List[dict]:
        # --- 任务状态部分 ---
        available_backups = self._get_available_backups()
        local_backup_count = sum(1 for b in available_backups if b['source'] == '本地备份')
        webdav_backup_count = sum(1 for b in available_backups if b['source'] == 'WebDAV备份')

        # 确定显示状态和颜色
        backup_display_status = self._backup_activity
        restore_display_status = self._restore_activity
        ip_group_display_status = self._ip_group_activity

        if backup_display_status == "空闲":
            backup_status_color = "success"
        elif "失败" in backup_display_status:
            backup_status_color = "error"
        else:
            backup_status_color = "warning"

        if restore_display_status == "空闲":
            restore_status_color = "success"
        elif "失败" in restore_display_status:
            restore_status_color = "error"
        else:
            restore_status_color = "warning"

        if ip_group_display_status == "空闲":
            ip_group_status_color = "success"
        elif "失败" in ip_group_display_status:
            ip_group_status_color = "error"
        else:
            ip_group_status_color = "warning"

        status_card = {
            'component': 'VCard',
            'props': {'variant': 'outlined', 'class': 'mb-4'},
            'content': [
                {
                    'component': 'VCardTitle',
                    'props': {'class': 'text-h6'},
                    'text': '📊 任务状态'
                },
                {
                    'component': 'VCardText',
                    'content': [
                        {
                            'component': 'VRow',
                            'props': {'align': 'center', 'no-gutters': True},
                            'content': [
                                {'component': 'VCol', 'props': {'cols': 'auto'}, 'content': [
                                    {'component': 'VChip', 'props': {
                                        'color': backup_status_color,
                                        'variant': 'elevated',
                                        'label': True,
                                        'prepend_icon': 'mdi-content-save'
                                    }, 'text': f"备份状态: {backup_display_status}"}
                                ]},
                                {'component': 'VCol', 'props': {'cols': 'auto', 'class': 'ml-2'}, 'content': [
                                    {'component': 'VChip', 'props': {
                                        'color': restore_status_color,
                                        'variant': 'elevated',
                                        'label': True,
                                        'prepend_icon': 'mdi-restore'
                                    }, 'text': f"恢复状态: {restore_display_status}"}
                                ]},
                                *([{'component': 'VCol', 'props': {'cols': 'auto', 'class': 'ml-4'}, 'content': [
                                    {'component': 'VChip', 'props': {
                                        'color': 'info',
                                        'variant': 'outlined',
                                        'label': True,
                                        'prepend_icon': 'mdi-harddisk'
                                    }, 'text': f"本地备份: {local_backup_count} 个"}
                                ]}] if self._enable_local_backup else []),
                                *([{'component': 'VCol', 'props': {'cols': 'auto', 'class': 'ml-2'}, 'content': [
                                    {'component': 'VChip', 'props': {
                                        'color': 'info',
                                        'variant': 'outlined',
                                        'label': True,
                                        'prepend_icon': 'mdi-cloud-outline'
                                    }, 'text': f"WebDAV备份: {webdav_backup_count} 个"}
                                ]}] if self._enable_webdav else []),
                                *([{'component': 'VCol', 'props': {'cols': 'auto', 'class': 'ml-2'}, 'content': [
                                    {'component': 'VChip', 'props': {
                                        'color': ip_group_status_color,
                                        'variant': 'elevated',
                                        'label': True,
                                        'prepend_icon': 'mdi-ip-network'
                                    }, 'text': f"IP分组状态: {ip_group_display_status}"}
                                ]}] if self._enable_ip_group else []),
                                {'component': 'VSpacer'},
                                {'component': 'VCol', 'props': {'cols': 'auto'}, 'content': [
                                    {'component': 'div', 'props': {'class': 'd-flex align-center text-h6'}, 'content':[
                                        {'component': 'VIcon', 'props': {'icon': 'mdi-router-network', 'size': 'large', 'class': 'mr-2'}},
                                        {'component': 'span', 'props': {'class': 'font-weight-medium'}, 'text': f"🌐 爱快路由: {self._original_ikuai_url or '未配置'}"},
                                    ]}
                                ]},
                            ]
                        }
                    ]
                }
            ]
        }
        
        # --- 历史记录部分 ---
        backup_history_data = self._load_backup_history()
        restore_history_data = self._load_restore_history()
        
        all_history = []
        if isinstance(backup_history_data, list):
            for item in backup_history_data:
                item['type'] = '备份'
                all_history.append(item)
        if isinstance(restore_history_data, list):
            for item in restore_history_data:
                item['type'] = '恢复'
                all_history.append(item)
        
        all_history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # 统一的历史记录卡片
        if not all_history:
            history_card = {
                'component': 'VAlert',
                'props': {
                    'type': 'info',
                    'variant': 'tonal',
                    'text': '暂无历史记录。当有备份或恢复操作后，历史将在此处显示。',
                    'class': 'mb-2'
                }
            }
        else:
            history_rows = []
            for item in all_history:
                timestamp_str = datetime.fromtimestamp(item.get("timestamp", 0)).strftime('%Y-%m-%d %H:%M:%S') if item.get("timestamp") else "N/A"
                status_success = item.get("success", False)
                status_text = "成功" if status_success else "失败"
                status_color = "success" if status_success else "error"
                filename_str = item.get("filename", "N/A")
                message_str = item.get("message", "")
                type_str = item.get("type", "未知")
                type_color = "primary" if type_str == "备份" else "accent"

                history_rows.append({
                    'component': 'tr',
                    'content': [
                        {'component': 'td', 'props': {'class': 'text-caption'}, 'text': timestamp_str},
                        {'component': 'td', 'content': [
                            {'component': 'VChip', 'props': {'color': type_color, 'size': 'small', 'variant': 'flat'}, 'text': type_str}
                        ]},
                        {'component': 'td', 'content': [
                            {'component': 'VChip', 'props': {'color': status_color, 'size': 'small', 'variant': 'outlined'}, 'text': status_text}
                        ]},
                        {'component': 'td', 'text': filename_str},
                        {'component': 'td', 'text': message_str},
                    ]
                })

            history_card = {
                "component": "VCard",
                "props": {"variant": "outlined", "class": "mb-4"},
                "content": [
                    {
                        "component": "VCardTitle",
                        "props": {"class": "text-h6"},
                        "text": "📋 任务历史"
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
                                                    {'component': 'th', 'text': '类型'},
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

        return [status_card, history_card]

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

            if not self._ikuai_url or not self._ikuai_username or not self._ikuai_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
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

    def run_ip_group_sync_job(self):
        """运行IP分组同步任务"""
        if not self._lock: 
            self._lock = threading.Lock()
        if not self._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} IP分组同步任务已有任务正在执行，本次调度跳过！")
            return
            
        try:
            self._ip_group_activity = "正在同步"
            logger.info(f"开始执行 {self.plugin_name} IP分组同步任务...")

            if not self._ikuai_url or not self._ikuai_username or not self._ikuai_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                return

            logger.info(f"{self.plugin_name} 正在创建IP分组管理器...")
            # 创建IP分组管理器
            ip_manager = IPGroupManager(
                ikuai_url=self._ikuai_url,
                username=self._ikuai_username,
                password=self._ikuai_password
            )
            
            logger.info(f"{self.plugin_name} 正在获取IP段信息，请稍候...")
            # 执行同步
            success, message = ip_manager.sync_ip_groups_from_22tool(
                province=self._ip_group_province,
                city=self._ip_group_city,
                isp=self._ip_group_isp,
                group_prefix=self._ip_group_prefix,
                address_pool=self._ip_group_address_pool
            )
            
            if success:
                logger.info(f"{self.plugin_name} IP分组同步成功: {message}")
                self._send_notification(success=True, message=message)
            else:
                logger.error(f"{self.plugin_name} IP分组同步失败: {message}")
                self._send_notification(success=False, message=message)
                
        except Exception as e:
            error_msg = f"IP分组同步任务执行异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            self._send_notification(success=False, message=error_msg)
        finally:
            self._ip_group_activity = "空闲"
            if self._lock and self._lock.locked():
                self._lock.release()

    def _api_sync_ip_groups(self, province: str = "", city: str = "", isp: str = "", 
                           group_prefix: str = "", address_pool: bool = False) -> Dict[str, Any]:
        """API接口：同步IP分组"""
        try:
            if not self._ikuai_url or not self._ikuai_username or not self._ikuai_password:
                return {"success": False, "message": "配置不完整：URL、用户名或密码未设置。"}
            
            # 创建IP分组管理器
            ip_manager = IPGroupManager(
                ikuai_url=self._ikuai_url,
                username=self._ikuai_username,
                password=self._ikuai_password
            )
            
            # 执行同步
            success, message = ip_manager.sync_ip_groups_from_22tool(
                province=province,
                city=city,
                isp=isp,
                group_prefix=group_prefix,
                address_pool=address_pool
            )
            
            return {"success": success, "message": message}
            
        except Exception as e:
            error_msg = f"API同步IP分组异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}

    def _api_get_ip_blocks_info(self, province: str = "", city: str = "", isp: str = "") -> Dict[str, Any]:
        """API接口：获取IP段信息"""
        try:
            # 创建IP分组管理器
            ip_manager = IPGroupManager(
                ikuai_url=self._ikuai_url,
                username=self._ikuai_username,
                password=self._ikuai_password
            )
            
            # 获取IP段信息
            ip_blocks = ip_manager.get_ip_blocks_from_22tool(province, city, isp)
            
            return {
                "success": True,
                "data": ip_blocks,
                "count": len(ip_blocks)
            }
            
        except Exception as e:
            error_msg = f"获取IP段信息异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}

    def _api_get_available_options(self) -> Dict[str, Any]:
        """API接口：获取可用的省份、城市、运营商选项"""
        try:
            # 创建IP分组管理器
            ip_manager = IPGroupManager(
                ikuai_url=self._ikuai_url,
                username=self._ikuai_username,
                password=self._ikuai_password
            )
            
            provinces = ip_manager.get_available_provinces()
            isps = ip_manager.get_available_isps()
            
            return {
                "success": True,
                "provinces": provinces,
                "isps": isps
            }
            
        except Exception as e:
            error_msg = f"获取可用选项异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}

    def _api_get_cities_by_province(self, province: str) -> Dict[str, Any]:
        """API接口：根据省份获取城市列表"""
        try:
            # 创建IP分组管理器
            ip_manager = IPGroupManager(
                ikuai_url=self._ikuai_url,
                username=self._ikuai_username,
                password=self._ikuai_password
            )
            
            cities = ip_manager.get_available_cities(province)
            
            return {
                "success": True,
                "cities": cities
            }
            
        except Exception as e:
            error_msg = f"获取城市列表异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # Consistent User-Agent for all requests in this session
        browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        session.headers.update({"User-Agent": browser_user_agent})
        
        sess_key_part = self._login_ikuai(session)
        if not sess_key_part:
            return False, "登录爱快路由失败，无法获取SESS_KEY", None
        
        # Cookie is set on the session for subsequent requests
        cookie_string = f"username={quote(self._ikuai_username)}; {sess_key_part}; login=1"
        session.headers.update({"Cookie": cookie_string})
        
        create_success, create_msg = self._create_backup_on_router(session)
        if not create_success:
            return False, f"创建备份失败: {create_msg}", None
        logger.info(f"{self.plugin_name} 成功触发创建备份。等待2秒让备份生成和准备就绪...")
        time.sleep(2)

        backup_list = self._get_backup_list(session)
        if backup_list is None:
             return False, "获取备份文件列表时出错 (在下载前调用)", None
        if not backup_list:
            return False, "路由器上没有找到任何备份文件 (在下载前获取列表为空)", None
        
        latest_backup = backup_list[0]
        actual_router_filename_from_api = latest_backup.get("name")
        if not actual_router_filename_from_api:
            return False, "无法从备份列表中获取最新备份的文件名", None
            
        # Filename to be used in the download URL is exactly what the API provided.
        filename_for_download_url = actual_router_filename_from_api
        
        # Determine the local filename, ensuring it has a .bak extension.
        base_name_for_local_file = os.path.splitext(actual_router_filename_from_api)[0]
        local_display_and_saved_filename = base_name_for_local_file + ".bak"
        
        local_filepath_to_save = Path(self._backup_path) / local_display_and_saved_filename

        logger.info(f"{self.plugin_name} API列表最新备份名: {actual_router_filename_from_api}. 将尝试以此名下载.")
        logger.info(f"{self.plugin_name} 最终本地保存文件名将为: {local_display_and_saved_filename}")

        # Send EXPORT request before downloading
        export_payload = {
            "func_name": "backup",
            "action": "EXPORT",
            "param": { "srcfile": local_display_and_saved_filename }
        }
        export_url = urljoin(self._ikuai_url, "/Action/call")
        try:
            logger.info(f"{self.plugin_name} 尝试向 {export_url} 发送 EXPORT 请求...")
            response = session.post(export_url, data=json.dumps(export_payload), headers={'Content-Type': 'application/json'}, timeout=10)
            response.raise_for_status()
            logger.info(f"{self.plugin_name} EXPORT 请求发送成功。响应: {response.text[:200]}")
        except requests.exceptions.RequestException as e:
            error_detail = f"尝试向 {export_url} 发送 EXPORT 请求失败: {e}"
            logger.error(f"{self.plugin_name} {error_detail}")
            return False, error_detail, None

        # 根据本地备份开关决定是否执行本地备份
        if self._enable_local_backup:
            if not self._backup_path:
                return False, "本地备份已启用但备份路径未配置且无法设置默认路径", None

            try:
                Path(self._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"创建本地备份目录失败: {e}", None

            download_success, download_msg = self._download_backup_file(session, filename_for_download_url, str(local_filepath_to_save))
            if not download_success:
                error_detail = f"尝试下载 {filename_for_download_url} (API原始名: {actual_router_filename_from_api}) 失败: {download_msg}"
                return False, error_detail, None
            
            # 清理本地旧备份
            self._cleanup_old_backups()
        else:
            logger.info(f"{self.plugin_name} 本地备份已禁用，跳过本地备份步骤")

        # 如果启用了WebDAV，上传到WebDAV服务器
        if self._enable_webdav:
            if self._enable_local_backup:
                # 如果启用了本地备份，使用已下载的文件上传
                webdav_success, webdav_msg = self._upload_to_webdav(str(local_filepath_to_save), local_display_and_saved_filename)
            else:
                # 如果禁用了本地备份，需要先下载到临时文件再上传
                temp_dir = Path(self.get_data_path()) / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_filepath = temp_dir / local_display_and_saved_filename
                
                download_success, download_msg = self._download_backup_file(session, filename_for_download_url, str(temp_filepath))
                if not download_success:
                    error_detail = f"尝试下载临时文件用于WebDAV上传失败: {download_msg}"
                    return False, error_detail, None
                
                webdav_success, webdav_msg = self._upload_to_webdav(str(temp_filepath), local_display_and_saved_filename)
                
                # 删除临时文件
                try:
                    temp_filepath.unlink()
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除临时文件失败: {e}")

            if webdav_success:
                logger.info(f"{self.plugin_name} 成功上传备份到WebDAV服务器")
                # 清理WebDAV上的旧备份
                self._cleanup_webdav_backups()
            else:
                logger.error(f"{self.plugin_name} 上传备份到WebDAV服务器失败: {webdav_msg}")
                # 即便WebDAV上传失败，如果本地备份成功，也应该继续执行删除路由器文件的操作（如果用户开启了此选项）
                # return False, f"WebDAV上传失败: {webdav_msg}", None

        # 如果开启了备份后删除功能，并且至少有一种备份方式成功，则执行删除操作
        if self._delete_after_backup:
            local_backup_successful = self._enable_local_backup and 'download_success' in locals() and download_success
            webdav_backup_successful = self._enable_webdav and 'webdav_success' in locals() and webdav_success

            if local_backup_successful or webdav_backup_successful:
                logger.info(f"{self.plugin_name} 备份成功，将删除路由器上的备份文件: {actual_router_filename_from_api}")
                delete_success, delete_msg = self._delete_backup_on_router(session, actual_router_filename_from_api)
                if delete_success:
                    logger.info(f"{self.plugin_name} 成功删除路由器上的备份文件。")
                else:
                    logger.warning(f"{self.plugin_name} 删除路由器上的备份文件失败: {delete_msg}")
            else:
                logger.warning(f"{self.plugin_name} 未执行任何成功的备份操作，跳过删除路由器上的文件。")

        return True, None, local_display_and_saved_filename

    def _login_ikuai(self, session: requests.Session) -> Optional[str]:
        login_url = urljoin(self._ikuai_url, "/Action/login")
        password_md5 = hashlib.md5(self._ikuai_password.encode('utf-8')).hexdigest()
        login_data = {"username": self._ikuai_username, "passwd": password_md5}
        try:
            logger.info(f"{self.plugin_name} 尝试登录到 {self._ikuai_url}...")
            response = session.post(login_url, data=json.dumps(login_data), headers={'Content-Type': 'application/json'}, timeout=10)
            response.raise_for_status()
            cookies = response.cookies
            sess_key_value = cookies.get("sess_key")
            if sess_key_value:
                logger.info(f"{self.plugin_name} 登录成功，获取到 sess_key。")
                return f"sess_key={sess_key_value}"
            set_cookie_header = response.headers.get('Set-Cookie')
            if set_cookie_header:
                match = re.search(r'sess_key=([^;]+)', set_cookie_header)
                if match:
                    logger.info(f"{self.plugin_name} 登录成功，从Set-Cookie头获取到 sess_key。")
                    return f"sess_key={match.group(1)}"
            logger.error(f"{self.plugin_name} 登录成功但未能从Cookie或头部提取 sess_key。响应: {response.text[:200]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 登录请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 登录过程中发生未知错误: {e}")
            return None

    def _create_backup_on_router(self, session: requests.Session) -> Tuple[bool, Optional[str]]:
        create_url = urljoin(self._ikuai_url, "/Action/call")
        backup_data = {"func_name": "backup", "action": "create", "param": {}}
        try:
            logger.info(f"{self.plugin_name} 尝试在 {self._ikuai_url} 创建新备份...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self._ikuai_url.rstrip('/'),
                'Referer': self._ikuai_url.rstrip('/') + '/'
            }
            # User-Agent and Cookie are on session.headers
            response = session.post(create_url, data=json.dumps(backup_data), headers=request_headers, timeout=30)
            response.raise_for_status()
            response_text = response.text.strip().lower()
            if "success" in response_text or response_text == '"success"':
                 logger.info(f"{self.plugin_name} 备份创建请求发送成功。响应: {response_text}")
                 return True, None
            try:
                res_json = response.json()
                if res_json.get("result") == 30000 and res_json.get("errmsg", "").lower() == "success":
                    logger.info(f"{self.plugin_name} 备份创建请求成功 (JSON)。响应: {res_json}")
                    return True, None
                
                err_msg = res_json.get("errmsg")
                if not err_msg:
                    err_msg = res_json.get("ErrMsg", "创建备份API未返回成功或指定错误信息")

                logger.error(f"{self.plugin_name} 备份创建失败 (JSON)。响应: {res_json}, 错误: {err_msg}")
                return False, f"路由器返回错误: {err_msg}"
            except json.JSONDecodeError:
                logger.error(f"{self.plugin_name} 备份创建失败，非JSON响应且不含 'success'。响应: {response_text}")
                return False, f"路由器返回非预期响应: {response_text[:100]}"
        except requests.exceptions.Timeout:
            logger.warning(f"{self.plugin_name} 创建备份请求超时。备份可能仍在后台进行。")
            return True, "请求超时，但备份可能已开始创建"
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 创建备份请求失败: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建备份过程中发生未知错误: {e}")
            return False, str(e)

    def _get_backup_list(self, session: requests.Session) -> Optional[List[Dict]]:
        list_url = urljoin(self._ikuai_url, "/Action/call")
        list_data = {"func_name": "backup", "action": "show", "param": {"ORDER": "desc", "ORDER_BY": "time", "LIMIT": "0,50"}}
        try:
            logger.info(f"{self.plugin_name} 尝试从 {self._ikuai_url} 获取备份列表...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self._ikuai_url.rstrip('/'),
                'Referer': self._ikuai_url.rstrip('/') + '/'
            }
            # User-Agent and Cookie are on session.headers
            response = session.post(list_url, data=json.dumps(list_data), headers=request_headers, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            if res_json.get("Result") == 30000 and res_json.get("ErrMsg", "").lower() == "success":
                data = res_json.get("Data", {})
                backup_items = data.get("data", [])
                if isinstance(backup_items, list) and backup_items:
                    logger.info(f"{self.plugin_name} 成功获取到 {len(backup_items)} 条备份记录。")
                    return backup_items
                else:
                    logger.warning(f"{self.plugin_name} 获取备份列表成功，但列表为空或格式不正确。Data content: {data}")
                    return []
            else:
                err_msg = res_json.get("ErrMsg") or res_json.get("errmsg", "获取列表API未返回成功或指定错误信息")
                logger.error(f"{self.plugin_name} 获取备份列表失败。响应: {res_json}, 错误: {err_msg}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 获取备份列表请求失败: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 获取备份列表响应非JSON格式: {response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取备份列表过程中发生未知错误: {e}")
            return None

    def _download_backup_file(self, session: requests.Session, router_filename: str, local_filepath_to_save: str) -> Tuple[bool, Optional[str]]:
        safe_router_filename = quote(router_filename)
        
        # Only use /Action/download URL as per user instruction
        download_url = urljoin(self._ikuai_url, f"/Action/download?filename={safe_router_filename}")
        last_error = None

        # Mimic browser headers for GET download request
        request_headers = {
            "Referer": self._ikuai_url.rstrip('/') + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            # User-Agent and Cookie are handled by the session object automatically
        }

        logger.info(f"{self.plugin_name} 尝试下载备份文件 {router_filename} 从 {download_url}, 保存到 {local_filepath_to_save}...")
        try:
            # session.get will use session.headers (Cookie, UA) and merge/override with request_headers (Referer, Accept)
            with session.get(download_url, stream=True, timeout=300, headers=request_headers) as r:
                r.raise_for_status()
                # No need to check content_type for HTML error page here, as we are only trying one URL that should directly serve the file or give a proper HTTP error.
                
                with open(local_filepath_to_save, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"{self.plugin_name} 文件 {router_filename} 下载完成，保存至 {local_filepath_to_save}")
                return True, None
        except requests.exceptions.HTTPError as e:
            last_error = f"HTTP错误 ({e.response.status_code}) 从 {download_url}: {e}"
            logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {download_url} 失败: {last_error}")
        except requests.exceptions.RequestException as e:
            last_error = f"请求错误从 {download_url}: {e}"
            logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {download_url} 失败: {last_error}")
        except Exception as e:
            last_error = f"未知错误从 {download_url}: {e}"
            logger.error(f"{self.plugin_name} 下载 {router_filename} 从 {download_url} 过程中发生未知错误: {last_error}")
        
        logger.error(f"{self.plugin_name} 尝试下载 {router_filename} 失败。最后错误: {last_error}")
        return False, last_error

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
        text_content += f"{router_prefix} 路由：{self._original_ikuai_url}\n"
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

    def _load_restore_history(self) -> List[Dict[str, Any]]:
        """加载恢复历史记录"""
        history = self.get_data('restore_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 恢复历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history

    def _save_restore_history_entry(self, entry: Dict[str, Any]):
        """保存单条恢复历史记录"""
        try:
            # 加载现有历史记录
            history = self._load_restore_history()
            
            # 添加新记录到开头
            history.insert(0, entry)
            
            # 如果超过最大记录数，删除旧记录
            if len(history) > self._max_restore_history_entries:
                history = history[:self._max_restore_history_entries]
            
            # 保存更新后的历史记录
            self.save_data('restore_history', history)
            logger.debug(f"{self.plugin_name} 已保存恢复历史记录")
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存恢复历史记录失败: {str(e)}")

    def _get_available_backups(self) -> List[Dict[str, Any]]:
        """获取可用的备份文件列表"""
        backups = []
        
        # 获取本地备份
        if self._enable_local_backup and self._backup_path:
            try:
                backup_dir = Path(self._backup_path)
                if backup_dir.is_dir():
                    for f_path_obj in backup_dir.iterdir():
                        if f_path_obj.is_file() and f_path_obj.suffix.lower() == ".bak":
                            try:
                                file_time = f_path_obj.stat().st_mtime
                                backups.append({
                                    'filename': f_path_obj.name,
                                    'source': '本地备份',
                                    'time': file_time
                                })
                            except Exception as e:
                                logger.error(f"{self.plugin_name} 处理本地备份文件 {f_path_obj.name} 时出错: {e}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取本地备份文件列表时发生错误: {str(e)}")
        
        # 获取WebDAV备份
        if self._enable_webdav and self._webdav_url:
            try:
                import requests
                from urllib.parse import urljoin
                from xml.etree import ElementTree
                
                # 规范化WebDAV URL
                webdav_url = self._webdav_url.rstrip('/')
                webdav_path = self._webdav_path.strip('/')
                
                # 构建完整的WebDAV URL
                full_url = urljoin(webdav_url + '/', webdav_path)
                
                # 发送PROPFIND请求获取文件列表
                headers = {
                    'Depth': '1',
                    'Content-Type': 'application/xml',
                    'Accept': '*/*',
                    'User-Agent': 'MoviePilot/1.0'
                }
                
                response = requests.request(
                    'PROPFIND',
                    full_url,
                    auth=(self._webdav_username, self._webdav_password),
                    headers=headers,
                    timeout=30,
                    verify=False
                )
                
                if response.status_code == 207:  # 207 Multi-Status
                    root = ElementTree.fromstring(response.content)
                    
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
                        last_modified = response.find('.//{DAV:}getlastmodified')
                        if last_modified is not None:
                            from email.utils import parsedate_to_datetime
                            try:
                                file_time = parsedate_to_datetime(last_modified.text).timestamp()
                            except:
                                file_time = time.time()
                        else:
                            file_time = time.time()
                            
                        filename = os.path.basename(file_path)
                        backups.append({
                            'filename': filename,
                            'source': 'WebDAV备份',
                            'time': file_time
                        })
                        
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表时发生错误: {str(e)}")
        
        # 按时间排序
        backups.sort(key=lambda x: x['time'], reverse=True)
        return backups

    def run_restore_job(self, filename: str, source: str = "本地备份"):
        """执行恢复任务"""
        if not self._enable_restore:
            logger.error(f"{self.plugin_name} 恢复功能未启用")
            return
        
        if not self._restore_lock:
            self._restore_lock = threading.Lock()
        if not self._global_task_lock:
            self._global_task_lock = threading.Lock()
            
        # 尝试获取全局任务锁，如果获取不到说明有其他任务在运行
        if not self._global_task_lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 检测到其他任务正在执行，恢复任务跳过！")
            return
            
        # 尝试获取恢复锁，如果获取不到说明有恢复任务在运行
        if not self._restore_lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有恢复任务正在执行，本次操作跳过！")
            self._global_task_lock.release()  # 释放全局锁
            return
            
        restore_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": filename,
            "message": "恢复任务开始"
        }
        self._restore_activity = "任务开始"
            
        try:
            logger.info(f"{self.plugin_name} 开始执行恢复任务，文件: {filename}, 来源: {source}")

            if not self._ikuai_url or not self._ikuai_username or not self._ikuai_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_restore_notification(success=False, message=error_msg, filename=filename)
                restore_entry["message"] = error_msg
                self._save_restore_history_entry(restore_entry)
                return

            # 执行恢复操作
            success, error_msg = self._perform_restore_once(filename, source)
            
            restore_entry["success"] = success
            restore_entry["message"] = "恢复成功" if success else f"恢复失败: {error_msg}"
            
            self._send_restore_notification(success=success, message=restore_entry["message"], filename=filename)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 恢复任务执行主流程出错：{str(e)}")
            restore_entry["message"] = f"恢复任务执行主流程出错: {str(e)}"
            self._send_restore_notification(success=False, message=restore_entry["message"], filename=filename)
        finally:
            self._restore_activity = "空闲"
            self._save_restore_history_entry(restore_entry)
            # 确保锁一定会被释放
            if self._restore_lock and hasattr(self._restore_lock, 'locked') and self._restore_lock.locked():
                try:
                    self._restore_lock.release()
                except RuntimeError:
                    pass
            # 释放全局任务锁
            if self._global_task_lock and hasattr(self._global_task_lock, 'locked') and self._global_task_lock.locked():
                try:
                    self._global_task_lock.release()
                except RuntimeError:
                    pass
            logger.info(f"{self.plugin_name} 恢复任务执行完成。")

    def _perform_restore_once(self, filename: str, source: str) -> Tuple[bool, Optional[str]]:
        """执行一次恢复操作"""
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # 一致的User-Agent
        browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        session.headers.update({"User-Agent": browser_user_agent})
        
        # 1. 登录爱快路由
        sess_key_part = self._login_ikuai(session)
        if not sess_key_part:
            return False, "登录爱快路由失败，无法获取SESS_KEY"
        
        # 设置Cookie
        cookie_string = f"username={quote(self._ikuai_username)}; {sess_key_part}; login=1"
        session.headers.update({"Cookie": cookie_string})
        
        # 2. 获取备份文件
        backup_file_path = None
        if source == "本地备份":
            backup_file_path = os.path.join(self._backup_path, filename)
            if not os.path.exists(backup_file_path):
                return False, f"本地备份文件不存在: {backup_file_path}"
        elif source == "WebDAV备份":
            # 从WebDAV下载备份文件到临时目录
            temp_dir = Path(self.get_data_path()) / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            backup_file_path = str(temp_dir / filename)
            
            self._restore_activity = f"下载WebDAV中: {filename}"
            download_success, download_error = self._download_from_webdav(filename, backup_file_path)
            if not download_success:
                self._restore_activity = "空闲"
                return False, f"从WebDAV下载备份文件失败: {download_error}"
        else:
            return False, f"不支持的备份来源: {source}"

        try:
            # 3. 读取备份文件内容
            with open(backup_file_path, 'rb') as f:
                backup_content = f.read()

            # 4. 发送恢复请求
            restore_url = urljoin(self._ikuai_url, "/Action/call")
            restore_payload = {
                "func_name": "backup",
                "action": "RESTORE",
                "param": {}
            }

            self._restore_activity = "正在恢复配置..."
            logger.info(f"{self.plugin_name} 发送恢复请求...")

            # 首先发送RESTORE请求
            response = session.post(restore_url, json=restore_payload, timeout=30)
            response.raise_for_status()

            # 然后上传备份文件
            upload_url = urljoin(self._ikuai_url, "/Action/upload")
            files = {
                'file': (filename, backup_content, 'application/octet-stream')
            }
            upload_response = session.post(upload_url, files=files, timeout=300)
            upload_response.raise_for_status()

            # 检查响应
            try:
                result = upload_response.json()
                if result.get("Result") == 30000 or (isinstance(result, str) and "success" in result.lower()):
                    logger.info(f"{self.plugin_name} 恢复成功完成")
                    return True, None
                else:
                    error_msg = result.get("ErrMsg") or result.get("errmsg", "恢复失败，未知错误")
                    return False, error_msg
            except json.JSONDecodeError:
                if "success" in upload_response.text.lower():
                    return True, None
                return False, f"恢复失败，响应解析错误: {upload_response.text[:200]}"

        except requests.exceptions.RequestException as e:
            return False, f"恢复请求失败: {str(e)}"
        except Exception as e:
            return False, f"恢复过程中发生错误: {str(e)}"
        finally:
            # 如果是WebDAV备份，删除临时文件
            if source == "WebDAV备份" and backup_file_path and os.path.exists(backup_file_path):
                try:
                    os.remove(backup_file_path)
                    logger.info(f"{self.plugin_name} 已删除临时文件: {backup_file_path}")
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除临时文件失败: {str(e)}")

    def _send_restore_notification(self, success: bool, message: str = "", filename: str = "", is_clear_history: bool = False):
        """发送恢复通知"""
        if not self._notify: return
        title = f"🛠️ {self.plugin_name} "
        if is_clear_history:
            title += "清理历史记录"
        else:
            title += "恢复" + ("成功" if success else "失败")
        status_emoji = "✅" if success else "❌"
        
        # 根据选择的通知样式设置分隔符和风格
        if self._notification_style == 1:
            # 简约星线
            divider = "★━━━━━━━━━━━━━━━━━━━━━━━★"
            status_prefix = "📌"
            router_prefix = "��"
            file_prefix = "📁"
            info_prefix = "ℹ️"
            congrats = "\n🎉 恢复任务已顺利完成！"
            error_msg = "\n⚠️ 恢复失败，请检查日志了解详情。"
        elif self._notification_style == 2:
            # 方块花边
            divider = "■□■□■□■□■□■□■□■□■□■□■□■□■"
            status_prefix = "🔰"
            router_prefix = "🔹"
            file_prefix = "📂"
            info_prefix = "📝"
            congrats = "\n🎊 太棒了！配置已成功恢复！"
            error_msg = "\n🚨 警告：恢复过程中出现错误！"
        elif self._notification_style == 3:
            # 箭头主题
            divider = "➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤"
            status_prefix = "🔔"
            router_prefix = "📡"
            file_prefix = "💾"
            info_prefix = "📢"
            congrats = "\n🏆 恢复任务圆满完成！"
            error_msg = "\n🔥 错误：恢复未能完成！"
        elif self._notification_style == 4:
            # 波浪边框
            divider = "≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈"
            status_prefix = "🌊"
            router_prefix = "🌍"
            file_prefix = "📦"
            info_prefix = "💫"
            congrats = "\n🌟 恢复任务完美收官！"
            error_msg = "\n💥 恢复任务遇到波折！"
        elif self._notification_style == 5:
            # 科技风格
            divider = "▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣"
            status_prefix = "⚡"
            router_prefix = "🔌"
            file_prefix = "💿"
            info_prefix = "📊"
            congrats = "\n🚀 系统恢复成功完成！"
            error_msg = "\n⚠️ 系统恢复出现异常！"
        else:
            # 默认样式
            divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
            status_prefix = "📣"
            router_prefix = "🔗"
            file_prefix = "📄"
            info_prefix = "📋"
            congrats = "\n✨ 恢复已成功完成！"
            error_msg = "\n❗ 恢复失败，请检查配置和连接！"
        
        # 失败时的特殊处理 - 添加额外的警告指示
        if not success:
            divider_failure = "❌" + divider[1:-1] + "❌"
            text_content = f"{divider_failure}\n"
        else:
            text_content = f"{divider}\n"
            
        text_content += f"{status_prefix} 状态：{status_emoji} {'恢复成功' if success else '恢复失败'}\n\n"
        text_content += f"{router_prefix} 路由：{self._original_ikuai_url}\n"
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
            logger.info(f"{self.plugin_name} 发送恢复通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送恢复通知失败: {e}")

    def _api_restore_backup(self, filename: str, source: str = "本地备份"):
        """API恢复接口"""
        try:
            # 启动恢复任务
            self.run_restore_job(filename, source)
            return {"success": True, "message": "恢复任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动恢复任务失败: {str(e)}"}

    def _get_processed_ikuai_url(self, url: str) -> str:
        """返回处理后的iKuai URL，确保有http/https前缀并移除末尾的斜杠"""
        url = url.strip().rstrip('/')
        if not url:
            return ""
        if not url.startswith(('http://', 'https://')):
            return f"http://{url}"
        return url

    def _delete_backup_on_router(self, session: requests.Session, filename: str) -> Tuple[bool, Optional[str]]:
        """删除路由器上的指定备份文件"""
        delete_url = urljoin(self._ikuai_url, "/Action/call")
        delete_data = {"func_name": "backup", "action": "delete", "param": {"srcfile": filename}}
        try:
            logger.info(f"{self.plugin_name} 尝试在 {self._ikuai_url} 删除备份文件: {filename}...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self._ikuai_url.rstrip('/'),
                'Referer': self._ikuai_url.rstrip('/') + '/'
            }
            response = session.post(delete_url, data=json.dumps(delete_data), headers=request_headers, timeout=30)
            response.raise_for_status()

            # 检查响应
            try:
                res_json = response.json()
                if res_json.get("Result") == 30000 and "success" in res_json.get("ErrMsg", "").lower():
                    logger.info(f"{self.plugin_name} 删除备份文件请求成功 (JSON)。响应: {res_json}")
                    return True, None
                
                err_msg = res_json.get("ErrMsg", "删除备份API未返回成功或指定错误信息")
                logger.error(f"{self.plugin_name} 删除备份文件失败 (JSON)。响应: {res_json}, 错误: {err_msg}")
                return False, f"路由器返回错误: {err_msg}"
            except json.JSONDecodeError:
                if "success" in response.text.lower():
                    logger.info(f"{self.plugin_name} 删除备份文件请求发送成功。响应: {response.text}")
                    return True, None
                logger.error(f"{self.plugin_name} 删除备份文件失败，非JSON响应且不含 'success'。响应: {response.text}")
                return False, f"路由器返回非预期响应: {response.text[:100]}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 删除备份文件请求失败: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"{self.plugin_name} 删除备份文件过程中发生未知错误: {e}")
            return False, str(e)

    def _api_test_ip_group(self) -> Dict[str, Any]:
        """测试IP分组创建API"""
        try:
            if not self._enable_ip_group:
                return {"code": 1, "msg": "IP分组功能未启用"}
            
            if not self._ikuai_url or not self._ikuai_username or not self._ikuai_password:
                return {"code": 1, "msg": "爱快路由器配置不完整"}
            
            # 创建IP分组管理器
            ip_manager = IPGroupManager(self._ikuai_url, self._ikuai_username, self._ikuai_password)
            
            # 测试创建最简单的IP分组
            success, error = ip_manager.test_create_simple_ip_group()
            
            if success:
                return {"code": 0, "msg": "测试IP分组创建成功"}
            else:
                return {"code": 1, "msg": f"测试IP分组创建失败: {error}"}
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 测试IP分组创建异常: {str(e)}")
            return {"code": 1, "msg": f"测试IP分组创建异常: {str(e)}"}

    def _api_backup(self, onlyonce: bool = False):
        """API备份接口"""
        try:
            # 启动备份任务
            self.run_backup_job()
            return {"success": True, "message": "备份任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动备份任务失败: {str(e)}"}