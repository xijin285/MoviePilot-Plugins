import base64
import hashlib
import json
import mimetypes
import time
from wsgiref.handlers import format_date_time
from threading import Lock
from pathlib import Path
from typing import Optional, List, Dict, Any
from xml.sax.saxutils import escape

import requests

import schemas
from app.core.cache import TTLCache
from app.core.config import settings
from app.log import logger


class RateLimiter:
    """
    简单速率限制器
    """

    def __init__(self, max_calls: int = 2, time_window: float = 1.0, name: str = ""):
        self.max_calls = max_calls
        self.time_window = time_window
        self.name = name
        self._lock = Lock()
        self._call_times: List[float] = []

    def acquire(self):
        now = time.monotonic()
        with self._lock:
            self._call_times = [
                call_at for call_at in self._call_times if now - call_at < self.time_window
            ]
            if len(self._call_times) >= self.max_calls:
                oldest_call = min(self._call_times)
                wait_time = self.time_window - (now - oldest_call)
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.monotonic()
                    self._call_times = [
                        call_at
                        for call_at in self._call_times
                        if now - call_at < self.time_window
                    ]
            self._call_times.append(now)


class IdPathCache:
    """
    路径与 ID 双向缓存
    """

    def __init__(self, region_prefix: str = "quarkdisk", maxsize: int = 512):
        self.id_to_dir = TTLCache(
            region=f"{region_prefix}_id_to_dir",
            maxsize=maxsize,
            ttl=60 * 30,
        )
        self.dir_to_id = TTLCache(
            region=f"{region_prefix}_dir_to_id",
            maxsize=maxsize,
            ttl=60 * 30,
        )

    def add_cache(self, file_id: str, directory: str):
        old_directory = self.id_to_dir.get(str(file_id))
        if old_directory and old_directory != directory:
            self.dir_to_id.delete(key=old_directory)

        old_id = self.dir_to_id.get(directory)
        if old_id and old_id != str(file_id):
            self.id_to_dir.delete(key=old_id)

        self.id_to_dir.set(key=str(file_id), value=directory)
        self.dir_to_id.set(key=directory, value=str(file_id))

    def get_id_by_dir(self, directory: str) -> Optional[str]:
        return self.dir_to_id.get(directory)

    def remove(self, file_id: Optional[str] = None, directory: Optional[str] = None):
        if file_id is not None:
            old_directory = self.id_to_dir.get(str(file_id))
            if old_directory:
                self.id_to_dir.delete(key=str(file_id))
                self.dir_to_id.delete(key=old_directory)
        elif directory is not None:
            old_id = self.dir_to_id.get(directory)
            if old_id:
                self.dir_to_id.delete(key=directory)
                self.id_to_dir.delete(key=old_id)
        else:
            raise ValueError("file_id 和 directory 至少提供一个")

    def clear(self):
        self.id_to_dir.clear()
        self.dir_to_id.clear()


class QuarkApi:
    """
    夸克网盘基础操作
    """

    # 请求重试次数
    _max_retries = 3
    
    # 请求超时时间(秒)
    _timeout = 30

    # 默认分片大小
    _default_part_size = 10 * 1024 * 1024

    transtype = {
        "move": "移动",
        "copy": "复制",
    }

    def __init__(self, cookie: str):
        try:
            self._cookie = cookie.strip()
            self._disk_name = "夸克网盘"
            self._base_url = "https://pan.quark.cn/1/clouddrive"
            self._drive_url = "https://drive.quark.cn/1/clouddrive"
            self._drive_pc_url = "https://drive-pc.quark.cn/1/clouddrive"
            self._id_cache = IdPathCache(region_prefix="quarkdisk_path")
            self._list_rate_limiter = RateLimiter(max_calls=1, time_window=1.5, name="list")
            self._path_rate_limiter = RateLimiter(max_calls=2, time_window=1.0, name="path_to_id")
            self._get_item_fail_records: Dict[str, int] = {}
            logger.info(f"【夸克】初始化API客户端, Cookie长度: {len(cookie)}")

            # 生成设备ID
            device_id = str(int(time.time() * 1000))

            def filter_cookies(cookie_str, exclude_keys):
                filtered = []
                for item in cookie_str.split(";"):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        if key not in exclude_keys:
                            filtered.append(f"{key}={value}")
                return '; '.join(filtered)

            self._headers = {
                "Cookie": self._cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Content-Type": "application/json;charset=UTF-8",
                "Referer": "https://pan.quark.cn",
                "Origin": "https://pan.quark.cn",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "x-requested-with": "XMLHttpRequest",
                "x-device-id": device_id,
                "x-client-version": "3.1.0",
                "x-platform-version": "web",
                "x-platform-type": "web",
                "x-sdk-version": "3.1.0",
                "x-web-timestamp": str(int(time.time() * 1000)),
                "x-device-model": "web",
                "x-device-name": "Chrome",
                "x-device-platform": "web",
                "x-app-id": "30",
                "x-app-version": "3.1.0",
                "x-app-package": "com.quark.pan"
            }
            # 日志输出前过滤Cookie字段
            filtered_headers = self._headers.copy()
            filtered_headers["Cookie"] = filter_cookies(self._headers["Cookie"], ["_UP_A4A_11_", "_UP_D_", "_qk_bx_ck_v1", "tfstk"])
            # logger.info(f"【夸克】请求头: {filtered_headers}")
            
            # 解析Cookie
            try:
                cookie_dict = {}
                for item in cookie.split(";"):
                    if "=" in item:
                        key, value = item.strip().split("=", 1)
                        cookie_dict[key] = value
                # logger.info(f"【夸克】Cookie解析结果: {cookie_dict.keys()}")
                
                # 验证cookie是否有效
                try:
                    logger.info("【夸克】开始验证Cookie（通过list接口）")
                    root_item = schemas.FileItem(
                        storage=self._disk_name,
                        fileid="0",
                        parent_fileid=None,
                        name="/",
                        basename="/",
                        extension=None,
                        type="dir",
                        path="/",
                        size=None,
                        modify_time=None,
                        pickcode=None
                    )
                    items = self.list(root_item)
                    if items is None:
                        raise Exception("Cookie验证失败: 无法获取根目录文件列表")
                    logger.info(f"【夸克】Cookie验证成功，根目录文件数: {len(items)}")
                except Exception as e:
                    logger.error(f"【夸克】Cookie验证失败: {str(e)}")
                    raise
                
            except Exception as e:
                logger.error(f"【夸克】解析Cookie失败: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"【夸克】初始化API客户端失败: {str(e)}")
            raise

    def _normalize_path(self, path: str, is_dir: bool = False) -> str:
        path_str = str(path or "/").replace("\\", "/")
        if not path_str.startswith("/"):
            path_str = "/" + path_str
        path_str = path_str.replace("//", "/")
        if path_str != "/" and path_str.endswith("/") and not is_dir:
            path_str = path_str[:-1]
        return path_str

    def _join_path(self, parent_path: str, name: str, is_dir: bool = False) -> str:
        parent = self._normalize_path(parent_path, is_dir=True)
        if parent != "/" and not parent.endswith("/"):
            parent = f"{parent}/"
        full_path = f"{parent}{name}"
        if is_dir and not full_path.endswith("/"):
            full_path += "/"
        return self._normalize_path(full_path, is_dir=is_dir)

    def _is_directory(self, item: Dict[str, Any]) -> bool:
        """
        判断夸克返回项是否为目录。
        根据 pan.quark.cn 前端逻辑，优先使用 file_type：file_type == 0 表示目录。
        """
        file_type = item.get("file_type")
        if file_type is not None:
            try:
                return int(file_type) == 0
            except (TypeError, ValueError):
                return str(file_type).lower() in {"0", "folder", "dir"}

        if "file" in item:
            return item.get("file") is False

        if item.get("dir") is True:
            return True

        obj_category = item.get("obj_category")
        if obj_category:
            return False

        format_type = item.get("format_type")
        if format_type:
            return False

        return False

    def _update_cookie_from_response(self, response: requests.Response):
        if not response or not response.cookies:
            return
        cookie_dict = {}
        for item in self._cookie.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                cookie_dict[key] = value
        updated = False
        for key in ["__puus", "__pus"]:
            if key in response.cookies:
                cookie_dict[key] = response.cookies.get(key)
                updated = True
        if updated:
            self._cookie = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
            self._headers["Cookie"] = self._cookie

    def _request(
        self,
        path: str,
        method: str = "GET",
        *,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_drive: bool = False,
        use_drive_pc: bool = False,
        use_pan: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        if use_drive_pc:
            base_url = self._drive_pc_url
        elif use_drive:
            base_url = self._drive_url
        elif use_pan:
            base_url = self._base_url
        else:
            base_url = self._base_url
        url = f"{base_url}{path}"
        request_headers = dict(self._headers)
        request_params = {"pr": "ucpro", "fr": "pc"}
        if params:
            request_params.update(params)
        if headers:
            request_headers.update(headers)

        last_error = None
        for retry in range(self._max_retries):
            try:
                resp = requests.request(
                    method=method,
                    url=url,
                    params=request_params,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout or self._timeout,
                )
                self._update_cookie_from_response(resp)
                if resp.status_code != 200:
                    last_error = Exception(f"HTTP {resp.status_code}: {resp.text}")
                else:
                    data = resp.json()
                    if data.get("status", 200) >= 400 or data.get("code", 0) != 0:
                        message = data.get("message") or data.get("msg") or "未知错误"
                        last_error = Exception(message)
                    else:
                        return data
            except Exception as e:
                last_error = e

            if retry < self._max_retries - 1:
                time.sleep(1)

        raise last_error or Exception("请求失败")

    def _file_to_item(self, parent_path: str, item: Dict[str, Any]) -> schemas.FileItem:
        is_dir = self._is_directory(item)
        file_path = self._join_path(parent_path, item["file_name"], is_dir=is_dir)
        cache_key = file_path[:-1] if is_dir and file_path != "/" else file_path
        self._id_cache.add_cache(str(item["fid"]), cache_key)
        return schemas.FileItem(
            storage=self._disk_name,
            fileid=str(item["fid"]),
            parent_fileid=str(item.get("pdir_fid") or item.get("parent_id") or "0"),
            name=item["file_name"],
            basename=Path(item["file_name"]).stem,
            extension=Path(item["file_name"]).suffix[1:] if not is_dir and Path(item["file_name"]).suffix else None,
            type="dir" if is_dir else "file",
            path=file_path,
            size=None if is_dir else item.get("size"),
            modify_time=int(item.get("updated_at") or item.get("modified_time") or 0),
            pickcode=str(item),
        )

    def _path_to_id(self, path: str):
        """
        通过路径获取ID
        """
        try:
            path = self._normalize_path(path)
            logger.info(f"【夸克】开始获取路径 {path} 的ID")
            
            # 根目录
            if path == "/" or path == "":
                logger.info("【夸克】根目录ID为0")
                return "0"

            # 检查缓存
            cache_id = self._id_cache.get_id_by_dir(path)
            if cache_id:
                logger.info(f"【夸克】从缓存获取到ID: {cache_id}")
                return cache_id
                
            logger.info(f"【夸克】开始逐级查找路径: {path}")
            
            parts = [p for p in Path(path).parts if p != "/"]
            if not parts:
                return "0"
                
            current_id = "0"
            current_path = ""
            for part in parts:
                try:
                    self._path_rate_limiter.acquire()
                    logger.info(f"【夸克】查找目录 {part} (当前ID: {current_id})")
                    resp_json = self._request(
                        "/file/sort",
                        method="GET",
                        params={
                            "pr": "ucpro",
                            "fr": "pc",
                            "uc_param_str": "",
                            "pdir_fid": current_id,
                            "_page": 1,
                            "_size": 100,
                            "_fetch_total": 1,
                            "_fetch_sub_dirs": 1,
                            "_sort": "file_type:asc,file_name:asc",
                        },
                        use_drive=True,
                    )
                        
                    found = False
                    for item in resp_json.get("data", {}).get("list", []):
                        if item["file_name"] == part:
                            current_id = str(item["fid"])
                            current_path = self._join_path(current_path or "/", part)
                            self._id_cache.add_cache(current_id, current_path)
                            found = True
                            logger.info(f"【夸克】找到目录 {part} 的ID: {current_id}")
                            break
                            
                    if not found:
                        logger.error(f"【夸克】未找到目录: {part}")
                        return None
                        
                except Exception as e:
                    logger.error(f"【夸克】查找目录ID失败: {str(e)}")
                    return None
                    
            # 缓存结果
            self._id_cache.add_cache(current_id, path)
            logger.info(f"【夸克】路径 {path} 的最终ID为: {current_id}")
            return current_id
            
        except Exception as e:
            logger.error(f"【夸克】获取路径ID失败: {str(e)}")
            return None

    def list(self, fileitem: schemas.FileItem) -> List[schemas.FileItem]:
        """
        获取文件列表（新版，完全模拟网页端接口，GET方式）
        """
        try:
            if fileitem.type == "file":
                detail_item = self.detail(fileitem)
                if detail_item:
                    return [detail_item]
                return [fileitem]

            items = []
            page = 1
            size = 100
            logger.info(f"【夸克】开始获取目录 {fileitem.path} 的文件列表（新版/sort接口）")
            parent_id = self._path_to_id(fileitem.path)
            if not parent_id:
                logger.error(f"【夸克】获取文件列表失败: 无法获取目录ID {fileitem.path}")
                return []
            logger.info(f"【夸克】目录 {fileitem.path} 的ID为 {parent_id}")
            while True:
                try:
                    self._list_rate_limiter.acquire()
                    logger.info(f"【夸克】请求第 {page} 页文件列表")
                    resp_json = self._request(
                        "/file/sort",
                        method="GET",
                        params={
                            "pr": "ucpro",
                            "fr": "pc",
                            "uc_param_str": "",
                            "pdir_fid": parent_id,
                            "_page": page,
                            "_size": size,
                            "_fetch_total": 1,
                            "_fetch_sub_dirs": 0,
                            "_sort": "file_type:asc,updated_at:desc",
                        },
                        use_drive=True,
                    )
                    data = resp_json.get("data", {})
                    item_list = data.get("list", [])
                    if not item_list:
                        logger.info("【夸克】没有更多文件")
                        break
                    for item in item_list:
                        try:
                            items.append(self._file_to_item(fileitem.path, item))
                        except Exception as e:
                            logger.error(f"【夸克】处理文件项失败: {str(e)}")
                            continue
                    if len(item_list) < size:
                        break
                    page += 1
                except Exception as e:
                    logger.error(f"【夸克】获取文件列表失败: {str(e)}")
                    return []
            logger.info(f"【夸克】共获取到 {len(items)} 个文件")
            return items
        except Exception as e:
            logger.error(f"【夸克】获取文件列表失败: {str(e)}")
            return []

    def get_item(self, path: Path) -> Optional[schemas.FileItem]:
        """
        获取文件信息
        """
        try:
            path_str = self._normalize_path(str(path))
            now = time.time()

            item = None
            file_id = self._id_cache.get_id_by_dir(path_str)
            if file_id:
                last_cache_error = None
                for _ in range(3):
                    try:
                        resp = self._request(
                            "/file/info",
                            method="GET",
                            params={
                                "fid": file_id,
                                "_fetch_full_path": 0,
                                "need_profile_tags": 1,
                            },
                            use_drive=True,
                        )
                        item = resp.get("data")
                        if item:
                            break
                    except Exception as e:
                        last_cache_error = e
                    time.sleep(0.3)
                if not item and last_cache_error:
                    logger.warning(f"【夸克】通过缓存ID获取文件信息失败，尝试父目录遍历: {str(last_cache_error)}")

            if not item:
                parent_path = self._normalize_path(str(Path(path_str).parent), is_dir=True)
                if parent_path == ".":
                    parent_path = "/"
                parent_id = self._path_to_id(parent_path)
                if parent_id is None:
                    return None

                target_name = Path(path_str).name
                page = 1
                size = 100
                while True:
                    resp = self._request(
                        "/file/sort",
                        method="GET",
                        params={
                            "pr": "ucpro",
                            "fr": "pc",
                            "uc_param_str": "",
                            "pdir_fid": parent_id,
                            "_page": page,
                            "_size": size,
                            "_fetch_total": 1,
                            "_fetch_sub_dirs": 1,
                            "_sort": "file_type:asc,file_name:asc",
                        },
                        use_drive=True,
                    )
                    item_list = resp.get("data", {}).get("list", [])
                    item = next(
                        (sub_item for sub_item in item_list if sub_item.get("file_name") == target_name),
                        None,
                    )
                    if item or len(item_list) < size:
                        break
                    page += 1
            if not item:
                self._get_item_fail_records[path_str] = self._get_item_fail_records.get(path_str, 0) + 1
                return None

            self._get_item_fail_records.pop(path_str, None)
            is_dir = self._is_directory(item)
            normalized_path = self._normalize_path(path_str, is_dir=is_dir)
            cache_key = normalized_path[:-1] if is_dir and normalized_path != "/" else normalized_path
            self._id_cache.add_cache(str(item["fid"]), cache_key)
            return schemas.FileItem(
                storage=self._disk_name,
                fileid=str(item["fid"]),
                parent_fileid=str(item.get("parent_id") or item.get("pdir_fid") or "0"),
                name=item["file_name"],
                basename=Path(item["file_name"]).stem,
                extension=Path(item["file_name"]).suffix[1:] if not is_dir and Path(item["file_name"]).suffix else None,
                type="dir" if is_dir else "file",
                path=normalized_path,
                size=item.get("size") if not is_dir else None,
                modify_time=int(item.get("modified_time") or item.get("updated_at") or 0),
                pickcode=str(item),
            )
        except Exception as e:
            logger.error(f"【夸克】获取文件信息失败: {str(e)}")
            self._get_item_fail_records[path_str] = self._get_item_fail_records.get(path_str, 0) + 1
            return None

    def detail(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取文件详情
        """
        return self.get_item(Path(fileitem.path))

    def get_parent(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取父目录
        """
        try:
            parent_path = self._normalize_path(str(Path(fileitem.path).parent))
            if parent_path == ".":
                parent_path = "/"
            return self.get_item(Path(parent_path))
        except Exception as e:
            logger.error(f"【夸克】获取父目录失败: {str(e)}")
            return None

    def create_folder(self, fileitem: schemas.FileItem, name: str) -> Optional[schemas.FileItem]:
        """
        创建文件夹
        """
        try:
            target_path = self._join_path(fileitem.path, name, is_dir=True)
            parent_id = self._path_to_id(fileitem.path)
            if not parent_id:
                return None
            resp = self._request(
                "/file",
                method="POST",
                json_data={
                    "dir_init_lock": False,
                    "dir_path": "",
                    "file_name": name,
                    "pdir_fid": parent_id,
                },
            )
            item = resp.get("data")
            if item:
                try:
                    created_item = self._file_to_item(fileitem.path, item)
                    if created_item:
                        return created_item
                except Exception as e:
                    logger.warning(f"【夸克】解析创建目录返回数据失败，尝试回查目录: {str(e)}")

            time.sleep(0.5)
            return self.get_item(Path(target_path))
        except Exception as e:
            logger.error(f"【夸克】创建文件夹失败: {str(e)}")
            return None

    def get_folder(self, path: Path) -> Optional[schemas.FileItem]:
        """
        获取目录，如目录不存在则创建
        """

        def __find_dir(parent_item: schemas.FileItem, dir_name: str) -> Optional[schemas.FileItem]:
            for sub_item in self.list(parent_item):
                if sub_item.type == "dir" and sub_item.name == dir_name:
                    return sub_item
            return None

        try:
            normalized_path = self._normalize_path(str(path), is_dir=True)
            folder = self.get_item(Path(normalized_path))
            if folder and folder.type == "dir":
                return folder

            current_item = schemas.FileItem(
                storage=self._disk_name,
                fileid="0",
                parent_fileid=None,
                name="/",
                basename="/",
                extension=None,
                type="dir",
                path="/",
                size=None,
                modify_time=None,
                pickcode=None,
            )

            for part in Path(normalized_path).parts[1:]:
                dir_item = __find_dir(current_item, part)
                if not dir_item:
                    dir_item = self.create_folder(current_item, part)
                    if not dir_item:
                        dir_item = self.get_item(Path(self._join_path(current_item.path, part, is_dir=True)))
                if not dir_item:
                    logger.error(f"【夸克】获取目录失败，无法创建目录: {normalized_path}")
                    return None
                current_item = dir_item

            return current_item
        except Exception as e:
            logger.error(f"【夸克】获取目录失败: {str(e)}")
            return None

    def upload(self, fileitem: schemas.FileItem, path: Path, new_name: Optional[str] = None) -> Optional[schemas.FileItem]:
        """
        上传文件
        """
        try:
            if not path.exists() or not path.is_file():
                logger.error(f"【夸克】上传文件不存在: {path}")
                return None

            parent_id = self._path_to_id(fileitem.path)
            if not parent_id:
                return None

            target_name = new_name or path.name
            file_size = path.stat().st_size
            now_ms = int(time.time() * 1000)
            md5_hex, sha1_hex = self._calculate_hashes(path)
            format_type = mimetypes.guess_type(target_name)[0] or ""
            if not format_type and Path(target_name).suffix.lower() == ".nfo":
                format_type = "text/xml"
            mime_type = format_type or "application/octet-stream"
            target_path = self._join_path(fileitem.path, target_name)

            def _build_uploaded_item(fid: Optional[str] = None) -> schemas.FileItem:
                return schemas.FileItem(
                    storage=self._disk_name,
                    fileid=str(fid or ""),
                    parent_fileid=str(parent_id),
                    name=target_name,
                    basename=Path(target_name).stem,
                    extension=Path(target_name).suffix[1:] if Path(target_name).suffix else None,
                    type="file",
                    path=target_path,
                    size=file_size,
                    modify_time=int(time.time()),
                    pickcode="",
                )

            pre_resp = self._request(
                "/file/upload/pre",
                method="POST",
                json_data={
                    "ccp_hash_update": True,
                    "dir_name": "",
                    "file_name": target_name,
                    "format_type": format_type,
                    "l_created_at": now_ms,
                    "l_updated_at": now_ms,
                    "pdir_fid": parent_id,
                    "size": file_size,
                },
            )

            pre_data = pre_resp.get("data")
            metadata = pre_resp.get("metadata") or {}
            if not pre_data:
                logger.error(f"【夸克】上传预检未返回 data: name={target_name}, size={file_size}, format_type={format_type!r}")
                return None

            if pre_data.get("finish"):
                uploaded_item = self.get_item(Path(target_path))
                if uploaded_item:
                    return uploaded_item
                fid = pre_data.get("fid")
                if fid:
                    self._id_cache.add_cache(str(fid), target_path)
                return _build_uploaded_item(fid=fid)

            hash_resp = self._request(
                "/file/update/hash",
                method="POST",
                json_data={
                    "md5": md5_hex,
                    "sha1": sha1_hex,
                    "task_id": pre_data.get("task_id"),
                },
            )

            hash_data = hash_resp.get("data") or {}
            if hash_data.get("finish"):
                uploaded_item = self.get_item(Path(target_path))
                if uploaded_item:
                    return uploaded_item
                fid = hash_data.get("fid") or pre_data.get("fid")
                if fid:
                    self._id_cache.add_cache(str(fid), target_path)
                return _build_uploaded_item(fid=fid)

            part_size = int(metadata.get("part_size") or self._default_part_size)
            if part_size <= 0:
                part_size = self._default_part_size
            etags = self._upload_parts(
                local_path=path,
                pre_data=pre_data,
                part_size=part_size,
                mime_type=mime_type,
            )
            if not etags:
                logger.error(f"【夸克】上传分片结果为空: name={target_name}")
                return None

            if not self._commit_upload(pre_data=pre_data, etags=etags):
                logger.error(f"【夸克】上传提交失败: name={target_name}")
                return None

            self._request(
                "/file/upload/finish",
                method="POST",
                json_data={
                    "obj_key": pre_data.get("obj_key"),
                    "task_id": pre_data.get("task_id"),
                },
            )

            time.sleep(1)
            uploaded_item = self.get_item(Path(target_path))
            if uploaded_item:
                return uploaded_item

            fid = pre_data.get("fid") or hash_data.get("fid")
            if fid:
                self._id_cache.add_cache(str(fid), target_path)
            return _build_uploaded_item(fid=fid)
        except Exception as e:
            logger.error(f"【夸克】上传文件失败: {str(e)}")
            return None

    def _calculate_hashes(self, path: Path) -> tuple[str, str]:
        md5_hasher = hashlib.md5()
        sha1_hasher = hashlib.sha1()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                if chunk:
                    md5_hasher.update(chunk)
                    sha1_hasher.update(chunk)
        return md5_hasher.hexdigest(), sha1_hasher.hexdigest()

    def _build_oss_url(self, pre_data: Dict[str, Any]) -> str:
        bucket = pre_data.get("bucket")
        upload_url = pre_data.get("upload_url") or ""
        obj_key = pre_data.get("obj_key")
        if not all([bucket, upload_url, obj_key]):
            raise Exception("OSS 上传地址参数不完整")
        if upload_url.startswith("http://"):
            suffix = upload_url[7:]
        elif upload_url.startswith("https://"):
            suffix = upload_url[8:]
        else:
            suffix = upload_url
        return f"https://{bucket}.{suffix}/{obj_key}"

    def _build_auth_meta(
        self,
        method: str,
        content_md5: str,
        content_type: str,
        date_str: str,
        extra_headers: Dict[str, str],
        bucket: str,
        obj_key: str,
        query_string: str,
    ) -> str:
        canonical_lines = [method, content_md5, content_type, date_str]
        for key in sorted(extra_headers.keys()):
            canonical_lines.append(f"{key}:{extra_headers[key]}")
        canonical_lines.append(f"/{bucket}/{obj_key}?{query_string}")
        return "\n".join(canonical_lines)

    @staticmethod
    def _http_gmt_date() -> str:
        """
        生成标准 HTTP-date / GMT 时间，格式示例：Sat, 18 Apr 2026 08:20:48 GMT
        """
        return format_date_time(time.time())

    def _request_upload_auth(self, pre_data: Dict[str, Any], auth_meta: str) -> str:
        resp = self._request(
            "/file/upload/auth",
            method="POST",
            json_data={
                "auth_info": pre_data.get("auth_info"),
                "auth_meta": auth_meta,
                "task_id": pre_data.get("task_id"),
            },
        )
        auth_key = (resp.get("data") or {}).get("auth_key")
        if not auth_key:
            raise Exception("获取上传鉴权失败")
        return auth_key

    def _upload_parts(
        self,
        local_path: Path,
        pre_data: Dict[str, Any],
        part_size: int,
        mime_type: str,
    ) -> List[str]:
        etags: List[str] = []
        bucket = pre_data.get("bucket")
        obj_key = pre_data.get("obj_key")
        upload_url = pre_data.get("upload_url")
        upload_id = pre_data.get("upload_id")
        if not all([bucket, obj_key, upload_url, upload_id]):
            raise Exception("上传预检返回信息不完整")

        target_url = self._build_oss_url(pre_data)

        with open(local_path, "rb") as handle:
            part_number = 1
            while True:
                chunk = handle.read(part_size)
                if not chunk:
                    break

                time_str = self._http_gmt_date()
                signed_headers = {
                    "x-oss-date": time_str,
                    "x-oss-user-agent": "aliyun-sdk-js/1.0.0 Microsoft Edge 142.0.0.0 on Windows 10 64-bit",
                }
                auth_meta = self._build_auth_meta(
                    method="PUT",
                    content_md5="",
                    content_type=mime_type,
                    date_str=time_str,
                    extra_headers=signed_headers,
                    bucket=bucket,
                    obj_key=obj_key,
                    query_string=f"partNumber={part_number}&uploadId={upload_id}",
                )
                auth_key = self._request_upload_auth(pre_data=pre_data, auth_meta=auth_meta)

                response = requests.put(
                    target_url,
                    params={"partNumber": part_number, "uploadId": upload_id},
                    headers={
                        "Authorization": auth_key,
                        "Content-Type": mime_type,
                        "Referer": "https://pan.quark.cn/",
                        "x-oss-date": time_str,
                        "x-oss-user-agent": signed_headers["x-oss-user-agent"],
                    },
                    data=chunk,
                    timeout=max(self._timeout, 120),
                )
                if response.status_code != 200:
                    raise Exception(f"分片上传失败: part={part_number}, status={response.status_code}, body={response.text}")

                etag = response.headers.get("Etag") or response.headers.get("ETag")
                if not etag:
                    raise Exception(f"分片上传缺少 ETag: part={part_number}")
                etags.append(etag)
                part_number += 1

        return etags

    def _commit_upload(self, pre_data: Dict[str, Any], etags: List[str]) -> bool:
        callback_info = pre_data.get("callback") or {}
        bucket = pre_data.get("bucket")
        obj_key = pre_data.get("obj_key")
        upload_url = pre_data.get("upload_url")
        upload_id = pre_data.get("upload_id")
        if not all([bucket, obj_key, upload_url, upload_id]):
            raise Exception("上传提交参数不完整")

        xml_body = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<CompleteMultipartUpload>"]
        for index, etag in enumerate(etags, start=1):
            xml_body.extend(
                [
                    "<Part>",
                    f"<PartNumber>{index}</PartNumber>",
                    f"<ETag>{escape(etag)}</ETag>",
                    "</Part>",
                ]
            )
        xml_body.append("</CompleteMultipartUpload>")
        body = "\n".join(xml_body)
        content_md5 = base64.b64encode(hashlib.md5(body.encode("utf-8")).digest()).decode("utf-8")
        callback_base64 = base64.b64encode(json.dumps(callback_info, ensure_ascii=False).encode("utf-8")).decode("utf-8")

        time_str = self._http_gmt_date()
        signed_headers = {
            "x-oss-callback": callback_base64,
            "x-oss-date": time_str,
            "x-oss-user-agent": "aliyun-sdk-js/1.0.0 Microsoft Edge 142.0.0.0 on Windows 10 64-bit",
        }
        auth_meta = self._build_auth_meta(
            method="POST",
            content_md5=content_md5,
            content_type="application/xml",
            date_str=time_str,
            extra_headers=signed_headers,
            bucket=bucket,
            obj_key=obj_key,
            query_string=f"uploadId={upload_id}",
        )
        auth_key = self._request_upload_auth(pre_data=pre_data, auth_meta=auth_meta)

        target_url = self._build_oss_url(pre_data)
        response = requests.post(
            target_url,
            params={"uploadId": upload_id},
            headers={
                "Authorization": auth_key,
                "Content-MD5": content_md5,
                "Content-Type": "application/xml",
                "Referer": "https://pan.quark.cn/",
                "x-oss-callback": callback_base64,
                "x-oss-date": time_str,
                "x-oss-user-agent": signed_headers["x-oss-user-agent"],
            },
            data=body.encode("utf-8"),
            timeout=max(self._timeout, 120),
        )
        if response.status_code != 200:
            raise Exception(f"上传提交失败: status={response.status_code}, body={response.text}")
        return True

    def download(self, fileitem: schemas.FileItem, path: Path = None) -> Optional[Path]:
        """
        下载文件
        """
        local_path = path
        try:
            current_item = self.get_item(Path(fileitem.path))
            if current_item:
                fileitem = current_item

            if fileitem.type != "file":
                logger.error(f"【夸克】下载失败，目标不是文件: path={fileitem.path}, type={fileitem.type}")
                return None

            file_id = str(fileitem.fileid) if getattr(fileitem, "fileid", None) else None
            if not file_id:
                parent_path = self._normalize_path(str(Path(fileitem.path).parent), is_dir=True)
                if parent_path == ".":
                    parent_path = "/"
                parent_id = self._path_to_id(parent_path)
                if parent_id:
                    resp = self._request(
                        "/file/sort",
                        method="GET",
                        params={
                            "uc_param_str": "",
                            "pdir_fid": parent_id,
                            "_page": 1,
                            "_size": 100,
                            "_fetch_total": 1,
                            "_fetch_sub_dirs": 1,
                            "_sort": "file_type:asc,file_name:asc",
                        },
                        use_drive=True,
                    )
                    target_name = Path(fileitem.path).name
                    matched_item = next(
                        (item for item in resp.get("data", {}).get("list", []) if item.get("file_name") == target_name),
                        None,
                    )
                    if matched_item:
                        file_id = str(matched_item.get("fid"))
            if not file_id:
                logger.error(f"【夸克】下载失败，无法获取文件ID: {fileitem.path}")
                return None

            # 获取下载地址
            resp = self._request(
                "/file/download",
                method="POST",
                json_data={"fids": [file_id]},
                use_drive=True,
            )
            download_data = resp.get("data") or []
            if isinstance(download_data, dict):
                download_data = [download_data]
            if not download_data:
                logger.error(f"【夸克】下载失败，下载接口未返回数据: fid={file_id}, resp={resp}")
                return None

            download_url = (
                download_data[0].get("download_url")
                or download_data[0].get("url")
                or download_data[0].get("DownloadUrl")
            )
            if not download_url:
                logger.error(f"【夸克】下载失败，下载链接为空: fid={file_id}, data={download_data[0]}")
                return None

            # 下载文件
            local_path = path or (Path(settings.TEMP_PATH) / fileitem.name)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"【夸克】开始下载: {fileitem.name} -> {local_path}")

            resp = requests.get(
                download_url,
                headers={
                    "User-Agent": self._headers.get("User-Agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Referer": "https://pan.quark.cn/",
                    "Cookie": self._cookie,
                    "Accept": "*/*",
                },
                stream=True,
                timeout=max(self._timeout, 120),
            )
            if resp.status_code != 200:
                logger.error(f"【夸克】下载失败，请求下载链接返回异常: status={resp.status_code}")
                return None

            # 保存文件
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return local_path
        except Exception as e:
            if local_path and local_path.exists():
                local_path.unlink(missing_ok=True)
            logger.error(f"【夸克】下载文件失败: {str(e)}")
            return None

    def delete(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        删除文件
        """
        try:
            file_id = self._path_to_id(fileitem.path)
            if not file_id:
                return None
            self._request(
                "/file/delete",
                method="POST",
                json_data={
                    "action_type": 1,
                    "exclude_fids": [],
                    "filelist": [file_id],
                },
            )
            self._id_cache.remove(file_id=file_id)
            return True
        except Exception as e:
            logger.error(f"【夸克】删除文件失败: {str(e)}")
            return None

    def rename(self, fileitem: schemas.FileItem, name: str) -> Optional[bool]:
        """
        重命名文件
        """
        try:
            file_id = fileitem.fileid or self._path_to_id(fileitem.path)
            if not file_id:
                return None
            self._request(
                "/file/rename",
                method="POST",
                json_data={
                    "fid": file_id,
                    "file_name": name,
                },
                use_drive=True,
            )
            self._id_cache.remove(file_id=file_id)
            new_path = self._join_path(str(Path(fileitem.path).parent), name, is_dir=fileitem.type == "dir")
            self._id_cache.add_cache(file_id, new_path[:-1] if fileitem.type == "dir" and new_path != "/" else new_path)
            return True
        except Exception as e:
            logger.error(f"【夸克】重命名文件失败: {str(e)}")
            return None

    def copy(self, fileitem: schemas.FileItem, path: Path, new_name: str) -> bool:
        """
        复制文件或目录
        """
        logger.warning(
            "【夸克】当前未确认支持复制接口，跳过 copy 操作: %s -> %s/%s",
            fileitem.path,
            path,
            new_name,
        )
        return False

    def move(self, fileitem: schemas.FileItem, path: Path, new_name: str) -> bool:
        """
        移动文件或目录
        """
        try:
            target_parent_id = self._path_to_id(str(path))
            if not target_parent_id:
                return False
            source_id = fileitem.fileid or self._path_to_id(fileitem.path)
            if not source_id:
                return False
            self._request(
                "/file/move",
                method="POST",
                json_data={
                    "action_type": 1,
                    "exclude_fids": [],
                    "filelist": [source_id],
                    "to_pdir_fid": target_parent_id,
                },
            )
            self._id_cache.remove(file_id=source_id)

            moved_path = self._join_path(str(path), fileitem.name, is_dir=fileitem.type == "dir")
            self._id_cache.add_cache(
                str(source_id),
                moved_path[:-1] if fileitem.type == "dir" and moved_path != "/" else moved_path,
            )

            if new_name and new_name != fileitem.name:
                moved_item = schemas.FileItem(
                    storage=self._disk_name,
                    fileid=str(source_id),
                    parent_fileid=str(target_parent_id),
                    name=fileitem.name,
                    basename=Path(fileitem.name).stem,
                    extension=fileitem.extension,
                    type=fileitem.type,
                    path=moved_path,
                    size=fileitem.size,
                    modify_time=fileitem.modify_time,
                    pickcode=fileitem.pickcode,
                )
                return bool(self.rename(moved_item, new_name))

            return True
        except Exception as e:
            logger.error(f"【夸克】移动文件失败: {str(e)}")
            return False

    def usage(self) -> Optional[schemas.StorageUsage]:
        """
        获取存储空间使用情况
        """
        try:
            resp = self._request(
                "/member",
                method="GET",
                params={
                    "uc_param_str": "",
                    "fetch_subscribe": "true",
                    "_ch": "home",
                    "fetch_identity": "true",
                },
                use_drive_pc=True,
            )
            data = resp.get("data")
            if not data:
                return None
            total_capacity = int(data.get("total_capacity") or data.get("secret_total_capacity") or 0)
            used_capacity = int(data.get("use_capacity") or data.get("secret_use_capacity") or 0)
            if total_capacity <= 0:
                return None
            available_capacity = max(total_capacity - used_capacity, 0)
            return schemas.StorageUsage(
                total=total_capacity,
                available=available_capacity,
            )
        except Exception as e:
            logger.error(f"【夸克】获取存储空间使用情况失败: {str(e)}")
            return None 

    def support_transtype(self) -> dict:
        """
        支持的整理方式
        """
        return self.transtype

    def is_support_transtype(self, transtype: str) -> bool:
        """
        是否支持整理方式
        """
        return transtype in self.transtype

    def clear_cache(self):
        """
        清理缓存
        """
        self._id_cache.clear()
        self._get_item_fail_records.clear()