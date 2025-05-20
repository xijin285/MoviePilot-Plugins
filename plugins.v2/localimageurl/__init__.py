import os
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType

class LocalImageUrl(_PluginBase):
    # 插件名称
    plugin_name = "本地图片URL映射"
    # 插件描述
    plugin_desc = "将本地图片文件映射为可访问的URL链接，支持多个目录映射。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/sitemonitor.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "localimageurl_"
    # 加载顺序
    plugin_order = 20
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _app: Optional[FastAPI] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False

    # 配置属性
    _enabled: bool = False
    _image_paths: List[str] = []
    _url_prefix: str = "/images"
    _notify: bool = False
    _supported_extensions: List[str] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()

        if config:
            self._enabled = bool(config.get("enabled", False))
            self._notify = bool(config.get("notify", False))
            paths = config.get("image_paths", "")
            self._image_paths = [p.strip() for p in paths.split(',') if p.strip()] if isinstance(paths, str) else []
            self._url_prefix = str(config.get("url_prefix", "/images")).strip().rstrip('/')
            
            # 验证和规范化路径
            valid_paths = []
            for path in self._image_paths:
                try:
                    abs_path = os.path.abspath(path)
                    if os.path.exists(abs_path):
                        valid_paths.append(abs_path)
                    else:
                        logger.warning(f"{self.plugin_name} 路径不存在: {path}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} 处理路径时出错 {path}: {str(e)}")
            self._image_paths = valid_paths

            if self._enabled and not self._image_paths:
                logger.warning(f"{self.plugin_name} 已启用但未配置有效的图片目录")

            self.__update_config()

        if self._enabled:
            self._init_fastapi_routes()

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """返回命令列表"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """返回API列表"""
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        """返回服务列表"""
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回表单配置"""
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件'}}]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '发送通知'}}]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'image_paths',
                                            'label': '图片目录',
                                            'placeholder': '输入图片目录路径，多个目录用英文逗号分隔',
                                            'rows': 3
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'url_prefix',
                                            'label': 'URL前缀',
                                            'placeholder': '例如: /images'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '说明：\n1. 图片目录支持配置多个，用英文逗号分隔\n2. 支持的图片格式：jpg, jpeg, png, gif, bmp, webp\n3. URL前缀将用于生成访问链接\n4. 访问格式：http(s)://your-domain{url_prefix}/目录名/图片名称\n5. 目录名使用实际目录的最后一级名称'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "notify": False,
            "image_paths": "",
            "url_prefix": "/images"
        }

    def get_page(self) -> List[dict]:
        """返回页面配置"""
        if not self._enabled or not self._image_paths:
            return [
                {
                    'component': 'VAlert',
                    'props': {
                        'type': 'info',
                        'variant': 'tonal',
                        'text': '插件未启用或未配置图片目录。',
                        'class': 'mb-2'
                    }
                }
            ]

        directories_info = []
        total_files = 0
        base_url = f"{settings.HOST}{self._url_prefix}"

        for path in self._image_paths:
            try:
                dir_name = os.path.basename(path)
                image_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) 
                             and os.path.splitext(f)[1].lower() in self._supported_extensions]
                total_files += len(image_files)
                
                sample_images = image_files[:3]  # 只显示前3个文件作为示例
                sample_urls = [f"{base_url}/{quote(dir_name)}/{quote(img)}" for img in sample_images]
                
                directories_info.append({
                    'dir_name': dir_name,
                    'path': path,
                    'file_count': len(image_files),
                    'sample_urls': sample_urls
                })
            except Exception as e:
                logger.error(f"{self.plugin_name} 处理目录 {path} 时出错: {str(e)}")

        return [
            {
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mb-4'},
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {'class': 'text-h6'},
                        'content': [
                            {
                                'component': 'VRow',
                                'props': {'align': 'center'},
                                'content': [
                                    {
                                        'component': 'VCol',
                                        'props': {'class': 'text-h6'},
                                        'text': f'📊 图片目录映射概况 (共 {total_files} 个图片文件)'
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VCardText',
                        'content': [
                            {
                                'component': 'VTable',
                                'props': {'hover': True, 'density': 'compact'},
                                'content': [
                                    {
                                        'component': 'thead',
                                        'content': [
                                            {
                                                'component': 'tr',
                                                'content': [
                                                    {'component': 'th', 'text': '目录名'},
                                                    {'component': 'th', 'text': '完整路径'},
                                                    {'component': 'th', 'text': '文件数量'},
                                                    {'component': 'th', 'text': '示例URL'}
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'tbody',
                                        'content': [
                                            {
                                                'component': 'tr',
                                                'content': [
                                                    {'component': 'td', 'text': info['dir_name']},
                                                    {'component': 'td', 'text': info['path']},
                                                    {'component': 'td', 'text': str(info['file_count'])},
                                                    {
                                                        'component': 'td',
                                                        'content': [
                                                            {
                                                                'component': 'div',
                                                                'props': {'class': 'text-caption'},
                                                                'text': url
                                                            } for url in info['sample_urls']
                                                        ] if info['sample_urls'] else [
                                                            {
                                                                'component': 'div',
                                                                'props': {'class': 'text-caption'},
                                                                'text': '无示例文件'
                                                            }
                                                        ]
                                                    }
                                                ]
                                            } for info in directories_info
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    def __update_config(self):
        """更新配置"""
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "image_paths": ','.join(self._image_paths),
            "url_prefix": self._url_prefix
        })

    def _init_fastapi_routes(self):
        """初始化FastAPI路由"""
        try:
            if not self._app:
                self._app = FastAPI()

            # 为每个图片目录创建静态文件挂载
            for path in self._image_paths:
                dir_name = os.path.basename(path)
                mount_path = f"{self._url_prefix}/{dir_name}"
                try:
                    self._app.mount(mount_path, StaticFiles(directory=path), name=f"static_{dir_name}")
                    logger.info(f"{self.plugin_name} 成功挂载目录 {path} 到 {mount_path}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} 挂载目录 {path} 失败: {str(e)}")

            # 添加根路径重定向
            @self._app.get(self._url_prefix)
            async def redirect_to_plugin_page():
                return RedirectResponse(url="/plugin?page=LocalImageUrl")

            logger.info(f"{self.plugin_name} FastAPI路由初始化完成")
            
            if self._notify:
                self._send_notification(True, "插件启动成功，图片URL映射服务已就绪")
        except Exception as e:
            error_msg = f"初始化FastAPI路由失败: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            if self._notify:
                self._send_notification(False, error_msg)

    def _send_notification(self, success: bool, message: str = ""):
        """发送通知"""
        if not self._notify:
            return

        title = f"🖼️ {self.plugin_name} "
        title += "成功" if success else "失败"
        
        # 通知内容
        text_content = "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text_content += f"📌 状态：{'✅ 成功' if success else '❌ 失败'}\n\n"
        
        if self._image_paths:
            text_content += "📂 已映射目录：\n"
            for path in self._image_paths:
                dir_name = os.path.basename(path)
                text_content += f"   • {dir_name} ({path})\n"
        
        if message:
            text_content += f"\nℹ️ 详情：{message}\n"
        
        text_content += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            self.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}") 