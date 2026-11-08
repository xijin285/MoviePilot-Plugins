"""
恢复执行模块
负责执行恢复任务的调度逻辑
"""
import threading
import time
from app.log import logger


class RestoreExecutor:
    """恢复执行器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化恢复执行器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def run_restore_job(self, filename: str, source: str = "本地备份", restore_vmid: str = "", restore_force: bool = False, restore_skip_existing: bool = True):
        """执行恢复任务"""
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
            "target_vmid": restore_vmid or "自动",
            "message": "恢复任务开始"
        }
        self.plugin._restore_activity = "任务开始"
            
        try:
            logger.info(f"{self.plugin_name} 开始执行恢复任务，文件: {filename}, 来源: {source}, 目标VMID: {restore_vmid}")

            if not self.plugin._pve_host or not self.plugin._ssh_username or (not self.plugin._ssh_password and not self.plugin._ssh_key_file):
                error_msg = "配置不完整：PVE主机地址、SSH用户名或SSH认证信息(密码/密钥)未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._notification_handler.send_restore_notification(success=False, message=error_msg, filename=filename)
                restore_entry["message"] = error_msg
                self.plugin._history_handler.save_restore_history_entry(restore_entry)
                return

            # 执行恢复操作
            success, error_msg, target_vmid = self.plugin._restore_manager.perform_restore_once(filename, source, restore_vmid, restore_force, restore_skip_existing)
            
            restore_entry["success"] = success
            restore_entry["target_vmid"] = target_vmid or restore_vmid or "自动"
            restore_entry["message"] = "恢复成功" if success else f"恢复失败: {error_msg}"
            
            self.plugin._notification_handler.send_restore_notification(success=success, message=restore_entry["message"], filename=filename, target_vmid=target_vmid)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 恢复任务执行主流程出错：{str(e)}")
            restore_entry["message"] = f"恢复任务执行主流程出错: {str(e)}"
            self.plugin._notification_handler.send_restore_notification(success=False, message=restore_entry["message"], filename=filename)
        finally:
            self.plugin._restore_activity = "空闲"
            self.plugin._history_handler.save_restore_history_entry(restore_entry)
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

