import base64
import inspect
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

import requests
from fastapi.responses import FileResponse, Response

from app.chain.media import MediaChain
from app.core.event import eventmanager, Event
from app.core.metainfo import MetaInfo
from app.plugins import _PluginBase
import sys as _sys
import importlib as _importlib


def _reload_cached_submodule(name: str) -> None:
    """MP 的「重载插件」只会重新执行本 __init__.py，子模块命中 sys.modules
    缓存后不会重新加载，磁盘上的新代码不生效（排查删除标记修复时确认）。
    这里在重新导入前强制 reload 一次缓存中的子模块。"""
    full_name = f"{__name__}.{name}"
    mod = _sys.modules.get(full_name)
    if mod is None:
        return
    try:
        _importlib.reload(mod)
        from app.log import logger as _logger
        _logger.info(f"豆瓣档案子模块已强制重载：{name}.py")
    except Exception as exc:
        try:
            from app.log import logger as _logger
            _logger.warn(f"豆瓣档案子模块重载失败（继续用缓存版本）：{name}.py - {exc}")
        except Exception:
            pass


_reload_cached_submodule("doubanapi")
_reload_cached_submodule("douban_qr")
_reload_cached_submodule("douban_collect")

from .doubanapi import DoubanApi
from .douban_qr import DoubanQrLogin, _UA as _DOUBAN_UA
from app.schemas import WebhookEventInfo, MediaInfo
from app.schemas.types import EventType, MediaType, MediaSource
import re
from app.log import logger
from app.schemas import Notification, NotificationType, MessageChannel

lock = threading.Lock()

# 豆瓣个人主页里的大头像地址（icon/up 开头为大图）
_AVATAR_RE = re.compile(r'src="(https://img\d+\.doubanio\.com/icon/up[^"]+)"')
_AVATAR_HOST_RE = re.compile(r"^https?://img\d+\.doubanio\.com")
_AVATAR_HOSTS = ("img1", "img2", "img9", "img3")


class DoubanFolio(_PluginBase):
    # 插件名称
    plugin_name = "豆瓣档案"
    # 插件描述
    plugin_desc = "追剧观影自动同步进度到豆瓣，打造专属观影档案"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/douban.png"
    # 插件版本
    plugin_version = "3.1.1"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "doubanfolio_"
    # 加载顺序
    plugin_order = 15
    # 可使用的用户级别
    auth_level = 1

    _enable = False
    _private = True
    _first = True
    _user = ""
    _exclude = ""
    _cookie = ""

    _pc_month = None
    _pc_num = None
    _mobile_month = None
    _mobile_num = None

    _wait_process: Dict = None

    # 豆瓣「想看」→ MoviePilot 自动订阅
    _auto_subscribe = False
    _auto_subscribe_interval = 5
    _auto_subscribe_existing = False
    _auto_subscribe_lock = threading.Lock()

    # 最近一次生效的完整配置（扫码成功后回写用）
    _config: Dict = None
    # 豆瓣扫码登录会话
    _qr_login: Optional[DoubanQrLogin] = None

    def __init__(self, *args, **kwargs):
        # V3 基类 __init__ 不接受参数，多余的 args/kwargs 不能透传
        super().__init__()
        self._sync_lock = threading.Lock()
        self._qr_login = DoubanQrLogin()

    def init_plugin(self, config: dict = None):
        config = config or {}
        # 插件实例可能被重建（重新加载/保存配置），类属性回到 None，这里补建扫码会话
        if self._qr_login is None:
            self._qr_login = DoubanQrLogin()
        self._enable = config.get("enable", False)
        self._private = config.get("private", True)
        self._first = config.get("first", True)
        self._user = config.get("user", "")
        self._exclude = config.get("exclude", "")
        self._cookie = config.get("cookie", "")

        self._pc_month = int(config.get("pc_month")) if config.get("pc_month", None) else 3
        self._pc_num = int(config.get("pc_num", 50)) if config.get("pc_num", None) else 50
        self._mobile_month = int(config.get("mobile_month")) if config.get("mobile_month", None) else 2
        self._mobile_num = int(config.get("mobile_num", None)) if config.get("mobile_num", None) else 15
        self._notify = config.get("notify", False)
        self._auto_subscribe = bool(config.get("auto_subscribe", False))
        try:
            self._auto_subscribe_interval = max(1, min(int(config.get("auto_subscribe_interval") or 5), 59))
        except (TypeError, ValueError):
            self._auto_subscribe_interval = 5
        self._auto_subscribe_existing = bool(config.get("auto_subscribe_existing", False))
        self._config = dict(config)

        # 扫码成功后若用户直接点击保存（此时表单里的 Cookie 还是空的），
        # 用扫码结果兜底，避免刚拿到的 Cookie 被空值覆盖
        if not self._cookie and self._qr_login:
            qr_state = self._qr_login.status()
            if qr_state.get("status") == "login" and qr_state.get("cookie"):
                self._cookie = qr_state["cookie"]

        if self.get_data("processed"):
            from app.db.plugindata_oper import PluginDataOper
            PluginDataOper().del_data(plugin_id="DoubanFolio")
            logger.warn("检测到本插件旧版本数据，删除旧版本数据，避免报错...")

        if self._enable:
            # 输出核心模块加载时间，便于确认更新后跑的是哪份代码
            # （子模块可能被 Python 缓存，重载插件不一定会重新加载）
            try:
                import os
                base_dir = os.path.dirname(os.path.abspath(__file__))
                stamps = []
                for name in ("__init__.py", "doubanapi.py", "douban_collect.py"):
                    path = os.path.join(base_dir, name)
                    if os.path.exists(path):
                        stamps.append(f"{name}={time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(path)))}")
                logger.info(f"豆瓣观影档案插件已启用 v{self.plugin_version}（{' '.join(stamps)}）")
            except Exception:
                logger.info(f"豆瓣观影档案插件已启用 v{self.plugin_version}")

    @eventmanager.register(EventType.WebhookMessage)
    def sync_log(self, event: Event, played: bool = False):
        if not hasattr(self, '_sync_lock'):
            self._sync_lock = threading.Lock()
        if not self._sync_lock.acquire(blocking=False):
            import time
            now = time.time()
            if not hasattr(self, '_last_skip_log_time'):
                self._last_skip_log_time = 0
            if now - self._last_skip_log_time > 600:  # 10分钟
               # logger.info("同步流程已在进行中，跳过本次事件处理，防止重复通知。")
                self._last_skip_log_time = now
            return
        try:
            # 优化：减少cookie检测频率，只在必要时检测
            import time
            if not hasattr(self, '_last_cookie_check_time'):
                self._last_cookie_check_time = 0
            now = time.time()
            # 每小时只检测一次cookie有效性，避免频繁检测
            if now - self._last_cookie_check_time > 3600:  # 1小时
                if not hasattr(self, '_last_cookie_invalid_time'):
                    self._last_cookie_invalid_time = 0
                # 用真实存在的电影名检测cookie有效性，避免误判
                try:
                    douban_helper = DoubanApi(user_cookie=self._cookie)
                    subject_name, subject_id = douban_helper.get_subject_id(title="肖申克的救赎")
                except Exception:
                    subject_id = None  # 检测异常时静默处理
                
                if subject_id:
                    # 10分钟内只输出一次cookie有效日志
                    if not hasattr(self, '_last_cookie_valid_time'):
                        self._last_cookie_valid_time = 0
                    if now - self._last_cookie_valid_time > 600:
                        logger.info("cookie有效性检测通过")
                        self._last_cookie_valid_time = now
                else:
                    # 10分钟内只推送一次失效通知
                    if now - self._last_cookie_invalid_time > 600:
                        self._send_notification(False, "豆瓣cookie可能已失效，请及时更换！")
                        self._last_cookie_invalid_time = now
                self._last_cookie_check_time = now
            
            event_info: WebhookEventInfo = event.event_data
            play_start = {"playback.start", "media.play", "PlaybackStart"}
            path = event_info.item_path
            processed_items: Dict = self.get_data('data') or {}
            self._wait_process: Dict = self.get_data('wait') or {}

            if (event_info.event in play_start and event_info.user_name in self._user.split(',')) or played:
                if played:
                    logger.info(f"标记播放完成 {event_info.item_name}")

                if not self.exclude_keyword(path=path, keywords=self._exclude).get("ret", False):
                    logger.info(self.exclude_keyword(path=path, keywords=self._exclude).get("message", ""))
                    return

                if event_info.item_type == "TV":
                    self._process_tv_show(event_info, processed_items, played=played)
                elif event_info.item_type == "MOV":
                    self._process_movie(event_info, processed_items, played=played)
                else:
                    return
        finally:
            self._sync_lock.release()
            self._skip_log_printed = False

    @eventmanager.register(EventType.WebhookMessage)
    def sync_played(self, event: Event):
        event_info: WebhookEventInfo = event.event_data
        played = {'item.markplayed', 'media.scrobble'}
        is_played = event_info.event in played
        if event_info.channel == "jellyfin":
            is_played = event_info.event == 'UserDataSaved' and event_info.save_reason == 'TogglePlayed'

        if is_played and event_info.user_name in self._user.split(','):
            with lock:
                self.sync_log(event=event, played=True)

    def _process_tv_show(self, event_info: WebhookEventInfo, processed_items: Dict, played: bool = False):
        item_name = event_info.item_name or ""
        # 从「剧名 S01」样式标题中分离剧名；标题无 Sxx 标记（如整剧层级事件）时按整名处理
        index = item_name.find(" S")
        if index != -1 and item_name[index + 2:index + 3].isdigit():
            title = item_name[:index]
        else:
            title = item_name
            logger.info(f"事件标题未包含 Sxx 标记，按整剧事件处理：{item_name}")
        try:
            season_id = int(event_info.season_id)
            episode_id = int(event_info.episode_id)
        except (TypeError, ValueError):
            logger.info(f"事件缺少季/集信息（整剧层级操作），跳过同步：{item_name}")
            return
        tmdb_id = event_info.tmdb_id

        if not played:
            logger.info(f"开始播放 {title} 第{season_id}季 第{episode_id}集")

        if episode_id < 2 and self._first:
            logger.info(f"剧集第1集的活动不同步到豆瓣档案，跳过")
            return

        meta = MetaInfo(title)
        meta.begin_season = season_id
        meta.type = MediaType("电视剧")
        mediainfo = self._recognize_media(meta, tmdb_id)

        if not mediainfo:
            logger.warn(f'标题：{title}，tmdbid：{tmdb_id}，指定tmdbid未识别到媒体信息，尝试仅使用标题识别')
            mediainfo = self._recognize_media(meta, None)
            if not mediainfo:
                logger.error(f'仍然未识别到媒体信息，请检查TMDB网络连接...')
                self._record_history(title, "fail", "未识别到媒体信息，请检查 TMDB 连接", "电视剧")
                return

        episodes = mediainfo.seasons.get(season_id, [])

        title = self.format_title(title, season_id)
        status = "collect" if len(episodes) == episode_id else "do"

        if processed_items.get(title) and len(episodes) != episode_id:
            logger.info(f"{title} 已同步到豆瓣在看，不处理")
            # 已处理过的条目直接跳过，无需发送通知
            if self._notify:
                logger.info(f"{title} 跳过同步，不发送通知")
            return

        sync_ret = self._sync_to_douban(title, status, event_info.item_type, processed_items, mediainfo.poster_path)
        # 尝试同步之前同步失败的
        if sync_ret:
            logger.info(f"尝试同步之前同步失败的条目")
            self._wait_process: Dict = self.get_data('wait') or {}
            for key, value in self._wait_process.items():
                logger.info(f"尝试同步: {key}")
                self._sync_to_douban(key, value["status"], value["type"], processed_items, value["poster_path"])

    def _process_movie(self, event_info: WebhookEventInfo, processed_items: Dict, played: bool = False):
        title = event_info.item_name

        if not played:
            logger.info(f"开始播放 {title}")

        meta = MetaInfo(title)
        meta.type = MediaType("电影")
        mediainfo = self._recognize_media(meta, event_info.tmdb_id)

        if not mediainfo:
            logger.warn(f'标题：{title}，tmdbid：{event_info.tmdb_id}，指定tmdbid未识别到媒体信息，尝试仅使用标题识别')
            mediainfo = self._recognize_media(meta, None)
            if not mediainfo:
                logger.error(f'仍然未识别到媒体信息，请检查TMDB网络连接...')
                self._record_history(title, "fail", "未识别到媒体信息，请检查 TMDB 连接", "电影")
                return

        if processed_items.get(title):
            logger.info(f"{title} 已同步到豆瓣在看，不处理")
            return

        self._sync_to_douban(title, "collect", event_info.item_type, processed_items, mediainfo.poster_path)

    def _recognize_media(self, meta: MetaInfo, tmdb_id: Optional[int]) -> Optional[MediaInfo]:
        # MoviePilot V3：tmdbid 参数已移除，改为 media_source + media_id 成对传入
        if tmdb_id:
            return MediaChain().recognize_media(meta=meta, mtype=meta.type,
                                                media_source=MediaSource.TMDB,
                                                media_id=str(tmdb_id), cache=True)
        return MediaChain().recognize_media(meta=meta, mtype=meta.type, cache=True)

    def _send_notification(self, success: bool, message: str):
        if not self._notify:
            return
        title = f"豆瓣观影档案 {'成功' if success else '失败'}"
        text_content = message.strip()
        text_content += f"\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            self.post_message(mtype=NotificationType.MediaServer, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            error_msg = f'{self.plugin_name} 发送通知失败: {e}'
            if 'The resource you requested could not be found.' in error_msg:
                logger.error('请求的资源未找到（可能是条目不存在或ID错误）')
            else:
                logger.error(error_msg)

    # ------------------------------------------------------------ 同步日志与头像
    def _record_history(self, title: str, result: str, message: str = "", media_type: str = "", sid: str = ""):
        """把一次同步结果写入历史（最新在前，最多保留 200 条）。sid 用于前端展示海报。"""
        try:
            logs = self.get_data("sync_logs")
            if not isinstance(logs, list):
                logs = []
            logs.insert(0, {
                "time": datetime.now().strftime("%m-%d %H:%M"),
                "title": title,
                "result": result,      # success / fail / not_found
                "message": message,
                "type": media_type,    # 电影 / 电视剧
                "sid": str(sid or ""),
            })
            self.save_data("sync_logs", logs[:200])
        except Exception as exc:
            logger.warn(f"记录同步日志失败: {exc}")

    def _fetch_avatar(self) -> str:
        """
        取豆瓣账号头像并转成 data URI。

        图床节点可用性因网络环境而异，沿用二维码的多节点兜底策略；
        结果按 uid 缓存，避免每次打开状态页都回源请求。
        """
        uid = self._uid_from_cookie()
        if not uid:
            return ""
        cache = self.get_data("avatar_cache")
        if isinstance(cache, dict) and cache.get("uid") == uid and cache.get("data"):
            return cache["data"]

        headers = {
            "User-Agent": _DOUBAN_UA,
            "Cookie": self._cookie or "",
            "Referer": "https://www.douban.com/",
        }
        avatar_url = ""
        try:
            resp = requests.get(f"https://www.douban.com/people/{uid}/",
                                headers=headers, timeout=8)
            match = _AVATAR_RE.search(resp.text or "")
            if match:
                avatar_url = match.group(1)
        except Exception:
            pass
        if not avatar_url:
            return ""

        path = _AVATAR_HOST_RE.sub("", avatar_url)
        for host in _AVATAR_HOSTS:
            try:
                resp = requests.get(f"https://{host}.doubanio.com{path}",
                                    headers=headers, timeout=8)
                data = resp.content if resp is not None else b""
                if resp is not None and resp.status_code == 200 and data.startswith(b"\xff\xd8\xff"):
                    uri = "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
                    self.save_data("avatar_cache", {"uid": uid, "data": uri})
                    return uri
            except Exception:
                continue
        return ""

    def _sync_to_douban(self, title: str, status: str, mediaType: str, processed_items: Dict,
                        poster_path: str) -> bool:
        logger.info(f"开始尝试获取 {title} 豆瓣id")
        douban_helper = DoubanApi(user_cookie=self._cookie)
        subject_name, subject_id = douban_helper.get_subject_id(title=title)

        if subject_id:
            logger.info(f"查询：{title} => 匹配豆瓣：{subject_name} https://movie.douban.com/subject/{subject_id}/")
            ret = douban_helper.set_watching_status(subject_id=subject_id, status=status, private=self._private)
            if ret:
                processed_items[title] = {
                    "subject_id": subject_id,
                    "subject_name": subject_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "poster_path": poster_path,
                    "type": "电视剧" if mediaType == "TV" else "电影"
                }

                if title in self._wait_process:
                    del self._wait_process[title]

                self.save_data('data', processed_items)
                self.save_data('wait', self._wait_process)
                # 本地刚改了豆瓣标记，立刻作废该状态的长缓存，避免列表沿用旧数据
                self._invalidate_collection(status)
                logger.info(f"{title} 同步到档案成功")
                self._record_history(title, "success",
                                     f"已标记为「{'看过' if status == 'collect' else '在看'}」",
                                     "电视剧" if mediaType == "TV" else "电影",
                                     sid=subject_id)
                # 通知：同步成功
                self._send_notification(True, f"《{title}》已成功同步到豆瓣档案。")
                return True
            else:
                error_msg = f'{title} 同步到档案失败'
                if 'The resource you requested could not be found.' in error_msg:
                    logger.error('请求的资源未找到（可能是条目不存在或ID错误）')
                else:
                    logger.error(error_msg)
                if title not in self._wait_process:
                    self._wait_process[title] = {
                        "subject_id": subject_id,
                        "subject_name": subject_name,
                        "status": status,
                        "poster_path": poster_path,
                        "type": mediaType
                    }
                    self.save_data('wait', self._wait_process)
                    error_msg = f'{title} 添加到待同步列表'
                    if 'The resource you requested could not be found.' in error_msg:
                        logger.error('请求的资源未找到（可能是条目不存在或ID错误）')
                    else:
                        logger.error(error_msg)
                # 通知：同步失败
                self._record_history(title, "fail", "同步失败，已加入待同步列表",
                                     "电视剧" if mediaType == "TV" else "电影",
                                     sid=subject_id)
                self._send_notification(False, f"《{title}》同步到豆瓣档案失败，请检查cookie或网络。")
        else:
            logger.warn(f"获取 {title} subject_id 失败，本条目不存在于豆瓣")
            self._record_history(title, "not_found", "豆瓣未收录该条目",
                                 "电视剧" if mediaType == "TV" else "电影")
            # 豆瓣上没有找到剧集，这是正常情况，不推送失败通知
            # 只有在cookie检测失败时才会推送通知
        return False


    # ------------------------------------------------------------ Vue 渲染与配置 API
    def _default_config(self) -> Dict[str, Any]:
        """当前配置快照，Vue 配置页据此回显。"""
        return {
            "enabled": bool(self._enable),
            "private": bool(self._private),
            "first": bool(self._first),
            "user": self._user or "",
            "exclude": self._exclude or "",
            "cookie": self._cookie or "",
            "pc_month": int(self._pc_month or 3),
            "pc_num": int(self._pc_num or 50),
            "mobile_month": int(self._mobile_month or 2),
            "mobile_num": int(self._mobile_num or 15),
            "notify": bool(self._notify),
            "auto_subscribe": bool(self._auto_subscribe),
            "auto_subscribe_interval": int(self._auto_subscribe_interval or 5),
            "auto_subscribe_existing": bool(self._auto_subscribe_existing),
        }

    def _uid_from_cookie(self) -> str:
        """从 dbcl2 中解析豆瓣 UID。"""
        match = re.search(r'dbcl2"?\s*[=:]\s*"?(\d+):', self._cookie or "")
        return match.group(1) if match else ""

    def _nickname(self) -> str:
        """
        昵称：扫码会话 → 持久化缓存 → 用 Cookie 回源豆瓣个人主页自动获取。

        重启后扫码会话丢失也能自动补全；回源失败记 30 分钟负缓存，
        避免每次打开页面都请求豆瓣。
        """
        if self._qr_login is not None:
            nickname = self._qr_login.status().get("nickname") or ""
            if nickname:
                self._save_nickname(nickname)
                return nickname
        uid = self._uid_from_cookie()
        cache = self.get_data("douban_nickname")
        if isinstance(cache, dict) and cache.get("uid") == uid:
            if cache.get("name"):
                return cache["name"]
            if time.time() - cache.get("ts", 0) < 30 * 60:
                return ""  # 刚自动获取失败，暂不重试
        nickname = self._fetch_nickname_remote()
        self.save_data("douban_nickname", {"uid": uid, "name": nickname, "ts": time.time()})
        return nickname

    def _save_nickname(self, nickname: str) -> None:
        """持久化豆瓣昵称（按 uid 绑定，换号自动失效）。"""
        if not nickname:
            return
        self.save_data("douban_nickname", {"uid": self._uid_from_cookie(), "name": nickname, "ts": time.time()})

    def _fetch_nickname_remote(self) -> str:
        """用 Cookie 访问豆瓣个人主页，从标题提取昵称。失败返回空串。"""
        uid = self._uid_from_cookie()
        if not uid or not self._cookie:
            return ""
        try:
            resp = requests.get(
                f"https://www.douban.com/people/{uid}/",
                headers={
                    "User-Agent": _DOUBAN_UA,
                    "Cookie": self._cookie,
                    "Referer": "https://www.douban.com/",
                },
                timeout=8,
            )
            if resp.status_code == 200:
                match = re.search(r"<title>\s*(.+?)\s*</title>", resp.text or "", re.S)
                if match:
                    nick = re.split(r"\s*[|｜]\s*", match.group(1))[0].strip()
                    if nick and "登录" not in nick and nick != "豆瓣":
                        return nick
        except Exception as exc:
            logger.warn(f"自动获取豆瓣昵称失败: {exc}")
        return ""

    def _persist_cookie(self, cookie: str) -> bool:
        """把 Cookie 写入插件配置并立即生效。"""
        cookie = (cookie or "").strip()
        if not cookie:
            return False
        self._cookie = cookie
        config = self._default_config()
        config["cookie"] = cookie
        try:
            self.update_config(config)
            self._config = config
            logger.info("豆瓣 Cookie 已保存")
            return True
        except Exception as exc:
            logger.error(f"保存豆瓣 Cookie 失败: {exc}")
            return False

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """配置页与状态页改由 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """Vue 模式下页面由前端渲染，这里只提供配置默认值。"""
        return None, self._default_config()

    def get_page(self) -> List[dict]:
        """Vue 模式下页面由前端渲染。"""
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        """豆瓣「想看」自动订阅周期服务（分钟级 cron）。"""
        if not self._enable or not self._auto_subscribe:
            return []
        try:
            from apscheduler.triggers.cron import CronTrigger

            minutes = max(1, min(int(self._auto_subscribe_interval or 5), 59))
            trigger = CronTrigger.from_crontab(f"*/{minutes} * * * *")
        except Exception as exc:
            logger.warn(f"豆瓣档案自动订阅服务注册失败: {exc}")
            return []
        return [
            {
                "id": "DoubanFolio.AutoSubscribe",
                "name": "豆瓣想看自动订阅",
                "trigger": trigger,
                "func": self._auto_subscribe_check,
                "kwargs": {},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/config",
                "endpoint": self.api_get_config,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取插件配置",
            },
            {
                "path": "/config",
                "endpoint": self.api_save_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存插件配置",
            },
            {
                "path": "/qr/start",
                "endpoint": self.api_qr_start,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取豆瓣登录二维码",
            },
            {
                "path": "/qr/poll",
                "endpoint": self.api_qr_poll,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "轮询扫码登录状态",
            },
            {
                "path": "/status",
                "endpoint": self._safe(self.api_status),
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取插件运行状态",
            },
            {
                "path": "/logs",
                "endpoint": self._safe(self.api_get_logs),
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取最近同步记录",
            },
            {
                "path": "/collection",
                "endpoint": self._safe(self.api_collection),
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取豆瓣书影音收藏列表",
            },
            {
                "path": "/collection/summary",
                "endpoint": self._safe(self.api_collection_summary),
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取豆瓣收藏统计",
            },
            {
                "path": "/cover",
                "endpoint": self.api_cover,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "豆瓣海报图片代理",
                "openapi_extra": {"x-moviepilot-raw-response": True},
            },
            {
                "path": "/mp_status",
                "endpoint": self._safe(self.api_mp_status),
                "auth": "bear",
                "methods": ["POST"],
                "summary": "批量查询入库与订阅状态",
            },
            {
                "path": "/subscribe",
                "endpoint": self._safe(self.api_subscribe),
                "auth": "bear",
                "methods": ["POST"],
                "summary": "加入 MoviePilot 订阅",
            },
            {
                "path": "/unmark",
                "endpoint": self._safe(self.api_unmark),
                "auth": "bear",
                "methods": ["POST"],
                "summary": "删除豆瓣标记（取消在看/想看/看过）",
            },
            {
                "path": "/auto_subscribe/check",
                "endpoint": self._safe(self.api_auto_subscribe_check),
                "auth": "bear",
                "methods": ["POST"],
                "summary": "立即检查豆瓣想看并自动订阅",
            },
        ]

    # ------------------------------------------------------------ API 实现

    @staticmethod
    def _safe(endpoint):
        """包一层异常兜底：插件 API 内部错误时返回结构化错误而不是 500，
        避免前端出现「未命名错误」且日志里只剩难以定位的单行异常。"""

        def wrapper(*args, **kwargs):
            try:
                return endpoint(*args, **kwargs)
            except Exception as exc:
                logger.error(f"豆瓣档案 API {getattr(endpoint, '__name__', '')} 异常: {exc}", exc_info=True)
                return {"success": False, "message": f"插件内部错误：{exc}"}

        wrapper.__signature__ = inspect.signature(endpoint)
        wrapper.__name__ = getattr(endpoint, "__name__", "endpoint")
        return wrapper

    @staticmethod
    def _body_dict(data: Any) -> Dict[str, Any]:
        """POST body 兼容：正常应为 dict，个别调用链会传 JSON 字符串。"""
        if isinstance(data, dict):
            return data
        if isinstance(data, str) and data.strip():
            try:
                parsed = json.loads(data)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    @staticmethod
    def _qr_view(info: Dict[str, Any]) -> Dict[str, Any]:
        """只把前端需要的字段透出去，不外泄二维码 code。"""
        login = info.get("status") == "login"
        return {
            "status": info.get("status", "idle"),
            "img": info.get("img", "") or "",
            "error": info.get("error", "") or "",
            "cookie": info.get("cookie", "") if login else "",
            "nickname": info.get("nickname", "") or "",
            "expire_in": int(info.get("expire_in") or 0),
        }

    def api_get_config(self) -> Dict[str, Any]:
        config = self._default_config()
        config["logged_in"] = bool(self._cookie)
        config["nickname"] = self._nickname()
        config["uid"] = self._uid_from_cookie()
        config["avatar"] = self._fetch_avatar()
        return config

    def api_save_config(self, config_payload: dict = None) -> Dict[str, Any]:
        payload = config_payload or {}
        try:
            new_config = self._default_config()
            new_config.update(
                {
                    "enable": bool(payload.get("enabled", self._enable)),
                    "private": bool(payload.get("private", self._private)),
                    "first": bool(payload.get("first", self._first)),
                    "user": payload.get("user", self._user) or "",
                    "exclude": payload.get("exclude", self._exclude) or "",
                    "cookie": (payload.get("cookie") or self._cookie or "").strip(),
                    "pc_month": int(payload.get("pc_month") or self._pc_month or 3),
                    "pc_num": int(payload.get("pc_num") or self._pc_num or 50),
                    "mobile_month": int(payload.get("mobile_month") or self._mobile_month or 2),
                    "mobile_num": int(payload.get("mobile_num") or self._mobile_num or 15),
                    "notify": bool(payload.get("notify", self._notify)),
                    "auto_subscribe": bool(payload.get("auto_subscribe", self._auto_subscribe)),
                    "auto_subscribe_interval": max(1, min(int(payload.get("auto_subscribe_interval") or 5), 59)),
                    "auto_subscribe_existing": bool(payload.get("auto_subscribe_existing", self._auto_subscribe_existing)),
                }
            )
            self.update_config(new_config)
            self.init_plugin(new_config)
            return {"success": True, "message": "配置保存成功", "data": self.api_get_config()}
        except Exception as exc:
            logger.error(f"保存豆瓣档案配置失败: {exc}")
            return {"success": False, "message": f"保存失败: {exc}"}

    def api_qr_start(self) -> Dict[str, Any]:
        if self._qr_login is None:
            self._qr_login = DoubanQrLogin()
        try:
            info = self._qr_login.start()
        except Exception as exc:
            logger.error(f"获取豆瓣登录二维码失败: {exc}")
            return {"status": "error", "img": "", "error": str(exc), "cookie": "", "nickname": "", "expire_in": 0}
        if info.get("status") == "login" and info.get("cookie"):
            self._persist_cookie(info["cookie"])
        return self._qr_view(info)

    def api_qr_poll(self) -> Dict[str, Any]:
        if self._qr_login is None:
            return {"status": "idle", "img": "", "error": "扫码会话不存在，请刷新二维码", "cookie": "", "nickname": "", "expire_in": 0}
        try:
            info = self._qr_login.check()
        except Exception as exc:
            logger.error(f"轮询豆瓣扫码状态失败: {exc}")
            return {"status": "error", "img": self._qr_login.status().get("img", ""), "error": str(exc), "cookie": "", "nickname": "", "expire_in": 0}
        if info.get("status") == "login" and info.get("cookie"):
            self._persist_cookie(info["cookie"])
            self._save_nickname(info.get("nickname") or "")
        return self._qr_view(info)

    def api_status(self) -> Dict[str, Any]:
        processed = self.get_data("data") or {}
        wait = self.get_data("wait") or {}
        return {
            "logged_in": bool(self._cookie),
            "nickname": self._nickname(),
            "uid": self._uid_from_cookie(),
            "avatar": self._fetch_avatar(),
            "enabled": bool(self._enable),
            "notify": bool(self._notify),
            "processed_count": len(processed) if isinstance(processed, dict) else 0,
            "wait_count": len(wait) if isinstance(wait, dict) else 0,
        }

    def api_get_logs(self) -> Dict[str, Any]:
        logs = self.get_data("sync_logs")
        if not isinstance(logs, list):
            logs = []
        # 用条目元数据缓存（含海报）给同步记录补全海报：sid 精确匹配，标题兜底
        meta_store = self.get_data("subject_meta")
        by_sid, by_title = {}, {}
        if isinstance(meta_store, dict):
            for key, entry in meta_store.items():
                data = entry.get("data") if isinstance(entry, dict) else None
                if not isinstance(data, dict) or not data.get("poster"):
                    continue
                sid = str(key).rsplit(":", 1)[-1]
                title = str(data.get("title") or "").strip()
                if sid:
                    by_sid[sid] = data["poster"]
                if title:
                    by_title[title] = data["poster"]
        for rec in logs:
            if not isinstance(rec, dict) or rec.get("poster"):
                continue
            poster = by_sid.get(str(rec.get("sid") or ""))
            if not poster:
                title = str(rec.get("title") or "").strip()
                poster = by_title.get(title) or next(
                    (p for t, p in by_title.items() if t and (t in title or title in t)), ""
                )
            rec["poster"] = poster or ""
        return {"success": True, "data": logs}

    # ------------------------------------------------------------ 豆瓣收藏与仪表盘
    def _collection_stores(self) -> Tuple[Dict, Dict]:
        """条目详情缓存与列表页缓存（持久化在插件数据里）。"""
        subject_store = self.get_data("subject_meta")
        if not isinstance(subject_store, dict):
            subject_store = {}
        page_store = self.get_data("collection_cache")
        if not isinstance(page_store, dict):
            page_store = {}
        return subject_store, page_store

    def _invalidate_collection(self, status: str, category: str = "movie") -> None:
        """作废某状态全部页缓存 + 总数校验缓存（本地标记发生变化时调用）。"""
        store = self.get_data("collection_cache")
        if isinstance(store, dict):
            prefix = f"{category}:{status}:"
            for key in [k for k in store if k.startswith(prefix)]:
                store.pop(key, None)
            self.save_data("collection_cache", store)
        state = self.get_data("summary_check")
        if isinstance(state, dict) and status in state:
            state.pop(status, None)
            self.save_data("summary_check", state)

    def _collection_page(
        self, status: str, start: int, category: str, force: bool = False
    ) -> Tuple[List[Dict[str, Any]], int]:
        """取一页收藏并补全条目详情，带缓存。force=True 时绕过页缓存。"""
        from .douban_collect import PageCache, SubjectMetaCache, enrich, fetch_page

        subject_store, page_store = self._collection_stores()
        page_cache = PageCache(page_store)
        cached = None if force else page_cache.get(category, status, start)
        if cached is not None:
            items, total = cached[1], cached[0]
            # 自愈：历史缓存里可能存在 subtype 为空的条目（当时条目详情接口
            # 批量失败被写入缓存），命中缓存后对这部分条目重新补全一次；
            # fetch_subject 自带熔断，接口不可用时不会产生额外请求压力
            missing = [it for it in items if isinstance(it, dict) and not it.get("subtype")]
            if category == "movie" and missing:
                enrich(missing, category, SubjectMetaCache(subject_store), self._cookie or "")
                if any(it.get("subtype") for it in missing):
                    page_cache.put(category, status, start, total, items)
                    self.save_data("subject_meta", subject_store)
                    self.save_data("collection_cache", page_store)
            return items, total

        items, total = fetch_page(self._cookie, self._uid_from_cookie(), category, status, start)
        if total < 0:
            return [], -1
        items = enrich(items, category, SubjectMetaCache(subject_store), self._cookie or "")
        page_cache.put(category, status, start, total, items)
        self.save_data("subject_meta", subject_store)
        self.save_data("collection_cache", page_store)
        return items, total

    def api_collection(
        self, status: str = "do", start: int = 0, category: str = "movie", force: int = 0
    ) -> Dict[str, Any]:
        """收藏列表（status: wish/do/collect，category: movie/book/music，force: 强制绕过页缓存）。"""
        if not self._cookie:
            return {"success": False, "message": "未登录豆瓣，请先在配置页扫码", "total": 0, "items": []}
        if status not in ("wish", "do", "collect"):
            status = "do"
        if category not in ("movie", "book", "music"):
            category = "movie"
        try:
            start = max(int(start), 0)
        except Exception:
            start = 0
        items, total = self._collection_page(status, start, category, force=bool(force))
        if total < 0:
            return {"success": False, "message": "豆瓣收藏获取失败，请稍后重试", "total": 0, "items": []}
        return {"success": True, "total": total, "start": start, "items": items}

    def api_collection_summary(self) -> Dict[str, Any]:
        """三个状态的收藏总数（仪表盘小卡用）。总数现查豆瓣，与缓存不一致时作废对应页缓存。"""
        if not self._cookie:
            return {"success": False, "logged_in": False}
        from .douban_collect import fetch_page

        uid = self._uid_from_cookie()
        store = self.get_data("collection_cache") or {}
        if not isinstance(store, dict):
            store = {}
        check_state = self.get_data("summary_check")
        if not isinstance(check_state, dict):
            check_state = {}
        now = time.time()
        counts = {}
        # 想看：每次现查（准实时）；在看/看过：6 小时内沿用上次总数，
        # 本地同步或删除标记时会主动作废校验缓存，不必反复请求豆瓣
        for status in ("wish", "do", "collect"):
            cached_check = check_state.get(status)
            if (
                status != "wish"
                and isinstance(cached_check, dict)
                and now - cached_check.get("ts", 0) < 6 * 3600
            ):
                counts[status] = max(int(cached_check.get("total") or 0), 0)
                continue
            _, fresh_total = fetch_page(self._cookie, uid, "movie", status, 0)
            if fresh_total < 0:
                # 请求失败：沿用上次总数，且不写入节流缓存，下轮继续现查
                prev = check_state.get(status)
                counts[status] = max(int(prev.get("total") or 0), 0) if isinstance(prev, dict) else 0
                continue
            counts[status] = fresh_total
            check_state[status] = {"ts": now, "total": counts[status]}
            # 现查总数与页缓存不一致（如刚在豆瓣新标记），作废该状态的页缓存
            prefix = f"movie:{status}:"
            cached = store.get(f"{prefix}0")
            if isinstance(cached, dict) and cached.get("total") != counts[status]:
                for key in [k for k in store if k.startswith(prefix)]:
                    store.pop(key, None)
        if store != (self.get_data("collection_cache") or {}):
            self.save_data("collection_cache", store)
        self.save_data("summary_check", check_state)
        recent = self._collection_page("do", 0, "movie")[0][:6]
        return {
            "success": True,
            "logged_in": True,
            "wish": counts.get("wish", 0),
            "doing": counts.get("do", 0),
            "done": counts.get("collect", 0),
            "recent": recent,
        }

    def api_cover(self, img: str = ""):
        """豆瓣海报代理：服务端下载并缓存到本地，规避图床 418 与节点不可达。"""
        import hashlib
        import os

        from .douban_collect import cover_hosts_path, download_cover

        path = cover_hosts_path(img or "")
        if not path:
            return Response(status_code=400, media_type="text/plain", content="invalid image url")
        try:
            data_dir = os.path.join(self.get_data_path(), "covers")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, hashlib.md5(path.encode()).hexdigest() + ".jpg")
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                content = download_cover(path)
                if not content:
                    return Response(status_code=502, media_type="text/plain", content="download failed")
                with open(file_path, "wb") as fh:
                    fh.write(content)
            return FileResponse(
                file_path,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"},
            )
        except Exception as exc:
            logger.error(f"海报代理失败: {exc}")
            return Response(status_code=500, media_type="text/plain", content="cover error")

    # ------------------------------------------------------------ 订阅与 MP 状态
    def _mp_api(self, path: str, json_body: Any = None,
                method: str = None, extra_params: Dict[str, Any] = None) -> Optional[Any]:
        """调用宿主自身官方 API（本地回环，API_TOKEN 鉴权）。失败返回 None。"""
        try:
            from app.sdk.config import settings
        except Exception:
            from app.core.config import settings
        base = f"http://127.0.0.1:{getattr(settings, 'PORT', 3001)}/api/v1"
        params = {}
        token = getattr(settings, "API_TOKEN", None) or getattr(settings, "API_KEY", None)
        if token:
            params["token"] = token
        if extra_params:
            params.update(extra_params)
        http_method = method or ("POST" if json_body is not None else "GET")
        # trust_env=False：避免系统代理环境变量劫持 127.0.0.1 回环请求。
        # trust_env 是 Session 属性而非 request() 参数，必须通过 Session 设置。
        try:
            session = requests.Session()
            session.trust_env = False
            resp = session.request(
                http_method,
                f"{base}{path}",
                json=json_body,
                params=params,
                timeout=30,
            )
            if resp.status_code != 200:
                logger.warn(
                    f"MP API {path} 返回 {resp.status_code}: {resp.text[:200] if resp.text else ''}"
                )
                return None
            return resp.json()
        except Exception as exc:
            logger.warn(f"MP API {path} 调用失败: {exc}")
            return None

    def _mp_status_store(self) -> Dict[str, Any]:
        store = self.get_data("mp_status") or {}
        return store if isinstance(store, dict) else {}

    def api_mp_status(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """批量查询条目的入库/订阅状态（代理宿主官方 /media/status 接口）。"""
        payload = self._body_dict(data)
        items = payload.get("items") or []
        if not isinstance(items, list):
            items = []
        if not items:
            return {"success": True, "statuses": {}}
        statuses: Dict[str, str] = {}
        now = time.time()
        store = self._mp_status_store()
        # 未过期的缓存直接用，剩余的走批量查询
        pending = []
        for it in items[:50]:
            if not isinstance(it, dict):
                continue
            sid = str(it.get("sid") or "")
            if not sid:
                continue
            cached = store.get(sid)
            if cached and now - cached.get("ts", 0) < 6 * 3600:
                statuses[sid] = cached.get("status", "")
            else:
                pending.append(
                    {
                        "media_source": "douban",
                        "media_id": sid,
                        "title": it.get("title") or "",
                        "year": str(it.get("year") or ""),
                        "mtype": "电视剧" if it.get("subtype") == "tv" else "电影",
                    }
                )
        if pending:
            results = self._mp_api("/media/status", json_body=pending)
            if isinstance(results, dict) and isinstance(results.get("data"), list):
                # V3 宿主普通 API 统一三段式 envelope：业务数据在 data 中
                results = results["data"]
            if results is None:
                logger.warn("豆瓣档案：查询入库/订阅状态失败（角标本次不显示，详见上方 MP API 日志）")
                return {"success": False, "message": "查询 MP 状态失败", "statuses": statuses}
            for it, result in zip(pending, results or []):
                sid = str(it.get("media_id") or "")
                if not isinstance(result, dict):
                    status = ""
                elif result.get("item_id"):
                    status = "library"
                elif result.get("subscribed"):
                    status = "subscribed"
                else:
                    status = ""
                statuses[sid] = status
                store[sid] = {"status": status, "ts": now}
            self.save_data("mp_status", store)
        return {"success": True, "statuses": statuses}

    def _subscribe_once(self, title: str, year: str, mtype: Any, sid: str) -> Tuple[bool, str]:
        """调用宿主 SubscribeChain 添加一次订阅，返回 (是否成功, 消息)。"""
        try:
            from app.chain.subscribe import SubscribeChain
            from app.schemas.types import MediaSource
            sub_id, message = SubscribeChain().add(
                title=title,
                year=str(year or ""),
                mtype=mtype,
                media_source=MediaSource.Douban,
                media_id=sid,
                exist_ok=True,
                source="DoubanFolio",
            )
            return bool(sub_id), message or ""
        except Exception as exc:
            logger.error(f"添加订阅异常: {exc}")
            return False, f"添加订阅异常：{exc}"

    def _add_subscription(self, item: Dict[str, Any]) -> Tuple[bool, str]:
        """把豆瓣条目加入 MoviePilot 订阅（手动按钮与自动订阅共用）。"""
        sid = str(item.get("sid") or "")
        title = str(item.get("title") or "").strip()
        if not sid or not title:
            return False, "参数不完整"
        if item.get("subtype") not in ("tv", "movie"):
            return False, "仅支持电影/剧集订阅"
        try:
            from app.chain.subscribe import SubscribeChain  # noqa: F401
            from app.schemas.types import MediaSource, MediaType
        except Exception as exc:
            logger.error(f"订阅接口导入失败: {exc}")
            return False, "宿主不支持订阅接口"
        mtype = MediaType.TV if item.get("subtype") == "tv" else MediaType.MOVIE
        ok, message = self._subscribe_once(title, item.get("year") or "", mtype, sid)
        if not ok and "未识别到媒体信息" in str(message):
            # 宿主豆瓣识别走 frodo API：指定类型只查单一详情接口，偶发为空或
            # 触发 IP 限流。换相反类型重试一次（ movie<->tv 都查，覆盖 subtype 误判）。
            swapped = MediaType.MOVIE if mtype == MediaType.TV else MediaType.TV
            logger.info(
                f"{title} 订阅识别失败，换用{'电视剧' if swapped == MediaType.TV else '电影'}类型重试"
            )
            time.sleep(2)
            ok, message = self._subscribe_once(title, item.get("year") or "", swapped, sid)
            if not ok:
                message = f"{message}（豆瓣接口暂时无法识别该条目，可能被限流，请稍后重试）"
        if not ok and "已存在" in str(message):
            # 对齐官方「豆瓣想看」：条目已在订阅/媒体库中视为成功，不计失败重试
            ok = True
        if ok:
            store = self._mp_status_store()
            store[sid] = {"status": "subscribed", "ts": time.time()}
            self.save_data("mp_status", store)
            logger.info(f"{title} 已加入订阅（douban:{sid}）")
            return True, message or "订阅成功"
        return False, message or "订阅失败"

    def api_subscribe(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """把豆瓣条目加入 MoviePilot 订阅（电影/剧集）。"""
        ok, message = self._add_subscription(self._body_dict(data))
        return {"success": ok, "message": message}

    @staticmethod
    def _norm_title(value: Any) -> str:
        """标题归一化：去空白、转小写，便于跨源匹配（豆瓣标题常带「/ 原名」）。"""
        return re.sub(r"\s+", "", str(value or "")).lower()

    def _mp_subscribe_list(self) -> Optional[List[Dict[str, Any]]]:
        """拉取 MoviePilot 全部订阅（失败返回 None，空列表表示确实没有订阅）。"""
        data = self._mp_api("/subscribe/", extra_params={"page": 1, "count": 200})
        if data is None:
            return None
        if isinstance(data, dict):
            inner = data.get("data")
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
            return None
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return None

    def _mp_match_subscribes(self, sid: str,
                             title: str = "") -> List[Dict[str, Any]]:
        """在 MP 订阅列表中找出与豆瓣条目对应的订阅。

        宿主创建订阅时会把 douban:<sid> 身份转换成 TMDB，单靠豆瓣 ID 匹配不到，
        因此同时按标题（豆瓣标题可能是「中文原名 / 外文名」）做包含匹配。
        """
        subs = self._mp_subscribe_list()
        if not subs:
            return []
        sid = str(sid or "").strip()
        target = self._norm_title(title)
        matched = []
        for sub in subs:
            media_id = str(sub.get("media_id") or "")
            source = str(sub.get("media_source") or "").lower()
            if sid and media_id == sid and source in ("", "douban"):
                matched.append(sub)
                continue
            name = self._norm_title(sub.get("name"))
            if not name:
                continue
            if target and (name == target or target in name or name in target):
                matched.append(sub)
        return matched

    def _cancel_mp_subscription(self, sid: str, title: str = "") -> Tuple[bool, str]:
        """
        取消 MoviePilot 中该豆瓣条目的订阅（删除「想看」标记时联动）。

        优先按订阅 ID 删除（先列出订阅、按豆瓣 ID/标题匹配），因为宿主会把
        douban 身份转换为 TMDB，直接用豆瓣身份删不到；失败再走官方按媒体
        身份删除接口。成功后清本地角标缓存，并把条目从自动订阅记录中移除，
        以便之后重新标记想看时能再次自动订阅。
        """
        sid = str(sid or "").strip()
        if not sid:
            return False, "缺少条目 ID"
        matched = self._mp_match_subscribes(sid, title)
        removed = 0
        for sub in matched:
            sub_id = sub.get("id")
            if sub_id is None:
                continue
            resp = self._mp_api(f"/subscribe/{sub_id}", method="DELETE")
            if resp is not None:
                removed += 1
                logger.info(f"已取消 MoviePilot 订阅：{sub.get('name') or title}（id={sub_id}）")
            else:
                logger.warn(f"删除订阅失败：id={sub_id} {sub.get('name') or title}")
        if matched and removed == 0:
            # 兜底：按豆瓣媒体身份删除（部分宿主版本支持）
            resp = self._mp_api(
                f"/subscribe/media/{sid}",
                method="DELETE",
                extra_params={"media_source": "douban"},
            )
            if resp is not None and not (isinstance(resp, dict) and resp.get("success") is False):
                removed = 1
                logger.info(f"已按豆瓣身份取消 MoviePilot 订阅（douban:{sid}）")
        if matched and removed == 0:
            return False, "MP 订阅删除接口调用失败，详见 MP API 日志"
        if not matched:
            logger.info(f"MoviePilot 中未找到 {title or sid} 的订阅，无需取消")        # 清理本地角标缓存
        store = self._mp_status_store()
        store[sid] = {"status": "", "ts": time.time()}
        self.save_data("mp_status", store)
        # 从自动订阅记录中移除，重新标记想看时可再次触发
        state = self.get_data("auto_subscribe_state")
        if isinstance(state, dict) and isinstance(state.get("seen"), dict) and sid in state["seen"]:
            state["seen"].pop(sid, None)
            self.save_data("auto_subscribe_state", state)
        if removed:
            logger.info(f"{title or sid} 已取消 MoviePilot 订阅（douban:{sid}，删除 {removed} 条）")
            return True, "已取消订阅"
        return True, "MP 中已无对应订阅"

    def api_auto_subscribe_check(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """手动触发一次「豆瓣想看 → 自动订阅」检查（配置页「立即检查」按钮）。"""
        payload = self._body_dict(data)
        return self._auto_subscribe_check(force=bool(payload.get("force")))

    def _auto_subscribe_check(self, force: bool = False) -> Dict[str, Any]:
        """周期检查豆瓣新增「想看」并自动加入 MP 订阅。"""
        if not self._enable or not self._auto_subscribe:
            return {"success": False, "message": "自动订阅未启用", "subscribed": 0}
        if not self._cookie:
            return {"success": False, "message": "尚未登录豆瓣", "subscribed": 0}
        if not self._auto_subscribe_lock.acquire(blocking=False):
            return {"success": True, "message": "上一轮检查尚未结束", "subscribed": 0}
        try:
            return self._do_auto_subscribe_check(force)
        except Exception as exc:
            logger.error(f"豆瓣想看自动订阅检查异常: {exc}", exc_info=True)
            return {"success": False, "message": f"检查异常：{exc}", "subscribed": 0}
        finally:
            self._auto_subscribe_lock.release()

    def _do_auto_subscribe_check(self, force: bool) -> Dict[str, Any]:
        from .douban_collect import SubjectMetaCache, fetch_page, fetch_subject

        uid = self._uid_from_cookie()
        # 想看列表不缓存，直接现查（新标记按时间排在最前，取第一页即可）
        items, total = fetch_page(self._cookie, uid, "movie", "wish", 0)
        if total < 0:
            return {"success": False, "message": "豆瓣想看列表获取失败", "subscribed": 0}
        now = time.time()
        state = self.get_data("auto_subscribe_state")
        if not isinstance(state, dict):
            state = {}
        seen = state.get("seen")
        if not isinstance(seen, dict):
            seen = {}
        if not state.get("init"):
            # 首次运行建立基线：已有的想看不自动订阅，避免开启瞬间批量下单
            state["init"] = True
            if not self._auto_subscribe_existing:
                seen = {
                    str(it.get("sid")): {"ts": now, "status": "baseline", "attempts": 0}
                    for it in items
                    if isinstance(it, dict) and it.get("sid")
                }
                state["seen"] = seen
                state["ts"] = now
                self.save_data("auto_subscribe_state", state)
                logger.info(f"豆瓣想看自动订阅：已建立基线 {len(seen)} 条，之后新增的想看会自动订阅")
                return {
                    "success": True,
                    "message": f"已建立基线（{len(seen)} 条），此后新增的想看会自动订阅",
                    "subscribed": 0,
                    "baseline": True,
                }

        subject_store, _ = self._collection_stores()
        meta_cache = SubjectMetaCache(subject_store)
        subscribed = 0
        skipped = 0
        baseline = 0
        for it in items:
            if not isinstance(it, dict):
                continue
            sid = str(it.get("sid") or "")
            if not sid:
                continue
            title = str(it.get("title") or "").strip()
            entry = seen.get(sid)
            if isinstance(entry, dict):
                state_name = entry.get("status")
                if (state_name == "baseline" and self._auto_subscribe_existing) or (state_name == "skipped" and force):
                    # 之后勾选「已有想看也订阅」或手动强制重试时，重新纳入处理
                    entry["status"] = "pending"
                    entry["attempts"] = 0
                elif state_name in ("baseline", "subscribed", "skipped"):
                    if state_name == "skipped":
                        skipped += 1
                    elif state_name == "baseline":
                        baseline += 1
                    continue
            attempts = int(entry.get("attempts") or 0) if isinstance(entry, dict) else 0
            if attempts >= 3 and not force:
                seen[sid] = {"ts": now, "status": "skipped", "attempts": attempts, "title": title}
                skipped += 1
                continue
            meta = meta_cache.get(sid, "movie") or {}
            if not meta:
                meta = fetch_subject(sid, "movie", cookie=self._cookie or "") or {}
                if meta:
                    meta_cache.put(sid, "movie", meta)
            subtype = meta.get("subtype")
            if subtype not in ("tv", "movie"):
                # 类型暂时无法确定（详情接口被风控/不可达），不猜测类型，下轮重试
                attempts += 1
                seen[sid] = {"ts": now, "status": "pending", "attempts": attempts, "title": title}
                logger.warn(f"自动订阅跳过 {title or sid}：条目类型暂无法确定，{attempts}/3 次后放弃")
                continue
            payload = {
                "sid": sid,
                "title": title or str(meta.get("title") or sid),
                "year": str(meta.get("year") or ""),
                "subtype": subtype,
            }
            ok, message = self._add_subscription(payload)
            media_type = "电视剧" if subtype == "tv" else "电影"
            if ok:
                seen[sid] = {"ts": now, "status": "subscribed", "attempts": 0, "title": title}
                subscribed += 1
                self._record_history(payload["title"], "success", "豆瓣想看 → 自动订阅", media_type, sid=sid)
                logger.info(f"豆瓣想看自动订阅成功：{payload['title']}（douban:{sid}）")
            else:
                attempts += 1
                seen[sid] = {"ts": now, "status": "pending", "attempts": attempts, "title": title}
                logger.warn(f"豆瓣想看自动订阅失败：{payload['title']}，{message}")
                if attempts >= 3:
                    seen[sid]["status"] = "skipped"
                    self._record_history(
                        payload["title"], "fail", f"自动订阅失败：{message}", media_type, sid=sid
                    )
        # 控制状态体积，只保留最近 500 条
        if len(seen) > 500:
            ordered = sorted(
                seen.items(),
                key=lambda kv: kv[1].get("ts", 0) if isinstance(kv[1], dict) else 0,
                reverse=True,
            )
            seen = dict(ordered[:500])
        state["seen"] = seen
        state["ts"] = now
        self.save_data("auto_subscribe_state", state)
        self.save_data("subject_meta", subject_store)
        msg = f"检查完成：新增订阅 {subscribed} 条"
        if baseline and not self._auto_subscribe_existing:
            msg += f"；{baseline} 条为开启前已有想看未订阅（可勾选「已有想看也订阅」后点「立即检查」补订）"
        if skipped:
            msg += f"；{skipped} 条此前失败已跳过"
        return {
            "success": True,
            "message": msg,
            "subscribed": subscribed,
            "skipped": skipped,
            "total": total,
        }

    def _delete_douban_mark(self, sid: str, category: str = "movie", mark_id: str = "") -> bool:
        """删除豆瓣标记（内置实现，不依赖 doubanapi 子模块，避免其被 Python 缓存成旧版本）。

        判定规则：j_cat_ui 返回 HTTP 200 即视为成功——豆瓣失败时会返回 500/403，
        成功时响应体是 {'result': 'y'}（y=yes），不同版本还可能是 True/1，
        因此不再纠结字段值，只看 HTTP 状态码。
        """
        sid = str(sid or "").strip()
        if not sid or not self._cookie:
            return False
        cookie_parts = []
        for chunk in str(self._cookie).split(";"):
            chunk = chunk.strip()
            if "=" in chunk:
                key, value = chunk.split("=", 1)
                cookie_parts.append((key.strip(), value.strip().strip('"')))
        cookie_dict = dict(cookie_parts)
        ck = cookie_dict.get("ck") or ""
        if not ck:
            for key, value in cookie_parts:
                if key == "dbcl2":
                    ck = value.split(":")[0]
                    break
        host = "movie" if category == "movie" else category
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookie_parts)
        headers = {
            "User-Agent": _DOUBAN_UA,
            "Referer": f"https://{host}.douban.com/",
            "Origin": f"https://{host}.douban.com",
            "Cookie": cookie_header,
        }
        logger.info(f"删除豆瓣标记（内置逻辑）：sid={sid} mark_id={mark_id or '-'} category={category}")
        candidates = []
        for value in (str(mark_id or "").strip(), sid):
            if value and value not in candidates:
                candidates.append(value)
        for value in candidates:
            try:
                resp = requests.post(
                    f"https://{host}.douban.com/j/mine/j_cat_ui",
                    headers=headers,
                    data={"sid": value, "ck": ck},
                    timeout=12,
                )
            except Exception as exc:
                logger.warn(f"删除豆瓣标记 j_cat_ui(sid={value}) 请求异常：{exc}")
                continue
            body = (resp.text or "")[:120]
            if resp.status_code == 200:
                payload: Any = None
                try:
                    payload = resp.json()
                except Exception:
                    payload = None
                # 200 且没有显式失败标记即视为成功：豆瓣成功返回 {'result': 'y'}，
                # 失败通常是 500/403；个别情况会 200 + result=n，这里显式排除。
                if isinstance(payload, dict):
                    val = payload.get("result", payload.get("r"))
                    if val in (False, 0, "n", "N", "no", "false"):
                        logger.warn(f"删除豆瓣标记 j_cat_ui(sid={value}) 明确失败：{body}")
                        continue
                logger.info(f"删除豆瓣标记成功（j_cat_ui, sid={value}）：{sid} 响应={body}")
                return True
            logger.warn(f"删除豆瓣标记 j_cat_ui(sid={value}) HTTP {resp.status_code}：{body}")
        # 兜底：移动端 frodo 删除标记（部分账号无权限，仅作最后尝试）
        try:
            resp2 = requests.delete(
                f"https://m.douban.com/rexxar/api/v2/{host}/{sid}/interest",
                headers={
                    "User-Agent": _DOUBAN_UA,
                    "Referer": f"https://m.douban.com/movie/subject/{sid}/",
                    "Cookie": cookie_header,
                },
                params={"ck": ck},
                timeout=12,
            )
            if resp2.status_code in (200, 204):
                logger.info(f"删除豆瓣标记成功（frodo 兜底）：{sid}")
                return True
            logger.warn(f"删除豆瓣标记 frodo HTTP {resp2.status_code}（兜底失败，可忽略）")
        except Exception as exc:
            logger.warn(f"删除豆瓣标记 frodo 兜底异常：{exc}")
        return False

    def api_unmark(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """删除豆瓣上的条目标记（豆瓣网页叫「删除 / 删除该标记」），并同步本地缓存。

        注意参数类型必须是 Dict：FastAPI 对 Any 类型参数不注入 POST body，
        会永远收到 None（表现为「缺少条目 ID」）。
        """
        item = self._body_dict(data)
        sid = str(item.get("sid") or "").strip()
        status = str(item.get("status") or "do").strip()
        title = str(item.get("title") or "").strip()
        category = str(item.get("category") or "movie").strip()
        mark_id = str(item.get("mark_id") or "").strip()
        if not sid:
            return {"success": False, "message": "缺少条目 ID"}
        if status not in ("do", "wish", "collect"):
            status = "do"
        if category not in ("movie", "book", "music"):
            category = "movie"
        if not self._cookie:
            return {"success": False, "message": "尚未登录豆瓣，无法删除标记"}
        try:
            ok = self._delete_douban_mark(sid, category, mark_id=mark_id)
        except Exception as exc:
            logger.error(f"删除豆瓣标记异常: {exc}")
            return {"success": False, "message": f"删除标记异常：{exc}"}
        if not ok:
            return {"success": False, "message": "删除豆瓣标记失败，请检查 Cookie 是否有效或稍后重试"}
        # 删除成功后作废该状态全部页缓存，避免刷新后条目又出现
        self._invalidate_collection(status, category)
        label = {"do": "在看", "wish": "想看", "collect": "看过"}.get(status, "标记")
        # 删除「想看」标记时联动取消 MoviePilot 订阅（自动订阅的撤销入口）
        unsubscribed = False
        extra = ""
        if status == "wish":
            unsubscribed, unsub_msg = self._cancel_mp_subscription(sid, title)
            if unsubscribed and unsub_msg == "已取消订阅":
                extra = "，并已取消 MoviePilot 订阅"
            elif unsubscribed:
                extra = f"（{unsub_msg}）"
            else:
                extra = f"（MP 订阅未取消：{unsub_msg}）"
                logger.warn(f"删除想看标记后取消 MP 订阅未成功：{title or sid}，{unsub_msg}")
        self._record_history(
            title or sid, "success", f"已删除豆瓣「{label}」标记{extra}",
            "电影" if category == "movie" else category, sid=sid,
        )
        logger.info(f"{title or sid} 已删除豆瓣「{label}」标记{extra}")
        return {"success": True, "message": f"已删除豆瓣「{label}」标记{extra}", "unsubscribed": unsubscribed}

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        return [{"key": "douban_dashboard", "name": "豆瓣档案"}]

    def get_sidebar_nav(self) -> Optional[List[Dict[str, Any]]]:
        """主界面左侧导航栏全页入口，前端跳转 #/plugin-app/DoubanFolio/main 加载 ./AppPage。"""
        return [
            {
                "nav_key": "main",
                "title": "豆瓣档案",
                "icon": "mdi-movie-open-outline",
                "section": "start",
                "permission": "manage",
                "order": 16,
            }
        ]

    def get_dashboard(self, key: str = None, **kwargs) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """概览小卡由前端联邦组件 ./Dashboard 渲染。"""
        if key != "douban_dashboard":
            return None
        return (
            {"cols": 12, "md": 6},
            {
                "refresh": 30,
                "border": True,
                "title": "豆瓣档案",
                "subtitle": "我的书影音收藏",
            },
            None,
        )

    def get_state(self) -> bool:
        return self._enable

    def stop_service(self):
        pass

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    @staticmethod
    def exclude_keyword(path: str, keywords: str) -> Dict[str, Any]:
        if not keywords:
            return {"ret": True, "message": "空关键词"}

        if not path:
            logger.warn('媒体路径为空,不执行过滤操作')
            return {"ret": True, "message": "媒体路径为空,不执行过滤操作"}

        keywords_list = re.split(r'[，,]', keywords)
        if any(k in path for k in keywords_list):
            return {"ret": False, "message": f"路径 {path} 包含 {keywords}"}

        return {"ret": True, "message": f"路径 {path} 不包含任何关键词 {keywords}"}

    @staticmethod
    def format_title(title: str, season_id: int) -> str:
        if season_id > 1:
            return f"{title} 第{season_id}季"
        else:
            return title
