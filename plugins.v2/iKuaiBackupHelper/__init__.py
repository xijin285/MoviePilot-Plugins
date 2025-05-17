# 插件入口 - __init__.py
from .backup_handler import IkuaiBackupHandler
from .config import ConfigManager
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IkuaiBackup")

# 初始化配置和处理器
config = ConfigManager()
backup_handler = IkuaiBackupHandler(config)

# 初始化调度器
scheduler = BackgroundScheduler()

def run_backup_task():
    """执行备份任务"""
    logger.info("开始执行爱快备份任务...")
    success, message = backup_handler.create_backup()
    
    if success:
        # 获取最新备份并下载
        backup_list = backup_handler.get_backup_list()
        if backup_list:
            latest_backup = backup_list[0].get("filename")
            if latest_backup:
                download_success, save_path = backup_handler.download_backup(latest_backup)
                if download_success:
                    logger.info(f"备份下载成功: {save_path}")
                    # 这里可以添加通知逻辑
                else:
                    logger.error(f"备份下载失败: {save_path}")
    else:
        logger.error(f"备份创建失败: {message}")

# 注册定时任务
scheduler.add_job(
    run_backup_task,
    'cron',
    minute=config.get('backup_interval').split(' ')[0],
    hour=config.get('backup_interval').split(' ')[1],
    day=config.get('backup_interval').split(' ')[2],
    month=config.get('backup_interval').split(' ')[3],
    day_of_week=config.get('backup_interval').split(' ')[4]
)

# 启动调度器
if not scheduler.running:
    scheduler.start()

# 提供插件信息
def get_plugin_info():
    return {
        "name": "iKuaiBackupHelper",
        "version": "1.0.0",
        "description": "爱快路由自动备份助手",
        "author": "Your Name",
        "url": "https://example.com"
    }
