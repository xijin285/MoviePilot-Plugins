import hashlib
import json
import os
import re
import time
import threading
from datetime import datetime, timedelta
from typing import Any, List, Dict, Tuple, Optional
from pathlib import Path

import pytz
import paramiko
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.core.event import eventmanager, Event
from app.schemas.types import EventType
from .pve import get_pve_status, get_container_status, get_qemu_status, clean_pve_tmp_files, clean_pve_logs, list_template_images, download_template_image, delete_template_image, upload_template_image, download_template_image_from_url
from .message_handler import MessageHandler


class ProxmoxVEBackup(_PluginBase):
    # 插件名称
    plugin_name = "PVE虚拟机守护神"
    # 插件描述
    plugin_desc = "一站式PVE虚拟化管理平台，智能自动化集成可视化界面高效掌控虚拟机与容器"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/proxmox.webp"
    # 插件版本
    plugin_version = "2.2.0"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "proxmox_backup_"
    # 加载顺序
    plugin_order = 11
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _backup_activity: str = "空闲"
    _restore_activity: str = "空闲"
    _max_history_entries: int = 100 # Max number of history entries to keep
    _restore_lock: Optional[threading.Lock] = None  # 恢复操作锁
    _max_restore_history_entries: int = 50  # 恢复历史记录最大数量
    _global_task_lock: Optional[threading.Lock] = None  # 全局任务锁，协调备份和恢复任务
    _last_config_hash: Optional[str] = None  # 上次配置的哈希值

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"  # 新增：定时任务cron表达式
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 0  # 默认不重试
    _retry_interval: int = 60
    _notification_message_type: str = "Plugin"  # 新增：消息类型
    
    # SSH配置
    _pve_host: str = ""  # PVE主机地址
    _ssh_port: int = 22
    _ssh_username: str = "root"
    _ssh_password: str = ""
    _ssh_key_file: str = ""

    # 备份配置
    _enable_local_backup: bool = True  # 本地备份开关
    _backup_path: str = ""
    _keep_backup_num: int = 5
    _backup_vmid: str = ""  # 要备份的容器ID，逗号分隔
    _storage_name: str = "local"  # 存储名称
    _backup_mode: str = "snapshot"  # 备份模式，默认snapshot
    _compress_mode: str = "zstd"    # 压缩模式，默认zstd
    _auto_delete_after_download: bool = True  # 下载后自动删除PVE备份
    _download_all_backups: bool = True  # 下载所有备份文件（多VM备份时）

    # WebDAV配置
    _enable_webdav: bool = False
    _webdav_url: str = ""
    _webdav_username: str = ""
    _webdav_password: str = ""
    _webdav_path: str = ""
    _webdav_keep_backup_num: int = 7
    _clear_history: bool = False  # 清理历史记录开关

    # 恢复配置
    _enable_restore: bool = False  # 启用恢复功能
    _restore_storage: str = "local"  # 恢复存储名称
    _restore_vmid: str = ""  # 恢复目标VMID
    _restore_force: bool = False  # 强制恢复（覆盖现有VM）
    _restore_skip_existing: bool = True  # 跳过已存在的VM
    _restore_file: str = "" # 要恢复的文件
    _restore_now: bool = False # 立即恢复开关
    _stopped: bool = False  # 增加已停止标志
    _instance = None  # 单例实例
    _message_handler: Optional[MessageHandler] = None  # 消息处理器实例

    # 新增：系统日志清理配置
    _enable_log_cleanup: bool = False
    _log_journal_days: int = 7
    _log_vzdump_keep: int = 7
    _log_pve_keep: int = 7
    _log_dpkg_keep: int = 7
    _cleanup_template_images: bool = False

    def init_plugin(self, config: Optional[dict] = None):
        # 停止已有服务，防止多实例冲突
        self.stop_service()
        self._lock = threading.Lock()
        self._restore_lock = threading.Lock()
        self._global_task_lock = threading.Lock()
        self._stopped = False

        # 加载配置
        saved_config = self.get_config()
        if saved_config:
            self._enabled = bool(saved_config.get("enabled", False))
            self._cron = str(saved_config.get("cron", "0 3 * * *"))
            self._onlyonce = bool(saved_config.get("onlyonce", False))
            self._notify = bool(saved_config.get("notify", False))
            self._retry_count = int(saved_config.get("retry_count", 0))
            self._retry_interval = int(saved_config.get("retry_interval", 60))
            self._notification_message_type = str(saved_config.get("notification_message_type", "Plugin"))
            self._pve_host = str(saved_config.get("pve_host", ""))
            self._ssh_port = int(saved_config.get("ssh_port", 22))
            self._ssh_username = str(saved_config.get("ssh_username", "root"))
            self._ssh_password = str(saved_config.get("ssh_password", ""))
            self._ssh_key_file = str(saved_config.get("ssh_key_file", ""))
            self._storage_name = str(saved_config.get("storage_name", "local"))
            self._enable_local_backup = bool(saved_config.get("enable_local_backup", True))
            self._backup_mode = str(saved_config.get("backup_mode", "snapshot"))
            self._compress_mode = str(saved_config.get("compress_mode", "zstd"))
            self._backup_vmid = str(saved_config.get("backup_vmid", ""))
            self._auto_delete_after_download = bool(saved_config.get("auto_delete_after_download", False))
            self._download_all_backups = bool(saved_config.get("download_all_backups", True))
            configured_backup_path = str(saved_config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(self.get_data_path() / "actual_backups")
                logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self._backup_path}")
            else:
                self._backup_path = configured_backup_path
            self._keep_backup_num = int(saved_config.get("keep_backup_num", 5))
            self._enable_webdav = bool(saved_config.get("enable_webdav", False))
            self._webdav_url = str(saved_config.get("webdav_url", ""))
            self._webdav_username = str(saved_config.get("webdav_username", ""))
            self._webdav_password = str(saved_config.get("webdav_password", ""))
            self._webdav_path = str(saved_config.get("webdav_path", ""))
            self._webdav_keep_backup_num = int(saved_config.get("webdav_keep_backup_num", 7))
            self._clear_history = bool(saved_config.get("clear_history", False))
            self._enable_restore = bool(saved_config.get("enable_restore", False))
            self._restore_storage = str(saved_config.get("restore_storage", "local"))
            self._restore_vmid = str(saved_config.get("restore_vmid", ""))
            self._restore_force = bool(saved_config.get("restore_force", False))
            self._restore_skip_existing = bool(saved_config.get("restore_skip_existing", True))
            self._restore_file = str(saved_config.get("restore_file", ""))
            self._restore_now = bool(saved_config.get("restore_now", False))
            self.auto_cleanup_tmp = saved_config.get("auto_cleanup_tmp", True)
            # 新增系统日志清理配置
            self._enable_log_cleanup = bool(saved_config.get("enable_log_cleanup", False))
            self._log_journal_days = int(saved_config.get("log_journal_days", 7))
            self._log_vzdump_keep = int(saved_config.get("log_vzdump_keep", 7))
            self._log_pve_keep = int(saved_config.get("log_pve_keep", 7))
            self._log_dpkg_keep = int(saved_config.get("log_dpkg_keep", 7))
            self._cleanup_template_images = bool(saved_config.get("cleanup_template_images", False))
            
        # 新配置覆盖
        if config:
            for k, v in config.items():
                if k == "cron":
                    self._cron = str(v)
                if hasattr(self, f"_{k}"):
                    setattr(self, f"_{k}", v)
                # 新增：支持 auto_cleanup_tmp
                if k == "auto_cleanup_tmp":
                    self.auto_cleanup_tmp = bool(v)
                if k == "enable_log_cleanup":
                    self._enable_log_cleanup = bool(v)
                if k == "log_journal_days":
                    self._log_journal_days = int(v)
                if k == "log_vzdump_keep":
                    self._log_vzdump_keep = int(v)
                if k == "log_pve_keep":
                    self._log_pve_keep = int(v)
                if k == "log_dpkg_keep":
                    self._log_dpkg_keep = int(v)
                if k == "cleanup_template_images":
                    self._cleanup_template_images = bool(v)
            self.__update_config()

        # 处理清理历史/立即恢复
            if self._clear_history:
                self._clear_all_history()
                self._clear_history = False
                self.__update_config()
            if self._restore_now and self._restore_file:
                try:
                    source, filename = self._restore_file.split('|', 1)
                    threading.Thread(target=self.run_restore_job, args=(filename, source)).start()
                    logger.info(f"{self.plugin_name} 已触发恢复任务，文件: {filename}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} 触发恢复任务失败: {e}")
                finally:
                    self._restore_now = False
                    self._restore_file = ""
                    self.__update_config()

        try:
            Path(self._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
             logger.error(f"{self.plugin_name} 创建实际备份目录 {self._backup_path} 失败: {e}")

        ProxmoxVEBackup._instance = self
        
        # 初始化消息处理器
        self._message_handler = MessageHandler(self)

        # 定时任务调度逻辑
        if self._scheduler:
            try:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown(wait=True)
            except Exception as e:
                logger.error(f"{self.plugin_name} 停止调度器时出错: {str(e)}")
            self._scheduler = None

        if self._enabled or self._onlyonce:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            if self._onlyonce:
                job_name = f"{self.plugin_name}服务_onlyonce"
                if self._scheduler.get_job(job_name):
                    self._scheduler.remove_job(job_name)
                logger.info(f"{self.plugin_name} 服务启动，立即运行一次")
                self._scheduler.add_job(func=self.run_backup_job, trigger='date',
                                     run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                     name=job_name, id=job_name)
                self._onlyonce = False
                self.__update_config()
            elif self._cron and self._cron.count(' ') == 4:
                job_name = f"{self.plugin_name}定时服务"
                if self._scheduler.get_job(job_name):
                    self._scheduler.remove_job(job_name)
                try:
                    trigger = CronTrigger.from_crontab(self._cron, timezone=settings.TZ)
                    self._scheduler.add_job(func=self.run_backup_job, trigger=trigger, name=job_name, id=job_name)
                    logger.info(f"{self.plugin_name} 已注册定时任务: {self._cron}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} cron表达式格式错误: {self._cron}, 错误: {e}")
            if not self._scheduler.running:
                self._scheduler.start()

    def stop_service(self):
        try:
            if self._scheduler:
                try:
                    self._scheduler.remove_all_jobs()
                    if self._scheduler.running:
                        self._scheduler.shutdown(wait=True)
                    self._scheduler = None
                except Exception as e:
                    logger.error(f"{self.plugin_name} 停止调度器时出错: {str(e)}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 停止调度器时出错: {str(e)}")

    def _should_skip_reinit(self, config: Optional[dict] = None) -> bool:
        """
        检查是否应该跳过重新初始化
        只有在关键配置发生变更时才重新初始化
        """
        if not config:
            return False
        # 检查特殊操作标志（这些操作需要立即执行）
        special_operations = {'clear_history', 'restore_now'}
        for op in special_operations:
            if op in config and config[op]:
                logger.debug(f"{self.plugin_name} 检测到特殊操作: {op}，需要重新初始化")
                return False
        # 计算当前配置的哈希值
        current_config_hash = self._calculate_config_hash(config)
        # 只有哈希完全一致才跳过，否则都重载
        if self._last_config_hash == current_config_hash:
            logger.debug(f"{self.plugin_name} 配置哈希未变更，跳过重新初始化 (哈希: {current_config_hash[:8]}...)")
            return True
        # 更新哈希值
        logger.debug(f"{self.plugin_name} 配置哈希已变更，需要重新初始化 (旧哈希: {self._last_config_hash[:8] if self._last_config_hash else 'None'}... -> 新哈希: {current_config_hash[:8]}...)")
        self._last_config_hash = current_config_hash
        return False

    def _calculate_config_hash(self, config: dict) -> str:
        """
        计算配置的哈希值，用于检测配置变更
        """
        try:
            # 全量纳入所有前端可配置项，确保每次保存都能生效
            critical_config = {}
            critical_keys = {
                'enabled', 'notify', 'onlyonce', 'retry_count', 'retry_interval', 'notification_message_type',
                'pve_host', 'ssh_port', 'ssh_username', 'ssh_password', 'ssh_key_file',
                'enable_local_backup', 'backup_path', 'keep_backup_num',
                'enable_webdav', 'webdav_url', 'webdav_username', 'webdav_password', 'webdav_path', 'webdav_keep_backup_num',
                'storage_name', 'backup_vmid', 'backup_mode', 'compress_mode', 'auto_delete_after_download', 'download_all_backups',
                'enable_restore', 'restore_force', 'restore_skip_existing', 'restore_storage', 'restore_vmid', 'restore_now', 'restore_file',
                'clear_history',
                'auto_cleanup_tmp'
                , 'cron'
            }
            for key in critical_keys:
                if key in config:
                    critical_config[key] = config[key]
            if 'auto_cleanup_tmp' not in critical_config:
                critical_config['auto_cleanup_tmp'] = True
            import json
            config_str = json.dumps(critical_config, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(config_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"{self.plugin_name} 计算配置哈希失败: {e}")
            return "error_hash"

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "notification_message_type": self._notification_message_type,  # 新增
            
            # SSH配置
            "pve_host": self._pve_host,
            "ssh_port": self._ssh_port,
            "ssh_username": self._ssh_username,
            "ssh_password": self._ssh_password,
            "ssh_key_file": self._ssh_key_file,
            
            # 备份配置
            "storage_name": self._storage_name,
            "backup_vmid": self._backup_vmid,
            "enable_local_backup": self._enable_local_backup,
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
            "backup_mode": self._backup_mode,
            "compress_mode": self._compress_mode,
            "auto_delete_after_download": self._auto_delete_after_download,
            "download_all_backups": self._download_all_backups,
            
            # WebDAV配置
            "enable_webdav": self._enable_webdav,
            "webdav_url": self._webdav_url,
            "webdav_username": self._webdav_username,
            "webdav_password": self._webdav_password,
            "webdav_path": self._webdav_path,
            "webdav_keep_backup_num": self._webdav_keep_backup_num,
            "clear_history": self._clear_history,
            
            # 恢复配置
            "enable_restore": self._enable_restore,
            "restore_storage": self._restore_storage,
            "restore_vmid": self._restore_vmid,
            "restore_force": self._restore_force,
            "restore_skip_existing": self._restore_skip_existing,
            "restore_file": self._restore_file,
            "restore_now": self._restore_now,
            "auto_cleanup_tmp": (self.get_config() or {}).get("auto_cleanup_tmp", True),
            
            # 新增系统日志清理配置
            "enable_log_cleanup": getattr(self, "_enable_log_cleanup", False),
            "log_journal_days": getattr(self, "_log_journal_days", 7),
            "log_vzdump_keep": getattr(self, "_log_vzdump_keep", 7),
            "log_pve_keep": getattr(self, "_log_pve_keep", 7),
            "log_dpkg_keep": getattr(self, "_log_dpkg_keep", 7),
            "cleanup_template_images": self._cleanup_template_images,
        })
        
        # 保存配置哈希
        if self._last_config_hash:
            self.save_data('last_config_hash', self._last_config_hash)

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """
        注册微信消息命令
        """
        return [
            {
                "cmd": "/pve",
                "event": EventType.PluginAction,
                "desc": "查看PVE主机状态信息",
                "category": "PVE",
                "data": {
                    "action": "pve_status"
                }
            },
            {
                "cmd": "/pve状态",
                "event": EventType.PluginAction,
                "desc": "查看PVE主机状态信息（别名）",
                "category": "PVE",
                "data": {
                    "action": "pve_status"
                }
            },
            {
                "cmd": "/pve主机",
                "event": EventType.PluginAction,
                "desc": "查看PVE主机状态信息（别名）",
                "category": "PVE",
                "data": {
                    "action": "pve_status"
                }
            },
            {
                "cmd": "/pve容器",
                "event": EventType.PluginAction,
                "desc": "查看所有容器/虚拟机状态",
                "category": "PVE",
                "data": {
                    "action": "container_status"
                }
            },
            {
                "cmd": "/容器",
                "event": EventType.PluginAction,
                "desc": "查看所有容器/虚拟机状态（别名）",
                "category": "PVE",
                "data": {
                    "action": "container_status"
                }
            },
            {
                "cmd": "/容器列表",
                "event": EventType.PluginAction,
                "desc": "查看所有容器/虚拟机状态（别名）",
                "category": "PVE",
                "data": {
                    "action": "container_status"
                }
            },
            {
                "cmd": "/pve帮助",
                "event": EventType.PluginAction,
                "desc": "查看PVE插件命令帮助",
                "category": "PVE",
                "data": {
                    "action": "help"
                }
            }
        ]

    def get_api(self) -> list:
        """
        API注册
        """
        return [
            {
                "path": "/config",
                "endpoint": self._get_config,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取插件配置"
            },
            {
                "path": "/config",
                "endpoint": self._save_config,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存插件配置"
            },
            {
                "path": "/status",
                "endpoint": self._get_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取插件运行状态"
            },
            {
                "path": "/backup_history",
                "endpoint": self._get_backup_history,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取备份历史记录"
            },
            {
                "path": "/restore_history",
                "endpoint": self._get_restore_history,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取恢复历史记录"
            },
            {
                "path": "/dashboard_data",
                "endpoint": self._get_dashboard_data,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取仪表板数据"
            },
            {
                "path": "/run_backup",
                "endpoint": self._run_backup,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "手动启动备份任务"
            },
            {
                "path": "/clear_history",
                "endpoint": self._clear_history_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清理备份和恢复历史"
            },
            {
                "path": "/pve_status",
                "endpoint": self._get_pve_status_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取PVE主机状态"
            },
            {
                "path": "/container_status",
                "endpoint": self._get_container_status_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取所有LXC容器状态"
            },
            {
                "path": "/available_backups",
                "endpoint": self._get_available_backups_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取可用备份文件列表"
            },
            {
                "path": "/delete_backup",
                "endpoint": self._delete_backup_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "删除备份文件"
            },
            {
                "path": "/restore",
                "endpoint": self._restore_backup_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "恢复备份文件"
            },
            {
                "path": "/download_backup",
                "endpoint": self._download_backup_api,
                "methods": ["GET"],
                "summary": "下载本地备份文件"
            },
            {
                "path": "/token",
                "endpoint": self._get_token,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取API令牌"
            },
            {
                "path": "/container_action",
                "endpoint": self._container_action_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "对指定虚拟机/容器执行操作"
            },
            {
                "path": "/container_snapshot",
                "endpoint": self._container_snapshot_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "对指定虚拟机/容器创建快照"
            },
            {
                "path": "/host_action",
                "endpoint": self._host_action_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "对PVE主机执行重启或关机"
            },
            {
                "path": "/cleanup_logs",
                "endpoint": self._cleanup_logs_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清理PVE系统日志"
            },
            {
                "path": "/cleanup_tmp",
                "endpoint": self._cleanup_tmp_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "清理PVE临时空间"
            },
            {
                "path": "/template_images",
                "endpoint": self._template_images_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "列出所有CT模板和ISO镜像"
            },
        ]

    @classmethod
    def get_instance(cls):
        return cls._instance

    def get_service(self) -> List[Dict[str, Any]]:
        return []

    @eventmanager.register(EventType.PluginAction)
    def handle_pve_command(self, event: Event = None):
        """
        处理PVE相关命令（通过事件系统）
        """
        if not event:
            return
        
        event_data = event.event_data
        if not event_data:
            return
        
        action = event_data.get("action")
        if action not in ["pve_status", "container_status", "help"]:
            return
        
        try:
            logger.info(f"{self.plugin_name} 收到命令事件: action={action}")
            
            # 检查SSH配置
            if not self._pve_host:
                error_msg = "❌ PVE主机未配置，请在插件配置中设置SSH连接信息"
                logger.warning(f"{self.plugin_name} {error_msg}")
                self.post_message(
                    channel=event_data.get("channel"),
                    title=error_msg,
                    userid=event_data.get("user")
                )
                return
            
            # 使用消息处理器处理命令
            if not self._message_handler:
                error_msg = "❌ 插件消息处理器未初始化，请重新加载插件"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.post_message(
                    channel=event_data.get("channel"),
                    title=error_msg,
                    userid=event_data.get("user")
                )
                return
            
            # 根据action获取消息内容
            result = None
            if action == "pve_status":
                result = self._message_handler.format_pve_status_message()
            elif action == "container_status":
                result = self._message_handler.format_container_status_message()
            elif action == "help":
                result = self._message_handler.format_help_message()
            
            if result:
                logger.info(f"{self.plugin_name} 命令处理成功，发送消息，长度: {len(result)}")
                self.post_message(
                    channel=event_data.get("channel"),
                    title=f"{self.plugin_name}",
                    text=result,
                    userid=event_data.get("user")
                )
            else:
                logger.warning(f"{self.plugin_name} 命令处理返回空结果: action={action}")
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 处理命令事件失败: {str(e)}", exc_info=True)
            error_msg = f"❌ 执行命令时发生错误: {str(e)}"
            self.post_message(
                channel=event_data.get("channel") if event_data else None,
                title=error_msg,
                userid=event_data.get("user") if event_data else None
            )

    def get_form(self):
        """
        Vue模式下，返回None和当前配置，所有UI交给前端Vue组件
        """
        return None, self.get_config() or {}

    def get_page(self):
        """
        Vue模式下，返回None，所有页面渲染交给前端Vue组件
        """
        return None

    def run_backup_job(self):
        """执行备份任务"""
        # 如果已有任务在运行,直接返回
        if not self._lock:
            self._lock = threading.Lock()
        if not self._global_task_lock:
            self._global_task_lock = threading.Lock()
            
        # 检查是否有恢复任务正在执行（恢复任务优先级更高）
        if self._restore_lock and hasattr(self._restore_lock, 'locked') and self._restore_lock.locked():
            logger.info(f"{self.plugin_name} 检测到恢复任务正在执行，备份任务跳过（恢复任务优先级更高）！")
            return
            
        # 尝试获取全局任务锁，如果获取不到说明有其他任务在运行
        if not self._global_task_lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 检测到其他任务正在执行，备份任务跳过！")
            return
            
        # 尝试获取备份锁，如果获取不到说明有备份任务在运行
        if not self._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有备份任务正在执行，本次调度跳过！")
            self._global_task_lock.release()  # 释放全局锁
            return
            
        history_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": None,
            "message": "任务开始"
        }
        self._backup_activity = "任务开始"
            
        try:
            self._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            if not self._pve_host or not self._ssh_username or (not self._ssh_password and not self._ssh_key_file):
                error_msg = "配置不完整：PVE主机地址、SSH用户名或SSH认证信息(密码/密钥)未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg, backup_details={})
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return

            if not self._backup_path:
                error_msg = "备份路径未配置且无法设置默认路径。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg, backup_details={})
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return

            try:
                Path(self._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"创建本地备份目录 {self._backup_path} 失败: {e}"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg, backup_details={})
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            backup_details_final = {}
            
            for i in range(self._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self._retry_count +1} 次备份尝试...")
                current_try_success, current_try_error_msg, current_try_downloaded_file, current_try_backup_details = self._perform_backup_once()
                
                if current_try_success:
                    success_final = True
                    downloaded_file_final = current_try_downloaded_file
                    backup_details_final = current_try_backup_details
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
            
            # 只在所有尝试都失败时保存一条失败历史
            if not success_final:
                history_entry["success"] = False
                history_entry["filename"] = None
                history_entry["message"] = f"备份失败: {error_msg_final}"
                self._save_backup_history_entry(history_entry)
            
            self._send_notification(success=success_final, message="备份成功" if success_final else f"备份失败: {error_msg_final}", filename=downloaded_file_final, backup_details=backup_details_final)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
            history_entry["message"] = f"任务执行主流程出错: {str(e)}"
            self._send_notification(success=False, message=history_entry["message"], backup_details={})
            self._save_backup_history_entry(history_entry)
        finally:
            self._running = False
            self._backup_activity = "空闲"
            # 不再在finally里保存合并历史
            if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                try:
                    self._lock.release()
                except RuntimeError:
                    pass
            if self._global_task_lock and hasattr(self._global_task_lock, 'locked') and self._global_task_lock.locked():
                try:
                    self._global_task_lock.release()
                except RuntimeError:
                    pass
            logger.info(f"{self.plugin_name} 任务执行完成。")

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str], Dict[str, Any]]:
        """
        执行一次备份操作
        :return: (是否成功, 错误消息, 备份文件名, 备份详情)
        """
        if not self._pve_host:
            return False, "未配置PVE主机地址", None, {}

        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None
        
        try:
            # 尝试SSH连接
            try:
                if self._ssh_key_file:
                    # 使用密钥认证
                    private_key = paramiko.RSAKey.from_private_key_file(self._ssh_key_file)
                    ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, pkey=private_key)
                else:
                    # 使用密码认证
                    ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, password=self._ssh_password)
                logger.info(f"{self.plugin_name} SSH连接成功")
            except Exception as e:
                return False, f"SSH连接失败: {str(e)}", None, {}

            # 1. 创建备份
            logger.info(f"{self.plugin_name} 开始创建备份...")
            
            # 检查PVE端是否有正在运行的备份任务
            check_running_cmd = "ps aux | grep vzdump | grep -v grep"
            stdin, stdout, stderr = ssh.exec_command(check_running_cmd)
            running_backups = stdout.read().decode().strip()
            
            if running_backups:
                logger.warning(f"{self.plugin_name}  logger.warning ")
                logger.info(f"{self.plugin_name} 正在运行的备份进程: {running_backups}")
                return False, "PVE端已有备份任务在运行，为避免冲突跳过本次备份", None, {}
            
            # 检查是否指定了要备份的容器ID
            if not self._backup_vmid or self._backup_vmid.strip() == "":
                # 如果没有指定容器ID，尝试获取所有可用的容器
                logger.info(f"{self.plugin_name} 未指定容器ID，尝试获取所有可用的容器...")
                list_cmd = "qm list | grep -E '^[0-9]+' | awk '{print $1}' | tr '\n' ',' | sed 's/,$//'"
                stdin, stdout, stderr = ssh.exec_command(list_cmd)
                available_vmids = stdout.read().decode().strip()
                
                if not available_vmids:
                    # 如果还是没有找到，尝试获取所有LXC容器
                    list_cmd = "pct list | grep -E '^[0-9]+' | awk '{print $1}' | tr '\n' ',' | sed 's/,$//'"
                    stdin, stdout, stderr = ssh.exec_command(list_cmd)
                    available_vmids = stdout.read().decode().strip()
                
                if not available_vmids:
                    return False, "未找到任何可用的虚拟机或容器，请检查PVE主机状态或手动指定容器ID", None, {}
                
                self._backup_vmid = available_vmids
                logger.info(f"{self.plugin_name} 自动获取到容器ID: {self._backup_vmid}")
            
            # 构建vzdump命令
            backup_cmd = f"vzdump {self._backup_vmid} "
            backup_cmd += f"--compress {self._compress_mode} "
            backup_cmd += f"--mode {self._backup_mode} "
            backup_cmd += f"--storage {self._storage_name} "
            
            # 执行备份命令
            logger.info(f"{self.plugin_name} 执行命令: {backup_cmd}")
            stdin, stdout, stderr = ssh.exec_command(backup_cmd)
    
            created_backup_files = []
            # 实时输出vzdump日志
            while True:
                line = stdout.readline()
                if not line:
                    break
                line = line.strip()
                #logger.info(f"{self.plugin_name} vzdump输出: {line}")
                # 从vzdump日志中解析出备份文件名
                match = re.search(r"creating vzdump archive '(.+)'", line)
                if match:
                    filepath = match.group(1)
                    logger.info(f"{self.plugin_name} 从日志中检测到备份文件: {filepath}")
                    created_backup_files.append(filepath)
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_output = stderr.read().decode().strip()
                
                # 检查是否是手动暂停或中断的情况
                if "got unexpected control message" in error_output or exit_status == -1:
                    # 检查PVE端是否有正在运行的备份任务
                    check_backup_cmd = "ps aux | grep vzdump | grep -v grep"
                    stdin, stdout, stderr = ssh.exec_command(check_backup_cmd)
                    running_backups = stdout.read().decode().strip()
                    
                    if running_backups:
                        error_msg = f"备份任务被手动暂停或中断。检测到PVE端仍有备份进程在运行，可能是您在PVE界面手动暂停了备份任务。"
                        logger.warning(f"{self.plugin_name} {error_msg}")
                        logger.info(f"{self.plugin_name} 检测到的备份进程: {running_backups}")
                    else:
                        error_msg = f"备份任务被中断。SSH连接出现意外控制消息，可能是网络问题或PVE端任务被强制终止。"
                        logger.warning(f"{self.plugin_name} {error_msg}")
                    
                    return False, error_msg, None, {}
                else:
                    # 其他类型的错误
                    return False, f"备份创建失败: {error_output}", None, {}

            if not created_backup_files:
                return False, "未能从vzdump日志中解析出备份文件名, 无法进行下载。", None, {}

            files_to_download = []
            if self._download_all_backups:
                files_to_download = created_backup_files
            elif created_backup_files:
                # 仅下载最后一个，即最新的
                files_to_download.append(created_backup_files[-1])

            if not files_to_download:
                return False, "没有找到需要下载的备份文件。", None, {}
            
            #logger.info(f"{self.plugin_name} 准备下载 {len(files_to_download)} 个文件: {', '.join(files_to_download)}")

            sftp = ssh.open_sftp()
            
            all_downloads_successful = True
            downloaded_files_info = []
            filenames = []
            vmids = []

            for remote_file_path in files_to_download:
                success, error_msg, filename, details = self._download_single_backup_file(ssh, sftp, remote_file_path, os.path.basename(remote_file_path))
                if success:
                    downloaded_files_info.append({
                        "filename": filename,
                        "details": details
                    })
                    filenames.append(filename)
                    # 提取VMID
                    vmid = self._extract_vmid_from_backup(filename)
                    if vmid:
                        vmids.append(vmid)
                else:
                    all_downloads_successful = False
                    logger.error(f"{self.plugin_name} 处理文件 {remote_file_path} 失败: {error_msg}")

            # --- 所有文件处理完成后，统一执行清理 ---
            if self._enable_local_backup:
                self._cleanup_old_backups()
            if self._enable_webdav and self._webdav_url:
                logger.info(f"{self.plugin_name} 开始清理WebDAV旧备份...")
                self._cleanup_webdav_backups()

            # 合并历史记录逻辑
            if downloaded_files_info:
                # 成功时保存一条合并历史
                history_entry = {
                    "timestamp": time.time(),
                    "success": True,
                    "filename": ", ".join(filenames),
                    "message": f"备份成功 [VMID: {', '.join(vmids)}]"
                }
                self._save_backup_history_entry(history_entry)
                # 返回最后一个成功下载的文件信息
                last_file = downloaded_files_info[-1]
                return True, None, last_file["filename"], {
                    "downloaded_files": downloaded_files_info,
                    "last_file_details": last_file["details"]
                }
            else:
                # 失败时只保存一条失败历史
                history_entry = {
                    "timestamp": time.time(),
                    "success": False,
                    "filename": None,
                    "message": "所有备份文件下载失败，详情请查看日志"
                }
                self._save_backup_history_entry(history_entry)
                return False, "所有备份文件下载失败，详情请查看日志", None, {}

        except Exception as e:
            error_msg = f"备份过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None, {}
            
        finally:
            # 确保关闭SFTP和SSH连接
            if sftp:
                try:
                    sftp.close()
                except:
                    pass
            if ssh:
                try:
                    ssh.close()
                except:
                    pass
            try:
                # 优先读取 self.auto_cleanup_tmp，没有就 get_config()
                if hasattr(self, 'auto_cleanup_tmp'):
                    auto_cleanup = getattr(self, 'auto_cleanup_tmp', False)
                else:
                    auto_cleanup = self.get_config().get('auto_cleanup_tmp', False)
                if auto_cleanup:
                    count, error = clean_pve_tmp_files(
                        self._pve_host,
                        self._ssh_port,
                        self._ssh_username,
                        self._ssh_password,
                        self._ssh_key_file
                    )
                    if error:
                        logger.warning(f"{self.plugin_name} 自动清理临时空间失败: {error}")
                    else:
                        logger.info(f"{self.plugin_name} 自动清理临时空间完成，已清理 {count} 个 .tmp 文件")
                else:
                    logger.info(f"{self.plugin_name} 未启用自动清理临时空间，跳过清理。")
            except Exception as e:
                logger.warning(f"{self.plugin_name} 自动清理临时空间异常: {e}")

    def _cleanup_old_backups(self):
        if not self._backup_path: return
        # 如果保留数量为0，表示保留全部备份，不进行清理
        if self._keep_backup_num <= 0:
            logger.info(f"{self.plugin_name} 保留数量设置为0，保留全部本地备份文件")
            return
        try:
            logger.info(f"{self.plugin_name} 开始清理本地备份目录: {self._backup_path}")
            backup_dir = Path(self._backup_path)
            if not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 本地备份目录 {self._backup_path} 不存在，无需清理。")
                return

            files = []
            for f_path_obj in backup_dir.iterdir():
                if f_path_obj.is_file() and (
                    f_path_obj.name.endswith('.tar.gz') or 
                    f_path_obj.name.endswith('.tar.lzo') or 
                    f_path_obj.name.endswith('.tar.zst') or
                    f_path_obj.name.endswith('.vma.gz') or 
                    f_path_obj.name.endswith('.vma.lzo') or 
                    f_path_obj.name.endswith('.vma.zst')
                ):
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
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个旧 Proxmox 备份文件需要删除。")
                for f_info in files_to_delete:
                    try:
                        f_info['path'].unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {f_info['name']}")
                    except OSError as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {f_info['name']} 失败: {e}")
            else:
                logger.info(f"{self.plugin_name} 当前 Proxmox 备份文件数量 ({len(files)}) 未超过保留限制 ({self._keep_backup_num})，无需清理。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时发生错误: {e}")

    def _create_webdav_directories(self, auth, base_url: str, path: str) -> Tuple[bool, Optional[str]]:
        """递归创建WebDAV目录"""
        try:
            import requests
            from urllib.parse import urljoin, urlparse

            # 检测是否为Alist服务器（端口5244）
            parsed_url = urlparse(base_url)
            is_alist = parsed_url.port == 5244 or '5244' in base_url

            # 分割路径
            path_parts = [p for p in path.split('/') if p]
            current_path = base_url.rstrip('/')

            # 如果是Alist服务器且base_url不包含/dav,添加dav前缀
            if is_alist and '/dav' not in current_path:
                current_path = f"{current_path}/dav"

            # 逐级创建目录
            for part in path_parts:
                current_path = f"{current_path}/{part}"
                
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
                        # 如果是405错误(Method Not Allowed),可能目录已存在
                        if mkdir_response.status_code == 405:
                            logger.warning(f"{self.plugin_name} 目录可能已存在: {current_path}")
                            continue
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
            
            # 检测是否为Alist服务器（端口5244）
            is_alist = parsed_url.port == 5244 or '5244' in self._webdav_url
            
            # 构建可能的上传URL列表
            possible_upload_urls = []
            
            if is_alist:
                # 如果base_url不包含/dav,添加dav前缀
                if '/dav' not in base_url:
                    base_url = f"{base_url}/dav"
                
                # Alist的特殊路径结构
                if webdav_path:
                    possible_upload_urls.extend([
                        f"{base_url}/{webdav_path}/{filename}"      # Alist标准路径
                    ])
                else:
                    possible_upload_urls.extend([
                        f"{base_url}/{filename}"      # Alist标准路径
                    ])
            else:
                # 标准WebDAV路径
                if webdav_path:
                    possible_upload_urls.extend([
                        f"{base_url}/{webdav_path}/{filename}",
                        f"{base_url}/dav/{webdav_path}/{filename}",
                        f"{base_url}/remote.php/webdav/{webdav_path}/{filename}",
                        f"{base_url}/dav/files/{self._webdav_username}/{webdav_path}/{filename}"
                    ])
                else:
                    possible_upload_urls.extend([
                        f"{base_url}/{filename}",
                        f"{base_url}/dav/{filename}",
                        f"{base_url}/remote.php/webdav/{filename}"
                    ])

            # 准备认证信息
            auth_methods = [
                HTTPBasicAuth(self._webdav_username, self._webdav_password),
                HTTPDigestAuth(self._webdav_username, self._webdav_password),
                (self._webdav_username, self._webdav_password)
            ]

            # 设置重试次数和间隔
            max_retries = 3  # 最大重试次数
            retry_interval = 5  # 重试间隔(秒)
            retry_count = 0

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
                        timeout=30,  # 增加超时时间
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
                    logger.warning(f"{self.plugin_name} 创建目录失败，但继续尝试上传: {create_error}")

            # 准备上传请求头
            headers = {
                'Content-Type': 'application/octet-stream',
                'User-Agent': 'MoviePilot/1.0',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }

            # 尝试多种上传方法
            upload_methods = [
                ('PUT', headers),
                ('PUT', {**headers, 'Content-Type': 'application/x-tar'}),
                ('PUT', {**headers, 'Overwrite': 'T'}),
                ('POST', headers),
                ('POST', {**headers, 'Content-Type': 'application/x-tar'}),
                ('POST', {**headers, 'Overwrite': 'T'})
            ]

            # 获取文件大小
            file_size = os.path.getsize(local_file_path)
            chunk_size = 8192 * 1024

            # 尝试每个URL和每种方法
            for upload_url in possible_upload_urls:
                logger.info(f"{self.plugin_name} 尝试上传到URL: {upload_url}")
                
                for method, method_headers in upload_methods:
                    retry_count = 0
                    while retry_count <= max_retries:
                        try:
                            if retry_count > 0:
                                logger.info(f"{self.plugin_name} 第{retry_count}次重试上传...")
                                time.sleep(retry_interval)
                            
                            logger.info(f"{self.plugin_name} 尝试使用 {method} 方法上传到WebDAV...")
                            
                            # 使用requests的data参数流式上传
                            with open(local_file_path, 'rb') as f:
                                uploaded_size = 0
                                last_progress = -1  # 记录上次显示的进度
                                last_activity_time = time.time()  # 记录最后活动时间
                                
                                def upload_callback():
                                    nonlocal uploaded_size, last_progress, last_activity_time
                                    while True:
                                        chunk = f.read(chunk_size)
                                        if not chunk:
                                            break
                                        uploaded_size += len(chunk)
                                        current_time = time.time()
                                        
                                        # 检查是否超过30秒没有进度更新
                                        if current_time - last_activity_time > 30:
                                            logger.warning(f"{self.plugin_name} 上传可能停滞，已有30秒没有进度更新")
                                        
                                        # 更新最后活动时间
                                        last_activity_time = current_time
                                        
                                        # 计算进度
                                        if file_size > 0:
                                            progress = (uploaded_size / file_size) * 100
                                            # 每10%显示一次进度
                                            current_progress = int(progress / 10) * 10
                                            if current_progress > last_progress:
                                                self._backup_activity = f"上传WebDAV中: {progress:.1f}%"
                                                logger.info(f"{self.plugin_name} WebDAV上传进度: {progress:.1f}%")
                                                last_progress = current_progress
                                        yield chunk
                                
                                # 设置请求超时
                                timeout = max(300, int(file_size / (1024 * 1024) * 2))  # 根据文件大小动态调整超时时间,最少5分钟
                                
                                if method == 'PUT':
                                    response = requests.put(
                                        upload_url,
                                        data=upload_callback(),
                                        auth=successful_auth,
                                        headers=method_headers,
                                        timeout=timeout,
                                        verify=False
                                    )
                                else:  # POST
                                    response = requests.post(
                                        upload_url,
                                        data=upload_callback(),
                                        auth=successful_auth,
                                        headers=method_headers,
                                        timeout=timeout,
                                        verify=False
                                    )

                            if response.status_code in [200, 201, 204]:
                                logger.info(f"{self.plugin_name} 成功使用 {method} 方法上传文件到WebDAV: {upload_url}")
                                return True, None
                            elif response.status_code == 405:
                                logger.warning(f"{self.plugin_name} {method} 方法不被支持，状态码: 405")
                                break  # 直接尝试下一种方法
                            elif response.status_code == 404:
                                logger.warning(f"{self.plugin_name} URL不存在，状态码: 404 - {upload_url}")
                                break  # 这个URL不存在，尝试下一个URL
                            elif response.status_code == 409:
                                # 文件冲突，这是WebDAV标准中的常见问题
                                logger.warning(f"{self.plugin_name} WebDAV文件冲突(409)，尝试使用Overwrite头: {upload_url}")
                                # 添加Overwrite头并重试
                                method_headers['Overwrite'] = 'T'
                                continue
                            elif response.status_code == 507:
                                logger.error(f"{self.plugin_name} WebDAV服务器存储空间不足，状态码: 507")
                                return False, "WebDAV服务器存储空间不足"
                            else:
                                error_msg = f"{method} 方法上传失败，状态码: {response.status_code}, 响应: {response.text}"
                                logger.warning(f"{self.plugin_name} {error_msg}")
                                if retry_count < max_retries:
                                    retry_count += 1
                                    continue
                                break  # 达到最大重试次数，尝试下一种方法

                        except requests.exceptions.Timeout:
                            error_msg = "上传请求超时"
                            logger.warning(f"{self.plugin_name} {error_msg}")
                            if retry_count < max_retries:
                                retry_count += 1
                                continue
                            break
                            
                        except requests.exceptions.RequestException as e:
                            error_msg = f"上传请求失败: {str(e)}"
                            logger.warning(f"{self.plugin_name} {error_msg}")
                            if retry_count < max_retries:
                                retry_count += 1
                                continue
                            break

            # 所有URL和方法都失败了
            error_msg = f"WebDAV上传失败：所有上传URL和方法均失败。\n\n尝试的URL:\n" + "\n".join([f"- {url}" for url in possible_upload_urls]) + f"\n\n可能的原因：\n1. WebDAV服务器不支持PUT/POST方法\n2. 服务器配置不允许文件上传\n3. 认证信息不正确或权限不足\n4. 服务器需要特定的请求头或协议版本\n5. URL路径构建不正确\n\n建议：\n1. 检查WebDAV服务器配置，确保支持PUT方法\n2. 验证用户权限，确保有写入权限\n3. 尝试使用其他WebDAV客户端测试\n4. 联系WebDAV服务提供商确认支持的功能\n5. 检查WebDAV路径配置是否正确"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"WebDAV上传过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

    def _cleanup_webdav_backups(self):
        """清理WebDAV上的旧备份文件"""
        if not self._enable_webdav or not self._webdav_url:
            return
        # 如果保留数量为0，表示保留全部备份，不进行清理
        if self._webdav_keep_backup_num <= 0:
            logger.info(f"{self.plugin_name} WebDAV保留数量设置为0，保留全部WebDAV备份文件")
            return

        try:
            import requests
            from urllib.parse import urljoin, quote, urlparse
            from xml.etree import ElementTree

            # 构建WebDAV基础URL
            base_url = self._webdav_url.rstrip('/')
            webdav_path = self._webdav_path.lstrip('/')
            
            parsed_url = urlparse(self._webdav_url)
            is_alist = parsed_url.port == 5244 or '5244' in self._webdav_url
            
            # 构建可能的URL列表
            possible_urls = []
            if is_alist:
                if webdav_path:
                    possible_urls.extend([
                        f"{base_url}/dav/{webdav_path}", 
                        f"{base_url}/{webdav_path}"
                    ])
                else:
                    possible_urls.extend([
                        f"{base_url}/dav",
                        f"{base_url}" 
                    ])
            else:
                # 标准WebDAV路径
                if webdav_path:
                    possible_urls.extend([
                        f"{base_url}/{webdav_path}",
                        f"{base_url}/dav/{webdav_path}",
                        f"{base_url}/remote.php/webdav/{webdav_path}",
                        f"{base_url}/dav/files/{self._webdav_username}/{webdav_path}"
                    ])
                else:
                    possible_urls.extend([
                        f"{base_url}",
                        f"{base_url}/dav",
                        f"{base_url}/remote.php/webdav"
                    ])
            
            # 尝试不同的URL结构
            working_url = None
            for test_url in possible_urls:
                try:
                    response = requests.request(
                        'PROPFIND',
                        test_url,
                        auth=(self._webdav_username, self._webdav_password),
                        headers={
                            'Depth': '1',
                            'Content-Type': 'application/xml',
                            'Accept': '*/*',
                            'User-Agent': 'MoviePilot/1.0'
                        },
                        timeout=10,
                        verify=False
                    )
                    if response.status_code == 207:
                        working_url = test_url
                        logger.info(f"{self.plugin_name} 找到可用的WebDAV清理URL: {working_url}")
                        break
                except Exception as e:
                    logger.debug(f"{self.plugin_name} 测试WebDAV清理URL失败: {test_url}, 错误: {e}")
                    continue
            
            if not working_url:
                logger.warning(f"{self.plugin_name} 无法找到可用的WebDAV清理URL，跳过清理")
                return
            
            # 发送PROPFIND请求获取文件列表
            headers = {
                'Depth': '1',
                'Content-Type': 'application/xml',
                'Accept': '*/*',
                'User-Agent': 'MoviePilot/1.0'
            }
            
            response = requests.request(
                'PROPFIND',
                working_url,
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
                # 只处理Proxmox备份文件
                if not (file_path.lower().endswith('.tar.gz') or 
                       file_path.lower().endswith('.tar.lzo') or 
                       file_path.lower().endswith('.tar.zst') or
                       file_path.lower().endswith('.vma.gz') or 
                       file_path.lower().endswith('.vma.lzo') or 
                       file_path.lower().endswith('.vma.zst')):
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
                        
                        # 构建删除URL
                        delete_url = urljoin(working_url + '/', file_path)
                        filename = os.path.basename(file_path)

                        # 删除文件
                        delete_response = requests.delete(
                            delete_url,
                            auth=(self._webdav_username, self._webdav_password),
                            headers={'User-Agent': 'MoviePilot/1.0'},
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

    def _clear_all_history(self):
        """清理所有历史记录"""
        try:
            self.save_data('backup_history', [])
            self.save_data('restore_history', [])
            logger.info(f"{self.plugin_name} 已清理所有历史记录")
            if self._notify:
                self._send_notification(
                    success=True,
                    message="已成功清理所有备份和恢复历史记录",
                    is_clear_history=True,
                    backup_details={}
                )
        except Exception as e:
            error_msg = f"清理历史记录失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            if self._notify:
                self._send_notification(
                    success=False,
                    message=error_msg,
                    is_clear_history=True,
                    backup_details={}
                )

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None, is_clear_history: bool = False, backup_details: Optional[Dict[str, Any]] = None):
        """发送通知（分隔线+emoji+结构化字段+结尾祝贺语，区分单/多容器）"""
        if not self._notify:
            return
        try:
            # 判断单容器还是多容器
            file_list = []
            if backup_details and "downloaded_files" in backup_details and backup_details["downloaded_files"]:
                file_list = [f["filename"] for f in backup_details["downloaded_files"]]
            is_multi = len(file_list) > 1
            
            # 标题
            status_emoji = "✅" if success else "❌"
            title_emoji = "🛠️"
            
            # 根据操作类型设置不同的标题
            if is_clear_history:
                title = f"{title_emoji} {self.plugin_name} 清理历史记录{'成功' if success else '失败'}"
            elif is_multi:
                title = f"{title_emoji} {self.plugin_name} 多容器备份{'成功' if success else '失败'}"
            else:
                title = f"{title_emoji} {self.plugin_name} 备份{'成功' if success else '失败'}"
            
            divider = "━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            # 根据操作类型构建不同的通知内容
            if is_clear_history:
                # 清理历史记录专用格式
                status_str = f"{status_emoji} 清理历史记录{'成功' if success else '失败'}"
                host_str = self._pve_host or "-"
                detail_str = message.strip() if message else ("历史记录清理完成" if success else "历史记录清理失败")
                end_str = "✨ 历史记录清理完成！" if success else "❗ 历史记录清理失败，请检查日志！"
                
                text_content = (
                    f"{divider}\n"
                    f"📣 状态：{status_str}\n"
                    f"🔗 主机：{host_str}\n"
                    f"📋 详情：{detail_str}\n"
                    f"{divider}\n"
                    f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"{end_str}"
                )
            else:
                # 备份操作格式
                status_str = f"{status_emoji} 备份{'成功' if success else '失败'}"
                host_str = self._pve_host or "-"
                if is_multi:
                    file_str = "\n".join(file_list)
                elif file_list:
                    file_str = file_list[0]
                else:
                    file_str = "-"
                path_str = "-"
                if backup_details and "downloaded_files" in backup_details and backup_details["downloaded_files"]:
                    details = backup_details["downloaded_files"][0]["details"]
                    if details["local_backup"]["enabled"] and details["local_backup"]["success"]:
                        path_str = details["local_backup"]["path"]
                # 详情
                if is_multi:
                    detail_str = f"共备份 {len(file_list)} 个容器。" + (message.strip() if message else ("备份已成功完成" if success else "备份失败，请检查日志"))
                else:
                    detail_str = message.strip() if message else ("备份已成功完成" if success else "备份失败，请检查日志")
                # 结尾祝贺语
                end_str = "✨ 备份已成功完成！" if success else "❗ 备份失败，请检查日志！"
                
                text_content = (
                    f"{divider}\n"
                    f"📣 状态：{status_str}\n"
                    f"🔗 主机：{host_str}\n"
                    f"�� 备份文件：{file_str}\n"
                    f"📁 路径：{path_str}\n"
                    f"📋 详情：{detail_str}\n"
                    f"{divider}\n"
                    f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"{end_str}"
                )
            
            mtype = getattr(NotificationType, self._notification_message_type, NotificationType.Plugin)
            self.post_message(
                title=title,
                text=text_content,
                mtype=mtype
            )
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {str(e)}")

    def _load_backup_history(self) -> List[Dict[str, Any]]:
        """加载备份历史记录"""
        history = self.get_data('backup_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history

    def _save_backup_history_entry(self, entry: Dict[str, Any]):
        """保存单条备份历史记录"""
        try:
            # 加载现有历史记录
            history = self._load_backup_history()
            
            # 添加新记录到开头
            history.insert(0, entry)
            
            # 如果超过最大记录数，删除旧记录
            if len(history) > self._max_history_entries:
                history = history[:self._max_history_entries]
            
            # 保存更新后的历史记录
            self.save_data('backup_history', history)
            logger.debug(f"{self.plugin_name} 已保存备份历史记录")
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存备份历史记录失败: {str(e)}")

    def _get_available_backups(self) -> List[Dict[str, Any]]:
        """获取可用的备份文件列表"""
        backups = []
        
        # 获取本地备份文件
        if self._enable_local_backup:
            try:
                # 如果_backup_path为空，使用默认路径
                backup_dir = Path(self._backup_path) if self._backup_path else Path(self.get_data_path()) / "actual_backups"
                if backup_dir.is_dir():
                    for file_path in backup_dir.iterdir():
                        if file_path.is_file() and (
                            file_path.name.endswith('.tar.gz') or 
                            file_path.name.endswith('.tar.lzo') or 
                            file_path.name.endswith('.tar.zst') or
                            file_path.name.endswith('.vma.gz') or 
                            file_path.name.endswith('.vma.lzo') or 
                            file_path.name.endswith('.vma.zst')
                        ):
                            try:
                                stat = file_path.stat()
                                size_mb = stat.st_size / (1024 * 1024)
                                time_str = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                                
                                backups.append({
                                    'filename': file_path.name,
                                    'path': str(file_path),
                                    'size_mb': size_mb,
                                    'time_str': time_str,
                                    'source': '本地备份'
                                })
                            except Exception as e:
                                logger.error(f"{self.plugin_name} 处理本地备份文件 {file_path.name} 时出错: {e}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取本地备份文件列表失败: {e}")
        
        # 获取WebDAV备份文件
        if self._enable_webdav and self._webdav_url:
            try:
                webdav_backups = self._get_webdav_backups()
                backups.extend(webdav_backups)
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表失败: {e}")
        
        # 按时间排序（最新的在前）
        backups.sort(key=lambda x: datetime.strptime(x['time_str'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        return backups

    def _get_webdav_backups(self) -> List[Dict[str, Any]]:
        """获取WebDAV上的备份文件列表"""
        backups = []
        
        try:
            import requests
            from urllib.parse import urljoin, urlparse
            from xml.etree import ElementTree
            
            # 构建WebDAV基础URL
            base_url = self._webdav_url.rstrip('/')
            webdav_path = self._webdav_path.lstrip('/')
            
            # 检测是否为Alist服务器（端口5244）
            parsed_url = urlparse(self._webdav_url)
            is_alist = parsed_url.port == 5244 or '5244' in self._webdav_url
            
            # 构建可能的URL列表
            possible_urls = []
            if is_alist:
                # Alist的特殊路径结构
                if webdav_path:
                    possible_urls.extend([
                        f"{base_url}/dav/{webdav_path}",
                        f"{base_url}/{webdav_path}" 
                    ])
                else:
                    possible_urls.extend([
                        f"{base_url}/dav",
                        f"{base_url}"
                    ])
            else:
                # 标准WebDAV路径
                if webdav_path:
                    possible_urls.extend([
                        f"{base_url}/{webdav_path}",
                        f"{base_url}/dav/{webdav_path}",
                        f"{base_url}/remote.php/webdav/{webdav_path}",
                        f"{base_url}/dav/files/{self._webdav_username}/{webdav_path}"
                    ])
                else:
                    possible_urls.extend([
                        f"{base_url}",
                        f"{base_url}/dav",
                        f"{base_url}/remote.php/webdav"
                    ])
            
            # 尝试不同的URL结构
            working_url = None
            for test_url in possible_urls:
                try:
                    response = requests.request(
                        'PROPFIND',
                        test_url,
                        auth=(self._webdav_username, self._webdav_password),
                        headers={
                            'Depth': '1',
                            'Content-Type': 'application/xml',
                            'Accept': '*/*',
                            'User-Agent': 'MoviePilot/1.0'
                        },
                        timeout=10,
                        verify=False
                    )
                    if response.status_code == 207:
                        working_url = test_url
                        break
                except Exception as e:
                    logger.debug(f"{self.plugin_name} 测试WebDAV清理URL失败: {test_url}, 错误: {e}")
                    continue
            
            if not working_url:
                return backups
            
            # 发送PROPFIND请求获取文件列表
            response = requests.request(
                'PROPFIND',
                working_url,
                auth=(self._webdav_username, self._webdav_password),
                headers={
                    'Depth': '1',
                    'Content-Type': 'application/xml',
                    'Accept': '*/*',
                    'User-Agent': 'MoviePilot/1.0'
                },
                timeout=30,
                verify=False
            )

            if response.status_code != 207:
                return backups

            # 解析XML响应
            root = ElementTree.fromstring(response.content)
            
            for response_elem in root.findall('.//{DAV:}response'):
                href = response_elem.find('.//{DAV:}href')
                if href is None or not href.text:
                    continue

                file_path = href.text
                # 只处理Proxmox备份文件
                if not (file_path.lower().endswith('.tar.gz') or 
                       file_path.lower().endswith('.tar.lzo') or 
                       file_path.lower().endswith('.tar.zst') or
                       file_path.lower().endswith('.vma.gz') or 
                       file_path.lower().endswith('.vma.lzo') or 
                       file_path.lower().endswith('.vma.zst')):
                    continue

                # 获取文件信息
                propstat = response_elem.find('.//{DAV:}propstat')
                if propstat is None:
                    continue

                prop = propstat.find('.//{DAV:}prop')
                if prop is None:
                    continue

                # 获取文件大小
                getcontentlength = prop.find('.//{DAV:}getcontentlength')
                size_mb = 0
                if getcontentlength is not None and getcontentlength.text:
                    size_mb = int(getcontentlength.text) / (1024 * 1024)

                # 获取文件修改时间
                getlastmodified = prop.find('.//{DAV:}getlastmodified')
                time_str = "未知"
                if getlastmodified is not None and getlastmodified.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        file_time = parsedate_to_datetime(getlastmodified.text)
                        time_str = file_time.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass

                filename = os.path.basename(file_path)
                backups.append({
                    'filename': filename,
                    'path': file_path,
                    'size_mb': size_mb,
                    'time_str': time_str,
                    'source': 'WebDAV备份'
                })

        except Exception as e:
            logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表时发生错误: {str(e)}")
        
        return backups

    def run_restore_job(self, filename: str, source: str = "本地备份", restore_vmid: str = "", restore_force: bool = False, restore_skip_existing: bool = True):
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
            "target_vmid": restore_vmid or "自动",
            "message": "恢复任务开始"
        }
        self._restore_activity = "任务开始"
            
        try:
            logger.info(f"{self.plugin_name} 开始执行恢复任务，文件: {filename}, 来源: {source}, 目标VMID: {restore_vmid}")

            if not self._pve_host or not self._ssh_username or (not self._ssh_password and not self._ssh_key_file):
                error_msg = "配置不完整：PVE主机地址、SSH用户名或SSH认证信息(密码/密钥)未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_restore_notification(success=False, message=error_msg, filename=filename)
                restore_entry["message"] = error_msg
                self._save_restore_history_entry(restore_entry)
                return

            # 执行恢复操作
            success, error_msg, target_vmid = self._perform_restore_once(filename, source, restore_vmid, restore_force, restore_skip_existing)
            
            restore_entry["success"] = success
            restore_entry["target_vmid"] = target_vmid or restore_vmid or "自动"
            restore_entry["message"] = "恢复成功" if success else f"恢复失败: {error_msg}"
            
            self._send_restore_notification(success=success, message=restore_entry["message"], filename=filename, target_vmid=target_vmid)
                
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

    def _perform_restore_once(self, filename: str, source: str, restore_vmid: str = "", restore_force: bool = False, restore_skip_existing: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行一次恢复操作
        :return: (是否成功, 错误消息, 目标VMID)
        """
        if not self._pve_host:
            return False, "未配置PVE主机地址", None

        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None
        
        try:
            # 尝试SSH连接
            try:
                if self._ssh_key_file:
                    private_key = paramiko.RSAKey.from_private_key_file(self._ssh_key_file)
                    ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, pkey=private_key)
                else:
                    ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, password=self._ssh_password)
                #logger.info(f"{self.plugin_name} SSH连接成功")
            except Exception as e:
                return False, f"SSH连接失败: {str(e)}", None

            # 1. 获取备份文件
            backup_file_path = None
            if source == "本地备份":
                backup_file_path = os.path.join(self._backup_path, filename)
                if not os.path.exists(backup_file_path):
                    return False, f"本地备份文件不存在: {backup_file_path}", None
            elif source == "WebDAV备份":
                # 从WebDAV下载备份文件到临时目录
                temp_dir = Path(self.get_data_path()) / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                backup_file_path = str(temp_dir / filename)
                
                self._restore_activity = f"下载WebDAV中: {filename}"
                download_success, download_error = self._download_from_webdav(filename, backup_file_path)
                if not download_success:
                    self._restore_activity = "空闲"
                    return False, f"从WebDAV下载备份文件失败: {download_error}", None
            else:
                return False, f"不支持的备份来源: {source}", None

            # 2. 上传备份文件到PVE
            sftp = ssh.open_sftp()
            remote_backup_path = f"/tmp/{filename}"
            
            self._restore_activity = f"上传PVE中: {filename}"
            logger.info(f"{self.plugin_name} 开始上传备份文件到PVE...")
            logger.info(f"{self.plugin_name} 本地路径: {backup_file_path}")
            logger.info(f"{self.plugin_name} 远程路径: {remote_backup_path}")
            
            # 获取文件大小
            local_stat = os.stat(backup_file_path)
            total_size = local_stat.st_size
            
            # 使用回调函数显示进度
            last_progress = -1  # 记录上次显示的进度
            def progress_callback(transferred: int, total: int):
                nonlocal last_progress
                if total > 0:
                    progress = (transferred / total) * 100
                    # 每20%显示一次进度
                    current_progress = int(progress / 20) * 20
                    if current_progress > last_progress or progress > 99.9:
                        self._restore_activity = f"上传PVE中: {progress:.1f}%"
                        logger.info(f"{self.plugin_name} 上传进度: {progress:.1f}%")
                        last_progress = current_progress
            
            # 上传文件
            sftp.put(backup_file_path, remote_backup_path, callback=progress_callback)
            logger.info(f"{self.plugin_name} 备份文件上传完成")

            # 3. 检查备份文件中的VMID
            original_vmid = self._extract_vmid_from_backup(filename)
            target_vmid = str(restore_vmid) if restore_vmid else original_vmid
            
            if not target_vmid:
                return False, "无法从备份文件名中提取VMID，请手动指定目标VMID", None

            # 4. 检查目标VM是否已存在
            vm_exists = self._check_vm_exists(ssh, target_vmid)
            if vm_exists:
                if restore_skip_existing:
                    return False, f"目标VM {target_vmid} 已存在，跳过恢复", target_vmid
                elif not restore_force:
                    return False, f"目标VM {target_vmid} 已存在，请启用强制恢复或跳过已存在选项", target_vmid
                else:
                    # 强制恢复：删除现有VM
                    logger.info(f"{self.plugin_name} 目标VM {target_vmid} 已存在，执行强制恢复")
                    is_lxc = 'lxc' in filename.lower()
                    delete_success, delete_error = self._delete_vm(ssh, target_vmid, is_lxc)
                    if not delete_success:
                        return False, f"删除现有VM失败: {delete_error}", target_vmid

            # 5. 执行恢复命令
            is_lxc = 'lxc' in filename.lower()
            if is_lxc:
                restore_cmd = f"pct restore {target_vmid} {remote_backup_path}"
            else:
                restore_cmd = f"qmrestore {remote_backup_path} {target_vmid}"

            if self._restore_storage:
                restore_cmd += f" --storage {self._restore_storage}"
            
            self._restore_activity = "等待PVE恢复中..."
            logger.info(f"{self.plugin_name} 执行恢复命令: {restore_cmd}")
            stdin, stdout, stderr = ssh.exec_command(restore_cmd)
    
            # 实时输出恢复日志
            while True:
                line = stdout.readline()
                if not line:
                    break
                logger.info(f"{self.plugin_name} 恢复输出: {line.strip()}")
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_output = stderr.read().decode().strip()
                return False, f"恢复失败: {error_output}", target_vmid

            logger.info(f"{self.plugin_name} 恢复成功完成，目标VMID: {target_vmid}")
            
            # 6. 清理临时文件
            try:
                sftp.remove(remote_backup_path)
                logger.info(f"{self.plugin_name} 已删除远程临时文件: {remote_backup_path}")
            except Exception as e:
                logger.warning(f"{self.plugin_name} 删除远程临时文件失败: {str(e)}")
            
            # 如果是WebDAV备份，删除本地临时文件
            if source == "WebDAV备份":
                try:
                    os.remove(backup_file_path)
                    logger.info(f"{self.plugin_name} 已删除本地临时文件: {backup_file_path}")
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除本地临时文件失败: {str(e)}")
            
            return True, None, target_vmid

        except Exception as e:
            error_msg = f"恢复过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None
            
        finally:
            # 确保关闭SFTP和SSH连接
            if sftp:
                try:
                    sftp.close()
                except:
                    pass
            if ssh:
                try:
                    ssh.close()
                except:
                    pass
            # 自动清理PVE临时空间（受开关控制）
            try:
                # 优先读取 self.auto_cleanup_tmp，没有就 get_config()
                if hasattr(self, 'auto_cleanup_tmp'):
                    auto_cleanup = getattr(self, 'auto_cleanup_tmp', False)
                else:
                    auto_cleanup = self.get_config().get('auto_cleanup_tmp', False)
                if auto_cleanup:
                    count, error = clean_pve_tmp_files(
                        self._pve_host,
                        self._ssh_port,
                        self._ssh_username,
                        self._ssh_password,
                        self._ssh_key_file
                    )
                    if error:
                        logger.warning(f"{self.plugin_name} 自动清理临时空间失败: {error}")
                    else:
                        logger.info(f"{self.plugin_name} 自动清理临时空间完成，已清理 {count} 个 .tmp 文件")
                else:
                    logger.info(f"{self.plugin_name} 未启用自动清理临时空间，跳过清理。")
            except Exception as e:
                logger.warning(f"{self.plugin_name} 自动清理临时空间异常: {e}")

    def _extract_vmid_from_backup(self, filename: str) -> Optional[str]:
        """从备份文件名中提取VMID"""
        try:
            # 备份文件名格式通常是: vzdump-{type}-{VMID}-{timestamp}.{format}.{compression}
            # 支持格式: tar.gz, tar.lzo, tar.zst, vma.gz, vma.lzo, vma.zst
            match = re.search(r'vzdump-(?:qemu|lxc)-(\d+)-', filename)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 从备份文件名提取VMID失败: {e}")
            return None

    def _check_vm_exists(self, ssh: paramiko.SSHClient, vmid: str) -> bool:
        """检查VM或CT是否存在"""
        try:
            # 检查QEMU VM
            check_qm_cmd = f"qm list | grep -q '^{vmid}\\s'"
            stdin, stdout, stderr = ssh.exec_command(check_qm_cmd)
            if stdout.channel.recv_exit_status() == 0:
                return True
            
            # 检查LXC容器
            check_pct_cmd = f"pct list | grep -q '^{vmid}\\s'"
            stdin, stdout, stderr = ssh.exec_command(check_pct_cmd)
            if stdout.channel.recv_exit_status() == 0:
                return True
                
            return False
        except Exception as e:
            logger.error(f"{self.plugin_name} 检查VM/CT存在性失败: {e}")
            return False

    def _delete_vm(self, ssh: paramiko.SSHClient, vmid: str, is_lxc: bool) -> Tuple[bool, Optional[str]]:
        """删除VM或CT"""
        try:
            cmd_prefix = "pct" if is_lxc else "qm"
            # 先停止VM/CT
            stop_cmd = f"{cmd_prefix} stop {vmid}"
            logger.info(f"{self.plugin_name} 尝试停止VM/CT: {stop_cmd}")
            stdin, stdout, stderr = ssh.exec_command(stop_cmd)
            stdout.channel.recv_exit_status()
            
            # 等待VM/CT完全停止
            time.sleep(5)
            
            # 删除VM/CT
            delete_cmd = f"{cmd_prefix} destroy {vmid}"
            logger.info(f"{self.plugin_name} 尝试删除VM/CT: {delete_cmd}")
            stdin, stdout, stderr = ssh.exec_command(delete_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode().strip()
                if "does not exist" in error_output:
                    logger.warning(f"{self.plugin_name} 删除VM/CT {vmid} 时未找到，可能已被删除。")
                    return True, None
                return False, error_output
            
            logger.info(f"{self.plugin_name} 成功删除VM/CT {vmid}")
            return True, None
        except Exception as e:
            return False, str(e)

    def _download_from_webdav(self, filename: str, local_path: str) -> Tuple[bool, Optional[str]]:
        """从WebDAV下载备份文件"""
        try:
            import requests
            from urllib.parse import urljoin, urlparse
            
            # 构建WebDAV基础URL
            base_url = self._webdav_url.rstrip('/')
            webdav_path = self._webdav_path.lstrip('/')
            
            # 检测是否为Alist服务器（端口5244）
            parsed_url = urlparse(self._webdav_url)
            is_alist = parsed_url.port == 5244 or '5244' in self._webdav_url
            
            # 构建可能的下载URL列表
            possible_urls = []
            if is_alist:
                # Alist的特殊路径结构
                if webdav_path:
                    possible_urls.extend([
                        f"{base_url}/dav/{webdav_path}/{filename}",      # Alist标准路径
                        f"{base_url}/{webdav_path}/{filename}"           # 直接路径
                    ])
                else:
                    possible_urls.extend([
                        f"{base_url}/dav/{filename}",      # Alist标准路径
                        f"{base_url}/{filename}"           # 直接路径
                    ])
            else:
                # 标准WebDAV路径
                if webdav_path:
                    possible_urls.extend([
                        f"{base_url}/{webdav_path}/{filename}",
                        f"{base_url}/dav/{webdav_path}/{filename}",
                        f"{base_url}/remote.php/webdav/{webdav_path}/{filename}",
                        f"{base_url}/dav/files/{self._webdav_username}/{webdav_path}/{filename}"
                    ])
                else:
                    possible_urls.extend([
                        f"{base_url}/{filename}",
                        f"{base_url}/dav/{filename}",
                        f"{base_url}/remote.php/webdav/{filename}"
                    ])
            
            # 尝试每个可能的URL
            for download_url in possible_urls:
                try:
                    logger.info(f"{self.plugin_name} 尝试从WebDAV下载文件: {download_url}")
                    
                    # 下载文件
                    response = requests.get(
                        download_url,
                        auth=(self._webdav_username, self._webdav_password),
                        headers={'User-Agent': 'MoviePilot/1.0'},
                        timeout=300,  # 5分钟超时
                        verify=False,
                        stream=True
                    )
                    
                    if response.status_code == 200:
                        # 获取文件大小
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        last_progress = -1
                        
                        # 写入文件
                        with open(local_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if total_size > 0:
                                        progress = (downloaded_size / total_size) * 100
                                        current_progress = int(progress / 10) * 10
                                        if current_progress > last_progress:
                                            logger.info(f"{self.plugin_name} 下载进度: {progress:.1f}%")
                                            last_progress = current_progress
                        
                        logger.info(f"{self.plugin_name} 文件下载完成: {filename}")
                        return True, None
                    
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 从URL下载失败: {download_url}, 错误: {str(e)}")
                    continue
            
            return False, "所有下载URL均失败"
            
        except Exception as e:
            error_msg = f"WebDAV下载过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

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

    def _send_restore_notification(self, success: bool, message: str = "", filename: str = "", target_vmid: Optional[str] = None, is_clear_history: bool = False):
        """发送恢复通知"""
        if not self._notify: return
        
        title = f"🔄 {self.plugin_name} "
        if is_clear_history:
            title += "清理恢复历史记录"
        else:
            title += f"恢复{'成功' if success else '失败'}"
        status_emoji = "✅" if success else "❌"
        
        # 失败时的特殊处理
        if not success:
            divider_failure = "❌━━━━━━━━━━━━━━━━━━━━━━━━━❌"
            text_content = f"{divider_failure}\n"
        else:
            text_content = f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
        text_content += f"📣 状态：{status_emoji} 恢复{'成功' if success else '失败'}\n\n"
        text_content += f"🔗 路由：{self._pve_host}\n"
        
        if filename:
            text_content += f"📄 备份文件：{filename}\n"
        
        if target_vmid:
            text_content += f"🎯 目标VMID：{target_vmid}\n"
        
        if message:
            text_content += f"📋 详情：{message.strip()}\n"
        
        # 添加底部分隔线和时间戳
        if not success:
            text_content += f"\n{divider_failure}\n"
        else:
            text_content += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 根据成功/失败添加不同信息
        if success:
            text_content += "\n✨ 恢复已成功完成！"
        else:
            text_content += "\n❗ 恢复失败，请检查配置和连接！"
        
        try:
            mtype = getattr(NotificationType, self._notification_message_type, NotificationType.Plugin)
            self.post_message(mtype=mtype, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送恢复通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送恢复通知失败: {e}")

    def _download_single_backup_file(self, ssh: paramiko.SSHClient, sftp: paramiko.SFTPClient, remote_file: str, backup_filename: str) -> Tuple[bool, Optional[str], Optional[str], Dict[str, Any]]:
        """
        下载单个备份文件
        :return: (是否成功, 错误消息, 备份文件名, 备份详情)
        """
        try:
            # 确保文件路径是绝对路径
            if not remote_file.startswith('/'):
                remote_file = f"/var/lib/vz/dump/{remote_file}"
            
            # 验证文件是否存在
            check_cmd = f"test -f '{remote_file}' && echo 'exists'"
            stdin, stdout, stderr = ssh.exec_command(check_cmd)
            if stdout.read().decode().strip() != 'exists':
                return False, f"备份文件不存在: {remote_file}", None, {}
            
            # 下载文件
            local_path = os.path.join(self._backup_path, backup_filename)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 获取文件大小
            remote_stat = sftp.stat(remote_file)
            total_size = remote_stat.st_size
            
            self._backup_activity = f"下载中: {backup_filename}"
            logger.info(f"{self.plugin_name} 开始下载备份文件: {backup_filename}")
            logger.info(f"{self.plugin_name} 远程路径: {remote_file}")
            logger.info(f"{self.plugin_name} 本地路径: {local_path}")
            logger.info(f"{self.plugin_name} 文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            # 使用回调函数显示进度
            last_progress = -1  # 记录上次显示的进度
            def progress_callback(transferred: int, total: int):
                nonlocal last_progress
                if total > 0:
                    progress = (transferred / total) * 100
                    # 每20%显示一次进度
                    current_progress = int(progress / 20) * 20
                    if current_progress > last_progress or progress > 99.9:
                        self._backup_activity = f"下载中: {progress:.1f}%"
                        logger.info(f"{self.plugin_name} 下载进度: {progress:.1f}%")
                        last_progress = current_progress
                    elif progress > 99.89 and progress < 99.91 and last_progress < 99:  # 只显示一次99.9%
                        self._backup_activity = f"下载中: 99.9%"
                        logger.info(f"{self.plugin_name} 下载进度: 99.9%")
                        last_progress = 99
                    elif progress >= 100 and last_progress < 100:  # 只在最后显示一次100%
                        self._backup_activity = f"下载中: 100.0%"
                        logger.info(f"{self.plugin_name} 下载进度: 100.0%")
                        last_progress = 100
            
            # 下载文件
            sftp.get(remote_file, local_path, callback=progress_callback)
            logger.info(f"{self.plugin_name} 文件下载完成: {backup_filename}")
            
            # 如果配置了下载后删除
            if self._auto_delete_after_download:
                try:
                    sftp.remove(remote_file)
                    logger.info(f"{self.plugin_name} 已删除远程备份文件: {remote_file}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} 删除远程备份文件失败: {str(e)}")

            # 构建备份详情
            backup_details = {
                "local_backup": {
                    "enabled": self._enable_local_backup,
                    "success": True,
                    "path": self._backup_path,
                    "filename": backup_filename
                },
                "webdav_backup": {
                    "enabled": self._enable_webdav and bool(self._webdav_url),
                    "success": False,
                    "url": self._webdav_url,
                    "path": self._webdav_path,
                    "filename": backup_filename,
                    "error": None
                }
            }

            # 如果启用了WebDAV备份,上传到WebDAV
            if self._enable_webdav and self._webdav_url:
                self._backup_activity = f"上传WebDAV中: {backup_filename}"
                webdav_success, webdav_error = self._upload_to_webdav(local_path, backup_filename)
                backup_details["webdav_backup"]["success"] = webdav_success
                backup_details["webdav_backup"]["error"] = webdav_error
                
                if webdav_success:
                    logger.info(f"{self.plugin_name} WebDAV备份成功: {backup_filename}")
                else:
                    logger.error(f"{self.plugin_name} WebDAV备份失败: {backup_filename} - {webdav_error}")
            
            return True, None, backup_filename, backup_details
            
        except Exception as e:
            error_msg = f"下载备份文件 {backup_filename} 时发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None, {}

    def get_render_mode(self) -> tuple:
        """
        声明为Vue模式，并指定前端静态资源目录（相对插件目录）
        """
        return "vue", "dist/assets"

    def _get_config(self):
        """API处理函数：返回当前配置"""
        return self.get_config() or {}

    def _get_status(self):
        """API处理函数：返回插件状态"""
        # 获取下次运行时间
        next_run_time = None
        if self._scheduler:
            job = self._scheduler.get_job(f"{self.plugin_name}定时服务")
            if job and job.next_run_time:
                import pytz
                from app.core.config import settings
                next_run_time = job.next_run_time.astimezone(pytz.timezone(settings.TZ)).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "enabled": self._enabled,
            "backup_activity": self._backup_activity,
            "restore_activity": self._restore_activity,
            "enable_restore": self._enable_restore,
            "cron": self._cron,
            "next_run_time": next_run_time,
            "enable_log_cleanup": getattr(self, "_enable_log_cleanup", False),
            "cleanup_template_images": self._cleanup_template_images,
            "auto_cleanup_tmp": (self.get_config() or {}).get("auto_cleanup_tmp", True),
        }

    def _save_config(self, data: dict = None):
        """API处理函数：保存配置"""
        if not data:
            # 尝试从请求中获取数据
            import sys
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        self.init_plugin(data)
        return {"success": True, "message": "配置已保存"}

    def _get_backup_history(self):
        return self._load_backup_history() or []

    def _run_backup(self):
        import threading
        threading.Thread(target=self.run_backup_job).start()
        return {"success": True, "message": "备份任务已启动"}

    def _clear_history_api(self):
        self._clear_all_history()
        return {"success": True, "message": "历史已清理"}

    def _get_restore_history(self):
        return self._load_restore_history() or []

    def _get_dashboard_data(self):
        """API处理函数：返回仪表板数据"""
        backup_history = self._load_backup_history()
        restore_history = self._load_restore_history()
        available_backups = self._get_available_backups()
        
        # 统计成功和失败的备份
        successful_backups = sum(1 for item in backup_history if item.get("success", False))
        failed_backups = len(backup_history) - successful_backups
        
        # 统计成功和失败的恢复
        successful_restores = sum(1 for item in restore_history if item.get("success", False))
        failed_restores = len(restore_history) - successful_restores
        
        # 统计本地和WebDAV备份数量
        local_backups_count = sum(1 for b in available_backups if b['source'] == '本地备份')
        webdav_backups_count = sum(1 for b in available_backups if b['source'] == 'WebDAV备份')
        
        return {
            "backup_stats": {
                "total": len(backup_history),
                "successful": successful_backups,
                "failed": failed_backups
            },
            "restore_stats": {
                "total": len(restore_history),
                "successful": successful_restores,
                "failed": failed_restores
            },
            "available_backups": {
                "local": local_backups_count,
                "webdav": webdav_backups_count,
                "total": len(available_backups)
            },
            "status": {
                "backup_activity": self._backup_activity,
                "restore_activity": self._restore_activity,
                "running": self._running
            }
        }

    def _get_pve_status_api(self):
        return get_pve_status(
            self._pve_host,
            self._ssh_port,
            self._ssh_username,
            self._ssh_password,
            self._ssh_key_file
        )

    def _get_container_status_api(self):
        # 合并QEMU和LXC
        qemu_list = get_qemu_status(
            self._pve_host,
            self._ssh_port,
            self._ssh_username,
            self._ssh_password,
            self._ssh_key_file
        )
        lxc_list = get_container_status(
            self._pve_host,
            self._ssh_port,
            self._ssh_username,
            self._ssh_password,
            self._ssh_key_file
        )
        # 直接返回，displayName字段已由pve.py补充
        return qemu_list + lxc_list

    def _get_available_backups_api(self):
        """API处理函数：返回可用备份文件列表"""
        return self._get_available_backups() or []

    def _delete_backup_api(self, data: dict = None):
        """API处理函数：删除本地备份文件或WebDAV备份文件"""
        import os
        from pathlib import Path
        if not data:
            # 兼容flask
            import sys
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        filename = data.get("filename")
        source = data.get("source", "本地备份")
        if not filename:
            return {"success": False, "message": "缺少文件名参数"}
        if source == "本地备份":
            # 防止路径穿越
            backup_dir = Path(self._backup_path)
            file_path = backup_dir / filename
            try:
                # 只允许删除实际备份目录下的文件
                if not file_path.is_file() or not str(file_path.resolve()).startswith(str(backup_dir.resolve())):
                    return {"success": False, "message": "文件不存在或路径非法"}
                os.remove(file_path)
                return {"success": True, "message": f"已删除备份文件: {filename}"}
            except Exception as e:
                return {"success": False, "message": f"删除失败: {str(e)}"}
        elif source == "WebDAV备份":
            # WebDAV 删除逻辑
            try:
                import requests
                from urllib.parse import urljoin, urlparse
                # 构建WebDAV基础URL
                base_url = self._webdav_url.rstrip('/')
                webdav_path = self._webdav_path.lstrip('/')
                parsed_url = urlparse(self._webdav_url)
                is_alist = parsed_url.port == 5244 or '5244' in self._webdav_url
                # 构建可能的URL列表
                possible_urls = []
                if is_alist:
                    if webdav_path:
                        possible_urls.extend([
                            f"{base_url}/dav/{webdav_path}/{filename}",
                            f"{base_url}/{webdav_path}/{filename}"
                        ])
                    else:
                        possible_urls.extend([
                            f"{base_url}/dav/{filename}",
                            f"{base_url}/{filename}"
                        ])
                else:
                    if webdav_path:
                        possible_urls.extend([
                            f"{base_url}/{webdav_path}/{filename}",
                            f"{base_url}/dav/{webdav_path}/{filename}",
                            f"{base_url}/remote.php/webdav/{webdav_path}/{filename}",
                            f"{base_url}/dav/files/{self._webdav_username}/{webdav_path}/{filename}"
                        ])
                    else:
                        possible_urls.extend([
                            f"{base_url}/{filename}",
                            f"{base_url}/dav/{filename}",
                            f"{base_url}/remote.php/webdav/{filename}"
                        ])
                # 依次尝试删除
                last_error = None
                for url in possible_urls:
                    try:
                        resp = requests.delete(
                            url,
                            auth=(self._webdav_username, self._webdav_password),
                            headers={'User-Agent': 'MoviePilot/1.0'},
                            timeout=30,
                            verify=False
                        )
                        if resp.status_code in [200, 201, 204, 404]:
                            return {"success": True, "message": f"已删除WebDAV备份文件: {filename}"}
                        else:
                            last_error = f"状态码: {resp.status_code}, 响应: {resp.text}"
                    except Exception as e:
                        last_error = str(e)
                        continue
                return {"success": False, "message": f"WebDAV删除失败: {last_error or '所有URL均失败'}"}
            except Exception as e:
                return {"success": False, "message": f"WebDAV删除异常: {str(e)}"}
        else:
            return {"success": False, "message": "仅支持本地备份和WebDAV备份删除"}

    def _restore_backup_api(self, data: dict = None):
        """API处理函数：恢复本地备份文件"""
        import threading
        if not data:
            # 兼容flask
            import sys
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        filename = data.get("filename")
        source = data.get("source", "本地备份")
        restore_vmid = data.get("restore_vmid", "")
        restore_force = data.get("restore_force", False)
        restore_skip_existing = data.get("restore_skip_existing", True)
        if not filename:
            return {"success": False, "message": "缺少文件名参数"}
        if source not in ["本地备份", "WebDAV备份"]:
            return {"success": False, "message": f"不支持的备份来源: {source}"}
        # 直接参数传递，不再赋值到self
        try:
            threading.Thread(
                target=self.run_restore_job,
                args=(filename, source, restore_vmid, restore_force, restore_skip_existing)
            ).start()
            return {"success": True, "message": f"已启动恢复任务: {filename}"}
        except Exception as e:
            return {"success": False, "message": f"恢复任务启动失败: {str(e)}"}

    def _download_backup_api(self, filename: str = None, source: str = "本地备份", apikey: str = None):
        """API处理函数：下载本地备份文件或WebDAV备份文件（兼容FastAPI/Flask插件系统，参数显式声明）"""
        import os
        from pathlib import Path
        import sys
        import tempfile
        # FastAPI 环境
        if 'fastapi' in sys.modules:
            from fastapi.responses import FileResponse, JSONResponse
            from app.core.config import settings
            if apikey is not None:
                if apikey != settings.API_TOKEN:
                    return JSONResponse({"success": False, "message": "API_KEY 校验不通过"}, status_code=401)
            if not filename:
                return JSONResponse({"success": False, "message": "缺少文件名参数"}, status_code=400)
            if source == "本地备份":
                backup_dir = Path(self._backup_path)
                file_path = backup_dir / filename
                if not file_path.is_file() or not str(file_path.resolve()).startswith(str(backup_dir.resolve())):
                    return JSONResponse({"success": False, "message": "文件不存在或路径非法"}, status_code=404)
                return FileResponse(
                    path=str(file_path),
                    filename=filename,
                    media_type="application/octet-stream"
                )
            elif source == "WebDAV备份":
                # 先下载到临时目录
                temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / filename
                success, error = self._download_from_webdav(filename, str(temp_file))
                if not success:
                    return JSONResponse({"success": False, "message": f"WebDAV下载失败: {error}"}, status_code=400)
                resp = FileResponse(
                    path=str(temp_file),
                    filename=filename,
                    media_type="application/octet-stream"
                )
                # 下载完自动清理临时文件
                import threading
                def cleanup():
                    try:
                        temp_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup, daemon=True).start()
                return resp
            else:
                return JSONResponse({"success": False, "message": "暂不支持该来源的备份文件下载"}, status_code=400)
        # Flask 环境
        elif 'flask' in sys.modules:
            from flask import request, send_file, abort
            filename = request.args.get("filename")
            source = request.args.get("source", "本地备份")
            apikey = request.args.get("apikey")
            from app.core.config import settings
            if apikey is not None:
                if apikey != settings.API_TOKEN:
                    return abort(401, description="API_KEY 校验不通过")
            if not filename:
                return abort(400, description="缺少文件名参数")
            if source == "本地备份":
                backup_dir = Path(self._backup_path)
                file_path = backup_dir / filename
                if not file_path.is_file() or not str(file_path.resolve()).startswith(str(backup_dir.resolve())):
                    return abort(404, description="文件不存在或路径非法")
                return send_file(
                    str(file_path),
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/octet-stream"
                )
            elif source == "WebDAV备份":
                temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / filename
                success, error = self._download_from_webdav(filename, str(temp_file))
                if not success:
                    return abort(400, description=f"WebDAV下载失败: {error}")
                resp = send_file(
                    str(temp_file),
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/octet-stream"
                )
                import threading
                def cleanup():
                    try:
                        temp_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup, daemon=True).start()
                return resp
            else:
                return abort(400, description="暂不支持该来源的备份文件下载")
        else:
            return {"success": False, "message": "仅支持Flask/FastAPI环境下载"}

    def _get_token(self):
        """API处理函数：返回API_TOKEN"""
        from app.core.config import settings
        return {"api_token": settings.API_TOKEN}

    def _container_action_api(self, data: dict = None):
        import paramiko
        if not data:
            import sys
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        vmid = str(data.get("vmid", "")).strip()
        action = str(data.get("action", "")).strip()  # start/stop/reboot
        vmtype = str(data.get("type", "")).strip().lower()  # qemu/lxc
        if not vmid or not action or not vmtype:
            return {"success": False, "message": "缺少参数"}
        if action not in ["start", "stop", "reboot"]:
            return {"success": False, "message": "不支持的操作"}
        if vmtype not in ["qemu", "lxc"]:
            return {"success": False, "message": "类型必须为qemu或lxc"}
        cmd = f"{'qm' if vmtype == 'qemu' else 'pct'} {action} {vmid}"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self._ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self._ssh_key_file)
                ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, pkey=private_key)
            else:
                ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, password=self._ssh_password)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                return {"success": True, "message": f"{vmtype.upper()} {vmid} {action} 成功"}
            else:
                error_output = stderr.read().decode().strip()
                return {"success": False, "message": f"操作失败: {error_output or '未知错误'}"}
        except Exception as e:
            return {"success": False, "message": f"SSH连接或命令执行失败: {str(e)}"}
        finally:
            try:
                ssh.close()
            except:
                pass

    def _container_snapshot_api(self, data: dict = None):
        import paramiko
        import time
        if not data:
            import sys
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        vmid = str(data.get("vmid", "")).strip()
        vmtype = str(data.get("type", "")).strip().lower()  # qemu/lxc
        snapname = str(data.get("name", "")).strip()
        if not vmid or not vmtype:
            return {"success": False, "message": "缺少参数"}
        if vmtype not in ["qemu", "lxc"]:
            return {"success": False, "message": "类型必须为qemu或lxc"}
        if not snapname:
            snapname = f"auto-{int(time.time())}"
        cmd = f"{'qm' if vmtype == 'qemu' else 'pct'} snapshot {vmid} {snapname}"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self._ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self._ssh_key_file)
                ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, pkey=private_key)
            else:
                ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, password=self._ssh_password)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                return {"success": True, "message": f"{vmtype.upper()} {vmid} 快照创建成功: {snapname}"}
            else:
                error_output = stderr.read().decode().strip()
                return {"success": False, "message": f"快照创建失败: {error_output or '未知错误'}"}
        except Exception as e:
            return {"success": False, "message": f"SSH连接或命令执行失败: {str(e)}"}
        finally:
            try:
                ssh.close()
            except:
                pass

    def _host_action_api(self, data: dict = None):
        import paramiko
        if not data:
            import sys
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        action = data.get("action", "")
        if action not in ("reboot", "shutdown"):
            return {"success": False, "msg": "action参数必须为reboot或shutdown"}
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self._ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self._ssh_key_file)
                ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, pkey=private_key, timeout=5)
            else:
                ssh.connect(self._pve_host, port=self._ssh_port, username=self._ssh_username, password=self._ssh_password, timeout=5)
            if action == "reboot":
                ssh.exec_command("reboot")
            else:
                ssh.exec_command("poweroff")
            ssh.close()
            return {"success": True, "msg": f"主机{action}命令已发送"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def _cleanup_tmp_api(self, data: dict = None):
        count, error = clean_pve_tmp_files(
            self._pve_host,
            self._ssh_port,
            self._ssh_username,
            self._ssh_password,
            self._ssh_key_file
        )
        if error:
            return {"success": False, "msg": f"清理失败: {error}"}
        return {"success": True, "msg": f"已清理 {count} 个临时文件"}

    def _cleanup_logs_api(self, data: dict = None):
        """API处理函数：清理PVE系统日志"""
        if not self._enable_log_cleanup:
            return {"success": False, "msg": "未启用日志清理功能"}
        try:
            res = clean_pve_logs(
                self._pve_host,
                self._ssh_port,
                self._ssh_username,
                self._ssh_password,
                self._ssh_key_file,
                journal_days=self._log_journal_days,
                log_dirs={
                    "/var/log/vzdump": self._log_vzdump_keep,
                    "/var/log/pve": self._log_pve_keep,
                    "/var/log/dpkg.log": self._log_dpkg_keep
                }
            )
            return {"success": True, "msg": "日志清理完成", "result": res}
        except Exception as e:
            return {"success": False, "msg": f"日志清理失败: {e}"}

    def _template_images_api(self):
        """列出所有CT模板和ISO镜像"""
        try:
            images = list_template_images(
                self._pve_host,
                self._ssh_port,
                self._ssh_username,
                self._ssh_password,
                self._ssh_key_file
            )
            return images  # 直接返回数组，兼容前端
        except Exception as e:
            return []