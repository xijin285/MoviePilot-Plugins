import hashlib
import json
import os
import re
import time
import threading
from typing import Any, List, Dict, Tuple, Optional
from pathlib import Path

import paramiko

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.core.event import eventmanager, Event
from app.schemas.types import EventType
from app.core.cache import TTLCache
from .pve.client import get_pve_status, get_container_status, get_qemu_status, clean_pve_tmp_files, clean_pve_logs, list_template_images, download_template_image, delete_template_image, upload_template_image, download_template_image_from_url
from .core import ConfigManager, ConfigLoader, HistoryHandler, SchedulerManager
from .core.pve_event_handler import PVEEventHandler
from .backup import BackupManager, BackupExecutor
from .restore import RestoreManager, RestoreExecutor
from .notification import NotificationHandler
from .notification.pve_message_handler import PVEMessageHandler
from .api.routes import get_api_routes
from .api.commands import get_plugin_commands


class ProxmoxVEBackup(_PluginBase):
    # 插件名称
    plugin_name = "PVE虚拟机守护神"
    # 插件描述
    plugin_desc = "一站式PVE虚拟化管理平台，智能自动化集成可视化界面高效掌控虚拟机与容器"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/proxmox.webp"
    # 插件版本
    plugin_version = "2.3.3"
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
    _scheduler = None  # 调度器实例（由SchedulerManager管理）
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
    _pve_message_handler: Optional[PVEMessageHandler] = None  # PVE消息处理器实例
    _notification_handler: Optional[NotificationHandler] = None  # 通知处理器实例
    _history_handler: Optional[HistoryHandler] = None  # 历史记录处理器实例
    _restore_manager: Optional[RestoreManager] = None  # 恢复管理器实例
    _config_manager: Optional[ConfigManager] = None  # 配置管理器实例
    _backup_executor: Optional[BackupExecutor] = None  # 备份执行器实例
    _restore_executor: Optional[RestoreExecutor] = None  # 恢复执行器实例
    _scheduler_manager: Optional[SchedulerManager] = None  # 调度器管理器实例
    _pve_event_handler: Optional[PVEEventHandler] = None  # PVE事件处理器实例
    _config_loader: Optional[ConfigLoader] = None  # 配置加载器实例

    # 新增：系统日志清理配置
    _enable_log_cleanup: bool = False
    _log_journal_days: int = 0
    _log_vzdump_keep: int = 0
    _log_pve_keep: int = 0
    _log_dpkg_keep: int = 0
    _cleanup_template_images: bool = False

    def init_plugin(self, config: Optional[dict] = None):
        # 停止已有服务，防止多实例冲突
        if self._scheduler_manager:
            self._scheduler_manager.stop_scheduler()
        self._lock = threading.Lock()
        self._restore_lock = threading.Lock()
        self._global_task_lock = threading.Lock()
        self._stopped = False

        # 初始化配置加载器和配置管理器（需要在加载配置之前）
        self._config_loader = ConfigLoader(self)
        self._config_manager = ConfigManager(self)
        
        # 初始化缓存实例（TTLCache会自动根据系统配置选择Redis或内存缓存）
        # PVE状态缓存：30秒TTL，最大10项
        self._pve_status_cache = TTLCache(region="proxmox_pve_status", maxsize=10, ttl=30)
        # 容器状态缓存：60秒TTL，最大50项
        self._container_status_cache = TTLCache(region="proxmox_container_status", maxsize=50, ttl=60)
        
        # 检测实际使用的缓存后端并记录日志
        # 系统会根据配置自动选择缓存后端
        try:
            cache_backend = "CacheTools缓存"  # 默认是CacheTools（MoviePilot默认内存缓存）
            config_detected = False  # 标记是否通过配置成功检测
            
            # 方法1: 严格按照官方文档，优先检查系统配置 CACHE_BACKEND_TYPE（最准确、最权威）
            try:
                # settings已在文件顶部导入，直接使用
                if hasattr(settings, 'CACHE_BACKEND_TYPE'):
                    cache_backend_type = str(getattr(settings, 'CACHE_BACKEND_TYPE', '')).strip().lower()
                    if cache_backend_type == 'redis':
                        cache_backend = "Redis缓存"
                        config_detected = True
                        logger.debug(f"{self.plugin_name} 缓存检测: 系统配置明确指定 CACHE_BACKEND_TYPE=redis")
                    elif cache_backend_type == 'memory':
                        cache_backend = "CacheTools缓存"
                        config_detected = True
                        logger.debug(f"{self.plugin_name} 缓存检测: 系统配置明确指定 CACHE_BACKEND_TYPE=memory")
                    else:
                        logger.debug(f"{self.plugin_name} 缓存检测: 系统配置 CACHE_BACKEND_TYPE={cache_backend_type}，使用默认CacheTools")
                else:
                    logger.debug(f"{self.plugin_name} 缓存检测: 系统配置中未找到 CACHE_BACKEND_TYPE，使用默认CacheTools")
            except Exception as config_e:
                logger.debug(f"{self.plugin_name} 缓存检测: 读取系统配置异常: {config_e}，使用默认CacheTools")
            
            # 方法2: 只有在系统配置无法确定时，才进行启发式检测（作为备选方案）
            # 注意：启发式检测可能不准确，应优先依赖系统配置
            if not config_detected:
                cache_obj = self._pve_status_cache
                try:
                    # 检查是否有Redis客户端的实际连接（更严格的检测）
                    if hasattr(cache_obj, 'backend'):
                        backend_obj = cache_obj.backend
                        backend_type_name = type(backend_obj).__name__
                        backend_module = type(backend_obj).__module__
                        logger.debug(f"{self.plugin_name} 缓存检测: backend类型={backend_type_name}, 模块={backend_module}")
                        
                        # 严格检测：必须是redis模块的类，且不是简单的字符串包含
                        if 'redis' in backend_module.lower() and ('Redis' in backend_type_name or 'Cache' in backend_type_name):
                            cache_backend = "Redis缓存"
                            logger.debug(f"{self.plugin_name} 缓存检测: 通过backend模块检测到Redis")
                        elif 'cachetools' in backend_module.lower():
                            cache_backend = "CacheTools缓存"
                            logger.debug(f"{self.plugin_name} 缓存检测: 通过backend模块检测到CacheTools")
                except Exception as backend_e:
                    logger.debug(f"{self.plugin_name} 缓存检测: backend检测异常: {backend_e}")
            
            logger.info(f"{self.plugin_name} 已初始化缓存实例（{cache_backend}）")
        except Exception as e:
            # 如果检测失败，默认使用CacheTools（MoviePilot标准内存缓存）
            logger.info(f"{self.plugin_name} 已初始化缓存实例（CacheTools缓存）")
            logger.debug(f"{self.plugin_name} 缓存后端检测失败，使用默认CacheTools: {e}")

        # 加载配置
        saved_config = self.get_config()
        if saved_config:
            self._config_loader.load_config(saved_config)
            
        # 新配置覆盖
        if config:
            self._config_loader.apply_config_updates(config)

        # 处理清理历史/立即恢复（需要在处理器初始化之后）
        # 先初始化所有处理器
        ProxmoxVEBackup._instance = self
        
        # 初始化PVE消息处理器
        self._pve_message_handler = PVEMessageHandler(self)

        # 初始化通知处理器
        self._notification_handler = NotificationHandler(self)
        
        # 初始化历史记录处理器
        self._history_handler = HistoryHandler(self)
        
        # 初始化备份文件管理器
        self._backup_manager = BackupManager(self)
        
        # 初始化恢复管理器
        self._restore_manager = RestoreManager(self)
        
        # 初始化备份执行器
        self._backup_executor = BackupExecutor(self)
        
        # 初始化恢复执行器
        self._restore_executor = RestoreExecutor(self)
        
        # 处理特殊操作（需要在处理器初始化之后）
        self._config_loader.process_special_actions()
        
        # 确保备份目录存在
        self._config_loader.ensure_backup_directory()
        
        # 初始化调度器管理器
        self._scheduler_manager = SchedulerManager(self)
        
        # 初始化PVE事件处理器
        self._pve_event_handler = PVEEventHandler(self)
        
        # 初始化API处理器
        from .api.handlers import APIHandler
        self._api_handler = APIHandler(self)

        # 设置定时任务调度器
        self._scheduler_manager.setup_scheduler()

    def stop_service(self):
        """停止服务"""
        if self._scheduler_manager:
            self._scheduler_manager.stop_scheduler()
        
        # 清理缓存
        if hasattr(self, '_pve_status_cache') and self._pve_status_cache:
            self._pve_status_cache.clear()
        if hasattr(self, '_container_status_cache') and self._container_status_cache:
            self._container_status_cache.clear()

    def _should_skip_reinit(self, config: Optional[dict] = None) -> bool:
        """
        检查是否应该跳过重新初始化
        只有在关键配置发生变更时才重新初始化
        """
        return self._config_manager.should_skip_reinit(config)

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """
        注册微信消息命令
        """
        return get_plugin_commands()

    def get_api(self) -> list:
        """
        API注册
        """
        return get_api_routes(self)

    @classmethod
    def get_instance(cls):
        return cls._instance

    def get_service(self) -> List[Dict[str, Any]]:
        return []

    @eventmanager.register(EventType.PluginAction)
    def handle_pve_command(self, event: Event = None):
        """
        处理PVE相关命令（通过事件系统）
        完全独立的PVE插件命令处理
        """
        if self._pve_event_handler:
            self._pve_event_handler.handle_pve_command(event)

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

    def get_render_mode(self) -> tuple:
        """
        声明为Vue模式，并指定前端静态资源目录（相对插件目录）
        """
        return "vue", "dist/assets"