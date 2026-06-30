"""
夸克网盘基础操作类
"""

import hashlib
import mimetypes
import requests
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app import schemas
from app.core.config import global_vars, settings
from app.log import logger
from app.modules.filemanager.storages import transfer_process

from .quark_client import QuarkClient


class QuarkApi:
    """
    夸克网盘基础操作类
    """

    ROOT_FID = "0"

    _id_cache: Dict[str, str] = {}
    _item_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        client: QuarkClient,
        disk_name: str,
        page_size: int = 50,
        sort_field: str = "file_name",
        sort_order: str = "asc",
    ):
        """
        初始化夸克网盘操作实例。
        """
        self.client = client
        self._disk_name = disk_name
        self._page_size = page_size or 50
        self._sort_field = sort_field
        self._sort_order = sort_order
        self.transtype = {"move": "移动", "copy": "复制"}
        self._id_cache["/"] = self.ROOT_FID

    # ==================== 路径与缓存工具 ====================

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        规范化路径格式。
        """
        normalized = str(path or "/").replace("\\", "/")
        if normalized in ("", "."):
            return "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        normalized = normalized.rstrip("/") or "/"
        return normalized

    def _build_path(self, parent_path: str, name: str, is_dir: bool) -> str:
        """
        根据父路径和名称构建完整路径。
        """
        normalized_parent = self._normalize_path(parent_path)
        item_path = (
            f"{normalized_parent.rstrip('/')}/{name}"
            if normalized_parent != "/"
            else f"/{name}"
        )
        return item_path + ("/" if is_dir else "")

    @staticmethod
    def _normalize_fileid(fileid: Optional[str], path: Optional[str] = None) -> str:
        """
        规范化文件 ID。
        """
        normalized_fileid = str(fileid or "")
        normalized_path = str(path or "").replace("\\", "/")
        if (normalized_fileid in ("root", "0") and normalized_path in ("", "/")):
            return "0"
        if not normalized_fileid:
            return "0"
        return normalized_fileid

    def _cache_item(self, item: schemas.FileItem) -> None:
        """
        缓存文件项与路径映射。
        """
        normalized_path = self._normalize_path(item.path)
        normalized_fileid = self._normalize_fileid(item.fileid, normalized_path)
        if normalized_path != "/" and normalized_fileid:
            self._id_cache[normalized_path] = normalized_fileid
        self._item_cache[normalized_path] = {
            "storage": item.storage,
            "fileid": normalized_fileid,
            "parent_fileid": str(item.parent_fileid or "0"),
            "name": item.name,
            "basename": item.basename,
            "extension": item.extension,
            "type": item.type,
            "path": item.path,
            "size": item.size,
            "modify_time": item.modify_time,
            "thumbnail": getattr(item, "thumbnail", None),
            "pickcode": item.pickcode,
            "drive_id": getattr(item, "drive_id", None),
        }

    def _invalidate_path_cache(self, path: str) -> None:
        """
        失效指定路径相关缓存。
        """
        normalized_path = self._normalize_path(path)
        self._id_cache.pop(normalized_path, None)
        self._item_cache.pop(normalized_path, None)
        dir_key = normalized_path if normalized_path == "/" else f"{normalized_path.rstrip('/')}/"
        file_key = normalized_path.rstrip("/") or "/"
        self._id_cache.pop(dir_key, None)
        self._item_cache.pop(dir_key, None)
        self._id_cache.pop(file_key, None)
        self._item_cache.pop(file_key, None)

    def _cache_path_id(self, path: str, file_id: str) -> None:
        """
        缓存路径与文件 ID 的映射关系。
        """
        normalized_path = self._normalize_path(path)
        normalized_fileid = self._normalize_fileid(file_id, normalized_path)
        if normalized_path != "/" and normalized_fileid:
            self._id_cache[normalized_path] = normalized_fileid

    # ==================== 响应解析工具 ====================

    @staticmethod
    def _is_success(resp: Dict[str, Any]) -> bool:
        """
        判断接口响应是否成功。
        """
        if not isinstance(resp, dict):
            return False
        status = resp.get("status")
        code = resp.get("code")
        return status in (200, "200", None) or code in (0, "0", 200, "200", None)

    @staticmethod
    def _get_data(resp: Dict[str, Any]) -> Any:
        """
        提取响应中的 data 数据。
        """
        if not isinstance(resp, dict):
            return {}
        return resp.get("data") or {}

    @staticmethod
    def _first_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
        """
        按候选字段顺序获取首个有效值。
        """
        for key in keys:
            if isinstance(data, dict) and data.get(key) is not None:
                return data.get(key)
        return default

    @staticmethod
    def _parse_time(value: Any) -> Optional[float]:
        """
        解析时间字段为时间戳（秒）。
        """
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return value / 1000 if value > 9999999999 else value
        if isinstance(value, str):
            try:
                if value.isdigit():
                    num = int(value)
                    return num / 1000 if num > 9999999999 else num
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).timestamp()
            except Exception:
                return None
        return None

    def _extract_list(self, resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从响应中提取列表数据。
        """
        data = self._get_data(resp)
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        for key in ("list", "files", "items", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []

    def _find_number(self, data: Any, keys: List[str]) -> Optional[float]:
        """
        在嵌套数据中查找数值字段。
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key in keys and value not in (None, ""):
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        pass
            for value in data.values():
                found = self._find_number(value, keys)
                if found is not None:
                    return found
        elif isinstance(data, list):
            for value in data:
                found = self._find_number(value, keys)
                if found is not None:
                    return found
        return None

    # ==================== FileItem 转换 ====================

    def _to_file_item(
        self, item: Dict[str, Any], parent_path: str = "/"
    ) -> schemas.FileItem:
        """
        将夸克 API 原始文件数据转换为 FileItem。
        """
        file_id = str(self._first_value(item, ["fid", "file_id", "id"], "0"))
        parent_id = str(self._first_value(item, ["pdir_fid", "parent_fid", "parent_file_id"], "0"))
        name = self._first_value(item, ["file_name", "name", "filename"], "") or ""
        is_dir = bool(
            item.get("dir")
            or item.get("is_dir")
            or item.get("file_type") == 0
        )
        if item.get("file_type") not in (None, 0):
            is_dir = False

        path = (
            f"{parent_path.rstrip('/')}/{name}"
            if parent_path != "/"
            else f"/{name}"
        )
        file_path = path + ("/" if is_dir else "")
        size = self._first_value(item, ["size", "file_size", "fileSize"], None)
        modify_time = self._parse_time(
            self._first_value(item, ["updated_at", "update_time", "modify_time", "mtime"])
        )

        if file_id and file_id != "0":
            self._id_cache[path] = file_id
            if is_dir:
                self._id_cache[file_path.rstrip("/")] = file_id

        file_item = schemas.FileItem(
            storage=self._disk_name,
            fileid=file_id,
            parent_fileid=parent_id,
            name=name,
            basename=Path(name).stem,
            extension=(
                Path(name).suffix[1:] if not is_dir and Path(name).suffix else None
            ),
            type="dir" if is_dir else "file",
            path=file_path,
            size=int(size) if size not in (None, "") and not is_dir else None,
            modify_time=modify_time,
            thumbnail=self._build_thumbnail_url(item),
            pickcode=str(item),
            drive_id=str(self._first_value(item, ["md5", "sha1", "hash"], "")) or None,
        )
        self._cache_item(file_item)
        return file_item

    @staticmethod
    def _build_thumbnail_url(item: Dict[str, Any]) -> Optional[str]:
        """
        构造缩略图代理 URL。夸克 API 返回的 thumbnail 是直连 URL，
        浏览器因无 Cookie 会 401，改为走插件 API 代理。
        """
        fid = item.get("fid") or item.get("file_id")
        obj_category = item.get("obj_category", "")
        if fid and obj_category in ("video",):
            return f"/api/v1/plugin/QuarkDisk/thumb?fid={fid}"
        return item.get("thumbnail") or item.get("thumb") or item.get("cover") or None

    # ==================== 路径解析 ====================

    def _path_to_id(self, path: str) -> str:
        """
        根据路径解析对应的文件 ID。
        """
        normalized_path = self._normalize_path(path)
        if normalized_path == "/":
            return self.ROOT_FID
        if normalized_path in self._id_cache:
            return self._id_cache[normalized_path]

        current_id = self.ROOT_FID
        current_path = "/"
        parts = Path(normalized_path).parts[1:]
        for part in parts:
            found = None
            parent_item = schemas.FileItem(
                storage=self._disk_name,
                fileid=current_id,
                path=current_path,
                type="dir",
            )
            for item in self.list(parent_item):
                if item.name == part:
                    found = item
                    break
            if not found:
                raise FileNotFoundError(f"【夸克网盘】{normalized_path} 不存在")
            current_id = found.fileid or self.ROOT_FID
            current_path = found.path if found.type == "dir" else str(Path(found.path).parent)
        self._id_cache[normalized_path] = current_id
        return current_id

    # ==================== 文件操作 ====================

    def list(
        self, fileitem: schemas.FileItem, page: int = 1, page_size: int = 50
    ) -> List[schemas.FileItem]:
        """
        获取目录下的文件列表。
        """
        if fileitem.type == "file":
            item = self.detail(fileitem)
            return [item] if item else []

        if fileitem.path == "/":
            file_id = self.ROOT_FID
        else:
            file_id = fileitem.fileid or self._path_to_id(fileitem.path)

        items: List[schemas.FileItem] = []
        try:
            response = self.client.get_file_list(
                pdir_fid=file_id,
                page=page,
                size=max(page_size, self._page_size),
                sort_field=self._sort_field,
                sort_order=self._sort_order,
            )
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】获取文件列表失败: {response}")
                return items
            for raw in self._extract_list(response):
                items.append(self._to_file_item(raw, fileitem.path or "/"))
        except Exception as err:
            logger.error(f"【夸克网盘】获取文件列表异常: {err}")
        return items

    def detail(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取文件详情。
        """
        if fileitem.path:
            item = self.get_item(Path(fileitem.path))
            if item:
                return item
        return fileitem if fileitem.fileid else None

    def create_folder(
        self, fileitem: schemas.FileItem, name: str
    ) -> Optional[schemas.FileItem]:
        """
        在指定目录下创建文件夹。
        """
        try:
            new_path = Path(fileitem.path) / name
            parent_id = fileitem.fileid or self._path_to_id(fileitem.path)
            response = self.client.create_folder(
                folder_name=name,
                parent_id=parent_id or self.ROOT_FID,
            )
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】创建目录失败: {response}")
                return None
            data = self._get_data(response)
            file_id = str(self._first_value(data, ["fid", "file_id", "id"], ""))
            self._id_cache[str(new_path).replace("\\", "/")] = file_id
            folder_item = schemas.FileItem(
                storage=self._disk_name,
                fileid=file_id,
                parent_fileid=parent_id,
                path=str(new_path).replace("\\", "/") + "/",
                name=name,
                basename=name,
                type="dir",
                modify_time=int(datetime.now().timestamp()),
                pickcode=str(data),
            )
            self._cache_item(folder_item)
            return folder_item
        except Exception as err:
            logger.error(f"【夸克网盘】创建目录异常: {err}")
            return None

    def get_folder(self, path: Path) -> Optional[schemas.FileItem]:
        """
        获取目录，不存在时自动创建。
        """
        folder = self.get_item(path)
        if folder:
            return folder

        current = schemas.FileItem(
            storage=self._disk_name,
            path="/",
            fileid=self.ROOT_FID,
            type="dir",
        )
        for part in path.parts[1:]:
            next_folder = None
            for sub_folder in self.list(current):
                if sub_folder.type == "dir" and sub_folder.name == part:
                    next_folder = sub_folder
                    break
            if not next_folder:
                next_folder = self.create_folder(current, part)
            if not next_folder:
                logger.warning(f"【夸克网盘】创建目录 {current.path}{part} 失败！")
                return None
            current = next_folder
        return current

    def get_item(self, path: Path) -> Optional[schemas.FileItem]:
        """
        按路径获取单个文件项。
        """
        normalized = self._normalize_path(str(path))
        if normalized == "/":
            root_item = schemas.FileItem(
                storage=self._disk_name,
                path="/",
                fileid=self.ROOT_FID,
                name=self._disk_name,
                basename=self._disk_name,
                type="dir",
            )
            self._cache_item(root_item)
            return root_item

        cached = self._item_cache.get(normalized)
        if cached:
            return schemas.FileItem(**cached)

        try:
            parent_path = path.parent if path.parent.as_posix() else Path("/")
            parent_id = self._path_to_id(parent_path.as_posix())
            parent = schemas.FileItem(
                storage=self._disk_name,
                path=parent_path.as_posix() if parent_path.as_posix() != "." else "/",
                fileid=parent_id,
                type="dir",
            )
            target_name = path.name
            for item in self.list(parent):
                if item.name == target_name:
                    return item
            return None
        except FileNotFoundError:
            return None
        except Exception as err:
            logger.error(f"【夸克网盘】获取文件信息异常: {err}")
            return None

    def get_parent(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取文件项的父目录。
        """
        return self.get_item(Path(fileitem.path).parent)

    def delete(self, fileitem: schemas.FileItem, permanently_delete: bool = False) -> bool:
        """
        删除文件或目录。
        """
        try:
            file_id = fileitem.fileid or self._path_to_id(fileitem.path)
            if file_id == self.ROOT_FID:
                logger.warning("【夸克网盘】不能删除根目录")
                return False
            response = self.client.delete_files([file_id])
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】删除文件失败: {response}")
                return False
            if permanently_delete:
                self._permanent_delete_from_recycle([file_id], fileitem.name)
            self._invalidate_path_cache(fileitem.path)
            return True
        except Exception as err:
            logger.error(f"【夸克网盘】删除文件异常: {err}")
            return False

    def _permanent_delete_from_recycle(self, file_ids: List[str], file_name: str = "") -> None:
        """
        在文件进入回收站后，从回收站中彻底删除。
        先按 fid 匹配，匹配不到则按文件名兜底（回收站按删除时间倒序，取最近一条）。
        """
        try:
            # 等待回收站列表刷新
            import time
            time.sleep(1.5)

            response = self.client.get_recycle_list(page=1, size=100, sort="move_recycle_at:desc")
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】查询回收站失败，无法彻底删除: {response}")
                return

            data = self._get_data(response) or {}
            recycle_list = data.get("list", []) if isinstance(data, dict) else []

            # 优先按 fid 匹配
            record_ids = [
                str(item.get("record_id"))
                for item in recycle_list
                if item.get("fid") in file_ids and item.get("record_id")
            ]

            # fid 匹配不到，按文件名兜底（取最近一条）
            if not record_ids and file_name:
                for item in recycle_list:
                    if item.get("file_name") == file_name and item.get("record_id"):
                        record_ids = [str(item.get("record_id"))]
                        logger.info(
                            f"【夸克网盘】fid 未匹配到回收站记录，按文件名兜底匹配: "
                            f"{file_name}, record_id={record_ids[0]}"
                        )
                        break

            if not record_ids:
                # 打印回收站前几条记录便于排查
                sample = [
                    {"fid": i.get("fid"), "file_name": i.get("file_name"), "record_id": i.get("record_id")}
                    for i in recycle_list[:5]
                ]
                logger.warning(
                    f"【夸克网盘】回收站中未找到刚删除的文件，跳过彻底删除。"
                    f"待匹配 fid={file_ids}, name={file_name}, 回收站前5条={sample}"
                )
                return

            remove_resp = self.client.remove_files_from_recycle(record_ids)
            if not self._is_success(remove_resp):
                logger.warning(f"【夸克网盘】彻底删除失败: {remove_resp}")
            else:
                logger.info(f"【夸克网盘】已彻底删除 {len(record_ids)} 个文件")
        except Exception as err:
            logger.error(f"【夸克网盘】彻底删除异常: {err}")

    def rename(self, fileitem: schemas.FileItem, name: str) -> bool:
        """
        重命名文件或目录。
        """
        try:
            file_id = fileitem.fileid or self._path_to_id(fileitem.path)
            response = self.client.rename_file(fid=file_id, new_name=name)
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】重命名失败: {response}")
                return False
            self._invalidate_path_cache(fileitem.path)
            return True
        except Exception as err:
            logger.error(f"【夸克网盘】重命名异常: {err}")
            return False

    # ==================== 下载 ====================

    def _get_download_url(self, fileitem: schemas.FileItem) -> Optional[str]:
        """
        获取文件下载链接。
        """
        file_id = fileitem.fileid or self._path_to_id(fileitem.path)
        response = self.client.get_download_url(file_id)
        if self._is_success(response):
            data = self._get_data(response)
            if isinstance(data, list) and data:
                first_entry = data[0]
                download_url = first_entry.get("download_url", "")
                if download_url:
                    return download_url
            elif isinstance(data, dict):
                download_url = data.get("download_url", "")
                if download_url:
                    return download_url
        logger.error(f"【夸克网盘】获取下载链接失败: {response}")
        return None

    def download(
        self, fileitem: schemas.FileItem, path: Path = None
    ) -> Optional[Path]:
        """
        下载文件到本地路径（参考 plugins.v2/quarkdisk 简洁实现）。
        """
        local_path = None
        try:
            # 1. 刷新文件信息，确保有 fileid
            current_item = self.get_item(Path(fileitem.path))
            if current_item:
                fileitem = current_item

            if fileitem.type != "file":
                logger.error(
                    f"【夸克网盘】下载失败，目标不是文件: path={fileitem.path}, type={fileitem.type}"
                )
                return None

            # 2. 获取下载地址
            download_url = self._get_download_url(fileitem)
            if not download_url:
                logger.error(f"【夸克网盘】下载失败，无法获取下载链接: {fileitem.path}")
                return None

            # 3. 准备本地路径
            local_path = path or (Path(settings.TEMP_PATH) / fileitem.name)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            if local_path.exists():
                local_path.unlink()

            logger.info(f"【夸克网盘】开始下载: {fileitem.name} -> {local_path}")

            # 4. 下载文件（与 v2 一致的最简请求头）
            resp = requests.get(
                download_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Referer": "https://pan.quark.cn/",
                    "Cookie": self.client.cookie or "",
                    "Accept": "*/*",
                },
                stream=True,
                timeout=120,
            )
            if resp.status_code != 200:
                logger.error(
                    f"【夸克网盘】下载失败，请求下载链接返回异常: status={resp.status_code}, body={resp.text[:200]}"
                )
                return None

            # 5. 保存文件
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return local_path
        except Exception as e:
            if local_path and local_path.exists():
                local_path.unlink(missing_ok=True)
            logger.error(f"【夸克网盘】下载文件失败: {e}")
            return None

    # ==================== 上传 ====================

    @staticmethod
    def _calculate_file_hashes(file_path: Path) -> tuple:
        """
        计算文件的 MD5 和 SHA1 哈希值。
        """
        md5_hash = hashlib.md5()
        sha1_hash = hashlib.sha1()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                md5_hash.update(chunk)
                sha1_hash.update(chunk)
        return md5_hash.hexdigest(), sha1_hash.hexdigest()

    @staticmethod
    def _calculate_incremental_hash_context(
        file_path: Path, part_number: int, part_size: int
    ) -> str:
        """
        计算分片的增量哈希上下文。
        """
        import base64
        import json as json_module
        import struct

        chunk_size = 4 * 1024 * 1024
        processed_bytes = (part_number - 1) * chunk_size
        processed_bits = processed_bytes * 8

        with open(file_path, "rb") as f:
            previous_data = f.read(processed_bytes)

        h0, h1, h2, h3, h4 = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0
        data_len = len(previous_data)
        for i in range(0, data_len - (data_len % 64), 64):
            block = previous_data[i : i + 64]
            w = []
            for j in range(0, 64, 4):
                w.append(struct.unpack(">I", block[j : j + 4])[0])
            for t in range(16, 80):
                val = w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16]
                w.append(((val << 1) | (val >> 31)) & 0xFFFFFFFF)
            a, b, c, d, e = h0, h1, h2, h3, h4
            for t in range(80):
                if t < 20:
                    f = (b & c) | ((~b) & d)
                    k = 0x5A827999
                elif t < 40:
                    f = b ^ c ^ d
                    k = 0x6ED9EBA1
                elif t < 60:
                    f = (b & c) | (b & d) | (c & d)
                    k = 0x8F1BBCDC
                else:
                    f = b ^ c ^ d
                    k = 0xCA62C1D6
                temp = (((a << 5) | (a >> 27)) + f + e + k + w[t]) & 0xFFFFFFFF
                e, d, c, b, a = d, c, ((b << 30) | (b >> 2)) & 0xFFFFFFFF, a, temp
            h0 = (h0 + a) & 0xFFFFFFFF
            h1 = (h1 + b) & 0xFFFFFFFF
            h2 = (h2 + c) & 0xFFFFFFFF
            h3 = (h3 + d) & 0xFFFFFFFF
            h4 = (h4 + e) & 0xFFFFFFFF

        hash_context = {
            "hash_type": "sha1",
            "h0": str(h0),
            "h1": str(h1),
            "h2": str(h2),
            "h3": str(h3),
            "h4": str(h4),
            "Nl": str(processed_bits),
            "Nh": "0",
            "data": "",
            "num": "0",
        }
        hash_json = json_module.dumps(hash_context, separators=(",", ":"))
        return base64.b64encode(hash_json.encode("utf-8")).decode("utf-8")

    def _confirm_uploaded_item(
        self, target_path: Path, retry: int = 20, interval: float = 0.5
    ) -> Optional[schemas.FileItem]:
        """
        确认上传后的文件在云盘中可见。
        """
        target_path = Path(target_path)
        for index in range(retry):
            parent_path = target_path.parent if target_path.parent.as_posix() else Path("/")
            parent_id = self._path_to_id(parent_path.as_posix())
            parent = schemas.FileItem(
                storage=self._disk_name,
                path=parent_path.as_posix() if parent_path.as_posix() != "." else "/",
                fileid=parent_id,
                type="dir",
            )
            for item in self.list(parent):
                if item.name == target_path.name:
                    return item
            self._id_cache.pop(target_path.as_posix(), None)
            if index < retry - 1:
                time.sleep(interval)
        return None

    def _upload_single_file(
        self,
        file_path: Path,
        task_id: str,
        auth_info: str,
        upload_id: str,
        obj_key: str,
        bucket: str,
        mime_type: str,
        callback_info: Dict[str, Any],
        progress_callback: Callable,
    ) -> bool:
        """
        单分片上传（< 5MB 文件）。
        """
        from datetime import datetime, timezone
        import base64
        import json as json_module

        oss_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

        # 1. 获取上传授权
        auth_meta = (
            f"PUT\n\n{mime_type}\n{oss_date}\n"
            f"x-oss-date:{oss_date}\n"
            f"x-oss-user-agent:aliyun-sdk-js/1.0.0 Chrome Mobile 139.0.0.0 on Google Nexus 5 (Android 6.0)\n"
            f"/{bucket}/{obj_key}?partNumber=1&uploadId={upload_id}"
        )
        auth_result = self.client.get_upload_auth(task_id, auth_info, auth_meta)
        if not self._is_success(auth_result):
            logger.error(f"【夸克网盘】获取上传授权失败: {auth_result}")
            return False

        auth_data = self._get_data(auth_result)
        auth_key = auth_data.get("auth_key", "")
        upload_url = f"https://{bucket}.pds.quark.cn/{obj_key}?partNumber=1&uploadId={upload_id}"

        headers = {
            "Content-Type": mime_type,
            "x-oss-date": oss_date,
            "x-oss-user-agent": "aliyun-sdk-js/1.0.0 Chrome Mobile 139.0.0.0 on Google Nexus 5 (Android 6.0)",
        }
        if auth_key:
            headers["authorization"] = auth_key

        # 2. 上传文件到 OSS
        progress_callback(50)
        with open(file_path, "rb") as f:
            file_data = f.read()
        etag = self.client.upload_part_to_oss(upload_url, file_data, headers)
        if not etag:
            logger.error("【夸克网盘】单分片上传失败：未获取到 ETag")
            return False

        # 3. POST 完成合并
        progress_callback(70)
        xml_data = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f"<CompleteMultipartUpload>\n<Part>\n<PartNumber>1</PartNumber>\n"
            f'<ETag>"{etag}"</ETag>\n</Part>\n</CompleteMultipartUpload>'
        )

        if not callback_info:
            logger.error("【夸克网盘】callback 信息缺失")
            return False

        time.sleep(0.1)
        oss_date_post = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        xml_md5 = base64.b64encode(
            hashlib.md5(xml_data.encode("utf-8")).digest()
        ).decode("utf-8")
        callback_b64 = base64.b64encode(
            json_module.dumps(callback_info, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")

        post_auth_meta = (
            f"POST\n{xml_md5}\napplication/xml\n{oss_date_post}\n"
            f"x-oss-callback:{callback_b64}\n"
            f"x-oss-date:{oss_date_post}\n"
            f"x-oss-user-agent:aliyun-sdk-js/1.0.0 Chrome 139.0.0.0 on OS X 10.15.7 64-bit\n"
            f"/{bucket}/{obj_key}?uploadId={upload_id}"
        )

        post_auth_result = self.client.get_upload_auth(task_id, auth_info, post_auth_meta)
        if not self._is_success(post_auth_result):
            logger.error(f"【夸克网盘】获取 POST 合并授权失败: {post_auth_result}")
            return False

        post_auth_data = self._get_data(post_auth_result)
        post_auth_key = post_auth_data.get("auth_key", "")
        post_upload_url = f"https://{bucket}.pds.quark.cn/{obj_key}?uploadId={upload_id}"

        post_headers = {
            "Content-Type": "application/xml",
            "x-oss-date": oss_date_post,
            "x-oss-user-agent": "aliyun-sdk-js/1.0.0 Chrome 139.0.0.0 on OS X 10.15.7 64-bit",
            "authorization": post_auth_key,
            "x-oss-callback": callback_b64,
            "Content-MD5": xml_md5,
        }

        progress_callback(85)
        return self.client.post_complete_upload(post_upload_url, xml_data, post_headers)

    def _upload_multiple_parts(
        self,
        file_path: Path,
        task_id: str,
        auth_info: str,
        upload_id: str,
        obj_key: str,
        bucket: str,
        mime_type: str,
        callback_info: Dict[str, Any],
        progress_callback: Callable,
    ) -> bool:
        """
        多分片上传（>= 5MB 文件）。
        """
        from datetime import datetime, timezone
        import base64
        import json as json_module

        file_size = file_path.stat().st_size
        chunk_size = 4 * 1024 * 1024

        parts = []
        remaining = file_size
        part_num = 1
        while remaining > 0:
            current_size = min(chunk_size, remaining)
            parts.append((part_num, current_size))
            remaining -= current_size
            part_num += 1

        uploaded_parts = []
        base_progress = 35
        progress_per_part = 45 / max(len(parts), 1)

        for i, (part_number, part_size) in enumerate(parts):
            current_progress = base_progress + int(i * progress_per_part)
            progress_callback(current_progress)

            max_retries = 3
            retry_count = 0
            while retry_count <= max_retries:
                try:
                    oss_date = datetime.now(timezone.utc).strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    )
                    hash_ctx = ""
                    if part_number > 1:
                        hash_ctx = self._calculate_incremental_hash_context(
                            file_path, part_number, part_size
                        )

                    if hash_ctx:
                        auth_meta = (
                            f"PUT\n\n{mime_type}\n{oss_date}\n"
                            f"x-oss-date:{oss_date}\n"
                            f"x-oss-hash-ctx:{hash_ctx}\n"
                            f"x-oss-user-agent:aliyun-sdk-js/1.0.0 Chrome Mobile 139.0.0.0 on Google Nexus 5 (Android 6.0)\n"
                            f"/{bucket}/{obj_key}?partNumber={part_number}&uploadId={upload_id}"
                        )
                    else:
                        auth_meta = (
                            f"PUT\n\n{mime_type}\n{oss_date}\n"
                            f"x-oss-date:{oss_date}\n"
                            f"x-oss-user-agent:aliyun-sdk-js/1.0.0 Chrome Mobile 139.0.0.0 on Google Nexus 5 (Android 6.0)\n"
                            f"/{bucket}/{obj_key}?partNumber={part_number}&uploadId={upload_id}"
                        )

                    auth_result = self.client.get_upload_auth(
                        task_id, auth_info, auth_meta
                    )
                    if not self._is_success(auth_result):
                        raise Exception(
                            f"获取分片 {part_number} 上传授权失败: {auth_result}"
                        )

                    auth_data = self._get_data(auth_result)
                    auth_key = auth_data.get("auth_key", "")
                    upload_url = f"https://{bucket}.pds.quark.cn/{obj_key}?partNumber={part_number}&uploadId={upload_id}"

                    headers = {
                        "Content-Type": mime_type,
                        "x-oss-date": oss_date,
                        "x-oss-user-agent": "aliyun-sdk-js/1.0.0 Chrome Mobile 139.0.0.0 on Google Nexus 5 (Android 6.0)",
                    }
                    if auth_key:
                        headers["authorization"] = auth_key
                    if hash_ctx:
                        headers["X-Oss-Hash-Ctx"] = hash_ctx

                    offset = (part_number - 1) * chunk_size
                    with open(file_path, "rb") as f:
                        f.seek(offset)
                        part_data = f.read(part_size)

                    etag = self.client.upload_part_to_oss(upload_url, part_data, headers)
                    if not etag:
                        raise Exception(f"分片 {part_number} 上传失败：未获取到 ETag")

                    uploaded_parts.append((part_number, etag))
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(
                            f"【夸克网盘】分片 {part_number} 上传失败，已重试 {max_retries} 次: {e}"
                        )
                        return False
                    time.sleep(min(2**retry_count, 10))

        # POST 完成合并
        progress_callback(80)
        xml_parts_list = []
        for part_number, etag in uploaded_parts:
            xml_parts_list.append(
                f"<Part>\n<PartNumber>{part_number}</PartNumber>\n<ETag>\"{etag}\"</ETag>\n</Part>"
            )
        xml_data = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n<CompleteMultipartUpload>\n'
            + "\n".join(xml_parts_list)
            + "\n</CompleteMultipartUpload>"
        )

        if not callback_info:
            logger.error("【夸克网盘】callback 信息缺失")
            return False

        time.sleep(0.1)
        oss_date_post = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        xml_md5 = base64.b64encode(
            hashlib.md5(xml_data.encode("utf-8")).digest()
        ).decode("utf-8")
        callback_b64 = base64.b64encode(
            json_module.dumps(callback_info, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")

        post_auth_meta = (
            f"POST\n{xml_md5}\napplication/xml\n{oss_date_post}\n"
            f"x-oss-callback:{callback_b64}\n"
            f"x-oss-date:{oss_date_post}\n"
            f"x-oss-user-agent:aliyun-sdk-js/1.0.0 Chrome 139.0.0.0 on OS X 10.15.7 64-bit\n"
            f"/{bucket}/{obj_key}?uploadId={upload_id}"
        )

        post_auth_result = self.client.get_upload_auth(
            task_id, auth_info, post_auth_meta
        )
        if not self._is_success(post_auth_result):
            logger.error(f"【夸克网盘】获取 POST 合并授权失败: {post_auth_result}")
            return False

        post_auth_data = self._get_data(post_auth_result)
        post_auth_key = post_auth_data.get("auth_key", "")
        post_upload_url = f"https://{bucket}.pds.quark.cn/{obj_key}?uploadId={upload_id}"

        post_headers = {
            "Content-Type": "application/xml",
            "x-oss-date": oss_date_post,
            "x-oss-user-agent": "aliyun-sdk-js/1.0.0 Chrome 139.0.0.0 on OS X 10.15.7 64-bit",
            "authorization": post_auth_key,
            "x-oss-callback": callback_b64,
            "Content-MD5": xml_md5,
        }

        return self.client.post_complete_upload(post_upload_url, xml_data, post_headers)

    def upload(
        self,
        target_dir: schemas.FileItem,
        local_path: Path,
        new_name: Optional[str] = None,
    ) -> Optional[schemas.FileItem]:
        """
        上传本地文件到目标目录。
        """
        if local_path.is_dir():
            return self.upload_folder(target_dir, local_path, new_name)

        target_name = new_name or local_path.name
        target_path = Path(target_dir.path) / target_name
        parent_id = target_dir.fileid or self._path_to_id(target_dir.path)

        try:
            progress_callback = transfer_process(local_path.as_posix())
            file_size = local_path.stat().st_size

            mime_type, _ = mimetypes.guess_type(str(local_path))
            if not mime_type:
                mime_type = "application/octet-stream"

            # 计算文件哈希
            md5_hash, sha1_hash = self._calculate_file_hashes(local_path)

            # 步骤1: 预上传请求
            progress_callback(10)
            pre_upload_result = self.client.pre_upload(
                file_name=target_name,
                file_size=file_size,
                parent_folder_id=parent_id or self.ROOT_FID,
                mime_type=mime_type,
            )
            if not self._is_success(pre_upload_result):
                logger.error(f"【夸克网盘】预上传失败: {pre_upload_result}")
                return None

            pre_data = self._get_data(pre_upload_result)
            task_id = pre_data.get("task_id", "")
            auth_info = pre_data.get("auth_info", "")
            upload_id = pre_data.get("upload_id", "")
            obj_key = pre_data.get("obj_key", "")
            bucket = pre_data.get("bucket", "ul-zb")
            callback_info = pre_data.get("callback", {})

            if not task_id:
                logger.error("【夸克网盘】预上传失败：未获取到任务ID")
                return None

            # 步骤2: 更新文件哈希（秒传检测）
            progress_callback(20)
            hash_result = self.client.update_file_hash(task_id, md5_hash, sha1_hash)
            hash_data = self._get_data(hash_result)
            if hash_data.get("finish"):
                # 秒传成功
                progress_callback(100)
                visible_item = self._confirm_uploaded_item(target_path, retry=10, interval=0.3)
                if visible_item:
                    return visible_item

            # 步骤3: 上传文件
            if file_size < 5 * 1024 * 1024:
                # 单分片上传
                progress_callback(30)
                success = self._upload_single_file(
                    file_path=local_path,
                    task_id=task_id,
                    auth_info=auth_info,
                    upload_id=upload_id,
                    obj_key=obj_key,
                    bucket=bucket,
                    mime_type=mime_type,
                    callback_info=callback_info,
                    progress_callback=progress_callback,
                )
            else:
                # 多分片上传
                progress_callback(30)
                success = self._upload_multiple_parts(
                    file_path=local_path,
                    task_id=task_id,
                    auth_info=auth_info,
                    upload_id=upload_id,
                    obj_key=obj_key,
                    bucket=bucket,
                    mime_type=mime_type,
                    callback_info=callback_info,
                    progress_callback=progress_callback,
                )

            if not success:
                logger.error("【夸克网盘】文件上传到 OSS 失败")
                return None

            # 步骤4: 完成上传（传入 obj_key 与 QuarkPan 保持一致）
            progress_callback(95)
            self.client.finish_upload(task_id, obj_key=obj_key)
            progress_callback(100)

            # 确认文件在云盘中可见
            visible_item = self._confirm_uploaded_item(target_path)
            if visible_item:
                return visible_item

            # 构造上传后的文件项
            return schemas.FileItem(
                storage=self._disk_name,
                fileid="",
                parent_fileid=parent_id,
                path=Path(target_path).as_posix(),
                type="file",
                name=target_name,
                basename=Path(target_name).stem,
                extension=Path(target_name).suffix[1:] if Path(target_name).suffix else None,
                size=file_size,
                modify_time=int(datetime.now().timestamp()),
                pickcode="",
            )
        except Exception as err:
            logger.error(f"【夸克网盘】上传失败: {target_name} - {err}")
            return None

    def upload_folder(
        self,
        target_dir: schemas.FileItem,
        local_path: Path,
        new_name: Optional[str] = None,
    ) -> Optional[schemas.FileItem]:
        """
        递归上传本地文件夹。
        """
        folder_name = new_name or local_path.name
        cloud_folder = self.create_folder(target_dir, folder_name)
        if not cloud_folder:
            return None
        for child in local_path.iterdir():
            if global_vars.is_transfer_stopped(child.as_posix()):
                return None
            if child.is_dir():
                if not self.upload_folder(cloud_folder, child):
                    return None
            else:
                if not self.upload(cloud_folder, child):
                    return None
        return cloud_folder

    # ==================== 分享管理 ====================

    def create_share(
        self,
        file_ids: List[str],
        title: str = "",
        expire_days: int = 0,
        password: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        创建分享链接。
        """
        try:
            response = self.client.create_share(
                file_ids=file_ids,
                title=title,
                expire_days=expire_days,
                password=password,
            )
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】创建分享失败: {response}")
                return None
            task_id = (response.get("data") or {}).get("task_id")
            if not task_id:
                return None
            task_result = self.client.wait_for_task(task_id, timeout=30)
            if task_result.get("status") != 200:
                return None
            share_id = (task_result.get("data") or {}).get("share_id")
            if not share_id:
                return None
            detail = self.client.get_share_details(share_id)
            if self._is_success(detail):
                return self._get_data(detail)
            return None
        except Exception as err:
            logger.error(f"【夸克网盘】创建分享异常: {err}")
            return None

    def get_my_shares(self, page: int = 1, size: int = 50) -> List[Dict[str, Any]]:
        """
        获取我的分享列表。
        """
        try:
            response = self.client.get_my_shares(page=page, size=size)
            if not self._is_success(response):
                logger.warning(f"【夸克网盘】获取分享列表失败: {response}")
                return []
            return self._extract_list(response)
        except Exception as err:
            logger.error(f"【夸克网盘】获取分享列表异常: {err}")
            return []

    def delete_share(self, share_id: str) -> bool:
        """
        删除分享。
        """
        try:
            response = self.client.delete_share(share_id)
            return self._is_success(response)
        except Exception as err:
            logger.error(f"【夸克网盘】删除分享异常: {err}")
            return False

    def parse_share_url(self, share_url: str) -> Dict[str, Any]:
        """
        解析分享链接。
        """
        return self.client.parse_share_url(share_url)

    def save_share_url(
        self,
        share_url: str,
        target_folder: schemas.FileItem,
        save_all: bool = True,
        wait_for_completion: bool = True,
        timeout: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """
        解析分享链接并转存到目标目录。
        """
        try:
            target_folder_id = target_folder.fileid or self._path_to_id(
                target_folder.path
            )
            result = self.client.parse_and_save(
                share_url=share_url,
                target_folder_id=target_folder_id,
                save_all=save_all,
                wait_for_completion=wait_for_completion,
                timeout=timeout,
            )
            if not self._is_success(result):
                logger.warning(f"【夸克网盘】转存分享失败: {result}")
                return None
            self._invalidate_path_cache(target_folder.path)
            return result
        except Exception as err:
            logger.error(f"【夸克网盘】转存分享异常: {err}")
            return None

    # ==================== 移动/复制 ====================

    def _copy_and_delete(
        self,
        fileitem: schemas.FileItem,
        target_parent: Path,
        target_name: str,
    ) -> bool:
        """
        copy 方式回退：下载 → 上传 → 删除源文件。
        用于夸克 move API 不支持的系统创建文件夹场景。
        """
        try:
            # 1. 下载到临时目录
            local_path = self.download(fileitem)
            if not local_path:
                logger.error(f"【夸克网盘】copy+delete 失败：下载文件失败")
                return False

            # 2. 构建目标 FileItem
            target_file_path = f"{target_parent.as_posix()}/{target_name}"
            target_fileitem = schemas.FileItem(
                storage=self._disk_name,
                path=target_file_path,
                type="file",
                name=target_name,
                size=local_path.stat().st_size,
            )

            # 3. 上传到目标目录
            result = self.upload(fileitem=target_fileitem, path=local_path)
            if not result:
                logger.error(f"【夸克网盘】copy+delete 失败：上传文件失败")
                local_path.unlink(missing_ok=True)
                return False

            # 4. 删除源文件
            delete_result = self.delete(fileitem)
            if not delete_result:
                logger.warning(f"【夸克网盘】copy+delete：文件已复制但源文件删除失败，请手动清理: {fileitem.path}")

            local_path.unlink(missing_ok=True)
            return True
        except Exception as err:
            logger.error(f"【夸克网盘】copy+delete 异常: {err}")
            return False

    def move(
        self, fileitem: schemas.FileItem, path: Path, new_name: str = None
    ) -> bool:
        """
        移动文件到目标目录。
        """
        try:
            target_parent = Path(path)
            source_path = Path(fileitem.path)
            current_name = fileitem.name or source_path.name
            target_name = new_name or current_name

            if target_parent.as_posix() == source_path.parent.as_posix():
                if target_name == current_name:
                    return True
                return self.rename(fileitem, target_name)

            target_id = self._path_to_id(target_parent.as_posix())
            file_id = fileitem.fileid or self._path_to_id(fileitem.path)
            response = self.client.move_files([file_id], target_id)
            if not self._is_success(response):
                # 部分文件夹（如系统创建/转存目录）不支持 move API，
                # 回退为 copy 方式：下载到本地 → 上传到目标 → 删除源文件
                error_code = response.get("data", {}).get("code") if isinstance(response.get("data"), dict) else None
                error_msg = response.get("message", "")
                if error_code == 23028 or "系统创建" in str(error_msg):
                    logger.info(f"【夸克网盘】move API 不支持该文件夹类型 (code=23028)，改用 copy+delete 方式")
                    return self._copy_and_delete(fileitem, target_parent, target_name)
                logger.warning(f"【夸克网盘】移动文件失败: {response}")
                return False

            task_id = self._get_data(response).get("task_id") if isinstance(self._get_data(response), dict) else None
            if task_id:
                self.client.wait_for_task(task_id, timeout=30)

            self._invalidate_path_cache(fileitem.path)
            # 同步失效源目录缓存，避免 any_files 误判目录仍含媒体文件
            self._invalidate_path_cache(Path(fileitem.path).parent.as_posix())

            if target_name != current_name:
                moved_item = self._confirm_uploaded_item(
                    target_parent / current_name, retry=10, interval=0.3
                )
                if moved_item:
                    return self.rename(moved_item, target_name)
            return True
        except Exception as err:
            logger.error(f"【夸克网盘】移动文件异常: {err}")
            return False

    def copy(
        self, fileitem: schemas.FileItem, path: Path, new_name: str = None
    ) -> bool:
        """
        复制文件到目标目录（通过下载再上传实现）。
        """
        try:
            target_parent = Path(path)
            target_name = new_name or fileitem.name or Path(fileitem.path).name

            target_id = self._path_to_id(target_parent.as_posix())
            file_id = fileitem.fileid or self._path_to_id(fileitem.path)

            # 夸克网盘没有直接的复制 API，使用移动 + 保留源的方式
            # 实际实现：下载文件到临时目录，再上传到目标目录
            local_path = self.download(fileitem, settings.TEMP_PATH)
            if not local_path:
                return False

            target_dir = schemas.FileItem(
                storage=self._disk_name,
                path=target_parent.as_posix(),
                fileid=target_id,
                type="dir",
            )
            uploaded = self.upload(target_dir, local_path, target_name)
            try:
                if local_path.exists():
                    local_path.unlink()
            except Exception:
                pass
            return uploaded is not None
        except Exception as err:
            logger.error(f"【夸克网盘】复制文件异常: {err}")
            return False

    # ==================== 快照/空间 ====================

    def snapshot(self, fileitem: schemas.FileItem) -> List[schemas.FileItem]:
        """
        递归获取目录下全部文件快照。
        """
        result: List[schemas.FileItem] = []

        def _walk(_item: schemas.FileItem):
            for child in self.list(_item):
                if child.type == "dir":
                    _walk(child)
                else:
                    result.append(child)

        _walk(fileitem)
        return result

    def exists(self, fileitem: schemas.FileItem) -> bool:
        """
        判断文件项是否存在。
        """
        return bool(self.get_item(Path(fileitem.path)))

    def usage(self) -> Optional[schemas.StorageUsage]:
        """
        获取存储空间使用情况。
        """
        try:
            response = self.client.get_capacity()
            if not self._is_success(response):
                return schemas.StorageUsage(total=0, available=0)
            data = self._get_data(response)
            total = self._find_number(data, [
                "total_capacity", "total", "totalCapacity", "total_space",
            ])
            used = self._find_number(data, [
                "use_capacity", "used", "useCapacity", "used_space",
            ])
            total = float(total or 0)
            available = max(total - float(used or 0), 0) if total else 0
            return schemas.StorageUsage(total=total, available=float(available or 0))
        except Exception as err:
            logger.warning(f"【夸克网盘】获取空间使用情况失败: {err}")
            return schemas.StorageUsage(total=0, available=0)

    def support_transtype(self) -> dict:
        """
        获取支持的传输类型。
        """
        return self.transtype

    def is_support_transtype(self, transtype: str) -> bool:
        """
        判断是否支持指定传输类型。
        """
        return transtype in self.transtype

    @staticmethod
    def copy_local(src: Path, dst: Path) -> bool:
        """
        本地复制文件或目录。
        """
        try:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            return True
        except Exception:
            return False
