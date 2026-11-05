"""
豆瓣书影音收藏抓取。

数据源：网页版个人收藏页（SSR，带 Cookie 可见私有标记）。
- movie.douban.com/people/{uid}/{wish|do|collect}  电影+剧集
- book.douban.com/people/{uid}/{wish|do|collect}   图书
- music.douban.com/people/{uid}/{wish|do|collect}  音乐

列表条目解析自 grid 视图；条目类型（电影/剧集）与豆瓣评分、
高清海报通过 frodo 条目接口（m.douban.com/rexxar/api/v2/{cat}/{sid}）
补全，公开接口无需 Cookie，仅带 Referer。
"""
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_SITES = {
    "movie": "https://movie.douban.com",
    "book": "https://book.douban.com",
    "music": "https://music.douban.com",
}
_PAGE_SIZE = 15

_ITEM_MARK = '<div class="item comment-item"'
_SID_RE = re.compile(r"subject/(\d+)/")
_TITLE_RE = re.compile(r"<em>([^<]+)</em>")
_POSTER_RE = re.compile(r'src="(https://img\d+\.doubanio\.com/view/photo/[^"]+)"')
_DATE_RE = re.compile(r'<span class="date">([^<]+)</span>')
_TOTAL_SEG_RE = re.compile(r'class="subject-num">([^<]+)<')
_MYRATE_RE = re.compile(r'class="rating(\d)-t"')
_COMMENT_RE = re.compile(r'<span class="comment">(.*?)</span>', re.S)
# 登录态收藏页里每条 item 带 data-cid（标记记录 ID），删除链接 a.d_link 的 rel 与之对应
_CID_RE = re.compile(r'data-cid="(\d+)"')
_DLINK_RE = re.compile(r'<a[^>]*class="[^"]*\bd_link\b[^"]*"[^>]*rel="([^"]+)"', re.S)
_DLINK_RE2 = re.compile(r'<a[^>]*rel="([^"]+)"[^>]*class="[^"]*\bd_link\b[^"]*"', re.S)

# frodo 条目接口的类别映射（网页类别 -> 接口路径段）
_FRODO_PATH = {"movie": "movie", "book": "book", "music": "music"}

# frodo 接口熔断：连续失败达到阈值后暂停补全一段时间，避免条目详情
# 批量不可达时（网络/风控）每次列表请求都串行打一堆超时请求
_CIRCUIT = {"fails": 0, "open_until": 0.0}
_CIRCUIT_THRESHOLD = 8
_CIRCUIT_PAUSE = 600

_SUBJECT_TTL = 7 * 86400   # 条目详情缓存 7 天

# 列表页缓存按状态分级：
#   想看：条目少、变动频繁，不缓存，每次现查（准实时）
#   在看：12 小时；看过：24 小时（基本不变，避免反复翻页请求豆瓣）
#   其他（图书/音乐）：保留 30 分钟
_PAGE_TTL_BY_STATUS = {
    "wish": 0,
    "do": 12 * 3600,
    "collect": 24 * 3600,
}
_PAGE_TTL_DEFAULT = 30 * 60


def page_ttl(status: str) -> int:
    """返回某个收藏状态的页缓存时长（秒）。"""
    return _PAGE_TTL_BY_STATUS.get(status, _PAGE_TTL_DEFAULT)


def _headers(cookie: str = "") -> Dict[str, str]:
    h = {"User-Agent": _UA, "Referer": "https://movie.douban.com/"}
    if cookie:
        h["Cookie"] = cookie
    return h


def _parse_page(html: str) -> Tuple[List[Dict[str, Any]], int]:
    """解析一个 grid 列表页，返回 (条目列表, 总数)。"""
    total = 0
    total_match = _TOTAL_SEG_RE.search(html)
    if total_match:
        # 形如 "1-15&nbsp;/&nbsp;133"，去掉实体后取最后一个数字
        nums = re.findall(r"\d+", total_match.group(1).replace("&nbsp;", " "))
        if len(nums) >= 3:
            total = int(nums[-1])

    items: List[Dict[str, Any]] = []
    blocks = html.split(_ITEM_MARK)[1:]
    for block in blocks:
        sid_match = _SID_RE.search(block)
        title_match = _TITLE_RE.search(block)
        if not sid_match or not title_match:
            continue
        poster_match = _POSTER_RE.search(block)
        date_match = _DATE_RE.search(block)
        rate_match = _MYRATE_RE.search(block)
        comment_match = _COMMENT_RE.search(block)
        cid_match = _CID_RE.search(block)
        dlink_match = _DLINK_RE.search(block) or _DLINK_RE2.search(block)
        item = {
            "sid": sid_match.group(1),
            "title": title_match.group(1).strip(),
            "poster": poster_match.group(1) if poster_match else "",
            "date": date_match.group(1).strip() if date_match else "",
            "my_rating": int(rate_match.group(1)) if rate_match else 0,
            "comment": comment_match.group(1).strip() if comment_match else "",
            "private": "（不公开）" in block,
            # 删除标记时优先用页面自带的值，避免猜测 j_cat_ui 需要哪种 ID
            "mark_id": (dlink_match.group(1) if dlink_match else (cid_match.group(1) if cid_match else "")),
        }
        items.append(item)
    return items, total


def fetch_page(
    cookie: str,
    uid: str,
    category: str,
    status: str,
    start: int = 0,
    timeout: int = 10,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    抓取一页收藏列表。

    :param category: movie / book / music
    :param status: wish(想看) / do(在看) / collect(看过)
    :return: (items, total)，网络失败时返回 ([], -1)
    """
    site = _SITES.get(category)
    if not site or status not in ("wish", "do", "collect") or not uid:
        return [], -1
    url = f"{site}/people/{uid}/{status}?sort=time&start={start}"
    last_error = ""
    for _ in range(2):
        try:
            resp = requests.get(url, headers=_headers(cookie), timeout=timeout)
            if resp.status_code == 200 and resp.text:
                return _parse_page(resp.text)
            last_error = f"HTTP {resp.status_code}"
        except Exception as exc:
            last_error = str(exc)
    return [], -1


def fetch_all(
    cookie: str,
    uid: str,
    category: str,
    status: str,
    max_items: int = 300,
    timeout: int = 10,
) -> Tuple[List[Dict[str, Any]], int]:
    """抓取整个收藏列表（翻页直到取够或取完）。"""
    items: List[Dict[str, Any]] = []
    total = 0
    start = 0
    while start < max_items:
        page_items, page_total = fetch_page(cookie, uid, category, status, start, timeout)
        if page_total < 0:
            break
        total = page_total
        items.extend(page_items)
        if not page_items or len(items) >= total:
            break
        start += _PAGE_SIZE
    return items, total


def fetch_subject(
    sid: str,
    category: str,
    cookie: str = "",
    timeout: int = 6,
) -> Optional[Dict[str, Any]]:
    """
    取条目详情（类型/年份/豆瓣评分/高清海报）。失败返回 None。

    双数据源：优先 rexxar 条目接口（快、字段全），失败后回退网页版
    条目页 SSR 解析（与收藏列表页同域，列表页可达即可用）。带 Cookie
    可减少风控拦截。连续失败达到阈值后熔断一段时间，期间不发请求。

    :return: {is_tv, subtype, year, rating, poster, title}
    """
    path = _FRODO_PATH.get(category)
    if not path or not sid:
        return None
    if time.time() < _CIRCUIT["open_until"]:
        return None
    meta = _fetch_subject_rexxar(sid, path, cookie, timeout)
    if meta is None and category == "movie":
        meta = _fetch_subject_web(sid, cookie, timeout)
    if meta:
        _CIRCUIT["fails"] = 0
    else:
        _CIRCUIT["fails"] = int(_CIRCUIT.get("fails", 0)) + 1
        if _CIRCUIT["fails"] >= _CIRCUIT_THRESHOLD:
            _CIRCUIT["open_until"] = time.time() + _CIRCUIT_PAUSE
            _CIRCUIT["fails"] = 0
    return meta


def _fetch_subject_rexxar(
    sid: str, path: str, cookie: str = "", timeout: int = 6
) -> Optional[Dict[str, Any]]:
    """rexxar 条目接口（m.douban.com）。"""
    url = f"https://m.douban.com/rexxar/api/v2/{path}/{sid}"
    try:
        resp = requests.get(url, headers=_headers(cookie), timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            rating = data.get("rating") or {}
            return {
                "is_tv": bool(data.get("is_tv")),
                "subtype": data.get("subtype") or ("tv" if data.get("is_tv") else path),
                "year": str(data.get("year") or ""),
                "rating": rating.get("value") or 0,
                "poster": data.get("cover_url") or "",
                "title": data.get("title") or "",
            }
    except Exception:
        pass
    return None


def _fetch_subject_web(
    sid: str, cookie: str = "", timeout: int = 8
) -> Optional[Dict[str, Any]]:
    """网页版条目页 SSR 解析（回退源）。电影页有「上映日期」，剧集页有「首播」。"""
    url = f"https://movie.douban.com/subject/{sid}/"
    try:
        resp = requests.get(url, headers=_headers(cookie), timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None
        html = resp.text
        title_match = re.search(r'property="v:itemreviewed">([^<]+)<', html)
        if not title_match:
            return None
        has_broadcast = "首播" in html
        has_release = "上映日期" in html
        if has_broadcast and not has_release:
            is_tv = True
        elif has_release and not has_broadcast:
            is_tv = False
        else:
            # 两者都有或都没有时无法判定，返回 None 走下一次重试
            return None
        rating_match = re.search(r'v:average">([\d.]+)<', html)
        year_match = re.search(r'v:initialReleaseDate[^>]*>(?:<[^>]*>)*(\d{4})', html)
        poster_match = re.search(r'src="(https://img\d+\.doubanio\.com/view/photo/s_ratio_poster[^"]+)"', html)
        year = year_match.group(1) if year_match else ""
        if not year:
            year_match = re.search(r'[\[（(]?(\d{4})[\]）)]?', title_match.group(1))
            year = year_match.group(1) if year_match else ""
        return {
            "is_tv": is_tv,
            "subtype": "tv" if is_tv else "movie",
            "year": year,
            "rating": float(rating_match.group(1)) if rating_match else 0,
            "poster": poster_match.group(1) if poster_match else "",
            "title": title_match.group(1).strip(),
        }
    except Exception:
        pass
    return None


class SubjectMetaCache:
    """条目详情持久缓存（由插件层用 save_data 提供存储）。"""

    def __init__(self, store: Dict[str, Any]):
        self._store = store if isinstance(store, dict) else {}

    def get(self, sid: str, category: str) -> Optional[Dict[str, Any]]:
        entry = self._store.get(f"{category}:{sid}")
        # 兼容历史脏数据：非 dict 结构直接剔除
        if not isinstance(entry, dict):
            if entry is not None:
                self._store.pop(f"{category}:{sid}", None)
            return None
        if time.time() - entry.get("ts", 0) > _SUBJECT_TTL:
            return None
        data = entry.get("data")
        return data if isinstance(data, dict) else None

    def put(self, sid: str, category: str, data: Dict[str, Any]) -> None:
        # 控制缓存体积：最多保留 3000 条，超出时丢弃最旧的
        if len(self._store) >= 3000:
            oldest = sorted(self._store.items(), key=lambda kv: kv[1].get("ts", 0))
            for key, _ in oldest[: len(self._store) - 2500]:
                self._store.pop(key, None)
        self._store[f"{category}:{sid}"] = {"ts": time.time(), "data": data}


def enrich(
    items: List[Dict[str, Any]],
    category: str,
    cache: SubjectMetaCache,
    cookie: str = "",
) -> List[Dict[str, Any]]:
    """给列表条目补全类型/年份/豆瓣评分/高清海报（带持久缓存）。"""
    for item in items:
        meta = cache.get(item["sid"], category)
        if meta is None:
            meta = fetch_subject(item["sid"], category, cookie) or {}
            if meta:
                cache.put(item["sid"], category, meta)
        item["subtype"] = meta.get("subtype", "")
        item["year"] = meta.get("year", "")
        item["douban_rating"] = meta.get("rating", 0)
        if meta.get("poster"):
            item["poster_hd"] = meta["poster"]
        else:
            item["poster_hd"] = item.get("poster", "")
    return items


class PageCache:
    """列表页缓存（按状态分级 TTL），由插件层提供存储。"""

    def __init__(self, store: Dict[str, Any]):
        self._store = store if isinstance(store, dict) else {}

    @staticmethod
    def _key(category: str, status: str, start: int) -> str:
        return f"{category}:{status}:{start}"

    def get(self, category: str, status: str, start: int):
        key = self._key(category, status, start)
        entry = self._store.get(key)
        # 兼容历史脏数据：非 dict 结构直接剔除，避免对 str 调 .get 报错
        if not isinstance(entry, dict):
            if entry is not None:
                self._store.pop(key, None)
            return None
        ttl = page_ttl(status)
        # ttl=0 表示不做缓存（想看），每次都回源豆瓣现查
        if ttl <= 0 or time.time() - entry.get("ts", 0) > ttl:
            return None
        total, items = entry.get("total"), entry.get("items")
        if not isinstance(total, int) or not isinstance(items, list):
            return None
        return total, items

    def put(self, category: str, status: str, start: int, total: int, items: List[Dict[str, Any]]) -> None:
        if len(self._store) >= 200:
            oldest = sorted(self._store.items(), key=lambda kv: kv[1].get("ts", 0))
            for key, _ in oldest[: len(self._store) - 150]:
                self._store.pop(key, None)
        self._store[self._key(category, status, start)] = {"ts": time.time(), "total": total, "items": items}


def cover_hosts_path(url: str) -> Optional[str]:
    """校验豆瓣图床 URL 并提取路径部分（供代理缓存）。"""
    match = re.match(r"^https://img\d+\.doubanio\.com(/view/photo/[\w./-]+\.(?:jpg|webp))$", url or "")
    return match.group(1) if match else None


def download_cover(path: str, timeout: int = 8) -> Optional[bytes]:
    """按多节点下载海报图片（img1/2/9/3 依次尝试）。"""
    headers = {
        "User-Agent": _UA,
        "Referer": "https://movie.douban.com/",
        "Accept": "image/avif,image/webp,image/jpeg,*/*",
    }
    for host in ("img1", "img2", "img9", "img3"):
        try:
            resp = requests.get(f"https://{host}.doubanio.com{path}", headers=headers, timeout=timeout)
            if resp.status_code == 200 and resp.content:
                return resp.content
        except Exception:
            continue
    return None
