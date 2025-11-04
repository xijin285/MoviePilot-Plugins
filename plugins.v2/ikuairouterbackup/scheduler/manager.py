"""
调度器管理模块
负责管理定时任务调度器
"""
from datetime import datetime, timedelta
from typing import Optional
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.log import logger


class SchedulerManager:
    """调度器管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化调度器管理器
        :param plugin_instance: IkuaiRouterBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def setup_scheduler(self):
        """设置定时任务调度器"""
        # 停止已有调度器
        if self.plugin._scheduler:
            try:
                self.plugin._scheduler.remove_all_jobs()
                if self.plugin._scheduler.running:
                    self.plugin._scheduler.shutdown(wait=True)
            except Exception as e:
                logger.error(f"{self.plugin_name} 停止调度器时出错: {str(e)}")
            self.plugin._scheduler = None

        if self.plugin._enabled or self.plugin._onlyonce:
            self.plugin._scheduler = BackgroundScheduler(timezone=settings.TZ)
            
            if self.plugin._onlyonce:
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
            
            if not self.plugin._scheduler.running:
                self.plugin._scheduler.print_jobs()
                self.plugin._scheduler.start()
    
    def setup_ip_group_scheduler(self):
        """设置IP分组同步调度器"""
        # 处理IP分组同步任务
        if self.plugin._ip_group_sync_now:
            try:
                if not self.plugin._scheduler or not self.plugin._scheduler.running:
                    self.plugin._scheduler = BackgroundScheduler(timezone=settings.TZ)
                job_name = f"{self.plugin_name}IP分组同步_onlyonce"
                if self.plugin._scheduler.get_job(job_name):
                    self.plugin._scheduler.remove_job(job_name)
                logger.info(f"{self.plugin_name} IP分组同步服务启动，立即运行一次")
                self.plugin._scheduler.add_job(
                    func=self.plugin.run_ip_group_sync_job,
                    trigger='date',
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                    name=job_name,
                    id=job_name
                )
                self.plugin._ip_group_sync_now = False
                self.plugin._config_manager.update_config()
                if not self.plugin._scheduler.running:
                    self.plugin._scheduler.print_jobs()
                    self.plugin._scheduler.start()
            except Exception as e:
                logger.error(f"启动一次性 {self.plugin_name} IP分组同步任务失败: {str(e)}")
    
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

