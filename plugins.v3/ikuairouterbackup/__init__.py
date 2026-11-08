import os
import threading
import time
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType

from .ip_group.manager import IPGroupManager
from .monitor.monitor_service import MonitorService
from .ui.form_builder import FormBuilder
from .notification.service import NotificationManager
from .notification.ikuai_message_handler import IkuaiMessageHandler
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
from .core.ikuai_event_handler import IkuaiEventHandler
from app.core.event import eventmanager, Event
from app.schemas.types import EventType

class IkuaiRouterBackup(_PluginBase):
    # 插件名称
    plugin_name = "爱快路由时光机"
    # 插件描述
    plugin_desc = "轻松配置您的爱快路由，Vue 仪表盘实时监控负载/设备/日志，备份支持本地/WebDAV/网盘"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/ikuai.png"
    # 插件版本
    plugin_version = "3.1.0"
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
    _ikuai_auth_mode: str = "auto"  # 认证方式：auto/password/token
    _ikuai_api_token: str = ""      # 爱快4.x 个人API令牌
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

    # Vue 仪表盘/侧边栏开关
    _monitor_enable: bool = True

    # 备份增强：变更检测 / 恢复点 / 统一存储备份目标
    _skip_unchanged_backup: bool = True
    _restore_point_enable: bool = True
    _enable_cloud_backup: bool = False   # 引擎属性：由统一存储字段推导
    _cloud_storage: str = ""
    _cloud_path: str = "ikuai_backups"
    _cloud_keep_backup_num: int = 7
    # 统一存储备份（本地磁盘 + MP 网盘存储合并为多个目标，可同时启用本地+网盘）
    _storage_backup_enable: bool = True
    _storage_type: str = "local"         # local 或 MP 存储类型（quark/u115/openlist...）— 兼容旧字段（第一个目标）
    _storage_path: str = ""              # 本地路径或远端目录 — 兼容旧字段
    _storage_keep_backup_num: int = 7
    _storage_targets: list = []          # 多目标列表：[{'type': 'local'|'quark'|..., 'path': str, 'keep_backup_num': int}]

    # 负载告警
    _load_warn_enable: bool = False
    _load_cpu_threshold: float = 90
    _load_mem_threshold: float = 90
    _load_warn_times: int = 3

    _original_ikuai_url: str = ""
    _last_config_hash: str = ""  # 配置哈希值，用于判断是否需要重新初始化

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        # 初始化管理器
        self._monitor_service = MonitorService(self)  # 初始化监控服务
        self._form_builder = FormBuilder(self)  # 初始化表单构建器
        self._notification_manager = NotificationManager(self)  # 初始化通知管理器
        self._ikuai_message_handler = IkuaiMessageHandler(self)  # 初始化爱快消息处理器
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
        self._ikuai_event_handler = IkuaiEventHandler(self)  # 初始化爱快事件处理器
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

        # 启动后立即采样一次监控趋势（后台线程，不阻塞插件加载）
        if getattr(self, '_monitor_enable', True) and getattr(self, '_enabled', False):
            threading.Thread(target=self._initial_sample, daemon=True).start()

    def _initial_sample(self):
        """首次加载延迟几秒后采样一次趋势，让仪表盘尽快有数据"""
        try:
            time.sleep(5)
            self._monitor_service.sample_trend()
        except Exception as e:
            logger.debug(f"{self.plugin_name} 初始趋势采样失败: {e}")

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
        services = []
        if self._enabled and self._cron:
            try:
                if str(self._cron).strip().count(" ") == 4:
                    services.append({
                        "id": "IkuaiRouterBackupService",
                        "name": f"{self.plugin_name}定时服务",
                        "trigger": CronTrigger.from_crontab(self._cron, timezone=settings.TZ),
                        "func": self.run_backup_job,
                        "kwargs": {}
                    })
                else:
                    logger.error(f"{self.plugin_name} cron表达式格式错误: {self._cron}")
            except Exception as err:
                logger.error(f"{self.plugin_name} 定时任务配置错误：{str(err)}")
        # 监控采样 + 负载告警：每 5 分钟一次
        if self._enabled or self._load_warn_enable or self._monitor_enable:
            try:
                from apscheduler.triggers.interval import IntervalTrigger
                services.append({
                    "id": "IkuaiRouterMonitorService",
                    "name": f"{self.plugin_name}监控采样服务",
                    "trigger": IntervalTrigger(minutes=5, timezone=settings.TZ),
                    "func": self.run_monitor_job,
                    "kwargs": {}
                })
            except Exception as err:
                logger.error(f"{self.plugin_name} 监控采样任务配置错误：{str(err)}")
        return services

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明 Vue 联邦渲染模式（与 RandomPic/VueQuarkDisk 一致）"""
        return 'vue', 'dist/assets'

    def get_sidebar_nav(self) -> Optional[List[Dict[str, Any]]]:
        """
        注册主界面左侧导航「爱快路由」入口，
        前端跳转 #/plugin-app/IkuaiRouterBackup/main 并加载 ./AppPage 组件。
        「监控仪表盘」关闭时同步隐藏。
        """
        if not getattr(self, '_monitor_enable', True):
            return None
        return [
            {
                'nav_key': 'main',
                'title': '爱快路由',
                'icon': 'mdi-router-network',
                'section': 'start',
                'permission': 'manage',
                'order': 16,
            }
        ]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """Vue 渲染模式：form 为 None，由前端 Config 组件接管"""
        return None, self.get_vue_config()

    def get_page(self) -> List[dict]:
        """Vue 渲染模式：插件页由前端 Page 组件接管"""
        return []

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        """注册仪表盘小组件"""
        if not getattr(self, '_monitor_enable', True):
            return None
        return [{'key': 'ikuai_monitor', 'name': '爱快路由状态'}]

    def get_dashboard(self, key: str = None, **kwargs) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], List[dict]]]:
        """仪表盘小组件由前端 Dashboard 组件渲染"""
        if key not in (None, 'ikuai_monitor') or not getattr(self, '_monitor_enable', True):
            return None
        return {
            'cols': 12,
            'md': 6,
        }, {
            'refresh': 30,
            'border': True,
            'title': '爱快路由状态',
            'subtitle': '实时负载 / 在线设备 / 流量',
        }, None

    def get_vue_config(self) -> Dict[str, Any]:
        """输出 Vue 配置页所需的完整配置"""
        return {
            "enabled": self._enabled,
            "cron": self._cron,
            "notify": self._notify,
            "notification_style": self._notification_style,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "ikuai_url": self._original_ikuai_url,
            "ikuai_username": self._ikuai_username,
            "ikuai_auth_mode": self._ikuai_auth_mode,
            "ikuai_api_token": self._ikuai_api_token,
            "storage_backup_enable": self._storage_backup_enable,
            "storage_type": self._storage_type,
            "storage_path": self._storage_path,
            "storage_keep_backup_num": self._storage_keep_backup_num,
            "storage_targets": self._storage_targets or [],
            "delete_after_backup": self._delete_after_backup,
            "enable_webdav": self._enable_webdav,
            "webdav_url": self._webdav_url,
            "webdav_username": self._webdav_username,
            "webdav_password": self._webdav_password,
            "webdav_path": self._webdav_path,
            "webdav_keep_backup_num": self._webdav_keep_backup_num,
            "skip_unchanged_backup": self._skip_unchanged_backup,
            "restore_point_enable": self._restore_point_enable,
            "enable_restore": self._enable_restore,
            "restore_force": self._restore_force,
            "monitor_enable": self._monitor_enable,
            "load_warn_enable": self._load_warn_enable,
            "load_cpu_threshold": self._load_cpu_threshold,
            "load_mem_threshold": self._load_mem_threshold,
            "load_warn_times": self._load_warn_times,
            "enable_ip_group": self._enable_ip_group,
            "ip_group_province": self._ip_group_province,
            "ip_group_city": self._ip_group_city,
            "ip_group_isp": self._ip_group_isp,
            "ip_group_prefix": self._ip_group_prefix,
            "ip_group_address_pool": self._ip_group_address_pool,
        }

    def save_vue_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """保存 Vue 配置页提交的完整配置（复用 ConfigLoader 逻辑）"""
        try:
            data = dict(data or {})
            # 密码字段不回传前端：为空时保留已存储的值，避免意外清空
            if not str(data.get('ikuai_password') or ''):
                data['ikuai_password'] = self._ikuai_password
            if not str(data.get('webdav_password') or ''):
                data['webdav_password'] = self._webdav_password
            self._config_loader.load_config(data)
            if self._clear_history:
                self._clear_backup_history()
                self._clear_history = False
            self._config_manager.update_config()
            self._scheduler_manager.setup_scheduler()
            self._scheduler_manager.setup_ip_group_scheduler()
            return {'success': True, 'msg': '配置保存成功'}
        except Exception as err:
            logger.error(f"{self.plugin_name} 保存配置失败: {err}")
            return {'success': False, 'msg': f'保存配置失败: {str(err)}'}

    def run_monitor_job(self):
        """监控采样 + 负载告警（每 5 分钟）"""
        try:
            if getattr(self, '_monitor_enable', True) or self._enabled:
                self._monitor_service.sample_trend()
            self._monitor_service.run_load_check()
        except Exception as e:
            logger.error(f"{self.plugin_name} 监控任务执行失败: {e}")
    
    @eventmanager.register(EventType.PluginAction)
    def handle_ikuai_command(self, event: Event = None):
        """处理爱快相关命令"""
        if self._ikuai_event_handler:
            self._ikuai_event_handler.handle_ikuai_command(event)

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

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None,
                           is_clear_history: bool = False, targets: Optional[List[Dict[str, Any]]] = None,
                           failed: Optional[List[str]] = None,
                           size: Any = 0, elapsed: Any = 0):
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
                notify=self._notify,
                targets=targets or [],
                failed=failed or [],
                size=size,
                elapsed=elapsed
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

    def run_restore_job(self, filename: str, source: str = "本地备份",
                        storage: str = "", remote_dir: str = ""):
        """执行恢复任务（使用RestoreExecutor）"""
        self._restore_executor.run_restore_job(filename, source, storage, remote_dir)

    # ---------- 仪表盘布局 ----------
    LAYOUT_KEY = "dashboard_layout"
    HIDDEN_KEY = "dashboard_hidden"
    LAYOUT_VER_KEY = "dashboard_layout_version"

    def get_dashboard_layout_version(self) -> int:
        try:
            return int(self.get_data(self.LAYOUT_VER_KEY) or 1)
        except Exception:
            return 1

    def save_dashboard_layout_version(self, version) -> bool:
        try:
            self.save_data(self.LAYOUT_VER_KEY, int(version or 1))
            return True
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存布局版本失败: {e}")
            return False

    def get_dashboard_layout(self) -> List[str]:
        """仪表盘卡片顺序（存储于插件数据）"""
        try:
            layout = self.get_data(self.LAYOUT_KEY)
            if isinstance(layout, list) and layout:
                return [str(x) for x in layout]
        except Exception:
            pass
        return []

    def get_dashboard_hidden(self) -> List[str]:
        """仪表盘隐藏的卡片"""
        try:
            hidden = self.get_data(self.HIDDEN_KEY)
            if isinstance(hidden, list):
                return [str(x) for x in hidden]
        except Exception:
            pass
        return []

    def save_dashboard_layout(self, layout) -> bool:
        """保存仪表盘卡片顺序"""
        try:
            clean = []
            for x in (layout if isinstance(layout, list) else []):
                s = str(x).strip()
                if s and s not in clean:
                    clean.append(s)
            self.save_data(self.LAYOUT_KEY, clean)
            return True
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存仪表盘布局失败: {e}")
            return False

    def save_dashboard_hidden(self, hidden) -> bool:
        """保存仪表盘隐藏卡片（与顺序一起持久化，跨设备一致）"""
        try:
            clean = []
            for x in (hidden if isinstance(hidden, list) else []):
                s = str(x).strip()
                if s and s not in clean:
                    clean.append(s)
            self.save_data(self.HIDDEN_KEY, clean)
            return True
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存仪表盘隐藏卡片失败: {e}")
            return False

    # ---------- 备份文件下载 / 删除 ----------
    @staticmethod
    def _safe_backup_name(filename: str) -> str:
        """只允许纯文件名，防止目录穿越"""
        name = os.path.basename(str(filename or "").strip().replace("\\", "/"))
        if not name or name.startswith("."):
            raise ValueError("非法文件名")
        return name

    def load_backup_bytes(self, filename: str, source: str = "本地备份",
                          storage: str = "", remote_dir: str = "") -> Tuple[Optional[bytes], Optional[str]]:
        """
        读取备份文件的原始内容（本地 / WebDAV / 网盘），供前端直接下载
        :return: (文件字节, 错误信息)
        """
        try:
            name = self._safe_backup_name(filename)
        except ValueError as e:
            return None, str(e)

        src = str(source or "本地备份")
        if src == "本地备份":
            path = Path(self._backup_path or "") / name
            if not path.is_file():
                return None, f"本地备份文件不存在: {name}"
            try:
                return path.read_bytes(), None
            except Exception as e:
                return None, f"读取备份文件失败: {e}"

        tmp_path = Path(self.get_data_path()) / "temp" / name
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src == "WebDAV备份":
                ok, err = self._download_from_webdav(name, str(tmp_path))
                if not ok:
                    return None, f"从 WebDAV 下载失败: {err}"
            elif "网盘" in src and storage:
                from .backup import cloud_storage
                ok, err = cloud_storage.download_backup_file(
                    storage, remote_dir or "ikuai_backups", name, str(tmp_path))
                if not ok:
                    return None, f"从网盘下载失败: {err}"
            else:
                return None, f"不支持的备份来源: {src}"
            try:
                return tmp_path.read_bytes(), None
            except Exception as e:
                return None, f"读取备份文件失败: {e}"
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass

    def delete_backup_file(self, filename: str, source: str = "本地备份",
                           storage: str = "", remote_dir: str = "") -> Tuple[bool, Optional[str]]:
        """删除备份文件（本地 / WebDAV / 网盘）"""
        try:
            name = self._safe_backup_name(filename)
        except ValueError as e:
            return False, str(e)

        src = str(source or "本地备份")
        try:
            if src == "本地备份":
                path = Path(self._backup_path or "") / name
                if not path.is_file():
                    return False, f"本地备份文件不存在: {name}"
                path.unlink()
                logger.info(f"{self.plugin_name} 已删除本地备份: {name}")
                return True, None

            if src == "WebDAV备份":
                from .webdav.webdav_client import WebDAVClient
                client = WebDAVClient(
                    url=self._webdav_url,
                    username=self._webdav_username,
                    password=self._webdav_password,
                    path=self._webdav_path,
                    skip_dir_check=True,
                    logger=logger,
                    plugin_name=self.plugin_name,
                )
                try:
                    ok, err = client.delete_file(name)
                finally:
                    client.close()
                if not ok:
                    return False, f"删除 WebDAV 备份失败: {err}"
                logger.info(f"{self.plugin_name} 已删除 WebDAV 备份: {name}")
                return True, None

            if "网盘" in src and storage:
                from .backup import cloud_storage
                ok, err = cloud_storage.delete_cloud_backup(
                    storage, remote_dir or "ikuai_backups", name)
                if not ok:
                    return False, f"删除网盘备份失败: {err}"
                logger.info(f"{self.plugin_name} 已删除网盘备份: {storage}/{name}")
                return True, None
            return False, f"不支持的备份来源: {src}"
        except Exception as e:
            logger.error(f"{self.plugin_name} 删除备份 {name} 失败: {e}")
            return False, str(e)


    def _send_restore_notification(self, success: bool, message: str = "", filename: str = "", is_clear_history: bool = False,
                                   source: str = "", elapsed: Any = 0, restore_point: str = ""):
        """发送恢复通知"""
        self._notification_manager.send_restore_notification(
            success=success,
            message=message,
            filename=filename,
            notification_style=self._notification_style,
            notify=self._notify,
            source=source,
            elapsed=elapsed,
            restore_point=restore_point
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
        """
        返回处理后的iKuai URL，确保有http/https前缀并移除末尾的斜杠。
        爱快4.x强制HTTPS登录，故未填写协议时默认补 https://（自动识别）。
        """
        url = url.strip().rstrip('/')
        if not url:
            return ""
        if url.startswith('https://'):
            return url
        if url.startswith('http://'):
            return url
        # 未指定协议，默认按 HTTPS 处理（爱快4.x强制HTTPS）
        return f"https://{url}"

