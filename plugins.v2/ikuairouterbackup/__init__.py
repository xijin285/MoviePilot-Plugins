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

class IkuaiRouterBackup(_PluginBase):
    # 插件名称
    plugin_name = "爱快路由备份助手"
    # 插件描述
    plugin_desc = "为爱快路由提供全自动的配置备份方案，支持本地保存和WebDAV云端备份。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/ikuai.png"
    # 插件版本
    plugin_version = "1.1.8"
    # 插件作者
    plugin_author = "jinxi"
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

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 60
    _notification_style: int = 1
    
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
            self._ikuai_url = str(config.get("ikuai_url", "")).rstrip('/')
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
            "ikuai_url": self._ikuai_url,
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
                                            {'component': 'VCol', 'props': {'cols': 3, 'sm': 3, 'md': 3, 'lg': 3}, 'content': [{'component': 'VSwitch', 'props': {'model': 'clear_history', 'label': '清理历史记录', 'color': 'warning', 'prepend-icon': 'mdi-delete-sweep'}}]},
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'ikuai_url', 'label': '爱快路由地址', 'placeholder': '例如: http://10.0.0.1', 'prepend-inner-icon': 'mdi-router-network'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VCronField', 'props': {'model': 'cron', 'label': '执行周期', 'prepend-inner-icon': 'mdi-clock-outline'}}]}
                                        ],
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'ikuai_username', 'label': '用户名', 'placeholder': '默认为 admin', 'prepend-inner-icon': 'mdi-account'}}]},
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'ikuai_password', 'label': '密码', 'type': 'password', 'placeholder': '请输入密码', 'prepend-inner-icon': 'mdi-lock'}}]},
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
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSelect', 'props': {'model': 'notification_style', 'label': '通知样式', 'items': [{'title': '简约星线', 'value': 1}, {'title': '方块花边', 'value': 2}, {'title': '箭头主题', 'value': 3}, {'title': '波浪边框', 'value': 4}, {'title': '科技风格', 'value': 5}], 'prepend-inner-icon': 'mdi-palette'}}]},
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
                                            {'component': 'VCol', 'props': {'cols': 12, 'md': 8}, 'content': [{'component': 'VTextField', 'props': {'model': 'webdav_path', 'label': 'WebDAV备份路径', 'placeholder': '例如: /backups/ikuai', 'prepend-inner-icon': 'mdi-folder-network'}}]},
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
                                            'text': f'【使用说明】\n1. 填写爱快路由的访问地址、用户名和密码。\n2. 备份文件存储路径：可留空，默认为{default_backup_location_desc}。或指定一个绝对路径。确保MoviePilot有权访问和写入此路径。\n3. 设置执行周期，例如每天凌晨3点执行 (0 3 * * *)。\n4. 设置备份文件保留数量，旧的备份会被自动删除。\n5. 可选开启通知，在备份完成后收到结果通知，并可选择不同通知样式。\n6. WebDAV远程备份：\n   - 启用后，备份文件会同时上传到WebDAV服务器\n   - 填写WebDAV服务器地址、用户名和密码\n   - 设置WebDAV备份路径和保留数量\n   - 支持常见的WebDAV服务，如坚果云、NextCloud等\n7. 启用插件并保存即可。\n8. 备份文件将以.bak后缀保存。',
                                            'class': 'mb-2'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False, "notify": False, "cron": "0 3 * * *", "onlyonce": False,
            "retry_count": 3, "retry_interval": 60, "ikuai_url": "", "ikuai_username": "admin",
            "ikuai_password": "", "enable_local_backup": True, "backup_path": "", "keep_backup_num": 7,
            "notification_style": 1, "enable_webdav": False, "webdav_url": "", "webdav_username": "",
            "webdav_password": "", "webdav_path": "", "webdav_keep_backup_num": 7, "clear_history": False
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
                        "text": "📊 爱快路由备份历史"
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
            
            logger.info(f"{self.plugin_name} 备份文件 {local_display_and_saved_filename} 已成功下载自 {filename_for_download_url} 并保存到 {local_filepath_to_save}")
            
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
                return False, f"WebDAV上传失败: {webdav_msg}", None

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
        text_content += f"{router_prefix} 路由：{self._ikuai_url}\n"
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