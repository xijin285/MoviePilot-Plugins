"""备份管理器模块"""
import os
import re
import time
from datetime import datetime
from typing import Any, List, Dict
from pathlib import Path
from app.log import logger


class BackupManager:
    """备份管理器类"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def cleanup_old_backups(self):
        """清理本地旧备份文件"""
        if not self.plugin._backup_path or self.plugin._keep_backup_num <= 0:
            return
        try:
            logger.info(f"{self.plugin_name} 开始清理本地备份目录: {self.plugin._backup_path}, 保留数量: {self.plugin._keep_backup_num} (仅处理 .bak 文件)")
            backup_dir = Path(self.plugin._backup_path)
            if not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 本地备份目录 {self.plugin._backup_path} 不存在，无需清理。")
                return

            files = []
            for f_path_obj in backup_dir.iterdir():
                if f_path_obj.is_file() and f_path_obj.suffix.lower() == ".bak":
                    try:
                        match = re.search(r'(\d{4}\d{2}\d{2}[_]?\d{2}\d{2}\d{2})', f_path_obj.stem)
                        file_time = None
                        if match:
                            time_str = match.group(1).replace('_','')
                            try:
                                file_time = datetime.strptime(time_str, '%Y%m%d%H%M%S').timestamp()
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
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个旧 .bak 备份文件需要删除。")
                for f_info in files_to_delete:
                    try:
                        f_info['path'].unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {f_info['name']}")
                    except OSError as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {f_info['name']} 失败: {e}")
            else:
                logger.info(f"{self.plugin_name} 当前 .bak 备份数量 ({len(files)}) 未超过保留限制 ({self.plugin._keep_backup_num})，无需清理。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时发生错误: {e}")
    
    def get_available_backups(self) -> List[Dict[str, Any]]:
        """获取可用的备份文件列表"""
        backups = []
        
        # 获取本地备份
        if self.plugin._enable_local_backup and self.plugin._backup_path:
            try:
                backup_dir = Path(self.plugin._backup_path)
                if backup_dir.is_dir():
                    for f_path_obj in backup_dir.iterdir():
                        if f_path_obj.is_file() and f_path_obj.suffix.lower() == ".bak":
                            try:
                                file_time = f_path_obj.stat().st_mtime
                                backups.append({
                                    'filename': f_path_obj.name,
                                    'source': '本地备份',
                                    'time': file_time
                                })
                            except Exception as e:
                                logger.error(f"{self.plugin_name} 处理本地备份文件 {f_path_obj.name} 时出错: {e}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取本地备份文件列表时发生错误: {str(e)}")
        
        # 获取WebDAV备份
        if self.plugin._enable_webdav and self.plugin._webdav_url:
            try:
                from ..webdav.webdav_client import WebDAVClient
                
                # 创建WebDAV客户端
                client = WebDAVClient(
                    url=self.plugin._webdav_url,
                    username=self.plugin._webdav_username,
                    password=self.plugin._webdav_password,
                    path=self.plugin._webdav_path,
                    skip_dir_check=True,
                    logger=logger,
                    plugin_name=self.plugin_name
                )
                
                # 获取文件列表（只获取.bak文件）
                files, error = client.list_files('.bak')
                client.close()
                
                if error:
                    logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表失败: {error}")
                else:
                    for file_info in files:
                        backups.append({
                            'filename': file_info['filename'],
                            'source': 'WebDAV备份',
                            'time': file_info['time']
                        })
                        
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表时发生错误: {str(e)}")
        
        # 按时间排序
        backups.sort(key=lambda x: x['time'], reverse=True)
        return backups

