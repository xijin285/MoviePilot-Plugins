"""备份执行模块"""
import hashlib
import os
import json
import shutil
import time
import threading
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urljoin
from app.log import logger
from ..ikuai.client import IkuaiClient
from ..backup.backup_manager import BackupManager
from ..backup import cloud_storage

# 变更检测哨兵：配置内容与上次一致，跳过保存
UNCHANGED_SENTINEL = "UNCHANGED"

# 上次备份内容哈希的持久化键
LAST_HASH_KEY = "ikuai_last_backup_hash"


class BackupExecutor:
    """备份执行器类"""
    
    def __init__(self, plugin_instance):
        """初始化备份执行器"""
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self._backup_manager = BackupManager(plugin_instance)
    
    def run_backup_job(self):
        """执行备份任务（带重试逻辑）"""
        if not self.plugin._lock:
            self.plugin._lock = threading.Lock()
        
        if not self.plugin._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有任务正在执行，本次调度跳过！")
            return
            
        history_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": None,
            "message": "任务开始"
        }
        job_started_at = time.time()
        self.plugin._backup_activity = "任务开始"
            
        try:
            self.plugin._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            auth_mode = (getattr(self.plugin, '_ikuai_auth_mode', 'auto') or 'auto').lower()
            api_token = (getattr(self.plugin, '_ikuai_api_token', '') or '').strip()
            if not self.plugin._ikuai_url:
                error_msg = "配置不完整：爱快路由器地址未设置。"
            elif auth_mode == "token" and not api_token:
                error_msg = "配置不完整：API令牌模式未填写令牌。"
            elif auth_mode == "token" and not self.plugin._ikuai_password:
                error_msg = "配置不完整：下载备份文件仍需账号密码（爱快4.x未开放令牌下载），请填写密码。"
            elif auth_mode != "token" and (not self.plugin._ikuai_username or not self.plugin._ikuai_password):
                error_msg = "配置不完整：URL、用户名或密码未设置。"
            else:
                error_msg = None
            if error_msg:
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self.plugin._save_backup_history_entry(history_entry)
                return

            if not self.plugin._enable_webdav and not (getattr(self.plugin, '_storage_backup_enable', False)
                                                       and getattr(self.plugin, '_storage_targets', [])):
                error_msg = "未配置任何备份目标（存储备份 / WebDAV）。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self.plugin._save_backup_history_entry(history_entry)
                return

            try:
                Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"{self.plugin_name} 创建备份目录 {self.plugin._backup_path} 失败: {e}")
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            
            for i in range(self.plugin._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self.plugin._retry_count +1} 次备份尝试...")
                current_try_success, current_try_error_msg, current_try_downloaded_file = self.perform_backup_once()
                
                if current_try_success:
                    success_final = True
                    downloaded_file_final = current_try_downloaded_file
                    error_msg_final = None
                    logger.info(f"{self.plugin_name} 第{i+1}次尝试成功。备份文件: {downloaded_file_final}")
                    break 
                else:
                    error_msg_final = current_try_error_msg
                    logger.warning(f"{self.plugin_name} 第{i+1}次备份尝试失败: {error_msg_final}")
                    if i < self.plugin._retry_count:
                        logger.info(f"{self.plugin._retry_interval}秒后重试...")
                        time.sleep(self.plugin._retry_interval)
                    else:
                        logger.error(f"{self.plugin_name} 所有 {self.plugin._retry_count +1} 次尝试均失败。最后错误: {error_msg_final}")
            
            history_entry["success"] = success_final
            history_entry["filename"] = downloaded_file_final
            history_entry["targets"] = list(getattr(self, '_last_targets', []))
            history_entry["failed"] = list(getattr(self, '_last_failed', []))
            if error_msg_final == UNCHANGED_SENTINEL:
                history_entry["unchanged"] = True
                history_entry["message"] = "备份成功（路由配置无变化，已跳过保存）"
            else:
                history_entry["message"] = "备份成功" if success_final else f"备份失败: {error_msg_final}"

            self.plugin._send_notification(
                success=success_final,
                message=history_entry["message"],
                filename=downloaded_file_final,
                targets=getattr(self, '_last_targets', []),
                failed=getattr(self, '_last_failed', []),
                size=getattr(self, '_last_size', 0),
                elapsed=round(time.time() - job_started_at, 1),
            )
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
            history_entry["message"] = f"任务执行主流程出错: {str(e)}"
            self.plugin._send_notification(success=False, message=history_entry["message"])
        finally:
            self.plugin._running = False
            self.plugin._backup_activity = "空闲"
            self.plugin._save_backup_history_entry(history_entry)
            if self.plugin._lock and hasattr(self.plugin._lock, 'locked') and self.plugin._lock.locked():
                try: self.plugin._lock.release()
                except RuntimeError: pass
            logger.info(f"{self.plugin_name} 任务执行完成。")
    
    def perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行一次备份操作
        
        :return: (是否成功, 错误信息, 备份文件名)
        """
        # 本次备份的落点 / 大小 / 耗时（供通知展示）
        started_at = time.time()
        self._last_targets: list = []
        self._last_failed: list = []
        self._last_size = 0
        self._last_elapsed = 0.0

        # 初始化iKuai客户端（自动适配认证方式：3.x 账号密码 / 4.x 令牌）
        client = IkuaiClient(
            url=self.plugin._ikuai_url,
            username=self.plugin._ikuai_username,
            password=self.plugin._ikuai_password,
            plugin_name=self.plugin_name,
            auth_mode=getattr(self.plugin, '_ikuai_auth_mode', 'auto'),
            api_token=getattr(self.plugin, '_ikuai_api_token', '')
        )
        
        # 登录
        if not client.login():
            return False, "登录爱快路由失败，无法获取SESS_KEY", None
        
        # 创建备份
        create_success, create_msg = client.create_backup()
        if not create_success:
            return False, f"创建备份失败: {create_msg}", None
        
        logger.info(f"{self.plugin_name} 成功触发创建备份。等待2秒让备份生成和准备就绪...")
        time.sleep(2)
        
        # 获取备份列表
        backup_list = client.get_backup_list()
        if backup_list is None:
            return False, "获取备份文件列表时出错 (在下载前调用)", None
        if not backup_list:
            return False, "路由器上没有找到任何备份文件 (在下载前获取列表为空)", None
        
        # 兼容新老版本，按 date 字段降序排序，优先取 filename，没有则取 name
        def get_date(x):
            # 兼容各种字段名：v3 用 date/backup_time，v4 用 timestamp(Unix秒)
            v = x.get("date") or x.get("backup_time") or ""
            if not v and x.get("timestamp"):
                try:
                    import datetime as _dt
                    v = _dt.datetime.fromtimestamp(int(x["timestamp"])).strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError, OSError):
                    v = ""
            return v
        sorted_backups = sorted(backup_list, key=get_date, reverse=True)
        latest_backup = sorted_backups[0] if sorted_backups else None
        actual_router_filename_from_api = None
        if latest_backup:
            actual_router_filename_from_api = latest_backup.get("filename") or latest_backup.get("name")
        if not actual_router_filename_from_api:
            return False, "无法从备份列表中获取最新备份的文件名", None
        # 确定文件名
        filename_for_download_url = actual_router_filename_from_api
        base_name_for_local_file = os.path.splitext(actual_router_filename_from_api)[0]
        local_display_and_saved_filename = base_name_for_local_file + ".bak"
        local_filepath_to_save = Path(self.plugin._backup_path) / local_display_and_saved_filename
        logger.info(f"{self.plugin_name} API列表最新备份名: {actual_router_filename_from_api}. 将尝试以此名下载.")
        logger.info(f"{self.plugin_name} 最终本地保存文件名将为: {local_display_and_saved_filename}")
        
        # 发送EXPORT请求
        if not self._send_export_request(client.session, local_display_and_saved_filename):
            return False, "EXPORT请求失败", None

        # 统一存储目标：文件先统一下载到临时目录，再分发到各个目标（本地 / 网盘）
        temp_dir = Path(self.plugin.get_data_path()) / "temp"
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"创建备份下载目录 {temp_dir} 失败: {e}", None
        local_filepath_to_save = temp_dir / local_display_and_saved_filename

        # 下载备份文件（本地目标与网盘/WebDAV 目标都需要先落地）
        download_success, download_msg = client.download_backup(
            filename_for_download_url,
            str(local_filepath_to_save)
        )
        if not download_success:
            error_detail = f"尝试下载 {filename_for_download_url} 失败: {download_msg}"
            return False, error_detail, None

        # 记录文件大小（通知中展示）
        try:
            self._last_size = int(local_filepath_to_save.stat().st_size)
        except Exception:
            self._last_size = 0

        # 配置变更检测：内容与上次一致则跳过保存
        if getattr(self.plugin, '_skip_unchanged_backup', True):
            unchanged, file_hash = self._check_unchanged(local_filepath_to_save)
            if unchanged:
                try:
                    local_filepath_to_save.unlink()
                    logger.info(f"{self.plugin_name} 路由配置无变化，已删除重复备份文件并跳过保存")
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除重复备份文件失败: {e}")
                return True, UNCHANGED_SENTINEL, None
            if file_hash:
                self._save_backup_hash(file_hash)

        # 分发到各个存储备份目标（本地磁盘 + 网盘可同时启用）
        targets = []
        if getattr(self.plugin, '_storage_backup_enable', False):
            targets = [t for t in (getattr(self.plugin, '_storage_targets', []) or []) if isinstance(t, dict)]
        for target in targets:
            t_type = str(target.get("type", "local") or "local")
            t_path = str(target.get("path", "") or "").strip()
            t_keep = int(target.get("keep_backup_num", 7) or 7)
            if t_type == "local":
                dest_dir = t_path or str(self.plugin._backup_path or self.plugin.get_data_path())
                if self._distribute_to_local(dest_dir, t_keep, local_filepath_to_save):
                    self._last_targets.append({"kind": "local", "label": "本地磁盘", "path": dest_dir})
                else:
                    self._last_failed.append("本地磁盘")
            else:
                if self._upload_to_cloud_target(t_type, t_path, t_keep, local_display_and_saved_filename,
                                                str(local_filepath_to_save)):
                    self._last_targets.append({"kind": "cloud", "label": t_type, "path": t_path})
                else:
                    self._last_failed.append(f"网盘·{t_type}")

        # 执行WebDAV备份（文件已下载到临时目录，直接上传）
        webdav_success = False
        if self.plugin._enable_webdav:
            webdav_success = self._upload_to_webdav(client,
                                                  True,
                                                  filename_for_download_url,
                                                  local_display_and_saved_filename,
                                                  str(local_filepath_to_save))
            if webdav_success:
                self._last_targets.append({
                    "kind": "webdav",
                    "label": "WebDAV",
                    "path": str(getattr(self.plugin, '_webdav_path', '') or ''),
                })
            else:
                self._last_failed.append("WebDAV")

        # 如果开启备份后删除，执行删除操作
        if self.plugin._delete_after_backup and (download_success or webdav_success):
            self._delete_backup_after_success(client, actual_router_filename_from_api)

        # 清理临时下载文件（本地目标已复制、网盘目标已上传）
        if not any(str(t.get("type", "local") or "local") == "local" and
                   (str(t.get("path", "") or "").strip() or str(self.plugin._backup_path or "")) == str(temp_dir)
                   for t in targets):
            try:
                local_filepath_to_save.unlink()
            except Exception as e:
                logger.warning(f"{self.plugin_name} 清理临时备份文件失败: {e}")

        self._last_elapsed = round(time.time() - started_at, 1)
        return True, None, local_display_and_saved_filename
    
    def _check_unchanged(self, filepath: Path) -> Tuple[bool, Optional[str]]:
        """
        检查备份文件内容是否与上次一致
        :return: (是否一致, 本次文件哈希)
        """
        try:
            md5 = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(1024 * 256), b''):
                    md5.update(chunk)
            file_hash = md5.hexdigest()
            last_hash = ""
            try:
                last_hash = str(self.plugin.get_data(LAST_HASH_KEY) or "")
            except Exception:
                pass
            return (bool(last_hash) and file_hash == last_hash), file_hash
        except Exception as e:
            logger.warning(f"{self.plugin_name} 计算备份文件哈希失败: {e}")
            return False, None

    def _save_backup_hash(self, file_hash: str):
        """记录本次备份内容哈希"""
        try:
            self.plugin.save_data(LAST_HASH_KEY, file_hash)
        except Exception as e:
            logger.warning(f"{self.plugin_name} 保存备份哈希失败: {e}")

    def _distribute_to_local(self, dest_dir: str, keep_num: int, temp_filepath: Path) -> bool:
        """分发备份文件到本地目标目录并清理旧备份"""
        try:
            self.plugin._backup_activity = f"保存本地: {dest_dir}"
            dest = Path(dest_dir)
            dest.mkdir(parents=True, exist_ok=True)
            target_file = dest / temp_filepath.name
            if target_file.resolve() != temp_filepath.resolve():
                shutil.copy2(str(temp_filepath), str(target_file))
                logger.info(f"{self.plugin_name} 备份已保存到本地目录: {target_file}")
            elif not target_file.exists():
                return False
            if keep_num > 0:
                deleted = self._cleanup_local_dir(dest, keep_num)
                if deleted > 0:
                    logger.info(f"{self.plugin_name} 本地目录 {dest_dir} 清理完成，删除了 {deleted} 个旧备份")
            return True
        except Exception as e:
            logger.error(f"{self.plugin_name} 本地备份目标 {dest_dir} 保存失败: {e}")
            return False

    @staticmethod
    def _cleanup_local_dir(dir_path: Path, keep_num: int) -> int:
        """清理本地目录旧备份，按文件名倒序保留最近 keep_num 个 .bak 文件"""
        if keep_num <= 0 or not dir_path.exists():
            return 0
        try:
            bak_files = sorted(
                [p for p in dir_path.glob("*.bak") if p.is_file()],
                key=lambda p: p.name,
                reverse=True,
            )
            deleted = 0
            for p in bak_files[keep_num:]:
                try:
                    p.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"删除本地旧备份失败: {p.name}: {e}")
            return deleted
        except Exception as e:
            logger.warning(f"清理本地旧备份失败: {e}")
            return 0

    def _upload_to_cloud_target(self, storage: str, remote_dir: str, keep_num: int,
                                local_filename: str, local_filepath: str) -> bool:
        """上传备份到指定 MP 网盘存储目标并清理旧备份"""
        try:
            self.plugin._backup_activity = f"上传网盘: {storage}"
            if not os.path.exists(local_filepath):
                logger.error(f"{self.plugin_name} 网盘备份源文件不存在: {local_filepath}")
                return False
            ok, err = cloud_storage.upload_backup_file(storage, remote_dir, local_filepath, local_filename)
            if ok:
                logger.info(f"{self.plugin_name} 成功上传备份到网盘存储 {storage}: {remote_dir}/{local_filename}")
                deleted, clean_err = cloud_storage.cleanup_cloud_backups(storage, remote_dir, keep_num)
                if deleted > 0:
                    logger.info(f"{self.plugin_name} 网盘 {storage}:{remote_dir} 清理完成，删除了 {deleted} 个旧备份")
                if clean_err:
                    logger.warning(f"{self.plugin_name} 网盘旧备份清理失败: {clean_err}")
                return True
            logger.error(f"{self.plugin_name} 网盘备份上传失败（存储 {storage}）: {err}")
            return False
        except Exception as e:
            logger.error(f"{self.plugin_name} 网盘备份过程中发生错误: {e}")
            return False

    def _send_export_request(self, session, filename: str) -> bool:
        """发送EXPORT请求"""
        export_payload = {
            "func_name": "backup",
            "action": "EXPORT",
            "param": {"srcfile": filename}
        }
        export_url = urljoin(self.plugin._ikuai_url, "/Action/call")
        
        try:
            logger.info(f"{self.plugin_name} 尝试向 {export_url} 发送 EXPORT 请求...")
            response = session.post(
                export_url, 
                data=json.dumps(export_payload), 
                headers={'Content-Type': 'application/json'}, 
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"{self.plugin_name} EXPORT 请求发送成功。响应: {response.text[:200]}")
            return True
        except Exception as e:
            logger.error(f"{self.plugin_name} EXPORT请求失败: {e}")
            return False
    
    def _upload_to_webdav(self, client, local_backup_enabled, 
                         router_filename, local_filename, local_filepath) -> bool:
        """处理WebDAV上传"""
        try:
            if local_backup_enabled:
                # 使用已下载的文件上传
                webdav_success, webdav_msg = self.plugin._upload_to_webdav(local_filepath, local_filename)
            else:
                # 下载到临时文件再上传
                temp_dir = Path(self.plugin.get_data_path()) / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_filepath = temp_dir / local_filename
                
                download_success, download_msg = client.download_backup(router_filename, str(temp_filepath))
                if not download_success:
                    logger.error(f"{self.plugin_name} WebDAV临时下载失败: {download_msg}")
                    return False
                
                webdav_success, webdav_msg = self.plugin._upload_to_webdav(str(temp_filepath), local_filename)
                
                # 删除临时文件
                try:
                    temp_filepath.unlink()
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除临时文件失败: {e}")
            
            if webdav_success:
                logger.info(f"{self.plugin_name} 成功上传备份到WebDAV服务器")
                self.plugin._cleanup_webdav_backups()
            else:
                logger.error(f"{self.plugin_name} WebDAV上传失败: {webdav_msg}")
            
            return webdav_success
            
        except Exception as e:
            logger.error(f"{self.plugin_name} WebDAV上传过程中发生错误: {e}")
            return False
    
    def _delete_backup_after_success(self, client, filename: str):
        """备份成功后删除路由器上的备份文件"""
        logger.info(f"{self.plugin_name} 备份成功，将删除路由器上的备份文件: {filename}")
        delete_success, delete_msg = client.delete_backup(filename)
        if delete_success:
            logger.info(f"{self.plugin_name} 成功删除路由器上的备份文件。")
        else:
            logger.warning(f"{self.plugin_name} 删除路由器上的备份文件失败: {delete_msg}")

