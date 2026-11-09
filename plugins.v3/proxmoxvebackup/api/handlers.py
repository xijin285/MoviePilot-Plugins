"""
API处理模块
包含所有API端点的处理函数
"""
import os
import sys
import time
import threading
import tempfile
from pathlib import Path
from typing import Optional
from fastapi.responses import JSONResponse, Response
import paramiko
import pytz
from app.core.config import settings
from app.log import logger
from ..pve.client import get_pve_status, get_container_status, get_qemu_status, clean_pve_tmp_files, clean_pve_logs, list_template_images


class APIHandler:
    """API处理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化API处理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def _get_config(self):
        """API处理函数：返回当前配置（附带 MP 存储列表供前端选择）"""
        config = self.plugin.get_config() or {}
        # 本地磁盘目标：路径留空时预填默认备份路径（原「本地备份路径」配置），便于直接查看与修改
        default_path = str(getattr(self.plugin, "_backup_path", "") or "")
        targets = config.get("storage_targets")
        if not isinstance(targets, list) or not targets:
            # 尚未配置存储目标：直接给一行预填好的本地磁盘目标
            if default_path:
                config["storage_targets"] = [{"type": "local", "path": default_path, "keep_backup_num": 0}]
        else:
            for t in targets:
                if not isinstance(t, dict):
                    continue
                ttype = str(t.get("type") or "").strip()
                tpath = str(t.get("path") or "").strip()
                if ttype in ("", "local") and not tpath and default_path:
                    t["path"] = default_path
                    if not ttype:
                        t["type"] = "local"
        try:
            from ..storage import cloud_storage
            config['mp_storages'] = cloud_storage.list_mp_storages()
        except Exception as e:
            logger.warning(f"{self.plugin_name} 枚举 MP 存储失败: {e}")
            config['mp_storages'] = []
        return config

    def _list_dir(self, path: str = "", storage: str = ""):
        """浏览目录（目录选择器）：storage 为 local/空时浏览 MP 本地磁盘，否则浏览对应 MP 存储"""
        try:
            if storage and storage != "local":
                from ..storage import cloud_storage
                return cloud_storage.list_storage_dir(storage, path or "/")
            target = Path(path) if path else Path("/")
            if not target.exists():
                return {"ok": False, "error": f"路径不存在: {path}", "path": "", "parent": "", "dirs": []}
            if not target.is_dir():
                target = target.parent
            dirs = []
            try:
                for child in target.iterdir():
                    try:
                        if child.is_dir():
                            dirs.append(child.name)
                    except Exception:
                        continue
            except Exception as e:
                return {"ok": False, "error": str(e), "path": "", "parent": "", "dirs": []}
            dirs.sort(key=str.lower)
            clean = "/" + str(target).replace("\\", "/").strip("/")
            parts = [p for p in clean.split("/") if p]
            parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
            return {"ok": True, "path": str(target), "parent": parent, "dirs": dirs}
        except Exception as e:
            return {"ok": False, "error": str(e), "path": "", "parent": "", "dirs": []}
    
    def _get_status(self):
        """API处理函数：返回插件状态"""
        # 获取下次运行时间
        next_run_time = None
        if self.plugin._scheduler:
            job = self.plugin._scheduler.get_job(f"{self.plugin_name}定时服务")
            if job and job.next_run_time:
                next_run_time = job.next_run_time.astimezone(pytz.timezone(settings.TZ)).strftime("%Y-%m-%d %H:%M:%S")
        # 获取配置中的轮询间隔（单位：毫秒）
        config = self.plugin.get_config() or {}
        return {
            "enabled": self.plugin._enabled,
            "backup_activity": self.plugin._backup_activity,
            "restore_activity": self.plugin._restore_activity,
            "enable_restore": self.plugin._enable_restore,
            "cron": self.plugin._cron,
            "next_run_time": next_run_time,
            "enable_log_cleanup": getattr(self.plugin, "_enable_log_cleanup", False),
            "cleanup_template_images": self.plugin._cleanup_template_images,
            "auto_cleanup_tmp": config.get("auto_cleanup_tmp", True),
            # 状态页轮询配置（单位：毫秒）
            "status_poll_interval": config.get("status_poll_interval", 30000),
            "container_poll_interval": config.get("container_poll_interval", 30000),
        }
    
    def _save_config(self, data: dict = None):
        """API处理函数：保存配置（部分字段保存时与现有配置合并，防止未传字段被重置为默认值）"""
        if not data:
            # 尝试从请求中获取数据
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        try:
            current = self.plugin.get_config() or {}
        except Exception:
            current = {}
        merged = dict(current)
        merged.update(data or {})
        self.plugin.init_plugin(merged)
        return {"success": True, "message": "配置已保存"}
    
    def _get_backup_history(self):
        return self.plugin._history_handler.load_backup_history() or []
    
    def _run_backup(self):
        threading.Thread(target=self.plugin._backup_executor.run_backup_job).start()
        return {"success": True, "message": "备份任务已启动"}
    
    def _clear_history_api(self):
        self.plugin._history_handler.clear_all_history()
        return {"success": True, "message": "历史已清理"}
    
    def _get_restore_history(self):
        return self.plugin._history_handler.load_restore_history() or []
    
    def _get_dashboard_data(self):
        """API处理函数：返回仪表板数据"""
        backup_history = self.plugin._history_handler.load_backup_history()
        restore_history = self.plugin._history_handler.load_restore_history()
        available_backups = self.plugin._backup_manager.get_available_backups()
        
        # 统计成功和失败的备份
        successful_backups = sum(1 for item in backup_history if item.get("success", False))
        failed_backups = len(backup_history) - successful_backups
        
        # 统计成功和失败的恢复
        successful_restores = sum(1 for item in restore_history if item.get("success", False))
        failed_restores = len(restore_history) - successful_restores
        
        # 统计本地和WebDAV备份数量
        local_backups_count = sum(1 for b in available_backups if b['source'] == '本地备份')
        webdav_backups_count = sum(1 for b in available_backups if b['source'] == 'WebDAV备份')
        
        return {
            "backup_stats": {
                "total": len(backup_history),
                "successful": successful_backups,
                "failed": failed_backups
            },
            "restore_stats": {
                "total": len(restore_history),
                "successful": successful_restores,
                "failed": failed_restores
            },
            "available_backups": {
                "local": local_backups_count,
                "webdav": webdav_backups_count,
                "total": len(available_backups)
            },
            "status": {
                "backup_activity": self.plugin._backup_activity,
                "restore_activity": self.plugin._restore_activity,
                "running": self.plugin._running
            }
        }
    
    def _get_api_client(self):
        """构造 PVE REST API 客户端（复用实例以复用登录票据，配置变化时重建）"""
        config = self.plugin.get_config() or {}
        try:
            api_port = int(config.get("pve_api_port") or 8006)
        except (TypeError, ValueError):
            api_port = 8006
        key = (self.plugin._pve_host, api_port, self.plugin._ssh_username, self.plugin._ssh_password)
        client = getattr(self.plugin, "_pve_api_client", None)
        if client is not None and getattr(self.plugin, "_pve_api_client_key", None) == key:
            return client
        from ..pve.api_client import PveApiClient
        client = PveApiClient(
            host=self.plugin._pve_host, port=api_port,
            username=self.plugin._ssh_username,
            password=self.plugin._ssh_password)
        self.plugin._pve_api_client = client
        self.plugin._pve_api_client_key = key
        return client

    def _local_backup_dir(self) -> str:
        """本地备份有效目录（存储目标中本地磁盘的路径，留空回落默认目录）"""
        try:
            return self.plugin._backup_manager.get_local_backup_settings()["path"]
        except Exception:
            return self.plugin._backup_path

    def _get_monitor_api(self, timeframe: str = "hour"):
        """API处理函数：节点监控（状态 + RRD 曲线 + 存储 + 最近任务）
        GET 端点必须用简单类型签名，FastAPI 才会从 query 参数注入 timeframe"""
        timeframe = str(timeframe or "hour")
        try:
            client = self._get_api_client()
            result = client.node_monitor(timeframe)
            if isinstance(result, dict):
                # 前端构建 noVNC 控制台链接用
                result["api_host"] = self.plugin._pve_host
            return result
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取PVE监控数据失败: {e}")
            return {"error": str(e)}

    def _get_guest_monitor_api(self, vmid: int = None, type: str = "qemu", timeframe: str = "hour"):
        """API处理函数：单虚机/容器监控（当前状态 + RRD 曲线）"""
        if vmid is None:
            return {"error": "缺少 vmid 参数"}
        gtype = str(type or "qemu")
        if gtype not in ("qemu", "lxc"):
            gtype = "qemu"
        try:
            client = self._get_api_client()
            return client.guest_monitor(int(vmid), gtype, str(timeframe or "hour"))
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取虚机监控数据失败: {e}")
            return {"error": str(e)}

    def _terminal_api(self, data: dict = None):
        """API处理函数：宿主机控制台（SSH 执行单条命令并返回输出）

        注意：非交互式执行，每次新建 SSH 连接，命令超时 20 秒。
        """
        if not data:
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        command = str(data.get("command", "")).strip()
        if not command:
            return {"success": False, "output": "", "message": "命令为空"}
        if len(command) > 2000:
            return {"success": False, "output": "", "message": "命令过长（上限2000字符）"}
        ssh = paramiko.SSHClient()
        try:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            key_file = getattr(self.plugin, "_ssh_key_file", None)
            connect_kwargs = dict(
                hostname=self.plugin._pve_host,
                port=int(self.plugin._ssh_port or 22),
                username=self.plugin._ssh_username,
                timeout=10,
            )
            if key_file and os.path.exists(str(key_file)):
                connect_kwargs.update(key_filename=str(key_file))
            else:
                connect_kwargs.update(password=self.plugin._ssh_password,
                                      allow_agent=False, look_for_keys=False)
            ssh.connect(**connect_kwargs)
            stdin, stdout, stderr = ssh.exec_command(command, timeout=20)
            out = stdout.read().decode("utf-8", "ignore")
            err = stderr.read().decode("utf-8", "ignore")
            try:
                code = stdout.channel.recv_exit_status()
            except Exception:
                code = -1
            output = out
            if err.strip():
                output = (output + "\n" + err) if output else err
            return {"success": True, "output": output, "exit_code": code}
        except Exception as e:
            logger.error(f"{self.plugin_name} 控制台执行命令失败: {e}")
            return {"success": False, "output": "", "message": str(e)}
        finally:
            try:
                ssh.close()
            except Exception:
                pass

    @staticmethod
    def _ppm_to_png(ppm: bytes):
        """QEMU screendump 的 P6 PPM 转 PNG（纯标准库，避免依赖 PIL）"""
        import zlib as _zlib
        import struct as _struct
        if ppm[:2] != b"P6":
            raise ValueError("不是 P6 PPM 数据")
        idx = 2
        fields = []
        while len(fields) < 3:
            while idx < len(ppm) and ppm[idx:idx + 1].isspace():
                idx += 1
            if ppm[idx:idx + 1] == b"#":
                while idx < len(ppm) and ppm[idx:idx + 1] != b"\n":
                    idx += 1
                continue
            start = idx
            while idx < len(ppm) and not ppm[idx:idx + 1].isspace():
                idx += 1
            fields.append(int(ppm[start:idx]))
        idx += 1
        w, h, _maxval = fields
        raw = ppm[idx: idx + w * h * 3]
        lines = b"".join(b"\x00" + raw[y * w * 3:(y + 1) * w * 3] for y in range(h))

        def chunk(tag, data):
            c = tag + data
            return _struct.pack(">I", len(data)) + c + _struct.pack(">I", _zlib.crc32(c) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", _zlib.compress(lines, 6))
        png += chunk(b"IEND", b"")
        return png, w, h

    # 截图节流缓存：{vmid: (time, png_bytes)}，避免多端同时轮询时重复 screendump
    _screen_cache = {}

    def _vm_screen_api(self, vmid: int = None, type: str = "qemu"):
        """API处理函数：虚机实时画面（QEMU screendump + SSH 取回 + PNG），无需浏览器登录 PVE"""
        if vmid is None:
            return JSONResponse({"success": False, "message": "缺少 vmid"}, status_code=400)
        gtype = str(type or "qemu").lower()
        if gtype != "qemu":
            return JSONResponse({"success": False, "message": "容器暂不支持实时画面，请使用完整控制台"}, status_code=400)

        # 1.5 秒内的请求直接复用上一张，防止多端轮询打爆 PVE
        now = time.time()
        cached = self._screen_cache.get(vmid)
        if cached and now - cached[0] < 1.5:
            return Response(content=cached[1], media_type="image/png")

        try:
            # 1) QEMU screendump 到 /tmp
            client = self._get_api_client()
            client.qemu_monitor(vmid, f"screendump /tmp/mp_screen_{vmid}.ppm")
            time.sleep(0.15)  # 等 QEMU 落盘

            # 2) SSH SFTP 读回并删除
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connect_kwargs = dict(
                hostname=self.plugin._pve_host,
                port=int(self.plugin._ssh_port or 22),
                username=self.plugin._ssh_username,
                timeout=8,
            )
            key_file = getattr(self.plugin, "_ssh_key_file", None)
            if key_file and os.path.exists(str(key_file)):
                connect_kwargs.update(key_filename=str(key_file))
            else:
                connect_kwargs.update(password=self.plugin._ssh_password,
                                      allow_agent=False, look_for_keys=False)
            ssh.connect(**connect_kwargs)
            try:
                sftp = ssh.open_sftp()
                with sftp.open(f"/tmp/mp_screen_{vmid}.ppm", "rb") as f:
                    ppm = f.read()
                try:
                    sftp.remove(f"/tmp/mp_screen_{vmid}.ppm")
                except Exception:
                    pass
                sftp.close()
            finally:
                ssh.close()

            # 3) PPM -> PNG
            png, w, h = self._ppm_to_png(ppm)
            self._screen_cache[vmid] = (now, png)
            return Response(content=png, media_type="image/png",
                            headers={"Cache-Control": "no-store", "X-Screen-W": str(w), "X-Screen-H": str(h)})
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取虚机 {vmid} 实时画面失败: {e}")
            return JSONResponse({"success": False, "message": str(e)}, status_code=500)

    def _get_pve_status_api(self):
        # 生成缓存键
        cache_key = "pve_status"
        
        # 检查缓存（使用Redis缓存，自动处理过期）
        if hasattr(self.plugin, '_pve_status_cache') and cache_key in self.plugin._pve_status_cache:
            logger.debug(f"{self.plugin_name} 使用缓存数据: PVE状态")
            return self.plugin._pve_status_cache[cache_key]
        
        # 获取新数据
        logger.debug(f"{self.plugin_name} 缓存未命中，从PVE获取新数据")
        status = get_pve_status(
            self.plugin._pve_host,
            self.plugin._ssh_port,
            self.plugin._ssh_username,
            self.plugin._ssh_password,
            self.plugin._ssh_key_file
        )
        # 更新缓存
        if hasattr(self.plugin, '_pve_status_cache'):
            self.plugin._pve_status_cache[cache_key] = status
            logger.debug(f"{self.plugin_name} 已将PVE状态存入缓存")
        return status
    
    def _get_container_status_api(self):
        """获取虚拟机/容器状态：30 秒短缓存（避免每次刷新都等 SSH，同时保持准实时）"""
        cache_key = "container_status"
        if hasattr(self.plugin, '_container_status_cache') and cache_key in self.plugin._container_status_cache:
            return self.plugin._container_status_cache[cache_key]
        # 合并QEMU和LXC
        qemu_list = get_qemu_status(
            self.plugin._pve_host,
            self.plugin._ssh_port,
            self.plugin._ssh_username,
            self.plugin._ssh_password,
            self.plugin._ssh_key_file
        )
        lxc_list = get_container_status(
            self.plugin._pve_host,
            self.plugin._ssh_port,
            self.plugin._ssh_username,
            self.plugin._ssh_password,
            self.plugin._ssh_key_file
        )
        # 直接返回，displayName字段已由pve.py补充
        result = qemu_list + lxc_list
        if hasattr(self.plugin, '_container_status_cache'):
            self.plugin._container_status_cache[cache_key] = result
        return result
    
    def _get_available_backups_api(self):
        """API处理函数：返回可用备份文件列表"""
        return self.plugin._backup_manager.get_available_backups() or []
    
    def _delete_backup_api(self, data: dict = None):
        """API处理函数：删除本地备份文件或WebDAV备份文件"""
        if not data:
            # 兼容flask
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        filename = data.get("filename")
        source = data.get("source", "本地备份")
        if not filename:
            return {"success": False, "message": "缺少文件名参数"}
        if source == "本地备份":
            # 防止路径穿越
            backup_dir = Path(self._local_backup_dir())
            file_path = backup_dir / filename
            try:
                # 只允许删除实际备份目录下的文件
                if not file_path.is_file() or not str(file_path.resolve()).startswith(str(backup_dir.resolve())):
                    return {"success": False, "message": "文件不存在或路径非法"}
                os.remove(file_path)
                return {"success": True, "message": f"已删除备份文件: {filename}"}
            except Exception as e:
                return {"success": False, "message": f"删除失败: {str(e)}"}
        elif source.endswith("网盘") and source not in ("本地备份", "WebDAV备份"):
            # MP 存储网盘删除
            storage = str(data.get("storage", "")).strip()
            remote_dir = str(data.get("remote_dir", "")).strip()
            if not storage:
                return {"success": False, "message": "缺少存储标识"}
            try:
                from ..storage import cloud_storage
                ok, err = cloud_storage.delete_cloud_backup(storage, remote_dir or "/pve_backups", filename)
                if ok:
                    return {"success": True, "message": f"已删除网盘备份: {filename}"}
                return {"success": False, "message": err or "删除失败"}
            except Exception as e:
                return {"success": False, "message": f"删除失败: {str(e)}"}
        elif source == "WebDAV备份":
            # WebDAV 删除逻辑（使用新的WebDAV客户端）
            try:
                from ..storage.webdav import WebDAVClient
                
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
                
                # 执行删除
                success, error = client.delete_file(filename)
                client.close()
                
                if success:
                    return {"success": True, "message": f"已删除WebDAV备份文件: {filename}"}
                else:
                    return {"success": False, "message": f"WebDAV删除失败: {error}"}
            except Exception as e:
                return {"success": False, "message": f"WebDAV删除异常: {str(e)}"}
        else:
            return {"success": False, "message": "仅支持本地备份和WebDAV备份删除"}
    
    def _find_cloud_target(self, source: str) -> Optional[dict]:
        """根据来源显示名（如「夸克网盘」）匹配已配置的 MP 存储目标"""
        try:
            targets = self.plugin._backup_manager.get_cloud_targets()
        except Exception:
            return None
        for t in targets:
            if source in (f"{t['name']}网盘", t["name"], t["type"]):
                return t
        return None

    def _restore_backup_api(self, data: dict = None):
        """API处理函数：恢复本地备份文件"""
        if not data:
            # 兼容flask
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        filename = data.get("filename")
        source = data.get("source", "本地备份")
        restore_vmid = data.get("restore_vmid", "")
        restore_force = data.get("restore_force", False)
        restore_skip_existing = data.get("restore_skip_existing", True)
        if not filename:
            return {"success": False, "message": "缺少文件名参数"}
        if source == "WebDAV备份" or source == "本地备份":
            pass
        elif not source.endswith("网盘"):
            return {"success": False, "message": f"不支持的备份来源: {source}"}
        # 直接参数传递，不再赋值到self
        try:
            threading.Thread(
                target=self.plugin._restore_executor.run_restore_job,
                args=(filename, source, restore_vmid, restore_force, restore_skip_existing)
            ).start()
            return {"success": True, "message": f"已启动恢复任务: {filename}"}
        except Exception as e:
            return {"success": False, "message": f"恢复任务启动失败: {str(e)}"}
    
    def _download_backup_api(self, filename: str = None, source: str = "本地备份", apikey: str = None):
        """API处理函数：下载本地备份文件或WebDAV备份文件（兼容FastAPI/Flask插件系统，参数显式声明）"""
        # FastAPI 环境
        if 'fastapi' in sys.modules:
            from fastapi.responses import FileResponse, JSONResponse
            if apikey is not None:
                if apikey != settings.API_TOKEN:
                    return JSONResponse({"success": False, "message": "API_KEY 校验不通过"}, status_code=401)
            if not filename:
                return JSONResponse({"success": False, "message": "缺少文件名参数"}, status_code=400)
            if source == "本地备份":
                backup_dir = Path(self._local_backup_dir())
                file_path = backup_dir / filename
                if not file_path.is_file() or not str(file_path.resolve()).startswith(str(backup_dir.resolve())):
                    return JSONResponse({"success": False, "message": "文件不存在或路径非法"}, status_code=404)
                return FileResponse(
                    path=str(file_path),
                    filename=os.path.basename(filename),
                    media_type="application/octet-stream"
                )
            elif source == "WebDAV备份":
                # 先下载到临时目录
                temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / filename
                success, error = self.plugin._backup_manager.download_from_webdav(filename, str(temp_file))
                if not success:
                    return JSONResponse({"success": False, "message": f"WebDAV下载失败: {error}"}, status_code=400)
                resp = FileResponse(
                    path=str(temp_file),
                    filename=filename,
                    media_type="application/octet-stream"
                )
                # 下载完自动清理临时文件
                def cleanup():
                    try:
                        temp_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup, daemon=True).start()
                return resp
            elif source.endswith("网盘"):
                # MP 存储网盘下载
                target = self._find_cloud_target(source)
                if not target:
                    return JSONResponse({"success": False, "message": f"未找到网盘来源: {source}"}, status_code=400)
                temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / filename
                from ..storage import cloud_storage
                success, error = cloud_storage.download_backup_file(
                    target["type"], target["path"] or "/pve_backups", filename, str(temp_file))
                if not success:
                    return JSONResponse({"success": False, "message": f"网盘下载失败: {error}"}, status_code=400)
                resp = FileResponse(
                    path=str(temp_file),
                    filename=filename,
                    media_type="application/octet-stream"
                )

                def cleanup():
                    try:
                        temp_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup, daemon=True).start()
                return resp
            else:
                return JSONResponse({"success": False, "message": "暂不支持该来源的备份文件下载"}, status_code=400)
        # Flask 环境
        elif 'flask' in sys.modules:
            from flask import request, send_file, abort
            filename = request.args.get("filename")
            source = request.args.get("source", "本地备份")
            apikey = request.args.get("apikey")
            if apikey is not None:
                if apikey != settings.API_TOKEN:
                    return abort(401, description="API_KEY 校验不通过")
            if not filename:
                return abort(400, description="缺少文件名参数")
            if source == "本地备份":
                backup_dir = Path(self._local_backup_dir())
                file_path = backup_dir / filename
                if not file_path.is_file() or not str(file_path.resolve()).startswith(str(backup_dir.resolve())):
                    return abort(404, description="文件不存在或路径非法")
                return send_file(
                    str(file_path),
                    as_attachment=True,
                    download_name=os.path.basename(filename),
                    mimetype="application/octet-stream"
                )
            elif source == "WebDAV备份":
                temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / filename
                success, error = self.plugin._backup_manager.download_from_webdav(filename, str(temp_file))
                if not success:
                    return abort(400, description=f"WebDAV下载失败: {error}")
                resp = send_file(
                    str(temp_file),
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/octet-stream"
                )
                import threading
                def cleanup():
                    try:
                        temp_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup, daemon=True).start()
                return resp
            elif source.endswith("网盘"):
                # MP 存储网盘下载（Flask）
                target = self._find_cloud_target(source)
                if not target:
                    return abort(400, description=f"未找到网盘来源: {source}")
                temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / filename
                from ..storage import cloud_storage
                success, error = cloud_storage.download_backup_file(
                    target["type"], target["path"] or "/pve_backups", filename, str(temp_file))
                if not success:
                    return abort(400, description=f"网盘下载失败: {error}")
                resp = send_file(
                    str(temp_file),
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/octet-stream"
                )

                def cleanup():
                    try:
                        temp_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                threading.Thread(target=cleanup, daemon=True).start()
                return resp
            else:
                return abort(400, description="暂不支持该来源的备份文件下载")
        else:
            return {"success": False, "message": "仅支持Flask/FastAPI环境下载"}
    
    def _get_token(self):
        """API处理函数：返回API_TOKEN"""
        return {"api_token": settings.API_TOKEN}
    
    def _container_action_api(self, data: dict = None):
        if not data:
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        vmid = str(data.get("vmid", "")).strip()
        action = str(data.get("action", "")).strip()  # start/stop/reboot
        vmtype = str(data.get("type", "")).strip().lower()  # qemu/lxc
        if not vmid or not action or not vmtype:
            return {"success": False, "message": "缺少参数"}
        if action not in ["start", "stop", "reboot"]:
            return {"success": False, "message": "不支持的操作"}
        if vmtype not in ["qemu", "lxc"]:
            return {"success": False, "message": "类型必须为qemu或lxc"}
        cmd = f"{'qm' if vmtype == 'qemu' else 'pct'} {action} {vmid}"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.plugin._ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self.plugin._ssh_key_file)
                ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, pkey=private_key)
            else:
                ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, password=self.plugin._ssh_password)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                return {"success": True, "message": f"{vmtype.upper()} {vmid} {action} 成功"}
            else:
                error_output = stderr.read().decode().strip()
                return {"success": False, "message": f"操作失败: {error_output or '未知错误'}"}
        except Exception as e:
            return {"success": False, "message": f"SSH连接或命令执行失败: {str(e)}"}
        finally:
            try:
                ssh.close()
            except:
                pass
    
    def _container_snapshot_api(self, data: dict = None):
        import time
        if not data:
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        vmid = str(data.get("vmid", "")).strip()
        vmtype = str(data.get("type", "")).strip().lower()  # qemu/lxc
        snapname = str(data.get("name", "")).strip()
        if not vmid or not vmtype:
            return {"success": False, "message": "缺少参数"}
        if vmtype not in ["qemu", "lxc"]:
            return {"success": False, "message": "类型必须为qemu或lxc"}
        if not snapname:
            snapname = f"auto-{int(time.time())}"
        cmd = f"{'qm' if vmtype == 'qemu' else 'pct'} snapshot {vmid} {snapname}"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.plugin._ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self.plugin._ssh_key_file)
                ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, pkey=private_key)
            else:
                ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, password=self.plugin._ssh_password)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                return {"success": True, "message": f"{vmtype.upper()} {vmid} 快照创建成功: {snapname}"}
            else:
                error_output = stderr.read().decode().strip()
                return {"success": False, "message": f"快照创建失败: {error_output or '未知错误'}"}
        except Exception as e:
            return {"success": False, "message": f"SSH连接或命令执行失败: {str(e)}"}
        finally:
            try:
                ssh.close()
            except:
                pass
    
    def _host_action_api(self, data: dict = None):
        if not data:
            if 'flask' in sys.modules:
                from flask import request
                data = request.json or {}
            else:
                data = {}
        action = data.get("action", "")
        if action not in ("reboot", "shutdown"):
            return {"success": False, "msg": "action参数必须为reboot或shutdown"}
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.plugin._ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self.plugin._ssh_key_file)
                ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, pkey=private_key, timeout=5)
            else:
                ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, password=self.plugin._ssh_password, timeout=5)
            if action == "reboot":
                ssh.exec_command("reboot")
            else:
                ssh.exec_command("poweroff")
            ssh.close()
            return {"success": True, "msg": f"主机{action}命令已发送"}
        except Exception as e:
            return {"success": False, "msg": str(e)}
    
    def _cleanup_tmp_api(self, data: dict = None):
        count, error = clean_pve_tmp_files(
            self.plugin._pve_host,
            self.plugin._ssh_port,
            self.plugin._ssh_username,
            self.plugin._ssh_password,
            self.plugin._ssh_key_file
        )
        if error:
            return {"success": False, "msg": f"清理失败: {error}"}
        return {"success": True, "msg": f"已清理 {count} 个临时文件"}
    
    def _cleanup_logs_api(self, data: dict = None):
        """API处理函数：清理PVE系统日志"""
        if not self.plugin._enable_log_cleanup:
            return {"success": False, "msg": "未启用日志清理功能"}
        try:
            res = clean_pve_logs(
                self.plugin._pve_host,
                self.plugin._ssh_port,
                self.plugin._ssh_username,
                self.plugin._ssh_password,
                self.plugin._ssh_key_file,
                journal_days=self.plugin._log_journal_days,
                log_dirs={
                    "/var/log/vzdump": self.plugin._log_vzdump_keep,
                    "/var/log/pve": self.plugin._log_pve_keep,
                    "/var/log/dpkg.log": self.plugin._log_dpkg_keep
                }
            )
            return {"success": True, "msg": "日志清理完成", "result": res}
        except Exception as e:
            return {"success": False, "msg": f"日志清理失败: {e}"}
    
    def _template_images_api(self):
        """列出所有CT模板和ISO镜像"""
        try:
            images = list_template_images(
                self.plugin._pve_host,
                self.plugin._ssh_port,
                self.plugin._ssh_username,
                self.plugin._ssh_password,
                self.plugin._ssh_key_file
            )
            return images  # 直接返回数组，兼容前端
        except Exception as e:
            return []
    
    def _stop_all_tasks_api(self, data: dict = None):
        """停止所有正在运行的任务"""
        stopped_tasks = []
        
        # 释放备份锁
        if self.plugin._lock and hasattr(self.plugin._lock, 'locked') and self.plugin._lock.locked():
            try:
                self.plugin._lock.release()
                stopped_tasks.append("备份任务")
                self.plugin._backup_activity = "空闲"
                logger.info(f"{self.plugin_name} 已释放备份任务锁")
            except RuntimeError:
                pass
        
        # 释放恢复锁
        if self.plugin._restore_lock and hasattr(self.plugin._restore_lock, 'locked') and self.plugin._restore_lock.locked():
            try:
                self.plugin._restore_lock.release()
                stopped_tasks.append("恢复任务")
                self.plugin._restore_activity = "空闲"
                logger.info(f"{self.plugin_name} 已释放恢复任务锁")
            except RuntimeError:
                pass
        
        # 释放全局任务锁
        if self.plugin._global_task_lock and hasattr(self.plugin._global_task_lock, 'locked') and self.plugin._global_task_lock.locked():
            try:
                self.plugin._global_task_lock.release()
                logger.info(f"{self.plugin_name} 已释放全局任务锁")
            except RuntimeError:
                pass
        
        # 重置运行状态
        self.plugin._running = False
        
        if stopped_tasks:
            logger.info(f"{self.plugin_name} 已停止任务: {', '.join(stopped_tasks)}")
            return {"success": True, "msg": f"已停止任务: {', '.join(stopped_tasks)}"}
        else:
            return {"success": True, "msg": "没有正在运行的任务"}

