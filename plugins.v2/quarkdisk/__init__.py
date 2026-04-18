from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

from app import schemas
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import ChainEventType
from app.helper.storage import StorageHelper
from schemas import StorageOperSelectionEventData, FileItem

from .quark_api import QuarkApi

class QuarkDisk(_PluginBase):
    # 插件名称
    plugin_name = "夸克网盘存储"
    # 插件描述
    plugin_desc = "为存储系统集成夸克网盘支持"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/quark.ico"
    # 插件版本
    plugin_version = "1.1.0"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "quarkdisk_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _cookie = None
    _disk_name = None
    _quark_api = None
    _inited = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _ensure_quark_api(self) -> bool:
        """
        确保 API 客户端已初始化
        """
        if self._quark_api:
            return True
        if not self._enabled or not self._cookie:
            return False
        try:
            logger.info("【夸克】按需初始化API客户端")
            self._quark_api = QuarkApi(cookie=self._cookie)
            return True
        except Exception as e:
            logger.error(f"【夸克】按需初始化API客户端失败: {str(e)}")
            self._quark_api = None
            return False

    def init_plugin(self, config: dict = None):
        if not QuarkDisk._inited:
            logger.info("【夸克】开始初始化插件")
            QuarkDisk._inited = True
        self._disk_name = "夸克网盘"

        if config:
            storage_helper = StorageHelper()
            storages = storage_helper.get_storagies()
            if not any(
                s.type == self._disk_name and s.name == self._disk_name
                for s in storages
            ):
                # 添加云盘存储配置
                logger.info("【夸克】添加存储配置")
                storage_helper.add_storage(
                    storage=self._disk_name, name=self._disk_name, conf={}
                )

            self._enabled = bool(config.get("enabled"))
            self._cookie = (config.get("cookie") or "").strip()
            self._quark_api = None
            
            logger.info(f"【夸克】插件启用状态: {self._enabled}")
            logger.info(f"【夸克】Cookie长度: {len(self._cookie) if self._cookie else 0}")

            if self._enabled and self._cookie:
                try:
                    logger.info("【夸克】开始创建API客户端")
                    self._quark_api = QuarkApi(cookie=self._cookie)
                    logger.info("【夸克】API客户端创建成功")
                except Exception as e:
                    logger.error(f"【夸克】API客户端创建失败: {str(e)}")
            else:
                logger.warning("【夸克】插件未启用或Cookie未设置,跳过API客户端创建")

    def get_state(self) -> bool:
        return bool(self._enabled and self._cookie)

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/clear_cache",
                "endpoint": self.clear_cache,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "清理缓存",
                "description": "清理夸克网盘路径 ID 缓存",
            }
        ]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VCard",
                        "props": {
                            "variant": "flat",
                            "class": "mb-6",
                            "color": "surface",
                        },
                        "content": [
                            {
                                "component": "VCardItem",
                                "props": {"class": "px-6 pb-0"},
                                "content": [
                                    {
                                        "component": "VCardTitle",
                                        "props": {"class": "d-flex align-center text-h6"},
                                        "content": [
                                            {
                                                "component": "VIcon",
                                                "props": {
                                                    "style": "color: #16b1ff;",
                                                    "class": "mr-3",
                                                    "size": "default",
                                                },
                                                "text": "mdi-cog-outline",
                                            },
                                            {
                                                "component": "span",
                                                "text": "基本设置",
                                            },
                                        ],
                                    }
                                ],
                            },
                            {
                                "component": "VDivider",
                                "props": {"class": "mx-4 my-2"},
                            },
                            {
                                "component": "VCardText",
                                "props": {"class": "px-6 pb-6"},
                                "content": [
                                    {
                                        "component": "VRow",
                                        "props": {
                                            "class": "align-center",
                                        },
                                        "content": [
                                            {
                                                "component": "VCol",
                                                "props": {"cols": 12, "sm": 4},
                                                "content": [
                                                    {
                                                        "component": "VSwitch",
                                                        "props": {
                                                            "model": "enabled",
                                                            "label": "启用插件",
                                                            "color": "primary",
                                                            "hide-details": True,
                                                        },
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "component": "VRow",
                                        "content": [
                                            {
                                                "component": "VCol",
                                                "props": {"cols": 12},
                                                "content": [
                                                    {
                                                        "component": "VTextarea",
                                                        "props": {
                                                            "model": "cookie",
                                                            "label": "夸克 Cookie",
                                                            "rows": 3,
                                                            "auto-grow": False,
                                                            "counter": 4000,
                                                            "placeholder": "请输入从 pan.quark.cn 获取到的完整 Cookie",
                                                            "persistent-hint": True,
                                                            "hint": "建议直接粘贴完整请求头中的 Cookie 值，避免缺字段导致列表、下载、上传异常。",
                                                        },
                                                    }
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VCard",
                        "props": {
                            "variant": "flat",
                            "class": "mb-6",
                            "color": "surface",
                        },
                        "content": [
                            {
                                "component": "VCardItem",
                                "props": {"class": "px-6 pb-0"},
                                "content": [
                                    {
                                        "component": "VCardTitle",
                                        "props": {"class": "d-flex align-center text-h6 mb-0"},
                                        "content": [
                                            {
                                                "component": "VIcon",
                                                "props": {
                                                    "style": "color: #16b1ff;",
                                                    "class": "mr-3",
                                                    "size": "default",
                                                },
                                                "text": "mdi-information-outline",
                                            },
                                            {
                                                "component": "span",
                                                "text": "使用说明",
                                            },
                                        ],
                                    }
                                ],
                            },
                            {
                                "component": "VDivider",
                                "props": {"class": "mx-4 my-2"},
                            },
                            {
                                "component": "VCardText",
                                "props": {"class": "px-6 pb-6"},
                                "content": [
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "info",
                                            "variant": "tonal",
                                            "class": "mb-4",
                                            "text": "Cookie 获取步骤：\n"
                                                   "1. 浏览器访问 https://pan.quark.cn 并完成登录；\n"
                                                   "2. 按 F12 打开开发者工具，切换到 Network（网络）标签；\n"
                                                   "3. 在夸克网盘页面点击任意目录或文件，找到 /file/sort、/file/info 等请求；\n"
                                                   "4. 在请求头中复制完整 Cookie；\n"
                                                   "5. 粘贴到上方配置框并保存。",
                                        },
                                    },
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "warning",
                                            "variant": "tonal",
                                            "text": "注意事项：\n"
                                                   "• Cookie 失效后需要重新获取；\n"
                                                   "• 建议使用网页端最新请求复制 Cookie，避免缺少 __puus / __pus 等关键字段；\n"
                                                   "• 如果目录识别异常，可在数据页面使用“清理缓存”按钮。",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "cookie": "",
        }

    def get_page(self) -> List[dict]:
        status_text = "已配置" if self.get_state() else "未配置"
        status_color = "success" if self.get_state() else "warning"

        return [
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VCard",
                                "props": {
                                    "variant": "flat",
                                    "color": "surface",
                                    "class": "h-100",
                                },
                                "content": [
                                    {
                                        "component": "VCardItem",
                                        "content": [
                                            {
                                                "component": "VCardTitle",
                                                "props": {"class": "d-flex align-center text-h6"},
                                                "content": [
                                                    {
                                                        "component": "VIcon",
                                                        "props": {
                                                            "class": "mr-3",
                                                            "color": "info",
                                                        },
                                                        "text": "mdi-cloud-check-outline",
                                                    },
                                                    {
                                                        "component": "span",
                                                        "text": "运行状态",
                                                    },
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "component": "VDivider",
                                        "props": {"class": "mx-4 my-2"},
                                    },
                                    {
                                        "component": "VCardText",
                                        "content": [
                                            {
                                                "component": "VAlert",
                                                "props": {
                                                    "type": status_color,
                                                    "variant": "tonal",
                                                    "text": f"当前状态：{status_text}",
                                                    "class": "mb-4",
                                                },
                                            },
                                            {
                                                "component": "div",
                                                "props": {"class": "text-body-2 text-medium-emphasis"},
                                                "text": "插件用于在 MoviePilot 文件管理中集成夸克网盘的浏览、下载、上传、整理与刮削保存能力。",
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VCard",
                                "props": {
                                    "variant": "flat",
                                    "color": "surface",
                                    "class": "h-100",
                                },
                                "content": [
                                    {
                                        "component": "VCardItem",
                                        "content": [
                                            {
                                                "component": "VCardTitle",
                                                "props": {"class": "d-flex align-center text-h6"},
                                                "content": [
                                                    {
                                                        "component": "VIcon",
                                                        "props": {
                                                            "class": "mr-3",
                                                            "color": "primary",
                                                        },
                                                        "text": "mdi-tools",
                                                    },
                                                    {
                                                        "component": "span",
                                                        "text": "维护工具",
                                                    },
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "component": "VDivider",
                                        "props": {"class": "mx-4 my-2"},
                                    },
                                    {
                                        "component": "VCardText",
                                        "props": {"class": "pa-6 d-flex flex-column align-center"},
                                        "content": [
                                            {
                                                "component": "VBtn",
                                                "props": {
                                                    "color": "primary",
                                                    "variant": "elevated",
                                                    "size": "large",
                                                    "prepend-icon": "mdi-delete-sweep",
                                                    "class": "mb-3",
                                                },
                                                "text": "清理缓存",
                                                "events": {
                                                    "click": {
                                                        "api": "plugin/QuarkDisk/clear_cache",
                                                        "method": "post",
                                                    },
                                                },
                                            },
                                            {
                                                "component": "div",
                                                "props": {"class": "text-caption text-medium-emphasis text-center"},
                                                "text": "清理夸克网盘路径与文件 ID 缓存，适用于移动、重命名或目录结构变化后的识别异常场景。",
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
            {
                "component": "VCard",
                "props": {
                    "variant": "flat",
                    "color": "surface",
                    "class": "mt-6",
                },
                "content": [
                    {
                        "component": "VCardItem",
                        "content": [
                            {
                                "component": "VCardTitle",
                                "props": {"class": "d-flex align-center text-h6"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {"class": "mr-3", "color": "info"},
                                        "text": "mdi-file-document-outline",
                                    },
                                    {
                                        "component": "span",
                                        "text": "功能说明",
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VDivider",
                        "props": {"class": "mx-4 my-2"},
                    },
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "info",
                                    "variant": "tonal",
                                    "text": "当前已适配：文件浏览、图片预览、下载、上传、目录创建、重命名、移动、容量读取、刮削图片/NFO 保存等能力。",
                                    "class": "mb-4",
                                },
                            },
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "warning",
                                    "variant": "tonal",
                                    "text": "如遇到文件刚移动/重命名后暂时查不到、列表不刷新、整理后识别异常等情况，建议优先清理缓存后再试。",
                                },
                            },
                        ],
                    },
                ],
            },
        ]

    def get_module(self) -> Dict[str, Any]:
        """
        获取插件模块声明，用于胁持系统模块实现（方法名：方法实现）
        """
        return {
            "list_files": self.list_files,
            "any_files": self.any_files,
            "download_file": self.download_file,
            "upload_file": self.upload_file,
            "delete_file": self.delete_file,
            "rename_file": self.rename_file,
            "get_folder": self.get_folder,
            "get_file_item": self.get_file_item,
            "get_parent_item": self.get_parent_item,
            "snapshot_storage": self.snapshot_storage,
            "storage_usage": self.storage_usage,
            "support_transtype": self.support_transtype,
            "create_folder": self.create_folder,
            "exists": self.exists,
            "get_item": self.get_item,
        }

    @eventmanager.register(ChainEventType.StorageOperSelection)
    def storage_oper_selection(self, event: Event):
        """
        监听存储选择事件，返回当前类为操作对象
        """
        if not self._enabled:
            return
        event_data: StorageOperSelectionEventData = event.event_data
        if event_data.storage == self._disk_name:
            # 处理云盘的操作
            event_data.storage_oper = self._quark_api

    def list_files(
        self, fileitem: schemas.FileItem, recursion: bool = False
    ) -> Optional[List[schemas.FileItem]]:
        """
        查询当前目录下所有目录和文件
        """
        if fileitem.storage != self._disk_name:
            return None

        # 只保留关键日志
        # logger.info(f"【夸克】开始获取目录 {fileitem.path} 的文件列表")
        # logger.info(f"【夸克】获取到 {len(result)} 个文件")
        # 只保留如下关键日志：
        # logger.info(f"【夸克】获取到 {len(result)} 个文件")
        
        if not self._enabled:
            logger.error("【夸克】插件未启用")
            return None
            
        if not self._cookie:
            logger.error("【夸克】Cookie未设置")
            return None
            
        if not self._ensure_quark_api():
            logger.error("【夸克】API客户端未初始化")
            return None

        def __get_files(_item: schemas.FileItem, _r: Optional[bool] = False):
            """
            递归处理
            """
            _items = self._quark_api.list(_item)
            if _items:
                if _r:
                    for t in _items:
                        result.append(t)
                        if t.type == "dir":
                            __get_files(t, _r)
                else:
                    result.extend(_items)

        # 返回结果
        result = []
        try:
            __get_files(fileitem, recursion)
            logger.info(f"【夸克】获取到 {len(result)} 个文件")
            return result
        except Exception as e:
            logger.error(f"【夸克】获取文件列表失败: {str(e)}")
            return []

    def any_files(
        self, fileitem: schemas.FileItem, extensions: list = None
    ) -> Optional[bool]:
        """
        查询当前目录下是否存在指定扩展名任意文件
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        def __any_file(_item: FileItem):
            """
            递归处理
            """
            _items = self._quark_api.list(_item)
            if _items:
                if not extensions:
                    return True
                for t in _items:
                    if (
                        t.type == "file"
                        and t.extension
                        and f".{t.extension.lower()}" in extensions
                    ):
                        return True
                    elif t.type == "dir":
                        if __any_file(t):
                            return True
            return False

        # 返回结果
        return __any_file(fileitem)

    def create_folder(
        self, fileitem: schemas.FileItem, name: str
    ) -> Optional[schemas.FileItem]:
        """
        创建目录
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.create_folder(fileitem=fileitem, name=name)

    def get_folder(self, storage: str, path: Path) -> Optional[schemas.FileItem]:
        """
        获取目录，不存在则递归创建
        """
        if storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.get_folder(path)

    def download_file(
        self, fileitem: schemas.FileItem, path: Path = None
    ) -> Optional[Path]:
        """
        下载文件
        :param fileitem: 文件项
        :param path: 本地保存路径
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.download(fileitem, path)

    def upload_file(
        self, fileitem: schemas.FileItem, path: Path, new_name: Optional[str] = None
    ) -> Optional[schemas.FileItem]:
        """
        上传文件
        :param fileitem: 保存目录项
        :param path: 本地文件路径
        :param new_name: 新文件名
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.upload(fileitem, path, new_name)

    def delete_file(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        删除文件或目录
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.delete(fileitem)

    def rename_file(self, fileitem: schemas.FileItem, name: str) -> Optional[bool]:
        """
        重命名文件或目录
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.rename(fileitem, name)

    def exists(self, fileitem: schemas.FileItem) -> Optional[bool]:
        """
        判断文件或目录是否存在
        """
        if fileitem.storage != self._disk_name:
            return None

        return True if self.get_item(fileitem) else False

    def get_item(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        查询目录或文件
        """
        if fileitem.storage != self._disk_name:
            return None

        return self.get_file_item(storage=fileitem.storage, path=Path(fileitem.path))

    def get_file_item(self, storage: str, path: Path) -> Optional[schemas.FileItem]:
        """
        根据路径获取文件项
        """
        if storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.get_item(path)

    def get_parent_item(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取上级目录项
        """
        if fileitem.storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.get_parent(fileitem)

    def snapshot_storage(self, storage: str, path: Path) -> Optional[Dict[str, float]]:
        """
        快照存储
        """
        if storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        files_info = {}

        def __snapshot_file(_fileitm: schemas.FileItem):
            """
            递归获取文件信息
            """
            if _fileitm.type == "dir":
                for sub_file in self._quark_api.list(_fileitm):
                    __snapshot_file(sub_file)
            else:
                files_info[_fileitm.path] = _fileitm.size

        fileitem = self._quark_api.get_item(path)
        if not fileitem:
            return {}

        __snapshot_file(fileitem)

        return files_info

    def storage_usage(self, storage: str) -> Optional[schemas.StorageUsage]:
        """
        存储使用情况
        """
        if storage != self._disk_name:
            return None

        if not self._ensure_quark_api():
            return None

        return self._quark_api.usage()

    def support_transtype(self, storage: str) -> Optional[dict]:
        """
        获取支持的整理方式
        """
        if storage != self._disk_name:
            return None

        return {"move": "移动", "copy": "复制"}

    def clear_cache(self) -> Dict[str, Any]:
        """
        清理缓存
        """
        try:
            if not self._quark_api:
                return {
                    "code": 1,
                    "msg": "插件未启用或未初始化",
                }

            self._quark_api.clear_cache()
            logger.info("【夸克】缓存清理成功")
            return {
                "code": 0,
                "msg": "缓存清理成功",
            }
        except Exception as e:
            logger.error(f"【夸克】缓存清理失败: {e}", exc_info=True)
            return {
                "code": 1,
                "msg": f"缓存清理失败: {str(e)}",
            }

    def stop_service(self):
        """
        退出插件
        """
        pass 