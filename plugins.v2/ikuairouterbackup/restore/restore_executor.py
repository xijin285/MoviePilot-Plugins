"""恢复执行模块"""
import os
import threading
import time
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urljoin
from app.log import logger
from ..ikuai.client import IkuaiClient


class RestoreExecutor:
    """恢复执行器类"""
    
    def __init__(self, plugin_instance):
        """初始化恢复执行器"""
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def run_restore_job(self, filename: str, source: str = "本地备份"):
        """执行恢复任务（带重试逻辑）"""
        
        if not self.plugin._enable_restore:
            logger.error(f"{self.plugin_name} 恢复功能未启用")
            return
        
        if not self.plugin._restore_lock:
            self.plugin._restore_lock = threading.Lock()
        if not self.plugin._global_task_lock:
            self.plugin._global_task_lock = threading.Lock()
            
        # 尝试获取全局任务锁，如果获取不到说明有其他任务在运行
        if not self.plugin._global_task_lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 检测到其他任务正在执行，恢复任务跳过！")
            return
            
        # 尝试获取恢复锁，如果获取不到说明有恢复任务在运行
        if not self.plugin._restore_lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有恢复任务正在执行，本次操作跳过！")
            self.plugin._global_task_lock.release()  # 释放全局锁
            return
            
        restore_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": filename,
            "message": "恢复任务开始"
        }
        self.plugin._restore_activity = "任务开始"
            
        try:
            logger.info(f"{self.plugin_name} 开始执行恢复任务，文件: {filename}, 来源: {source}")

            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_restore_notification(success=False, message=error_msg, filename=filename)
                restore_entry["message"] = error_msg
                self.plugin._save_restore_history_entry(restore_entry)
                return

            # 执行恢复操作
            success, error_msg = self.perform_restore_once(filename, source)
            
            restore_entry["success"] = success
            restore_entry["message"] = "恢复成功" if success else f"恢复失败: {error_msg}"
            
            self.plugin._send_restore_notification(success=success, message=restore_entry["message"], filename=filename)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 恢复任务执行主流程出错：{str(e)}")
            restore_entry["message"] = f"恢复任务执行主流程出错: {str(e)}"
            self.plugin._send_restore_notification(success=False, message=restore_entry["message"], filename=filename)
        finally:
            self.plugin._restore_activity = "空闲"
            self.plugin._save_restore_history_entry(restore_entry)
            # 确保锁一定会被释放
            if self.plugin._restore_lock and hasattr(self.plugin._restore_lock, 'locked') and self.plugin._restore_lock.locked():
                try:
                    self.plugin._restore_lock.release()
                except RuntimeError:
                    pass
            # 释放全局任务锁
            if self.plugin._global_task_lock and hasattr(self.plugin._global_task_lock, 'locked') and self.plugin._global_task_lock.locked():
                try:
                    self.plugin._global_task_lock.release()
                except RuntimeError:
                    pass
            logger.info(f"{self.plugin_name} 恢复任务执行完成。")
    
    def perform_restore_once(self, filename: str, source: str) -> Tuple[bool, Optional[str]]:
        """
        执行一次恢复操作
        
        :param filename: 备份文件名
        :param source: 备份来源（本地备份/WebDAV备份）
        :return: (是否成功, 错误信息)
        """
        # 初始化iKuai客户端
        client = IkuaiClient(
            url=self.plugin._ikuai_url,
            username=self.plugin._ikuai_username,
            password=self.plugin._ikuai_password,
            plugin_name=self.plugin_name
        )
        
        # 登录
        if not client.login():
            return False, "登录爱快路由失败，无法获取SESS_KEY"
        
        # 获取备份文件路径
        backup_file_path = None
        if source == "本地备份":
            backup_file_path = os.path.join(self.plugin._backup_path, filename)
            if not os.path.exists(backup_file_path):
                return False, f"本地备份文件不存在: {backup_file_path}"
        elif source == "WebDAV备份":
            # 从WebDAV下载备份文件到临时目录
            temp_dir = Path(self.plugin.get_data_path()) / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            backup_file_path = str(temp_dir / filename)
            
            self.plugin._restore_activity = f"下载WebDAV中: {filename}"
            download_success, download_error = self.plugin._download_from_webdav(filename, backup_file_path)
            if not download_success:
                self.plugin._restore_activity = "空闲"
                return False, f"从WebDAV下载备份文件失败: {download_error}"
        else:
            return False, f"不支持的备份来源: {source}"

        try:
            # 读取备份文件内容
            with open(backup_file_path, 'rb') as f:
                backup_content = f.read()

            # 发送恢复请求
            restore_url = urljoin(self.plugin._ikuai_url, "/Action/call")
            restore_payload = {
                "func_name": "backup",
                "action": "RESTORE",
                "param": {}
            }

            self.plugin._restore_activity = "正在恢复配置..."
            logger.info(f"{self.plugin_name} 发送恢复请求...")

            # 首先发送RESTORE请求
            response = client.session.post(restore_url, json=restore_payload, timeout=30)
            response.raise_for_status()

            # 然后上传备份文件
            upload_url = urljoin(self.plugin._ikuai_url, "/Action/upload")
            files = {
                'file': (filename, backup_content, 'application/octet-stream')
            }
            upload_response = client.session.post(upload_url, files=files, timeout=300)
            upload_response.raise_for_status()

            # 检查响应
            try:
                result = upload_response.json()
                if result.get("Result") == 30000 or (isinstance(result, str) and "success" in result.lower()):
                    logger.info(f"{self.plugin_name} 恢复成功完成")
                    return True, None
                else:
                    error_msg = result.get("ErrMsg") or result.get("errmsg", "恢复失败，未知错误")
                    return False, error_msg
            except Exception:
                if "success" in upload_response.text.lower():
                    return True, None
                return False, f"恢复失败，响应解析错误: {upload_response.text[:200]}"

        except Exception as e:
            return False, f"恢复请求失败: {str(e)}"
        finally:
            # 如果是WebDAV备份，删除临时文件
            if source == "WebDAV备份" and backup_file_path and os.path.exists(backup_file_path):
                try:
                    os.remove(backup_file_path)
                    logger.info(f"{self.plugin_name} 已删除临时文件: {backup_file_path}")
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除临时文件失败: {str(e)}")

