import threading
from typing import Any, List, Dict, Tuple, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType

from .ip_group.manager import IPGroupManager
from .ui.form_builder import FormBuilder
from .notification.service import NotificationManager
from .notification.message_handler import MessageHandler
from .ui.history_manager import HistoryManager
from .ui.page_builder import PageBuilder
from .ui.dashboard_builder import DashboardBuilder
from .backup.backup_manager import BackupManager
from .config.loader import ConfigLoader
from .config.manager import ConfigManager
from .scheduler.manager import SchedulerManager
from .backup.backup_executor import BackupExecutor
from .restore.restore_executor import RestoreExecutor
from .api.handlers import APIHandler
from .api.routes import get_api_routes
from .api.commands import get_plugin_commands
from .core.event_handler import EventHandler
from app.core.event import eventmanager, Event
from app.schemas.types import EventType

class IkuaiRouterBackup(_PluginBase):
    # 插件名称
    plugin_name = "爱快路由时光机"
    # 插件描述
    plugin_desc = "轻松配置您的爱快路由，让路由管理更简单"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/ikuai.png"
    # 插件版本
    plugin_version = "1.3.2"
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
    _last_config_hash: str = ""  # 配置哈希值，用于判断是否需要重新初始化

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        # 初始化事件处理去重状态（实例变量）
        self._processed_events = set()
        self._event_cache_time = 0.0
        self._event_cache_ttl = 1  # 1秒内的重复事件将被忽略
        # 初始化管理器
        self._form_builder = FormBuilder(self)  # 初始化表单构建器
        self._notification_manager = NotificationManager(self)  # 初始化通知管理器
        self._message_handler = MessageHandler(self)  # 初始化消息处理器（用于事件处理）
        self._history_manager = HistoryManager(self, self._max_history_entries, self._max_restore_history_entries)  # 初始化历史管理器
        self._page_builder = PageBuilder(self)  # 初始化页面构建器
        self._dashboard_builder = DashboardBuilder(self)  # 初始化仪表盘构建器
        self._backup_manager = BackupManager(self)  # 初始化备份管理器
        self._config_loader = ConfigLoader(self)  # 初始化配置加载器
        self._config_manager = ConfigManager(self)  # 初始化配置管理器
        self._scheduler_manager = SchedulerManager(self)  # 初始化调度器管理器
        self._backup_executor = BackupExecutor(self)  # 初始化备份执行器
        self._restore_executor = RestoreExecutor(self)  # 初始化恢复执行器
        self._api_handler = APIHandler(self)  # 初始化API处理器
        self._event_handler = EventHandler(self)  # 初始化事件处理器
        self.stop_service()
        
        if config:
            # 使用ConfigLoader加载配置
            self._config_loader.load_config(config)
            
            # 使用ConfigManager更新配置
            self._config_manager.update_config()

            # 处理清理历史记录请求
            if self._clear_history:
                self._clear_backup_history()
                self._clear_history = False
                self._config_manager.update_config()

        # 使用SchedulerManager设置调度器
        self._scheduler_manager.setup_scheduler()
        self._scheduler_manager.setup_ip_group_scheduler()

    def _load_backup_history(self) -> List[Dict[str, Any]]:
        return self._history_manager.load_backup_history()

    def _save_backup_history_entry(self, entry: Dict[str, Any]):
        self._history_manager.save_backup_history_entry(entry)

    def __update_config(self):
        """委托给ConfigManager更新配置"""
        if hasattr(self, '_config_manager'):
            self._config_manager.update_config()
        else:
            # 兼容旧代码，暂不使用
            pass

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
        """使用FormBuilder构建表单"""
        return self._form_builder.build_form()

    def get_page(self) -> List[dict]:
        """使用PageBuilder构建页面"""
        return self._page_builder.build_page()
    
    def get_dashboard(self, **kwargs) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], List[dict]]]:
        """构建仪表盘 - 显示系统概况和线路监控"""
        return self._dashboard_builder.build_dashboard(**kwargs)
    
    @eventmanager.register(EventType.PluginAction)
    def handle_ikuai_command(self, event: Event = None):
        """处理爱快相关命令"""
        if event:
            event_data = event.event_data
            if not event_data:
                return
            action = event_data.get("action")
            if not action:
                data = event_data.get("data", {})
                if isinstance(data, dict):
                    action = data.get("action")
            
            if not action or action not in ["help", "status", "line", "list", "history", "backup"]:
                return
            
            # 在主插件层面添加去重检查
            import time
            
            # 生成事件的唯一标识 - 使用命令+用户+动作的hash，不依赖event_id（因为框架会生成不同的event_id）
            cmd = event_data.get("cmd", "")
            userid = event_data.get("user", "")
            event_key = f"{cmd}|{userid}|{action}"
            dedup_id = hash(event_key)
            
            # 记录event_id用于日志
            event_id = None
            if hasattr(event, 'event_id'):
                event_id = event.event_id
            elif hasattr(event, 'id'):
                event_id = event.id
            
            # 检查是否已处理过
            if dedup_id in self._processed_events:
                logger.debug(f"{self.plugin_name} 主插件检测到重复事件，跳过: dedup_id={dedup_id}, event_id={event_id}")
                return
            
            # 记录已处理的事件
            current_time = time.time()
            
            # 清理过期的缓存
            if current_time - self._event_cache_time > self._event_cache_ttl:
                self._processed_events.clear()
                self._event_cache_time = current_time
            
            self._processed_events.add(dedup_id)
            
            # 确认是我们的命令
            logger.info(f"{self.plugin_name} 收到命令: action={action}, cmd={event_data.get('cmd', '')}, dedup_id={dedup_id}, event_id={event_id}")
            
            # 使用事件处理器处理命令
            if self._event_handler:
                self._event_handler.handle_ikuai_command(event)
            else:
                logger.warning(f"{self.plugin_name} 事件处理器未初始化")

    def stop_service(self):
        """委托给SchedulerManager停止服务"""
        if hasattr(self, '_scheduler_manager'):
            self._scheduler_manager.stop_scheduler()
        else:
            # 兼容旧代码
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
        """执行备份任务（使用BackupExecutor）"""
        self._backup_executor.run_backup_job()

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

    def _cleanup_old_backups(self):
        """委托给BackupManager清理旧备份"""
        self._backup_manager.cleanup_old_backups()

    def _upload_to_webdav(self, local_file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
        """上传文件到WebDAV服务器"""
        if not self._enable_webdav or not self._webdav_url:
            return False, "WebDAV未启用或URL未配置"
        
        try:
            from .webdav.webdav_client import WebDAVClient
            
            # 创建WebDAV客户端
            client = WebDAVClient(
                url=self._webdav_url,
                username=self._webdav_username,
                password=self._webdav_password,
                path=self._webdav_path,
                skip_dir_check=True,
                logger=logger,
                plugin_name=self.plugin_name
            )
            
            # 执行上传
            success, error = client.upload(local_file_path, filename)
            client.close()
            
            return success, error
            
        except Exception as e:
            error_msg = f"WebDAV上传过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

    def _cleanup_webdav_backups(self):
        """清理WebDAV上的旧备份文件"""
        if not self._enable_webdav or not self._webdav_url or self._webdav_keep_backup_num <= 0:
            return
        
        try:
            from .webdav.webdav_client import WebDAVClient
            
            # 创建WebDAV客户端
            client = WebDAVClient(
                url=self._webdav_url,
                username=self._webdav_username,
                password=self._webdav_password,
                path=self._webdav_path,
                skip_dir_check=True,
                logger=logger,
                plugin_name=self.plugin_name
            )
            
            # 执行清理，只保留指定数量的.bak文件
            deleted_count, error = client.cleanup_old_files(self._webdav_keep_backup_num, '.bak')
            client.close()
            
            if error:
                logger.error(f"{self.plugin_name} WebDAV清理失败: {error}")
            elif deleted_count > 0:
                logger.info(f"{self.plugin_name} WebDAV清理完成，删除了 {deleted_count} 个旧备份文件")
                
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
        """发送通知"""
        if is_clear_history:
            self._notification_manager.send_clear_history_notification(
                success=success, 
                message=message,
                notification_style=self._notification_style,
                notify=self._notify
            )
        else:
            self._notification_manager.send_backup_notification(
                success=success,
                message=message,
                filename=filename,
                notification_style=self._notification_style,
                notify=self._notify
            )

    def _load_restore_history(self) -> List[Dict[str, Any]]:
        """加载恢复历史记录"""
        return self._history_manager.load_restore_history()

    def _save_restore_history_entry(self, entry: Dict[str, Any]):
        """保存单条恢复历史记录"""
        self._history_manager.save_restore_history_entry(entry)

    def _get_available_backups(self) -> List[Dict[str, Any]]:
        """获取可用的备份文件列表"""
        return self._backup_manager.get_available_backups()

    def run_restore_job(self, filename: str, source: str = "本地备份"):
        """执行恢复任务（使用RestoreExecutor）"""
        self._restore_executor.run_restore_job(filename, source)


    def _send_restore_notification(self, success: bool, message: str = "", filename: str = "", is_clear_history: bool = False):
        """发送恢复通知"""
        self._notification_manager.send_restore_notification(
            success=success,
            message=message,
            filename=filename,
            notification_style=self._notification_style,
            notify=self._notify
        )



    def _download_from_webdav(self, filename: str, local_filepath: str) -> Tuple[bool, Optional[str]]:
        """从WebDAV下载文件"""
        if not self._enable_webdav or not self._webdav_url:
            return False, "WebDAV未启用或URL未配置"
        
        try:
            from .webdav.webdav_client import WebDAVClient
            
            # 创建WebDAV客户端
            client = WebDAVClient(
                url=self._webdav_url,
                username=self._webdav_username,
                password=self._webdav_password,
                path=self._webdav_path,
                skip_dir_check=True,
                logger=logger,
                plugin_name=self.plugin_name
            )
            
            # 执行下载
            success, error = client.download(filename, local_filepath)
            client.close()
            
            return success, error
            
        except Exception as e:
            error_msg = f"WebDAV下载过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

    def _get_processed_ikuai_url(self, url: str) -> str:
        """返回处理后的iKuai URL，确保有http/https前缀并移除末尾的斜杠"""
        url = url.strip().rstrip('/')
        if not url:
            return ""
        if not url.startswith(('http://', 'https://')):
            return f"http://{url}"
        return url

