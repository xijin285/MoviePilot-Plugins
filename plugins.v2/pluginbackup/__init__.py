import glob
import os
import shutil
import time
import tempfile 
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app import schemas # Assuming 'app' is your project's root package
from app.core.config import settings # Assuming settings are here
from app.plugins import _PluginBase # Assuming base plugin class is here
from app.log import logger # Assuming logger is configured here
from app.schemas import NotificationType # Assuming NotificationType is here

class PluginBackup(_PluginBase):
    # 插件名称
    plugin_name = "插件配置备份"
    # 插件描述
    plugin_desc = "自动备份 MoviePilot 所有插件的配置文件。"
    # 插件图标 (建议使用新图标)
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins1/refs/heads/main/icons/backup.png"
    # 插件版本
    plugin_version = "1.0" # 版本号增加，表示有功能更新
    # 插件作者
    plugin_author = "jinxi" # Or your name if you adapted it
    # 作者主页
    author_url = "https://github.com/xijin285" # Or your URL
    # 插件配置项ID前缀
    plugin_config_prefix = "pluginbackup_"
    # 加载顺序
    plugin_order = 8
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    # 任务执行间隔
    _cron = None
    _cnt = None # 最大备份数量
    _onlyonce = False # 是否立即运行一次
    _notify = False # 是否通知

    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None

    def init_plugin(self, config: dict = None):
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = config.get("enabled", False)
            self._cron = config.get("cron")
            self._cnt = config.get("cnt")
            self._notify = config.get("notify", False)
            self._onlyonce = config.get("onlyonce", False)

        if self._enabled:
            logger.info(f"{self.plugin_name} 插件已启用。")
            if self._onlyonce:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                run_time = datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=5)
                logger.info(f"{self.plugin_name} 服务启动，将在 {run_time.strftime('%Y-%m-%d %H:%M:%S')} 运行一次。")
                self._scheduler.add_job(func=self.__do_plugin_config_backup,
                                         trigger='date',
                                         run_date=run_time,
                                         name=self.plugin_name)
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config({
                    "onlyonce": False,
                    "cron": self._cron,
                    "enabled": self._enabled,
                    "cnt": self._cnt,
                    "notify": self._notify,
                })
                if self._scheduler and self._scheduler.get_jobs(): # 检查scheduler是否存在且有任务
                    self._scheduler.print_jobs()
                    self._scheduler.start()
            # For regular cron jobs, they will be picked up by get_service
        else:
            logger.info(f"{self.plugin_name} 插件未启用。")


    def api_trigger_backup(self, apikey: str):
        """
        API调用插件配置备份
        """
        if not settings.API_TOKEN or apikey != settings.API_TOKEN:
            return schemas.Response(success=False, message="API密钥错误或未配置")

        success, msg_or_data = self.__do_plugin_config_backup()
        if success:
            return schemas.Response(success=True, message=msg_or_data)
        else:
            return schemas.Response(success=False, message=msg_or_data)

    def __do_plugin_config_backup(self):
        """
        自动备份插件配置、删除旧备份
        """
        logger.info(f"当前时间 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} 开始插件配置备份")

        # 插件配置备份的存储路径 (通常是 /config/plugins/PluginConfigBackup/data)
        bk_storage_path = self.get_data_path()
        bk_storage_path.mkdir(parents=True, exist_ok=True)

        # 备份
        # 将 bk_storage_path 传递给 _create_plugin_config_archive 以便排除
        zip_file_path = self._create_plugin_config_archive(bk_storage_path, bk_storage_path)

        backup_creation_success = False
        backup_message = ""

        if zip_file_path:
            backup_creation_success = True
            backup_message = f"插件配置备份完成，备份文件: {zip_file_path}"
            logger.info(backup_message)
        else:
            backup_creation_success = False
            backup_message = "创建插件配置备份失败"
            logger.error(backup_message)

        # 清理备份
        bk_cnt_total = 0
        del_cnt = 0
        if self._cnt is not None and int(self._cnt) >= 0: # 确保 cnt 是有效的非负整数
            num_to_keep = int(self._cnt)
            # 获取指定路径下所有以 "bk_plugins_config_" 开头的文件，按创建时间从旧到新排序
            # Ensure bk_storage_path is a string for glob
            # 使用 Path().glob().iterdir() 更pythonic
            files = sorted(bk_storage_path.glob("bk_plugins_config_*.zip"), key=os.path.getctime)

            bk_cnt_total = len(files)

            # 计算需要删除的文件数
            del_cnt = bk_cnt_total - num_to_keep

            if del_cnt > 0:
                logger.info(
                    f"获取到 {bk_storage_path} 路径下插件配置备份文件数量 {bk_cnt_total}，"
                    f"保留数量 {num_to_keep}，需要删除备份文件数量 {del_cnt}")

                # 遍历并删除最旧的几个备份
                for i in range(del_cnt):
                    try:
                        os.remove(files[i])
                        logger.debug(f"删除旧的插件配置备份文件 {files[i]} 成功")
                    except OSError as e:
                        logger.error(f"删除插件配置备份文件 {files[i]} 失败: {e}")
            else:
                 logger.info(
                    f"获取到 {bk_storage_path} 路径下插件配置备份文件数量 {bk_cnt_total}，"
                    f"保留数量 {num_to_keep}，无需删除旧备份。")
            # 更新实际剩余数量
            files_after_deletion = list(bk_storage_path.glob("bk_plugins_config_*.zip"))
            remaining_backups = len(files_after_deletion)

        else:
            logger.info("未配置最大备份数量或配置为负数，不清理旧备份。")
            # 如果不清理，获取当前文件数量
            files = list(bk_storage_path.glob("bk_plugins_config_*.zip"))
            bk_cnt_total = len(files)
            del_cnt = 0
            remaining_backups = bk_cnt_total # 如果不清理，剩余就是总数


        # 发送通知
        if self._notify:
             # 修正通知信息，显示实际删除和剩余数量
            self.post_message(
                mtype=NotificationType.SiteMessage, # Or any other appropriate type
                title="【插件配置备份任务完成】",
                text=f"创建插件配置备份{'成功' if backup_creation_success else '失败'}\n"
                     f"清理的旧备份数量: {del_cnt}\n"
                     f"剩余备份数量: {remaining_backups}"
            )

        return backup_creation_success, backup_message

    @staticmethod
    def _create_plugin_config_archive(backup_destination_path: Path, exclusion_path: Path) -> Optional[str]:
        """
        创建插件配置文件的zip压缩包，排除指定的路径。
        @param backup_destination_path: 备份文件存储的目标文件夹路径 (e.g., /config/plugins/PluginConfigBackup/data)
        @param exclusion_path: 需要从备份中排除的路径 (例如，backup_destination_path本身)
        @return: 成功则返回zip文件路径，否则返回None
        """
        plugins_config_source_dir = Path(settings.CONFIG_PATH) / "plugins"
        temp_dir = None # 初始化临时目录变量

        try:
            if not plugins_config_source_dir.is_dir():
                logger.error(f"插件配置目录 {plugins_config_source_dir} 不存在或不是一个目录。")
                return None

            # 创建一个临时目录用于存放需要备份的文件
            temp_dir = Path(tempfile.mkdtemp())
            logger.debug(f"创建临时备份目录: {temp_dir}")

            # 遍历源目录，将需要备份的文件复制到临时目录
            for entry in plugins_config_source_dir.iterdir():
                # 获取完整路径，并进行路径解析，以便准确比较（处理软链接等情况）
                full_path = plugins_config_source_dir / entry.name
                try:
                    # 排除备份文件存放的目录 itself
                    if full_path.resolve() == exclusion_path.resolve():
                        logger.debug(f"排除备份目录: {full_path}")
                        continue

                    # 复制文件或目录到临时目录
                    dest_path = temp_dir / entry.name
                    if entry.is_dir():
                        shutil.copytree(full_path, dest_path)
                        logger.debug(f"复制目录 {full_path} 到 {dest_path}")
                    else:
                        shutil.copy2(full_path, dest_path) # copy2 保留元数据
                        logger.debug(f"复制文件 {full_path} 到 {dest_path}")

                except Exception as copy_error:
                    logger.warning(f"复制 {full_path} 到临时目录失败: {copy_error}", exc_info=True)
                    # 这里的错误可能是由于文件正在被使用等，通常不应该中断整个备份
                    continue # 继续处理下一个文件/目录


            # 定义备份文件名，包含时间戳
            timestamp = time.strftime('%Y%m%d%H%M%S')
            archive_name_base = f"bk_plugins_config_{timestamp}"

            # 压缩包的完整基本路径 (不含.zip后缀)，指定到备份目标目录
            archive_path_base = backup_destination_path / archive_name_base

            # 创建压缩文件，压缩临时目录的内容
            # base_name: 压缩文件的路径和名称（不含扩展名），这里是最终存放zip的位置
            # format: 压缩格式
            # root_dir: 要压缩的根目录，压缩包中的文件路径将相对于此目录，这里是临时目录
            zip_file_path_str = shutil.make_archive(
                base_name=str(archive_path_base),
                format='zip',
                root_dir=str(temp_dir) # 压缩临时目录的内容
            )

            logger.info(f"插件配置文件（排除自身备份目录后）已压缩到: {zip_file_path_str}")
            return zip_file_path_str

        except Exception as e:
            logger.error(f"创建插件配置备份压缩包失败: {e}", exc_info=True)
            return None
        finally:
            # 清理临时目录
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"清理临时备份目录: {temp_dir}")
                except Exception as cleanup_error:
                    logger.error(f"清理临时备份目录 {temp_dir} 失败: {cleanup_error}", exc_info=True)


    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        # 如果不需要命令行交互，可以返回空列表或None
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return [{
            "path": "/backup_plugin_configs", # API路径
            "endpoint": self.api_trigger_backup, # 调用的方法
            "methods": ["GET"], # HTTP方法
            "summary": "手动触发插件配置备份",
            "description": "通过API密钥调用，立即执行一次插件配置的备份和清理操作。",
        }]

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件定时服务
        """
        services = []
        if self._enabled and self._cron:
            try:
                # 验证cron表达式
                CronTrigger.from_crontab(self._cron, timezone=settings.TZ)
                services.append({
                    "id": "PluginConfigBackupService", # 服务ID
                    "name": "插件配置自动备份服务", # 服务名称
                    "trigger": CronTrigger.from_crontab(self._cron, timezone=settings.TZ), # 触发器
                    "func": self.__do_plugin_config_backup, # 执行的函数
                    "kwargs": {} # 定时器参数
                })
                logger.info(f"插件配置自动备份服务已注册，CRON: '{self._cron}'")
            except ValueError as e:
                logger.error(f"无效的CRON表达式 '{self._cron}' for PluginConfigBackupService: {e}")
        return services

    def trigger_manual_backup(self) -> schemas.Response:
        """
        供UI或其他内部调用手动触发备份 (不通过API密钥)
        """
        if not self._enabled:
            return schemas.Response(success=False, message="插件配置备份功能未启用。")

        logger.info("手动触发插件配置备份...")
        success, msg = self.__do_plugin_config_backup()
        return schemas.Response(
            success=success,
            message=msg
        )

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面
        """
        form_structure = [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件配置备份'}}]
                            },
                            {
                                'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '开启完成通知'}}]
                            },
                            {
                                'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'onlyonce', 'label': '保存后立即运行一次'}}]
                            },
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                                'content': [{'component': 'VTextField', 'props': {'model': 'cron', 'label': '备份周期 (Cron表达式)', 'placeholder': '例如: 0 2 * * * (每天凌晨2点)'}}]
                            },
                            {
                                'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                                'content': [{'component': 'VTextField', 'props': {'model': 'cnt', 'label': '最大保留备份数量', 'type': 'number', 'placeholder': '例如: 7 (留最近7个)', 'hint': '设置为 0 或留空 不清理旧备份'}}]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol', 'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info', 'variant': 'tonal',
                                            'text': (
                                                '此插件用于备份所有插件的配置文件。 '
                                                f'插件配置文件通常位于 {Path(settings.CONFIG_PATH) / "plugins"} 目录。 '
                                                f'备份文件将存储在插件自身的数据目录中 (通常是 {self.get_data_path()})。 '
                                                'Cron表达式示例： "0 3 * * *" 表示每天凌晨3点执行。'
                                            )
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        # 默认数据结构
        default_data = {
            "enabled": self._enabled,
            "cron": self._cron or "0 2 * * *", # Default to 2 AM daily
            "cnt": self._cnt if self._cnt is not None else 7, # Default to keeping 7 backups, allow 0
            "notify": self._notify,
            "onlyonce": self._onlyonce
        }
        return form_structure, default_data

    def get_page(self) -> List[dict]:
        # 如果插件有自定义页面，在此定义其结构
        return []

    def stop_service(self):
        """
        停止插件服务，清理定时器
        """
        try:
            # 尝试停止一次性调度器（如果在运行）
            if hasattr(self, '_scheduler') and self._scheduler and self._scheduler.running:
                 self._scheduler.shutdown(wait=False)
                 logger.info(f"{self.plugin_name} 的一次性调度器已停止。")
            # 注意：主调度器（get_service注册的）由 MoviePilot 核心管理停止
            # 只需要确保本插件创建的一次性调度器被妥善处理
            self._scheduler = None # 清空引用
        except Exception as e:
            # 停止服务时不应该抛出异常导致核心崩溃，记录错误即可
            logger.error(f"停止 {self.plugin_name} 插件服务失败: {e}", exc_info=True)
