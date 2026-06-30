"""
夸克网盘 MoviePilot 插件
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from app import schemas
from app.core.event import Event, eventmanager
from app.helper.storage import StorageHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import FileItem, StorageOperSelectionEventData
from app.schemas.types import ChainEventType

from .quark_api import QuarkApi
from .quark_client import QuarkClient


class VueQuarkDisk(_PluginBase):
    """
    夸克网盘插件主类
    """

    # ==================== 插件元信息 ====================

    # 插件名称
    plugin_name = "Vue-夸克网盘存储"
    # 插件描述
    plugin_desc = "使存储支持夸克网盘"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/vuequarkdisk.png"
    # 插件版本
    plugin_version = "1.0.1"
    # 插件作者
    plugin_author = "xijin285,KoWming"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项 ID 前缀
    plugin_config_prefix = "vuequarkdisk_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1

    # ==================== 插件状态字段 ====================

    _enabled = False
    _disk_name = "夸克网盘"
    _cookie: str = ""
    _page_size: int = 50
    _sort_field: str = "file_name"
    _sort_order: str = "asc"
    _permanently_delete: bool = False

    # 扫码登录临时状态
    _qr_token: str = ""
    _qr_expires_at: float = 0

    # 客户端实例
    _client: Optional[QuarkClient] = None
    _quark_api: Optional[QuarkApi] = None

    # 脚本路径
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)

    # ==================== 初始化 ====================

    def __init__(self):
        """
        初始化插件。
        """
        super().__init__()

    # ==================== 辅助方法 ====================

    @staticmethod
    def _mask_cookie(cookie: str) -> str:
        """
        脱敏显示 Cookie 字符串。
        """
        if not cookie:
            return ""
        cookie = str(cookie)
        if len(cookie) <= 40:
            return cookie[:8] + "..." if len(cookie) > 8 else "***"
        return f"{cookie[:16]}...{cookie[-16:]}"

    def _build_config_payload(self) -> Dict[str, Any]:
        """
        构造配置持久化数据。
        """
        return {
            "enabled": self._enabled,
            "cookie": self._cookie,
            "page_size": self._page_size,
            "sort_field": self._sort_field,
            "sort_order": self._sort_order,
            "permanently_delete": self._permanently_delete,
        }

    def _clear_auth_state(self, reason: str = ""):
        """
        清理认证状态并持久化。
        """
        if reason:
            logger.warning(f"【夸克网盘】清理登录状态: {reason}")
        self._cookie = ""
        self._qr_token = ""
        self._qr_expires_at = 0
        if self._client:
            self._client._cookie = ""
        self.update_config(self._build_config_payload())

    # ==================== 插件生命周期 ====================

    def init_plugin(self, config: dict = None):
        """
        初始化插件，注册存储并创建客户端。
        """
        if not config:
            return

        # 注册存储
        storage_helper = StorageHelper()
        storages = storage_helper.get_storagies()
        if not any(
            s.type == self._disk_name and s.name == self._disk_name for s in storages
        ):
            storage_helper.add_storage(
                storage=self._disk_name,
                name=self._disk_name,
                conf={},
            )

        # 读取配置
        self._enabled = bool(config.get("enabled"))
        self._cookie = (config.get("cookie") or "").strip()
        self._page_size = int(config.get("page_size") or 50)
        self._sort_field = (config.get("sort_field") or "file_name").strip()
        self._sort_order = (config.get("sort_order") or "asc").strip()
        self._permanently_delete = bool(config.get("permanently_delete"))

        logger.info(
            "【夸克网盘】初始化插件: enabled=%s, has_cookie=%s, page_size=%d, sort=%s:%s",
            self._enabled,
            bool(self._cookie),
            self._page_size,
            self._sort_field,
            self._sort_order,
        )

        # Cookie 刷新回调
        def on_cookie_refresh(cookie: str):
            """
            Cookie 更新后自动持久化。
            """
            logger.info("【夸克网盘】收到 Cookie 更新回调，准备保存配置")
            self._cookie = cookie
            self.update_config(self._build_config_payload())
            logger.info("【夸克网盘】Cookie 已自动保存")

        try:
            self._client = QuarkClient(
                cookie=self._cookie,
                on_cookie_refresh=on_cookie_refresh,
            )
            self._quark_api = QuarkApi(
                client=self._client,
                disk_name=self._disk_name,
                page_size=self._page_size,
                sort_field=self._sort_field,
                sort_order=self._sort_order,
            )
        except Exception as err:
            logger.error(f"【夸克网盘】客户端创建失败: {err}")
            self._client = None
            self._quark_api = None

    def get_state(self) -> bool:
        """
        获取插件启用状态。
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        获取插件命令。
        """
        return []

    def get_render_mode(self) -> Tuple[str, Optional[str]]:
        """
        返回 Vue 渲染模式。
        """
        return "vue", "dist/assets"

    def stop_service(self):
        """
        退出插件时的清理。
        """
        pass

    # ==================== 表单与页面 ====================

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        Vue 模式下返回空表单与初始配置。
        """
        return None, {
            "enabled": False,
            "cookie": "",
            "page_size": 50,
            "sort_field": "file_name",
            "sort_order": "asc",
            "permanently_delete": False,
        }

    def get_page(self) -> List[dict]:
        """
        Vue 模式下返回空页面。
        """
        return []

    # ==================== API 端点 ====================

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件 API 端点。
        """
        return [
            {
                "path": "/config",
                "endpoint": self._get_config,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取配置",
            },
            {
                "path": "/config",
                "endpoint": self._save_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存配置",
            },
            {
                "path": "/login/qrcode",
                "endpoint": self.get_qrcode,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取扫码登录二维码",
            },
            {
                "path": "/login/poll",
                "endpoint": self.poll_login,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "轮询扫码登录状态",
            },
            {
                "path": "/login/logout",
                "endpoint": self.logout,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "退出登录",
            },
            {
                "path": "/share/create",
                "endpoint": self.api_create_share,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "创建分享链接",
            },
            {
                "path": "/share/list",
                "endpoint": self.api_get_my_shares,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取我的分享列表",
            },
            {
                "path": "/share/delete",
                "endpoint": self.api_delete_share,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "删除分享",
            },
            {
                "path": "/share/save",
                "endpoint": self.api_save_share,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "转存分享链接",
            },
            {
                "path": "/thumb",
                "endpoint": self.api_thumb,
                "auth": "bear",
                "allow_anonymous": True,
                "methods": ["GET"],
                "summary": "代理视频缩略图",
            },
        ]

    # ==================== API 实现 ====================

    def _get_config(self) -> Dict[str, Any]:
        """
        获取当前配置，包含登录状态和用户信息。
        """

        def _pick_first(data: Dict[str, Any], *keys: str) -> Any:
            for key in keys:
                value = data.get(key)
                if value not in (None, ""):
                    return value
            return None

        def _to_int(value: Any) -> int:
            if value in (None, ""):
                return 0
            try:
                return int(value)
            except (TypeError, ValueError):
                try:
                    return int(float(value))
                except (TypeError, ValueError):
                    return 0

        def _format_timestamp_ms(value: Any) -> str:
            """将毫秒时间戳格式化为可读的日期时间字符串。"""
            if value in (None, ""):
                return ""
            ts_ms = _to_int(value)
            if ts_ms <= 0:
                return ""
            try:
                dt = datetime.fromtimestamp(ts_ms / 1000)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except (OSError, ValueError, OverflowError):
                return str(value)

        def _is_auth_invalid(result: Dict[str, Any]) -> bool:
            if not isinstance(result, dict):
                return False
            status = result.get("status")
            code = result.get("code")
            message = str(result.get("message") or "")
            # HTTP 标准认证错误码
            # Quark 账号 API 认证错误码 (50001001=未登录, 50001002=登录过期, 32003=未登录)
            # Quark clouddrive API 认证错误码 (31001=未登录, 31002=登录过期)
            return (
                status in (401, 403)
                or code in (401, 403)
                or status in (50001001, 50001002, 32003, 31001, 31002)
                or code in (50001001, 50001002, 32003, 31001, 31002)
                or any(
                    kw in message.lower()
                    for kw in [
                        "unauthorized", "认证失败", "cookie", "过期",
                        "未登录", "login", "not logged", "登录已过期",
                    ]
                )
            )

        config: Dict[str, Any] = {
            "enabled": self._enabled,
            "cookie": self._cookie,
            "page_size": self._page_size,
            "sort_field": self._sort_field,
            "sort_order": self._sort_order,
            "permanently_delete": self._permanently_delete,
            "logged_in": False,
            "user_name": "",
            "user_id": "",
            "vip_level": "",
            "svip_exp_at": "",
            "total_space": 0,
            "used_space": 0,
            "free_space": 0,
            "qr_expires_in": max(int(self._qr_expires_at - time.time()), 0) if self._qr_expires_at else 0,
        }

        # 如果已登录，尝试获取用户信息和空间统计
        if self._cookie and self._client:
            try:
                # 获取用户信息
                user_info = self._client.get_user_info()
                if _is_auth_invalid(user_info):
                    logger.warning(
                        f"【夸克网盘】Cookie 可能已过期: {user_info.get('message', '')}"
                    )
                    self._clear_auth_state("Cookie 已过期，需要重新扫码登录")
                    config["cookie"] = ""
                    config["user_name"] = ""
                    config["user_id"] = ""
                    config["vip_level"] = ""
                    config["svip_exp_at"] = ""
                    config["total_space"] = 0
                    config["used_space"] = 0
                    config["free_space"] = 0
                    return config

                # Quark account/info 可能直接返回用户字段，也可能嵌套在 data.members 中
                raw_data = user_info.get("data")
                if not isinstance(raw_data, dict):
                    # 如果 data 不是 dict，尝试从顶层提取用户字段
                    raw_data = user_info if isinstance(user_info, dict) else {}
                user_data = raw_data
                # 检查嵌套的 members 结构 (Quark 账号 API 常见格式)
                if not user_data.get("nick_name") and not user_data.get("user_name") and not user_data.get("nickname"):
                    members = user_data.get("members")
                    if isinstance(members, dict) and members:
                        user_data = {**user_data, **members}
                user_name = _pick_first(
                    user_data,
                    "nick_name",
                    "name",
                    "user_name",
                    "username",
                    "nickname",
                    "display_name",
                )
                # account/info 响应中没有 user_id 字段，从 Cookie 的 __uid 中提取
                user_id = _pick_first(
                    user_data,
                    "user_id",
                    "userId",
                    "id",
                    "uid",
                )
                if not user_id and self._client:
                    user_id = self._client.get_uid_from_cookie()

                # 默认 vip_level 为空，后续根据 member 端点的 identity 数组确定
                vip_level = ""

                config["user_name"] = "" if user_name is None else str(user_name)
                config["user_id"] = "" if user_id is None else str(user_id)
                config["vip_level"] = vip_level
                config["logged_in"] = True

                # 获取空间统计
                capacity_info = self._client.get_capacity()
                cap_status = capacity_info.get("status")
                cap_message = capacity_info.get("message", "")
                if _is_auth_invalid(capacity_info):
                    logger.warning(f"【夸克网盘】获取空间信息失败: Cookie 可能已过期 ({cap_message})")
                    config["total_space"] = 0
                    config["used_space"] = 0
                    config["free_space"] = 0
                    return config

                # 检查 API 是否返回成功 (Quark clouddrive API status=200 或 2000000 表示成功)
                if cap_status not in (200, "200", 2000000, "2000000", 0, "0"):
                    logger.warning(
                        f"【夸克网盘】空间统计 API 返回非成功状态: status={cap_status}, message={cap_message}"
                    )
                    config["total_space"] = 0
                    config["used_space"] = 0
                    config["free_space"] = 0
                    return config

                capacity_data = (
                    capacity_info.get("data")
                    if isinstance(capacity_info.get("data"), dict)
                    else {}
                )
                # Quark API 可能将容量数据嵌套在 data.member_capacity_info 中
                if not capacity_data.get("total_capacity") and not capacity_data.get("use_capacity"):
                    nested = capacity_data.get("member_capacity_info")
                    if isinstance(nested, dict) and nested:
                        capacity_data = {**capacity_data, **nested}

                total_space = _to_int(
                    _pick_first(
                        capacity_data,
                        "total_capacity",
                        "totalCapacity",
                        "total_space",
                        "total",
                    )
                )
                used_space = _to_int(
                    _pick_first(
                        capacity_data,
                        "use_capacity",
                        "useCapacity",
                        "used_capacity",
                        "usedCapacity",
                        "used_space",
                        "used",
                    )
                )
                free_space = _to_int(
                    _pick_first(
                        capacity_data,
                        "free_capacity",
                        "freeCapacity",
                        "free_space",
                        "free",
                    )
                )
                if free_space == 0 and total_space > 0:
                    free_space = max(total_space - used_space, 0)

                logger.info(
                    f"【夸克网盘】空间统计: total={total_space}, used={used_space}, free={free_space}"
                )
                config["total_space"] = total_space
                config["used_space"] = used_space
                config["free_space"] = free_space

                # ========== 会员类型 & 会员到期 ==========
                # member 端点返回的字段: member_type, exp_at, exp_svip_exp_at,
                # super_vip_exp_at(开通时间), subscribe_pay_channel, member_info 等
                # 部分账号还会有 identity 数组（优先使用）
                vip_display = ""
                member_expire_at = ""

                # 1) 优先尝试 identity 数组（部分账号有）
                identity_list = capacity_data.get("identity")
                if isinstance(identity_list, list) and identity_list:
                    logger.info(f"【夸克网盘】identity 数组长度: {len(identity_list)}")
                    best_88vip = None
                    best_identity = None
                    for idx, identity in enumerate(identity_list):
                        if not isinstance(identity, dict):
                            continue
                        itype = identity.get("user_identity_type")
                        iextra = identity.get("extra") if isinstance(identity.get("extra"), dict) else {}
                        idistribute = str(iextra.get("distribute_id", "")).lower()
                        iexpire = identity.get("expire_time")
                        if "88_vip" in idistribute or itype == 4:
                            if best_88vip is None:
                                best_88vip = identity
                        if best_identity is None and itype is not None:
                            best_identity = identity
                        if not member_expire_at and iexpire not in (None, ""):
                            member_expire_at = _format_timestamp_ms(iexpire)

                    chosen = best_88vip or best_identity
                    if isinstance(chosen, dict):
                        utype = chosen.get("user_identity_type")
                        d_id = str((chosen.get("extra") or {}).get("distribute_id", "")).lower()
                        if "88_vip" in d_id or utype == 4:
                            vip_display = "88会员"
                        else:
                            identity_map = {
                                1: "普通用户", 2: "VIP", 3: "超级会员",
                                4: "88会员", 5: "体验超级会员", 6: "MINI VIP",
                            }
                            vip_display = identity_map.get(utype, f"身份{utype}")

                # 2) 没有 identity，用 member_type + subscribe_pay_channel
                if not vip_display:
                    member_type = str(_pick_first(capacity_data, "member_type", "memberType") or "").upper()
                    pay_channel = str(_pick_first(capacity_data, "subscribe_pay_channel") or "").lower()
                    logger.info(
                        f"【夸克网盘】member_type={member_type}, "
                        f"subscribe_pay_channel={pay_channel}"
                    )
                    # 88VIP 识别: pay_channel 包含 88 或 member_type == Z_VIP
                    if "88" in pay_channel or member_type == "Z_VIP":
                        vip_display = "88会员"
                    elif member_type:
                        member_type_map = {
                            "NORMAL": "普通用户",
                            "SUPER_VIP": "超级会员",
                            "EXP_SVIP": "体验超级会员",
                            "Z_VIP": "88会员",
                            "VIP": "会员",
                        }
                        vip_display = member_type_map.get(member_type, member_type)

                # 3) 会员到期时间：优先 exp_at，其次 exp_svip_exp_at
                if not member_expire_at:
                    exp_ms = _pick_first(capacity_data, "exp_at", "exp_svip_exp_at")
                    if exp_ms not in (None, ""):
                        member_expire_at = _format_timestamp_ms(exp_ms)

                config["vip_level"] = vip_display
                config["svip_exp_at"] = member_expire_at
                logger.info(f"【夸克网盘】会员类型: {vip_display}, 会员到期: {member_expire_at}")

            except Exception as err:
                logger.error(f"【夸克网盘】获取用户信息失败: {err}")
                config["logged_in"] = False
                config["user_name"] = ""
                config["user_id"] = ""
                config["vip_level"] = ""
                config["svip_exp_at"] = ""
                config["total_space"] = 0
                config["used_space"] = 0
                config["free_space"] = 0
        else:
            config["user_name"] = ""
            config["user_id"] = ""
            config["vip_level"] = ""
            config["svip_exp_at"] = ""
            config["total_space"] = 0
            config["used_space"] = 0
            config["free_space"] = 0

        return config

    def _save_config(self, config_payload: dict) -> Dict[str, Any]:
        """
        保存插件配置。
        """
        try:
            config_payload = config_payload or {}
            new_config = {
                "enabled": bool(config_payload.get("enabled", self._enabled)),
                "cookie": (config_payload.get("cookie") or self._cookie or "").strip(),
                "page_size": int(
                    config_payload.get("page_size") or self._page_size or 50
                ),
                "sort_field": (
                    config_payload.get("sort_field") or self._sort_field or "file_name"
                ).strip(),
                "sort_order": (
                    config_payload.get("sort_order") or self._sort_order or "asc"
                ).strip(),
                "permanently_delete": bool(
                    config_payload.get("permanently_delete", self._permanently_delete)
                ),
            }
            self.update_config(new_config)
            self.init_plugin(new_config)
            return {
                "success": True,
                "message": "配置保存成功",
                "data": self._get_config(),
            }
        except Exception as err:
            logger.error(f"【夸克网盘】保存配置失败: {err}")
            return {
                "success": False,
                "message": f"保存配置失败: {err}",
            }

    def get_qrcode(self) -> Dict[str, Any]:
        """
        获取扫码登录二维码。
        """
        try:
            temp_client = QuarkClient(cookie="")
            result = temp_client.get_qrcode()
            if not result:
                return {"success": False, "message": "获取二维码失败"}

            self._qr_token = result.get("qr_token", "")
            self._qr_expires_at = time.time() + result.get("expires_in", 300)

            return {
                "success": True,
                "qr_url": result.get("qr_url", ""),
                "qr_token": self._qr_token,
                "expires_in": result.get("expires_in", 300),
            }
        except Exception as err:
            logger.error(f"【夸克网盘】获取二维码失败: {err}")
            return {"success": False, "message": f"获取二维码失败: {err}"}

    def poll_login(self) -> Dict[str, Any]:
        """
        轮询扫码登录状态。
        """
        if not self._qr_token:
            return {"success": False, "message": "请先获取二维码"}
        if self._qr_expires_at and time.time() > self._qr_expires_at:
            self._qr_token = ""
            self._qr_expires_at = 0
            return {"success": False, "message": "二维码已过期，请重新获取"}

        try:
            temp_client = QuarkClient(cookie="")
            result = temp_client.poll_qrcode(self._qr_token)

            if not result:
                return {"success": False, "message": "等待扫码中...", "waiting": True}

            if result.get("waiting"):
                return {
                    "success": False,
                    "message": result.get("message") or "等待扫码中...",
                    "waiting": True,
                }

            if not result.get("success"):
                return {
                    "success": False,
                    "message": result.get("message") or "登录失败",
                }

            # 登录成功，保存 Cookie
            cookie = result.get("cookie", "")
            if not cookie:
                return {"success": False, "message": "获取 Cookie 失败"}

            self._cookie = cookie
            self._qr_token = ""
            self._qr_expires_at = 0

            # 持久化并重新初始化
            config_payload = self._build_config_payload()
            self.update_config(config_payload)
            self.init_plugin(config_payload)

            logger.info("【夸克网盘】扫码登录成功")
            return {
                "success": True,
                "message": "登录成功",
            }
        except Exception as err:
            logger.error(f"【夸克网盘】轮询登录失败: {err}")
            return {"success": False, "message": f"轮询失败: {err}"}

    def logout(self) -> Dict[str, Any]:
        """
        退出登录。
        """
        self._cookie = ""
        self._qr_token = ""
        self._qr_expires_at = 0
        self._client = None
        self._quark_api = None

        self.update_config(self._build_config_payload())
        return {"success": True, "message": "已退出登录"}

    # ==================== 分享 API 实现 ====================

    def api_create_share(self, request: Any) -> Dict[str, Any]:
        """
        创建分享链接。
        Body: {"file_ids": [...], "title": "", "expire_days": 0, "password": ""}
        """
        try:
            if not self._quark_api:
                return {"success": False, "message": "插件未初始化"}

            body = request.form or {}
            if hasattr(request, "json"):
                body = request.json or body

            file_ids = body.get("file_ids") or []
            if not file_ids:
                return {"success": False, "message": "请选择要分享的文件"}

            result = self._quark_api.create_share(
                file_ids=file_ids,
                title=body.get("title", ""),
                expire_days=int(body.get("expire_days", 0) or 0),
                password=body.get("password") or None,
            )
            if not result:
                return {"success": False, "message": "创建分享失败"}
            return {"success": True, "data": result}
        except Exception as err:
            logger.error(f"【夸克网盘】创建分享接口异常: {err}")
            return {"success": False, "message": f"创建分享失败: {err}"}

    def api_get_my_shares(self, request: Any) -> Dict[str, Any]:
        """
        获取我的分享列表。
        Query: ?page=1&size=50
        """
        try:
            if not self._quark_api:
                return {"success": False, "message": "插件未初始化"}

            page = int(getattr(request, "args", {}).get("page", 1) or 1)
            size = int(getattr(request, "args", {}).get("size", 50) or 50)
            result = self._quark_api.get_my_shares(page=page, size=size)
            return {"success": True, "data": result}
        except Exception as err:
            logger.error(f"【夸克网盘】获取分享列表接口异常: {err}")
            return {"success": False, "message": f"获取分享列表失败: {err}"}

    def api_delete_share(self, request: Any) -> Dict[str, Any]:
        """
        删除分享。
        Body: {"share_id": "..."}
        """
        try:
            if not self._quark_api:
                return {"success": False, "message": "插件未初始化"}

            body = request.form or {}
            if hasattr(request, "json"):
                body = request.json or body

            share_id = body.get("share_id")
            if not share_id:
                return {"success": False, "message": "缺少 share_id"}

            if self._quark_api.delete_share(share_id):
                return {"success": True, "message": "删除成功"}
            return {"success": False, "message": "删除失败"}
        except Exception as err:
            logger.error(f"【夸克网盘】删除分享接口异常: {err}")
            return {"success": False, "message": f"删除分享失败: {err}"}

    def api_save_share(self, request: Any) -> Dict[str, Any]:
        """
        转存分享链接。
        Body: {"share_url": "...", "target_path": "/", "save_all": true}
        """
        try:
            if not self._quark_api:
                return {"success": False, "message": "插件未初始化"}

            body = request.form or {}
            if hasattr(request, "json"):
                body = request.json or body

            share_url = body.get("share_url")
            if not share_url:
                return {"success": False, "message": "缺少分享链接"}

            target_path = body.get("target_path", "/")
            save_all = bool(body.get("save_all", True))

            target_item = schemas.FileItem(
                storage=self._disk_name,
                path=target_path,
                type="dir",
            )
            result = self._quark_api.save_share_url(
                share_url=share_url,
                target_folder=target_item,
                save_all=save_all,
            )
            if not result:
                return {"success": False, "message": "转存失败"}
            return {"success": True, "data": result}
        except Exception as err:
            logger.error(f"【夸克网盘】转存分享接口异常: {err}")
            return {"success": False, "message": f"转存失败: {err}"}

    def api_thumb(self, fid: str = ""):
        """
        代理获取视频/图片缩略图，绕过浏览器跨域 Cookie 限制。
        """
        from starlette.responses import Response
        if not fid or not self._quark_api:
            return Response(status_code=400)
        try:
            thumb_url = f"https://drive-pc.quark.cn/1/clouddrive/file/video/thumbnail?fid={fid}&pr=ucpro&fr=pc"
            resp = requests.get(
                thumb_url,
                headers=self._quark_api.client._build_headers(),
                timeout=30,
                allow_redirects=True,
            )
            if resp.status_code != 200:
                logger.warning(f"【夸克网盘】缩略图代理失败: HTTP {resp.status_code}, url={thumb_url}")
                return Response(status_code=resp.status_code)
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(content=resp.content, media_type=content_type)
        except Exception as err:
            logger.error(f"【夸克网盘】缩略图代理异常: {err}")
            return Response(status_code=500)

    # ==================== 模块导出 ====================

    def get_module(self) -> Dict[str, Any]:
        """
        获取插件模块声明，暴露存储操作方法。
        """
        return {
            "list_files": self.list_files,
            "any_files": self.any_files,
            "download_file": self.download_file,
            "upload_file": self.upload_file,
            "delete_file": self.delete_file,
            "rename_file": self.rename_file,
            "get_file_item": self.get_file_item,
            "get_parent_item": self.get_parent_item,
            "snapshot_storage": self.snapshot_storage,
            "storage_usage": self.storage_usage,
            "support_transtype": self.support_transtype,
            "create_folder": self.create_folder,
            "exists": self.exists,
            "get_item": self.get_item,
        }

    # ==================== 事件监听 ====================

    @eventmanager.register(ChainEventType.StorageOperSelection)
    def storage_oper_selection(self, event: Event):
        """
        监听存储选择事件，注入夸克网盘操作实例。
        """
        if not self._enabled:
            return
        event_data: StorageOperSelectionEventData = event.event_data
        if event_data.storage == self._disk_name:
            event_data.storage_oper = self._quark_api  # noqa: SLF001

    # ==================== 存储操作包装方法 ====================

    def list_files(
        self, fileitem: schemas.FileItem, recursion: bool = False
    ) -> Optional[List[schemas.FileItem]]:
        """
        查询目录下所有目录和文件。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return []

        result: List[schemas.FileItem] = []

        def _walk(_item: FileItem, _recursion: bool = False):
            items = self._quark_api.list(_item)
            if not items:
                return
            if _recursion:
                for sub_item in items:
                    if sub_item.type == "dir":
                        _walk(sub_item, _recursion)
                    else:
                        result.append(sub_item)
            else:
                result.extend(items)

        _walk(fileitem, recursion)
        return result

    def any_files(
        self, fileitem: schemas.FileItem, extensions: list = None
    ) -> Optional[bool]:
        """
        查询目录下是否存在任意目标文件。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return False

        def _any(_item: FileItem) -> bool:
            items = self._quark_api.list(_item)
            if not items:
                return False
            if not extensions:
                return True
            for sub_item in items:
                if (
                    sub_item.type == "file"
                    and sub_item.extension
                    and f".{sub_item.extension.lower()}" in extensions
                ):
                    return True
                if sub_item.type == "dir" and _any(sub_item):
                    return True
            return False

        return _any(fileitem)

    def create_folder(
        self, fileitem: schemas.FileItem, name: str
    ) -> Optional[schemas.FileItem]:
        """
        在指定目录下创建文件夹。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.create_folder(fileitem=fileitem, name=name)

    def download_file(
        self, fileitem: schemas.FileItem, path: Path = None
    ) -> Optional[Path]:
        """
        下载文件到本地路径。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.download(fileitem, path)

    def upload_file(
        self, fileitem: schemas.FileItem, path: Path, new_name: Optional[str] = None
    ) -> Optional[schemas.FileItem]:
        """
        上传本地文件到目标目录。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.upload(fileitem, path, new_name)

    def delete_file(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        删除文件或文件夹。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.delete(fileitem, permanently_delete=self._permanently_delete)

    def rename_file(self, fileitem: schemas.FileItem, name: str) -> Optional[bool]:
        """
        重命名文件或文件夹。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.rename(fileitem, name)

    def exists(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        判断文件项是否存在。
        """
        if fileitem.storage != self._disk_name:
            return None
        return True if self.get_item(fileitem) else False

    def get_item(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取文件项信息。
        """
        if fileitem.storage != self._disk_name:
            return None
        return self.get_file_item(storage=fileitem.storage, path=Path(fileitem.path))

    def get_file_item(self, storage: str, path: Path) -> Optional[schemas.FileItem]:
        """
        根据路径获取文件项。
        """
        if storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.get_item(path)

    def get_parent_item(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取文件项的父目录。
        """
        if fileitem.storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.get_parent(fileitem)

    def snapshot_storage(
        self,
        storage: str,
        path: Path,
        last_snapshot_time: float = None,
        max_depth: int = 5,
    ) -> Optional[Dict[str, Dict]]:
        """
        获取存储快照。
        """
        if storage != self._disk_name:
            return None
        if not self._quark_api:
            return {}

        files_info: Dict[str, Dict] = {}

        def _snapshot(_fileitem: schemas.FileItem, current_depth: int = 0):
            try:
                if _fileitem.type == "dir":
                    if current_depth >= max_depth:
                        return
                    if (
                        self.snapshot_check_folder_modtime  # noqa
                        and last_snapshot_time
                        and _fileitem.modify_time
                        and _fileitem.modify_time <= last_snapshot_time
                    ):
                        return
                    for sub_file in self._quark_api.list(_fileitem):
                        _snapshot(sub_file, current_depth + 1)
                else:
                    modify_time = getattr(_fileitem, "modify_time", 0) or 0
                    if not last_snapshot_time or modify_time > last_snapshot_time:
                        files_info[_fileitem.path] = {
                            "size": _fileitem.size or 0,
                            "modify_time": modify_time,
                            "type": _fileitem.type,
                        }
            except Exception:
                return

        root_item = self._quark_api.get_item(path)
        if not root_item:
            return {}
        _snapshot(root_item)
        return files_info

    def storage_usage(self, storage: str) -> Optional[schemas.StorageUsage]:
        """
        获取存储空间使用情况。
        """
        if storage != self._disk_name:
            return None
        if not self._quark_api:
            return None
        return self._quark_api.usage()

    def support_transtype(self, storage: str) -> Optional[dict]:
        """
        获取支持的传输类型。
        """
        if storage != self._disk_name:
            return None
        return {"move": "移动", "copy": "复制"}
