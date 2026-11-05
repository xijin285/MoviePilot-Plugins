"""
豆瓣扫码登录（自动获取 Cookie）

流程：
1. GET  https://accounts.douban.com/j/mobile/login/qrlogin_code
   返回 payload.code 与 payload.img（二维码图片地址）
2. GET  https://accounts.douban.com/j/mobile/login/qrlogin_status?ck=&code=xxx
   payload.login_status：pending（待扫码）/ scan（已扫码待确认）/ login（已确认）
3. 确认后需要再访问 stat.html 与豆瓣首页，dbcl2 / bid / ck 等 Cookie
   才会真正落到会话里，最后拼接成可直接使用的 Cookie 字符串。

注意：
- 二维码与会话是绑定关系，重复生成会让手机上已扫的码失效，
  所以同一会话内必须复用 code，直到过期或被使用。
- 图片地址在 imgN.doubanio.com 上，部分节点会因网络环境不可达，
  且不带 Referer 会返回 418，所以这里由服务端下载后转成 data URI，
  前端不再依赖图床可达性；下载失败时才回退到原始地址。
"""
import base64
import re
import threading
import time
from typing import Any, Dict, List, Optional

import requests

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_QRCODE_URL = "https://accounts.douban.com/j/mobile/login/qrlogin_code"
_STATUS_URL = "https://accounts.douban.com/j/mobile/login/qrlogin_status"
_SUCCESS_URL = (
    "https://www.douban.com/stat.html?&action=login_success"
    "&platform=qrcode&callback=jsonp_doubanfolio"
)
_HOME_URL = "https://www.douban.com/"

# 二维码图片的 CDN 节点，按可用性依次尝试
_QR_HOSTS: List[str] = ["img3", "img1", "img2", "img9"]
_QR_HOST_RE = re.compile(r"^https?://img\d+\.doubanio\.com")

# 首页源码里的昵称
_NICK_RE = re.compile(r'name="nick"[^>]*?value="([^"]*)"')
# dbcl2 的值格式是 "uid:token"（可能带引号），据此访问个人主页兜底取昵称
_UID_RE = re.compile(r'^"?(\d+):')
_TITLE_RE = re.compile(r"<title>\s*(.*?)\s*</title>", re.S)

# Cookie 拼接顺序：登录态关键字段优先，其余按 jar 顺序补在后面
_COOKIE_ORDER = (
    "dbcl2",
    "ck",
    "bid",
    "push_noty_num",
    "push_doumail_num",
    "ll",
    "frodotk_db",
)


class DoubanQrLogin:
    """豆瓣 App 扫码登录，成功后产出可用 Cookie。"""

    def __init__(self, ttl: int = 300, timeout: int = 8):
        self._ttl = ttl
        self._timeout = timeout
        self._lock = threading.RLock()
        self._session: Optional[requests.Session] = None
        self._code = ""
        self._img = ""
        self._login_url = ""
        self._status = "idle"
        self._expire_at = 0.0
        self._cookie = ""
        self._nickname = ""
        self._error = ""

    # ------------------------------------------------------------------ 内部
    @staticmethod
    def _new_session() -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": _UA,
                "Referer": "https://accounts.douban.com/passport/login",
                "Origin": "https://accounts.douban.com",
            }
        )
        return session

    def _expired(self) -> bool:
        return not self._code or bool(self._expire_at and time.time() > self._expire_at)

    def _reset(self) -> None:
        self._session = None
        self._code = ""
        self._img = ""
        self._login_url = ""
        self._status = "idle"
        self._expire_at = 0.0
        self._error = ""

    def _download_qr(self, url: str) -> str:
        """
        服务端下载二维码并转成 data URI。

        图床节点在不同网络环境下可用性差别很大，且不带 Referer 会返回 418，
        这里逐个节点尝试；全部失败时退回原始地址，交给浏览器再试一次。
        """
        path = _QR_HOST_RE.sub("", url or "")
        candidates = [url] + [f"https://{host}.doubanio.com{path}" for host in _QR_HOSTS]
        headers = {
            "User-Agent": _UA,
            "Referer": "https://accounts.douban.com/",
            "Accept": "image/avif,image/webp,image/png,*/*",
        }
        # 配置页会同步等这一步，整体预算控制在 8 秒内，避免页面长时间无响应
        budget = time.time() + 8
        for candidate in candidates:
            if not candidate or time.time() > budget:
                continue
            try:
                resp = requests.get(candidate, timeout=min(self._timeout, 5), headers=headers)
            except Exception:
                continue
            data = resp.content if resp is not None else b""
            if resp is None or resp.status_code != 200 or not data:
                continue
            if not (data.startswith(b"\x89PNG") or data.startswith(b"\xff\xd8\xff")):
                continue
            return "data:image/png;base64," + base64.b64encode(data).decode("ascii")
        return url

    def _collect_cookie(self) -> str:
        jar: Dict[str, str] = {}
        if self._session is not None:
            for cookie in self._session.cookies:
                if cookie.domain and "douban" in cookie.domain:
                    jar[cookie.name] = cookie.value
        parts = [f"{key}={jar[key]}" for key in _COOKIE_ORDER if key in jar]
        parts += [f"{key}={value}" for key, value in jar.items() if key not in _COOKIE_ORDER]
        return "; ".join(parts)

    def _fetch_nickname(self) -> str:
        """取昵称：优先首页 hidden 字段，取不到再用 dbcl2 里的 uid 访问个人主页。"""
        try:
            resp = self._session.get(_HOME_URL, timeout=self._timeout)
            match = _NICK_RE.search(resp.text or "")
            if match and match.group(1).strip():
                return match.group(1).strip()
        except Exception:
            pass

        jar = {cookie.name: cookie.value for cookie in self._session.cookies}
        match = _UID_RE.search(jar.get("dbcl2", ""))
        if not match:
            return ""
        try:
            resp = self._session.get(
                f"https://www.douban.com/people/{match.group(1)}/", timeout=self._timeout
            )
            title = _TITLE_RE.search(resp.text or "")
            if title:
                nick = re.split(r"\s*[|｜]\s*", title.group(1))[0].strip()
                if nick and "登录" not in nick and nick != "豆瓣":
                    return nick
        except Exception:
            pass
        return ""

    def _finish(self) -> None:
        """扫码确认后把登录态补全并提取 Cookie。"""
        try:
            self._session.get(_SUCCESS_URL, timeout=self._timeout)
        except Exception:
            # 这一步只用于补齐 Cookie，失败不阻断主流程
            pass
        self._nickname = self._fetch_nickname()

        cookie = self._collect_cookie()
        if "dbcl2" not in cookie:
            self._status = "error"
            self._error = "登录成功但未取到 dbcl2，请重新扫码或手动填写 Cookie"
            return
        self._cookie = cookie
        self._status = "login"
        self._expire_at = 0.0

    # ------------------------------------------------------------------ 对外
    def start(self) -> Dict[str, Any]:
        """生成二维码（会重置上一个会话）。"""
        with self._lock:
            self._reset()
            self._session = self._new_session()
            try:
                resp = self._session.get(_QRCODE_URL, timeout=self._timeout)
                data = resp.json()
            except Exception as exc:
                self._status = "error"
                self._error = f"请求二维码接口失败：{exc}"
                return self.status()

            payload = (data or {}).get("payload") or {}
            code = payload.get("code")
            img = payload.get("img")
            if (data or {}).get("status") != "success" or not code or not img:
                self._status = "error"
                self._error = f"二维码接口返回异常：{data}"
                return self.status()

            self._code = code
            self._img = self._download_qr(img)
            self._login_url = payload.get("login_url", "")
            self._status = "pending"
            self._expire_at = time.time() + self._ttl
            return self.status()

    def check(self) -> Dict[str, Any]:
        """查询一次扫码状态；已登录时提取 Cookie。"""
        with self._lock:
            if self._status == "login":
                return self.status()
            if self._session is None or self._expired():
                self._status = "expired"
                return self.status()

            try:
                resp = self._session.get(
                    _STATUS_URL,
                    params={"ck": "", "code": self._code},
                    timeout=self._timeout,
                )
                data = resp.json()
            except Exception as exc:
                self._error = f"查询扫码状态失败：{exc}"
                return self.status()

            payload = (data or {}).get("payload") or {}
            login_status = (payload.get("login_status") or "").lower()

            if login_status in ("pending", ""):
                return self.status()
            if login_status in ("scan", "scanned", "confirm"):
                self._status = "scanned"
                return self.status()
            if login_status == "login":
                self._finish()
                return self.status()

            self._status = "error"
            self._error = f"未知登录状态：{login_status}"
            return self.status()

    def status(self) -> Dict[str, Any]:
        expire_in = int(self._expire_at - time.time()) if self._expire_at else 0
        return {
            "status": self._status,
            "img": self._img,
            "code": self._code,
            "login_url": self._login_url,
            "cookie": self._cookie,
            "nickname": self._nickname,
            "error": self._error,
            "expire_in": max(expire_in, 0),
        }

    def reset(self) -> None:
        with self._lock:
            self._reset()
