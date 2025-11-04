"""
备份管理模块
负责备份文件的清理和管理
"""
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from app.log import logger


class BackupManager:
    """备份管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化备份管理器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def cleanup_old_backups(self):
        """清理旧的备份文件"""
        if not self.plugin._backup_path or self.plugin._keep_backup_num <= 0:
            return
        try:
            logger.info(f"{self.plugin_name} 开始清理本地备份目录: {self.plugin._backup_path}, 保留数量: {self.plugin._keep_backup_num} (仅处理 .tar.gz 文件)")
            backup_dir = Path(self.plugin._backup_path)
            if not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 本地备份目录 {self.plugin._backup_path} 不存在，无需清理。")
                return

            files = []
            for f_path_obj in backup_dir.iterdir():
                if f_path_obj.is_file() and f_path_obj.suffix.lower() == ".gz" and f_path_obj.stem.endswith('.tar'):
                    try:
                        match = re.search(r'(\d{8}_\d{6})', f_path_obj.stem)
                        file_time = None
                        if match:
                            time_str = match.group(1)
                            try:
                                file_time = datetime.strptime(time_str, '%Y%m%d_%H%M%S').timestamp()
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
            
            if len(files) > self.plugin._keep_backup_num:
                files_to_delete = files[self.plugin._keep_backup_num:]
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个旧备份文件需要删除。")
                for f_info in files_to_delete:
                    try:
                        f_info['path'].unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {f_info['name']}")
                    except OSError as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {f_info['name']} 失败: {e}")
            else:
                logger.info(f"{self.plugin_name} 当前备份数量 ({len(files)}) 未超过保留限制 ({self.plugin._keep_backup_num})，无需清理。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时发生错误: {e}")

