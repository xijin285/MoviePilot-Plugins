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
        :param plugin_instance: ProxmoxVEBackup插件实例
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
                    func=self.plugin._backup_executor.run_backup_job,
                    trigger='date',
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                    name=job_name,
                    id=job_name
                )
                self.plugin._onlyonce = False
                self.plugin._config_manager.update_config()
            elif self.plugin._cron and self.plugin._cron.count(' ') == 4:
                job_name = f"{self.plugin_name}定时服务"
                if self.plugin._scheduler.get_job(job_name):
                    self.plugin._scheduler.remove_job(job_name)
                try:
                    trigger = CronTrigger.from_crontab(self.plugin._cron, timezone=settings.TZ)
                    self.plugin._scheduler.add_job(
                        func=self.plugin._backup_executor.run_backup_job,
                        trigger=trigger,
                        name=job_name,
                        id=job_name
                    )
                    logger.info(f"{self.plugin_name} 已注册定时任务: {self.plugin._cron}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} cron表达式格式错误: {self.plugin._cron}, 错误: {e}")
            
            if not self.plugin._scheduler.running:
                self.plugin._scheduler.start()
    
    def stop_scheduler(self):
        """停止调度器"""
        try:
            if self.plugin._scheduler:
                try:
                    self.plugin._scheduler.remove_all_jobs()
                    if self.plugin._scheduler.running:
                        self.plugin._scheduler.shutdown(wait=True)
                    self.plugin._scheduler = None
                except Exception as e:
                    logger.error(f"{self.plugin_name} 停止调度器时出错: {str(e)}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 停止调度器时出错: {str(e)}")

