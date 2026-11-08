"""
配置加载模块
负责加载和更新插件配置
"""
import threading
from pathlib import Path
from typing import Optional
from app.log import logger


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化配置加载器
        :param plugin_instance: IkuaiRouterBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def load_config(self, saved_config: Optional[dict] = None):
        """从保存的配置中加载所有配置项"""
        if not saved_config:
            return
        
        # 基本配置
        self.plugin._enabled = bool(saved_config.get("enabled", False))
        self.plugin._cron = str(saved_config.get("cron", "0 3 * * *"))
        self.plugin._onlyonce = bool(saved_config.get("onlyonce", False))
        self.plugin._notify = bool(saved_config.get("notify", False))
        self.plugin._retry_count = int(saved_config.get("retry_count", 3))
        self.plugin._retry_interval = int(saved_config.get("retry_interval", 60))
        self.plugin._notification_style = int(saved_config.get("notification_style", 0))

        # 处理ikuai_url，保留原始值用于显示，处理后的值用于后端请求
        self.plugin._original_ikuai_url = str(saved_config.get("ikuai_url", "")).strip()
        self.plugin._ikuai_url = self.plugin._get_processed_ikuai_url(self.plugin._original_ikuai_url)

        self.plugin._ikuai_username = str(saved_config.get("ikuai_username", "admin"))
        self.plugin._ikuai_password = str(saved_config.get("ikuai_password", ""))
        self.plugin._ikuai_auth_mode = str(saved_config.get("ikuai_auth_mode", "auto"))
        self.plugin._ikuai_api_token = str(saved_config.get("ikuai_api_token", ""))

        # WebDAV配置
        self.plugin._enable_webdav = bool(saved_config.get("enable_webdav", False))
        self.plugin._webdav_url = str(saved_config.get("webdav_url", ""))
        self.plugin._webdav_username = str(saved_config.get("webdav_username", ""))
        self.plugin._webdav_password = str(saved_config.get("webdav_password", ""))
        self.plugin._webdav_path = str(saved_config.get("webdav_path", ""))
        self.plugin._webdav_keep_backup_num = int(saved_config.get("webdav_keep_backup_num", 7))
        self.plugin._clear_history = bool(saved_config.get("clear_history", False))
        self.plugin._delete_after_backup = bool(saved_config.get("delete_after_backup", False))

        # Vue 仪表盘/侧边栏开关
        monitor_enable = saved_config.get("monitor_enable")
        self.plugin._monitor_enable = True if monitor_enable is None else bool(monitor_enable)

        # 备份增强：配置变更检测 / 恢复点
        skip_unchanged = saved_config.get("skip_unchanged_backup")
        self.plugin._skip_unchanged_backup = True if skip_unchanged is None else bool(skip_unchanged)
        restore_point = saved_config.get("restore_point_enable")
        self.plugin._restore_point_enable = True if restore_point is None else bool(restore_point)

        # 统一存储备份目标（本地磁盘 + MP 网盘存储，支持多个目标同时备份）
        # 兼容迁移：storage_targets（新版多目标）> storage_type 单字段 > enable_local/enable_cloud 旧版
        if "storage_targets" in saved_config:
            self.plugin._storage_backup_enable = bool(saved_config.get("storage_backup_enable", False))
            self.plugin._storage_targets = self._normalize_targets(saved_config.get("storage_targets"))
        elif "storage_type" in saved_config:
            self.plugin._storage_backup_enable = bool(saved_config.get("storage_backup_enable", False))
            single_type = str(saved_config.get("storage_type", "local")).strip() or "local"
            single_path = str(saved_config.get("storage_path", "")).strip()
            single_keep = int(saved_config.get("storage_keep_backup_num", 7) or 7)
            self.plugin._storage_targets = [
                {"type": single_type, "path": single_path, "keep_backup_num": single_keep}
            ] if self.plugin._storage_backup_enable else []
        else:
            old_cloud_enable = bool(saved_config.get("enable_cloud_backup", False))
            old_cloud_storage = str(saved_config.get("cloud_storage", "")).strip()
            # 旧配置显式携带开关字段时尊重其取值；全新配置（无任何标记）默认启用本地备份
            has_legacy_flags = ("enable_local_backup" in saved_config) or ("enable_cloud_backup" in saved_config)
            old_targets = []
            if old_cloud_enable and old_cloud_storage:
                old_targets.append({
                    "type": old_cloud_storage,
                    "path": str(saved_config.get("cloud_path", "ikuai_backups")).strip(),
                    "keep_backup_num": int(saved_config.get("cloud_keep_backup_num", 7) or 7),
                })
            if bool(saved_config.get("enable_local_backup", not has_legacy_flags)):
                old_targets.append({
                    "type": "local",
                    "path": str(saved_config.get("backup_path", "")).strip(),
                    "keep_backup_num": int(saved_config.get("keep_backup_num", 7) or 7),
                })
            self.plugin._storage_backup_enable = bool(old_targets)
            self.plugin._storage_targets = old_targets

        # 规范化 + 兼容镜像（保留第一个目标到旧字段，供旧逻辑/回滚使用）
        self.plugin._storage_targets = self._normalize_targets(self.plugin._storage_targets)
        first = (self.plugin._storage_targets or [{}])[0]
        self.plugin._storage_type = str(first.get("type", "local") or "local")
        self.plugin._storage_path = str(first.get("path", "") or "")
        self.plugin._storage_keep_backup_num = int(first.get("keep_backup_num", 7) or 7)
        if not self.plugin._storage_backup_enable:
            self.plugin._storage_targets = []

        # 由多目标推导引擎属性（供备份执行器/恢复点使用）
        local_targets = [t for t in self.plugin._storage_targets if t.get("type", "local") == "local"]
        cloud_targets = [t for t in self.plugin._storage_targets if t.get("type", "local") != "local"]
        first_local = local_targets[0] if local_targets else None
        first_cloud = cloud_targets[0] if cloud_targets else None
        self.plugin._enable_cloud_backup = bool(first_cloud)
        self.plugin._cloud_storage = str(first_cloud.get("type", "")) if first_cloud else ""
        self.plugin._cloud_path = str(first_cloud.get("path", "") or "ikuai_backups") if first_cloud else "ikuai_backups"
        self.plugin._cloud_keep_backup_num = int(first_cloud.get("keep_backup_num", 7) or 7) if first_cloud else 7
        if first_local and first_local.get("path"):
            self.plugin._backup_path = str(first_local.get("path"))
            self.plugin._enable_local_backup = True
            self.plugin._keep_backup_num = int(first_local.get("keep_backup_num", 7) or 7)
        else:
            # 无本地目标：备份文件先落到插件数据目录（供网盘/WebDAV 上传）
            self.plugin._enable_local_backup = bool(first_local)
            self.plugin._backup_path = str(self.plugin.get_data_path())
            self.plugin._keep_backup_num = int(first_local.get("keep_backup_num", 7) or 7) if first_local else 7
            if self.plugin._storage_backup_enable and self.plugin._storage_targets:
                logger.info(f"{self.plugin_name} 未配置本地备份目录，备份文件使用默认: {self.plugin._backup_path}")

        # 负载告警
        self.plugin._load_warn_enable = bool(saved_config.get("load_warn_enable", False))
        self.plugin._load_cpu_threshold = float(saved_config.get("load_cpu_threshold", 90) or 90)
        self.plugin._load_mem_threshold = float(saved_config.get("load_mem_threshold", 90) or 90)
        self.plugin._load_warn_times = int(saved_config.get("load_warn_times", 3) or 3)
        
        # 恢复配置
        self.plugin._enable_restore = bool(saved_config.get("enable_restore", False))
        self.plugin._restore_force = bool(saved_config.get("restore_force", False))
        self.plugin._restore_file = str(saved_config.get("restore_file", ""))
        self.plugin._restore_now = bool(saved_config.get("restore_now", False))
        
        # IP分组配置
        self.plugin._enable_ip_group = bool(saved_config.get("enable_ip_group", False))
        self.plugin._ip_group_province = str(saved_config.get("ip_group_province", ""))
        self.plugin._ip_group_city = str(saved_config.get("ip_group_city", ""))
        self.plugin._ip_group_isp = str(saved_config.get("ip_group_isp", ""))
        self.plugin._ip_group_prefix = str(saved_config.get("ip_group_prefix", ""))
        self.plugin._ip_group_address_pool = bool(saved_config.get("ip_group_address_pool", False))
        self.plugin._ip_group_sync_now = bool(saved_config.get("ip_group_sync_now", False))
        
        # 创建备份目录
        self._ensure_backup_directory()

    @staticmethod
    def _normalize_targets(raw) -> list:
        """规范化存储备份目标列表：[{'type': str, 'path': str, 'keep_backup_num': int}]"""
        targets = []
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            return []
        for item in raw:
            if not isinstance(item, dict):
                continue
            t_type = str(item.get("type", "local") or "local").strip() or "local"
            t_path = str(item.get("path", "") or "").strip()
            try:
                t_keep = max(0, int(item.get("keep_backup_num", 7)))
            except (TypeError, ValueError):
                t_keep = 7
            # 网盘目标必须有远端目录
            if t_type != "local" and not t_path:
                continue
            # 本地目标路径为空时由执行器回退插件数据目录，保留该行
            targets.append({"type": t_type, "path": t_path, "keep_backup_num": t_keep})
        return targets

    def _ensure_backup_directory(self):
        """确保备份目录存在（所有本地目标目录 + 默认数据目录）"""
        paths = [self.plugin._backup_path]
        for t in getattr(self.plugin, '_storage_targets', []) or []:
            if t.get("type", "local") == "local" and t.get("path"):
                paths.append(t.get("path"))
        for p in paths:
            if not p:
                continue
            try:
                Path(p).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"{self.plugin_name} 创建备份目录 {p} 失败: {e}")

