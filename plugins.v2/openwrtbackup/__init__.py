import threading
from typing import Any, List, Dict, Tuple, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase

from .config.loader import ConfigLoader
from .config.manager import ConfigManager
from .backup.backup_executor import BackupExecutor
from .backup.backup_manager import BackupManager
from .ui.form_builder import FormBuilder
from .ui.page_builder import PageBuilder
from .ui.dashboard_builder import DashboardBuilder
from .ui.history_manager import HistoryManager
from .notification.service import NotificationService
from .notification.openwrt_message_handler import OpenWrtMessageHandler
from .scheduler.manager import SchedulerManager
from .core.openwrt_event_handler import OpenWrtEventHandler
from .api.commands import get_plugin_commands
from .api.routes import get_api_routes
from app.core.event import eventmanager, Event
from app.schemas.types import EventType


class OpenWrtBackup(_PluginBase):
    # 插件名称
    plugin_name = "OpenWrt路由助手"
    # 插件描述
    plugin_desc = "OpenWrt路由器管理助手，支持配置备份、状态监控和消息交互"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/openwrt.png"
    # 插件版本
    plugin_version = "1.1.4"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "openwrt_backup_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _max_history_entries: int = 100  # Max number of history entries to keep

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 60
    
    _openwrt_host: str = ""
    _openwrt_username: str = "root"
    _openwrt_password: str = ""
    _enable_local_backup: bool = True  # 本地备份开关
    _backup_path: str = ""
    _keep_backup_num: int = 7

    # WebDAV配置属性
    _enable_webdav: bool = False
    _webdav_url: str = ""
    _webdav_username: str = ""
    _webdav_password: str = ""
    _webdav_path: str = ""
    _webdav_keep_backup_num: int = 7

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        
        # 初始化管理器
        self._config_loader = ConfigLoader(self)
        self._config_manager = ConfigManager(self)
        self._form_builder = FormBuilder(self)
        self._page_builder = PageBuilder(self)
        self._dashboard_builder = DashboardBuilder(self)
        self._history_manager = HistoryManager(self, self._max_history_entries)
        self._notification_service = NotificationService(self)
        self._openwrt_message_handler = OpenWrtMessageHandler(self)
        self._openwrt_event_handler = OpenWrtEventHandler(self)
        self._scheduler_manager = SchedulerManager(self)
        self._backup_manager = BackupManager(self)
        self._backup_executor = BackupExecutor(self)
        
        self.stop_service()
        
        if config:
            # 使用ConfigLoader加载配置
            self._config_loader.load_config(config)
            
            # 使用ConfigManager更新配置
            self._config_manager.update_config()

        # 使用SchedulerManager设置调度器
        self._scheduler_manager.setup_scheduler()
    

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """注册消息渠道命令"""
        return get_plugin_commands()

    def get_api(self) -> List[Dict[str, Any]]:
        """注册插件API（使用routes模块）"""
        return get_api_routes(self)

    def get_service(self) -> List[Dict[str, Any]]:
        if self._enabled and self._cron:
            try:
                if str(self._cron).strip().count(" ") == 4:
                    return [{
                        "id": "OpenWrtBackupService",
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
        """使用FormBuilder构建表单"""
        return self._form_builder.build_form()

    def get_page(self) -> List[dict]:
        """使用PageBuilder构建页面"""
        return self._page_builder.build_page()
    
    def get_dashboard(self, **kwargs) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], List[dict]]]:
        """构建仪表盘 - 显示系统概况和网络流量"""
        return self._dashboard_builder.build_dashboard(**kwargs)

    def stop_service(self):
        """委托给SchedulerManager停止服务"""
        if hasattr(self, '_scheduler_manager'):
            self._scheduler_manager.stop_scheduler()

    def run_backup_job(self):
        """执行备份任务（使用BackupExecutor）"""
        self._backup_executor.run_backup_job()

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None):
        """发送通知"""
        self._notification_service.send_notification(
            success=success,
            message=message,
            filename=filename,
            notify=self._notify
        )
    
    @eventmanager.register(EventType.PluginAction)
    def handle_openwrt_command(self, event: Event = None):
        """处理OpenWrt相关命令"""
        if self._openwrt_event_handler:
            self._openwrt_event_handler.handle_openwrt_command(event)
