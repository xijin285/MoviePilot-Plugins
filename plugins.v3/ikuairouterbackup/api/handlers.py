"""API处理模块"""
from typing import Any, Dict
from app.log import logger


class APIHandler:
    """API处理器类"""
    
    def __init__(self, plugin_instance):
        """初始化API处理器"""
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def backup(self, onlyonce: bool = False):
        """API备份接口"""
        try:
            self.plugin.run_backup_job()
            return {"success": True, "message": "备份任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动备份任务失败: {str(e)}"}
    
    def restore_backup(self, filename: str, source: str = "本地备份",
                       storage: str = "", remote_dir: str = ""):
        """API恢复接口（支持本地/WebDAV/网盘来源）"""
        try:
            self.plugin.run_restore_job(filename, source, storage or "", remote_dir or "")
            return {"success": True, "message": "恢复任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动恢复任务失败: {str(e)}"}
    
    def sync_ip_groups(self, province: str = "", city: str = "", isp: str = "", 
                      group_prefix: str = "", address_pool: bool = False) -> Dict[str, Any]:
        """API接口：同步IP分组"""
        try:
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {"success": False, "message": "配置不完整：URL、用户名或密码未设置。"}
            
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            # 执行同步
            success, message = ip_manager.sync_ip_groups_from_22tool(
                province=province,
                city=city,
                isp=isp,
                group_prefix=group_prefix,
                address_pool=address_pool
            )
            
            return {"success": success, "message": message}
            
        except Exception as e:
            error_msg = f"API同步IP分组异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_ip_blocks_info(self, province: str = "", city: str = "", isp: str = "") -> Dict[str, Any]:
        """API接口：获取IP段信息"""
        try:
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            # 获取IP段信息
            ip_blocks = ip_manager.get_ip_blocks_from_22tool(province, city, isp)
            
            return {
                "success": True,
                "data": ip_blocks,
                "count": len(ip_blocks)
            }
            
        except Exception as e:
            error_msg = f"获取IP段信息异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_available_options(self) -> Dict[str, Any]:
        """API接口：获取可用的省份、城市、运营商选项"""
        try:
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            provinces = ip_manager.get_available_provinces()
            isps = ip_manager.get_available_isps()
            
            return {
                "success": True,
                "provinces": provinces,
                "isps": isps
            }
            
        except Exception as e:
            error_msg = f"获取可用选项异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_cities_by_province(self, province: str) -> Dict[str, Any]:
        """API接口：根据省份获取城市列表"""
        try:
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            cities = ip_manager.get_available_cities(province)
            
            return {
                "success": True,
                "cities": cities
            }
            
        except Exception as e:
            error_msg = f"获取城市列表异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def test_ip_group(self) -> Dict[str, Any]:
        """测试IP分组创建API"""
        try:
            if not self.plugin._enable_ip_group:
                return {"code": 1, "msg": "IP分组功能未启用"}
            
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {"code": 1, "msg": "爱快路由器配置不完整"}
            
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(self.plugin._ikuai_url, self.plugin._ikuai_username, self.plugin._ikuai_password)
            
            # 测试创建最简单的IP分组
            success, error = ip_manager.test_create_simple_ip_group()
            
            if success:
                return {"code": 0, "msg": "测试IP分组创建成功"}
            else:
                return {"code": 1, "msg": f"测试IP分组创建失败: {error}"}
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 测试IP分组创建异常: {str(e)}")
            return {"code": 1, "msg": f"测试IP分组创建异常: {str(e)}"}

    # ---------- Vue 前端接口 ----------

    def get_config(self) -> Dict[str, Any]:
        """获取完整配置（Vue 配置页），附带 MP 已配置存储列表"""
        config = self.plugin.get_vue_config()
        try:
            from ..backup import cloud_storage
            config['mp_storages'] = cloud_storage.list_mp_storages()
        except Exception:
            config['mp_storages'] = []
        return config

    def save_config(self, data: dict) -> Dict[str, Any]:
        """保存完整配置（Vue 配置页）"""
        return self.plugin.save_vue_config(data or {})

    def get_status(self, force: bool = False) -> Dict[str, Any]:
        """实时监控状态（带缓存）"""
        try:
            return self.plugin._monitor_service.get_status(force=bool(force))
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def get_devices(self) -> Dict[str, Any]:
        """在线设备列表"""
        try:
            return self.plugin._monitor_service.get_devices()
        except Exception as e:
            return {'ok': False, 'error': str(e), 'devices': []}

    def get_logs(self, log_type: str = "system", page_size: int = 100) -> Dict[str, Any]:
        """系统日志"""
        try:
            return self.plugin._monitor_service.get_logs(log_type=log_type, page_size=int(page_size or 100))
        except Exception as e:
            return {'ok': False, 'error': str(e), 'logs': []}

    def get_trend(self) -> Dict[str, Any]:
        """24h 负载/流量趋势"""
        try:
            return {'ok': True, 'points': self.plugin._monitor_service.get_trend()}
        except Exception as e:
            return {'ok': False, 'error': str(e), 'points': []}

    def get_protocol_flow(self) -> Dict[str, Any]:
        """协议流量分布（爱快「协议监控」）"""
        try:
            return self.plugin._monitor_service.get_protocol_flow()
        except Exception as e:
            return {'ok': False, 'error': str(e), 'protocols': []}

    def get_monitor_view(self, view: str = "", datetype: str = "hour") -> Dict[str, Any]:
        """监控面板多视图（perf/network/flowsplit/devices6/camera）"""
        try:
            return self.plugin._monitor_service.get_monitor_view(view, datetype=datetype or "hour")
        except Exception as e:
            return {'ok': False, 'error': str(e), 'view': view}

    def get_alert_history(self, limit: int = 30) -> Dict[str, Any]:
        """负载告警记录（触发时间 / 峰值 / 恢复时间）"""
        try:
            return self.plugin._monitor_service.get_alert_history(int(limit or 30))
        except Exception as e:
            return {'ok': False, 'error': str(e), 'items': [], 'total': 0}

    def clear_alert_history(self) -> Dict[str, Any]:
        """清空负载告警记录"""
        try:
            return self.plugin._monitor_service.clear_alert_history()
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def get_dashboard_layout(self) -> Dict[str, Any]:
        """仪表盘卡片顺序 + 隐藏卡片 + 布局版本"""
        try:
            return {
                'ok': True,
                'layout': self.plugin.get_dashboard_layout(),
                'hidden': self.plugin.get_dashboard_hidden(),
                'version': self.plugin.get_dashboard_layout_version(),
            }
        except Exception as e:
            return {'ok': False, 'error': str(e), 'layout': [], 'hidden': [], 'version': 1}

    def save_dashboard_layout(self, layout=None, hidden=None, version=None) -> Dict[str, Any]:
        """保存仪表盘卡片顺序、隐藏状态与布局版本"""
        ok = self.plugin.save_dashboard_layout(layout)
        if hidden is not None:
            ok = self.plugin.save_dashboard_hidden(hidden) and ok
        if version is not None:
            ok = self.plugin.save_dashboard_layout_version(version) and ok
        return {'success': ok, 'msg': '布局已保存' if ok else '布局保存失败'}

    def download_backup(self, filename: str = "", source: str = "本地备份",
                        storage: str = "", remote_dir: str = "") -> Dict[str, Any]:
        """读取备份文件内容（base64），供浏览器直接下载"""
        import base64 as _b64
        if not filename:
            return {'ok': False, 'error': '缺少文件名'}
        try:
            content, err = self.plugin.load_backup_bytes(filename, source, storage, remote_dir)
        except Exception as e:
            return {'ok': False, 'error': str(e)}
        if content is None:
            return {'ok': False, 'error': err or '读取备份文件失败'}
        # 前端下载走 JSON，超大文件直接拒绝，避免响应体过重
        if len(content) > 20 * 1024 * 1024:
            return {'ok': False, 'error': '备份文件超过 20MB，暂不支持网页下载'}
        return {
            'ok': True,
            'filename': str(filename),
            'size': len(content),
            'content': _b64.b64encode(content).decode('ascii'),
        }

    def delete_backup(self, filename: str = "", source: str = "本地备份",
                      storage: str = "", remote_dir: str = "") -> Dict[str, Any]:
        """删除备份文件（本地 / WebDAV / 网盘）"""
        if not filename:
            return {'ok': False, 'error': '缺少文件名'}
        try:
            ok, err = self.plugin.delete_backup_file(filename, source, storage, remote_dir)
        except Exception as e:
            return {'ok': False, 'error': str(e)}
        return {'ok': ok, 'msg': '已删除' if ok else (err or '删除失败')}

    def get_available_backups(self) -> Dict[str, Any]:
        """可用于恢复的备份文件列表（含恢复功能开关状态）"""
        try:
            backups = self.plugin._get_available_backups() or []
            return {
                'ok': True,
                'enable_restore': bool(getattr(self.plugin, '_enable_restore', False)),
                'backups': backups,
            }
        except Exception as e:
            return {'ok': False, 'error': str(e), 'enable_restore': False, 'backups': []}

    def list_dir(self, path: str = "", storage: str = "") -> Dict[str, Any]:
        """浏览目录（备份路径选择器）：storage 为 local/空时浏览本地磁盘，否则浏览对应 MP 存储"""
        try:
            if storage and storage != "local":
                from ..backup import cloud_storage
                return cloud_storage.list_storage_dir(storage, path or "/")
            from pathlib import Path as _Path
            target = _Path(path) if path else _Path("/")
            if not target.exists():
                return {"ok": False, "error": f"路径不存在: {path}"}
            if not target.is_dir():
                target = target.parent
            dirs = []
            try:
                for child in target.iterdir():
                    try:
                        if child.is_dir():
                            dirs.append(child.name)
                    except (PermissionError, OSError):
                        continue
            except PermissionError:
                pass
            dirs.sort(key=str.lower)
            parent = str(target.parent) if target.parent != target else ""
            return {"ok": True, "path": str(target), "parent": parent, "dirs": dirs}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_histories(self) -> Dict[str, Any]:
        """备份与恢复历史"""
        try:
            return {
                'ok': True,
                'backup_history': self.plugin._load_backup_history() or [],
                'restore_history': self.plugin._load_restore_history() or [],
                'backup_activity': getattr(self.plugin, '_backup_activity', '空闲'),
                'restore_activity': getattr(self.plugin, '_restore_activity', '空闲'),
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def test_connection(self, data: dict = None) -> Dict[str, Any]:
        """测试爱快连接（支持使用配置页未保存的表单值）"""
        try:
            if data:
                # 表单临时值测试：不落盘，仅构建临时配置
                plugin = self.plugin
                saved = (plugin._original_ikuai_url, plugin._ikuai_username,
                         plugin._ikuai_password, plugin._ikuai_auth_mode, plugin._ikuai_api_token)
                try:
                    url = str(data.get('ikuai_url') or '').strip()
                    plugin._original_ikuai_url = url
                    plugin._ikuai_url = plugin._get_processed_ikuai_url(url) if url else plugin._ikuai_url
                    plugin._ikuai_username = str(data.get('ikuai_username') or 'admin')
                    pwd = str(data.get('ikuai_password') or '')
                    plugin._ikuai_password = pwd if pwd else saved[2]
                    plugin._ikuai_auth_mode = str(data.get('ikuai_auth_mode') or 'auto')
                    token = str(data.get('ikuai_api_token') or '')
                    plugin._ikuai_api_token = token if token else saved[4]
                except Exception:
                    pass
                try:
                    return self.plugin._monitor_service.test_connection()
                finally:
                    (plugin._original_ikuai_url, plugin._ikuai_username,
                     plugin._ikuai_password, plugin._ikuai_auth_mode, plugin._ikuai_api_token) = saved
            return self.plugin._monitor_service.test_connection()
        except Exception as e:
            return {'ok': False, 'error': str(e)}

