"""
调度器管理模块
负责管理定时任务和一次性任务
"""
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.log import logger


class SchedulerManager:
    """调度器管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化调度器管理器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def setup_scheduler(self):
        """设置调度器"""
        # 确保备份目录存在
        try:
            Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建实际备份目录 {self.plugin._backup_path} 失败: {e}")

        if self.plugin._enabled or self.plugin._onlyonce:
            if self.plugin._onlyonce:
                try:
                    if not self.plugin._scheduler or not self.plugin._scheduler.running:
                        self.plugin._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    job_name = f"{self.plugin_name}服务_onlyonce"
                    if self.plugin._scheduler.get_job(job_name):
                        self.plugin._scheduler.remove_job(job_name)
                    logger.info(f"{self.plugin_name} 服务启动，立即运行一次")
                    self.plugin._scheduler.add_job(
                        func=self.plugin.run_backup_job,
                        trigger='date',
                        run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                        name=job_name,
                        id=job_name
                    )
                    self.plugin._onlyonce = False
                    self.plugin._config_manager.update_config()
                    if self.plugin._scheduler and not self.plugin._scheduler.running:
                        self.plugin._scheduler.print_jobs()
                        self.plugin._scheduler.start()
                except Exception as e:
                    logger.error(f"启动一次性 {self.plugin_name} 任务失败: {str(e)}")
    
    def stop_scheduler(self):
        """停止调度器"""
        try:
            if self.plugin._scheduler:
                job_name = f"{self.plugin_name}服务_onlyonce"
                if self.plugin._scheduler.get_job(job_name):
                    self.plugin._scheduler.remove_job(job_name)
                if self.plugin._lock and hasattr(self.plugin._lock, 'locked') and self.plugin._lock.locked():
                    logger.info(f"等待 {self.plugin_name} 当前任务执行完成...")
                    acquired = self.plugin._lock.acquire(timeout=300)
                    if acquired:
                        self.plugin._lock.release()
                    else:
                        logger.warning(f"{self.plugin_name} 等待任务超时。")
                if hasattr(self.plugin._scheduler, 'remove_all_jobs') and not self.plugin._scheduler.get_jobs(jobstore='default'):
                    pass
                elif hasattr(self.plugin._scheduler, 'remove_all_jobs'):
                    self.plugin._scheduler.remove_all_jobs()
                if hasattr(self.plugin._scheduler, 'running') and self.plugin._scheduler.running:
                    if not self.plugin._scheduler.get_jobs():
                        self.plugin._scheduler.shutdown(wait=False)
                        self.plugin._scheduler = None
                logger.info(f"{self.plugin_name} 服务已停止或已无任务。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 退出插件失败：{str(e)}")

