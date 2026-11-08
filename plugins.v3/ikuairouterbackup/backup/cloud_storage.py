"""MP 存储层网盘备份

将爱快备份文件上传到 MoviePilot「存储」（设置→存储与应用 中已配置的网盘，
如夸克网盘 / 115 / OpenList / RClone 等），复用宿主存储抽象：

- StorageHelper（app.helper.storage / app.application.storage）：枚举已配置存储
- StorageChain（app.chain.storage）：get_folder + upload_file + list_files + delete_file

不同 MP v3 版本模块路径有差异，这里做双路径兼容导入，失败时给出明确报错。
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.log import logger


def _import_storage_helper():
    """兼容导入 StorageHelper"""
    try:
        from app.helper.storage import StorageHelper  # noqa
        return StorageHelper
    except Exception:
        pass
    try:
        from app.application.storage import StorageHelper  # noqa
        return StorageHelper
    except Exception:
        return None


def _import_storage_chain():
    """兼容导入 StorageChain"""
    try:
        from app.chain.storage import StorageChain  # noqa
        return StorageChain
    except Exception:
        pass
    try:
        from app.chain import StorageChain  # noqa
        return StorageChain
    except Exception:
        return None


def list_mp_storages() -> List[Dict[str, str]]:
    """
    枚举 MP 中已配置的存储（设置→存储与应用）。
    :return: [{'type': 'quark', 'name': '夸克网盘'}, ...]；失败返回 []
    """
    helper_cls = _import_storage_helper()
    if not helper_cls:
        logger.warning("当前 MoviePilot 版本未找到 StorageHelper，无法枚举存储")
        return []
    try:
        confs = helper_cls().get_storagies() or []
        return [{'type': c.type, 'name': c.name or c.type} for c in confs if c.type]
    except Exception as e:
        logger.warning(f"枚举 MP 存储失败: {e}")
        return []


def upload_backup_file(storage: str, remote_dir: str, local_path: str,
                       filename: str) -> Tuple[bool, Optional[str]]:
    """
    上传备份文件到 MP 配置的网盘存储
    :param storage: 存储类型标识（如 quark / 115 / openlist）
    :param remote_dir: 远端目录（如 /MoviePilot/ikuai_backups）
    :param local_path: 本地文件路径
    :param filename: 上传后的文件名
    :return: (是否成功, 错误信息)
    """
    if not storage:
        return False, "未指定存储类型"
    chain_cls = _import_storage_chain()
    if not chain_cls:
        return False, "当前 MoviePilot 版本未找到 StorageChain，无法上传到网盘"

    local_file = Path(local_path)
    if not local_file.exists():
        return False, f"本地备份文件不存在: {local_path}"

    try:
        chain = chain_cls()
        folder_path = Path(remote_dir or "/")
        folder = chain.get_folder(storage=storage, path=folder_path)
        if folder is None:
            return False, f"在存储 {storage} 上创建目录 {remote_dir} 失败"
        result = chain.upload_file(fileitem=folder, path=local_file, new_name=filename)
        if result is None:
            return False, f"上传文件到存储 {storage} 失败"
        return True, None
    except Exception as e:
        logger.error(f"上传备份到网盘存储 {storage} 失败: {e}")
        return False, str(e)


def list_storage_dir(storage: str, path: str = "") -> Dict[str, Any]:
    """
    浏览 MP 存储的目录（远端目录选择器用）
    :return: {'ok': True, 'path': '/xxx', 'parent': '/yyy', 'dirs': ['a', 'b']}
    """
    if not storage:
        return {"ok": False, "error": "未指定存储类型", "path": "", "parent": "", "dirs": []}
    chain_cls = _import_storage_chain()
    if not chain_cls:
        return {"ok": False, "error": "未找到 StorageChain", "path": "", "parent": "", "dirs": []}
    clean_path = "/" + str(path or "/").strip().strip("/")
    try:
        chain = chain_cls()
        folder = None
        try:
            folder = chain.get_file_item(storage=storage, path=Path(clean_path))
        except Exception as e:
            # 部分存储对不存在/根目录会抛 StorageQueryError，降级到 get_folder
            logger.debug(f"{storage} get_file_item({clean_path}) 失败，降级 get_folder: {e}")
            folder = None
        if not folder:
            folder = chain.get_folder(storage=storage, path=Path(clean_path))
        if folder is None:
            return {"ok": False, "error": f"无法访问存储目录: {clean_path}", "path": "", "parent": "", "dirs": []}
        files = chain.list_files(folder) or []
        dirs = sorted(
            # FileItem 用 type 字段区分 dir/file（部分存储可能不返回 type，非 file 均按目录展示）
            [str(f.name) for f in files if getattr(f, "type", None) != "file" and f.name],
            key=str.lower,
        )
        # 计算上级目录
        if clean_path == "/":
            parent = ""
        else:
            parts = [p for p in clean_path.split("/") if p]
            parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        return {"ok": True, "path": clean_path, "parent": parent, "dirs": dirs}
    except Exception as e:
        logger.error(f"浏览存储 {storage} 目录 {clean_path} 失败: {e}")
        return {"ok": False, "error": str(e), "path": "", "parent": "", "dirs": []}


def list_cloud_backups(storage: str, remote_dir: str) -> List[Dict[str, Any]]:
    """
    列出网盘存储上的备份文件（恢复选择器用）
    :return: [{'filename':..., 'time': mtime时间戳, 'size': 字节}]，失败返回 []
    """
    if not storage:
        return []
    chain_cls = _import_storage_chain()
    if not chain_cls:
        logger.warning("当前 MoviePilot 版本未找到 StorageChain，无法读取网盘备份")
        return []
    try:
        chain = chain_cls()
        folder = None
        try:
            folder = chain.get_file_item(storage=storage, path=Path(remote_dir or "/"))
        except Exception as e:
            logger.debug(f"{storage} get_file_item({remote_dir}) 失败，降级 get_folder: {e}")
            folder = None
        if not folder:
            folder = chain.get_folder(storage=storage, path=Path(remote_dir or "/"))
        if folder is None:
            logger.warning(f"访问网盘存储 {storage} 目录 {remote_dir} 失败")
            return []
        result = []
        for f in (chain.list_files(folder) or []):
            name = str(getattr(f, "name", "") or "")
            if not name or getattr(f, "type", None) == "dir":
                continue
            if not name.lower().endswith(".bak"):
                continue
            mod_time = getattr(f, "modify_time", None) or getattr(f, "ctime", None) or 0
            try:
                mod_time = float(mod_time)
            except (TypeError, ValueError):
                mod_time = 0
            result.append({
                'filename': name,
                'time': mod_time,
                'size': getattr(f, "size", 0) or 0,
            })
        result.sort(key=lambda x: (x['time'], x['filename']), reverse=True)
        return result
    except Exception as e:
        logger.error(f"列出网盘存储 {storage} 备份失败: {e}")
        return []


def download_backup_file(storage: str, remote_dir: str, filename: str,
                         local_path: str) -> Tuple[bool, Optional[str]]:
    """
    从网盘存储下载备份文件到本地临时路径（恢复前用）
    :return: (是否成功, 错误信息)
    """
    if not storage:
        return False, "未指定存储类型"
    chain_cls = _import_storage_chain()
    if not chain_cls:
        return False, "当前 MoviePilot 版本未找到 StorageChain"
    try:
        chain = chain_cls()
        folder = None
        try:
            folder = chain.get_file_item(storage=storage, path=Path(remote_dir or "/"))
        except Exception as e:
            logger.debug(f"{storage} get_file_item({remote_dir}) 失败，降级 get_folder: {e}")
            folder = None
        if not folder:
            folder = chain.get_folder(storage=storage, path=Path(remote_dir or "/"))
        if folder is None:
            return False, f"无法访问存储 {storage} 目录 {remote_dir}"
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)
        result = chain.download_file(fileitem=folder, path=local_file, new_name=filename)
        if result is None:
            return False, f"从存储 {storage} 下载 {filename} 失败"
        if not local_file.exists():
            return False, f"下载后未找到文件: {local_path}"
        return True, None
    except Exception as e:
        logger.error(f"从网盘存储 {storage} 下载备份 {filename} 失败: {e}")
        return False, str(e)


def delete_cloud_backup(storage: str, remote_dir: str, filename: str) -> Tuple[bool, Optional[str]]:
    """
    删除网盘存储上的单个备份文件
    :return: (是否成功, 错误信息)
    """
    if not storage:
        return False, "未指定存储类型"
    chain_cls = _import_storage_chain()
    if not chain_cls:
        return False, "当前 MoviePilot 版本未找到 StorageChain"
    try:
        chain = chain_cls()
        folder = None
        try:
            folder = chain.get_file_item(storage=storage, path=Path(remote_dir or "/"))
        except Exception as e:
            logger.debug(f"{storage} get_file_item({remote_dir}) 失败，降级 get_folder: {e}")
            folder = None
        if not folder:
            folder = chain.get_folder(storage=storage, path=Path(remote_dir or "/"))
        if folder is None:
            return False, f"无法访问存储 {storage} 目录 {remote_dir}"
        target = None
        for f in (chain.list_files(folder) or []):
            if str(getattr(f, "name", "") or "") == filename:
                target = f
                break
        if target is None:
            return False, f"网盘上未找到文件: {filename}"
        ok = chain.delete_file(target)
        if not ok:
            return False, "存储层返回删除失败"
        return True, None
    except Exception as e:
        logger.error(f"删除网盘备份 {storage}/{filename} 失败: {e}")
        return False, str(e)


def cleanup_cloud_backups(storage: str, remote_dir: str, keep_num: int) -> Tuple[int, Optional[str]]:
    """
    清理网盘上的旧备份，按文件名倒序保留最近 keep_num 个 .bak 文件
    :return: (删除数量, 错误信息)
    """
    if not storage or keep_num <= 0:
        return 0, None
    chain_cls = _import_storage_chain()
    if not chain_cls:
        return 0, "未找到 StorageChain"
    try:
        chain = chain_cls()
        folder = chain.get_file_item(storage=storage, path=Path(remote_dir or "/"))
        if folder is None:
            return 0, None
        files = chain.list_files(folder) or []
        bak_files = [
            f for f in files
            if getattr(f, "type", None) != "dir" and str(f.name or "").lower().endswith(".bak")
        ]
        bak_files.sort(key=lambda x: str(x.name or ""), reverse=True)
        deleted = 0
        for f in bak_files[keep_num:]:
            ok = chain.delete_file(f)
            if ok:
                deleted += 1
            else:
                logger.warning(f"删除网盘旧备份失败: {f.name}")
        return deleted, None
    except Exception as e:
        logger.error(f"清理网盘旧备份失败: {e}")
        return 0, str(e)
