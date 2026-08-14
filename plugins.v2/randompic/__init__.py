import mimetypes
import random
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, Query, Request
from fastapi.responses import FileResponse, Response

import app.plugins as plugin_runtime
from app.log import logger
from app.plugins import _PluginBase
from app.utils.http import RequestUtils

from .network_image_provider import count_network_images, get_network_image_url

_IMAGE_PATTERNS = ('*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp')
_MOBILE_UA_PATTERN = re.compile(
    r'(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|'
    r'IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|'
    r'Symbian|Windows Phone)',
    re.I,
)
_LEGACY_RUNTIME_REGISTRY = '_randompic_runtime_registry'
_LEGACY_RUNTIME_LOCK = '_randompic_runtime_lock'

visit_lock = threading.Lock()
today_visit_count = 0
today_date = datetime.now().date()


def _increment_visit_count() -> None:
    global today_visit_count, today_date
    with visit_lock:
        current_date = datetime.now().date()
        if current_date != today_date:
            today_visit_count = 0
            today_date = current_date
        today_visit_count += 1


def _get_today_visit_count() -> int:
    with visit_lock:
        return today_visit_count


def _count_local_images(directory: Optional[str]) -> int:
    if not directory:
        return 0
    image_dir = Path(directory)
    if not image_dir.is_dir():
        return 0
    return sum(1 for pattern in _IMAGE_PATTERNS for _ in image_dir.glob(pattern))


def _close_legacy_runtime() -> None:
    """升级无端口版本时关闭旧版本登记的独立 HTTP 服务。"""
    registry = getattr(plugin_runtime, _LEGACY_RUNTIME_REGISTRY, None)
    if not isinstance(registry, dict):
        return

    lock = getattr(plugin_runtime, _LEGACY_RUNTIME_LOCK, None)
    if lock:
        with lock:
            runtime = registry.pop('RandomPic', None)
    else:
        runtime = registry.pop('RandomPic', None)
    if not runtime:
        return

    server = runtime.get('server')
    server_thread = runtime.get('thread')
    if server and server_thread and server_thread.is_alive():
        try:
            server.shutdown()
        except Exception as err:
            logger.warning(f'停止旧版随机图库服务失败: {str(err)}')
    if server_thread and server_thread is not threading.current_thread():
        try:
            server_thread.join(timeout=5)
        except Exception as err:
            logger.warning(f'等待旧版随机图库服务退出失败: {str(err)}')
    if server:
        try:
            server.server_close()
            logger.info('已释放旧版随机图库独立服务端口')
        except Exception as err:
            logger.warning(f'释放旧版随机图库端口失败: {str(err)}')


class RandomPic(_PluginBase):
    # 插件名称
    plugin_name = '随机图床API'
    # 插件描述
    plugin_desc = '基于MoviePilot同源接口的随机图片API，支持横屏/竖屏图片分类'
    # 插件图标
    plugin_icon = 'https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/randompic.png'
    # 插件版本
    plugin_version = '2.3.0'
    # 插件作者
    plugin_author = 'xijin285'
    # 作者主页
    author_url = 'https://github.com/xijin285'
    # 插件配置项ID前缀
    plugin_config_prefix = 'randompic_'
    # 加载顺序
    plugin_order = 15
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        self._enable = False
        self._pc_path: Optional[str] = None
        self._mobile_path: Optional[str] = None
        self._network_image_url_pc: Optional[str] = None
        self._network_image_url_mobile: Optional[str] = None
        self._network_image_url: Optional[str] = None

    def init_plugin(self, config: Optional[Dict[str, Any]] = None):
        _close_legacy_runtime()
        if not config:
            return
        self._enable = bool(config.get('enable'))
        self._pc_path = config.get('pc_path')
        self._mobile_path = config.get('mobile_path')
        self._network_image_url_pc = config.get('network_image_url_pc')
        self._network_image_url_mobile = config.get('network_image_url_mobile')
        self._network_image_url = config.get('network_image_url')

    def get_state(self) -> bool:
        return self._enable

    def get_render_mode(self) -> Tuple[str, Optional[str]]:
        return 'vue', 'dist/assets'

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        apis = [
            {
                'path': '/config',
                'endpoint': self._get_config,
                'methods': ['GET'],
                'auth': 'bear',
                'summary': '获取配置',
            },
            {
                'path': '/config',
                'endpoint': self._save_config,
                'methods': ['POST'],
                'auth': 'bear',
                'summary': '保存配置',
            },
            {
                'path': '/status',
                'endpoint': self._get_status,
                'methods': ['GET'],
                'auth': 'bear',
                'summary': '获取状态',
            },
            {
                'path': '/preview',
                'endpoint': self._get_preview,
                'methods': ['GET'],
                'auth': 'bear',
                'summary': '获取图片预览',
            },
            {
                'path': '/random',
                'endpoint': self._get_random,
                'methods': ['GET'],
                'allow_anonymous': True,
                'summary': '获取随机图片',
            },
            {
                'path': '/stats',
                'endpoint': self._get_stats,
                'methods': ['GET'],
                'allow_anonymous': True,
                'summary': '获取随机图库统计',
            },
        ]
        # v3 兼容：保持插件自定义响应格式（纯 dict），
        # 绕过宿主 ResponseAPIRoute 的统一 envelope 自动包装
        for _api in apis:
            if isinstance(_api, dict) and "openapi_extra" not in _api:
                _api["openapi_extra"] = {"x-moviepilot-raw-response": True}
        return apis

    def _get_config(self) -> Dict[str, Any]:
        return {
            'enable': self._enable,
            'pc_path': self._pc_path,
            'mobile_path': self._mobile_path,
            'network_image_url_pc': self._network_image_url_pc,
            'network_image_url_mobile': self._network_image_url_mobile,
            'network_image_url': self._network_image_url,
        }

    def _save_config(self, data: dict) -> dict:
        try:
            enable = bool(data.get('enable'))
            pc_path = data.get('pc_path')
            mobile_path = data.get('mobile_path')
            network_image_url_pc = data.get('network_image_url_pc')
            network_image_url_mobile = data.get('network_image_url_mobile')
            network_image_url = data.get('network_image_url')

            if enable:
                has_pc_source = bool(
                    (pc_path and pc_path.strip())
                    or (network_image_url_pc and network_image_url_pc.strip())
                )
                has_mobile_source = bool(
                    (mobile_path and mobile_path.strip())
                    or (network_image_url_mobile and network_image_url_mobile.strip())
                )
                if not has_pc_source:
                    return {'success': False, 'msg': '必须配置横屏图片源（本地目录或网络地址）'}
                if not has_mobile_source:
                    return {'success': False, 'msg': '必须配置竖屏图片源（本地目录或网络地址）'}

            self._enable = enable
            self._pc_path = pc_path
            self._mobile_path = mobile_path
            self._network_image_url_pc = network_image_url_pc
            self._network_image_url_mobile = network_image_url_mobile
            self._network_image_url = network_image_url
            self.update_config(self._get_config())
            return {'success': True, 'msg': '配置保存成功'}
        except Exception as err:
            logger.error(f'保存配置失败: {str(err)}')
            return {'success': False, 'msg': f'保存配置失败: {str(err)}'}

    def _ensure_enabled(self) -> None:
        if not self._enable:
            raise HTTPException(status_code=503, detail='随机图库插件未启用')

    @staticmethod
    def _is_mobile_request(request: Request) -> bool:
        return bool(_MOBILE_UA_PATTERN.search(request.headers.get('user-agent', '')))

    def _select_image_source(
        self,
        request: Request,
        image_type: Optional[str],
    ) -> Tuple[str, str]:
        if image_type not in (None, 'pc', 'mobile'):
            raise HTTPException(status_code=400, detail='不支持的图片类型')

        use_mobile = image_type == 'mobile' or (
            image_type is None and self._is_mobile_request(request)
        )
        if use_mobile:
            network_source = self._network_image_url_mobile or self._network_image_url
            local_directory = self._mobile_path
        else:
            network_source = self._network_image_url_pc or self._network_image_url
            local_directory = self._pc_path

        if network_source:
            image_url = get_network_image_url(network_source)
            if image_url:
                return 'network', image_url

        if not local_directory:
            raise HTTPException(status_code=404, detail='未配置对应类型的图片源')
        image_dir = Path(local_directory)
        if not image_dir.is_dir():
            raise HTTPException(status_code=404, detail='对应类型的图片目录不存在')

        image_files = [
            image_path
            for pattern in _IMAGE_PATTERNS
            for image_path in image_dir.glob(pattern)
        ]
        if not image_files:
            raise HTTPException(status_code=404, detail='对应类型的图片目录中没有图片')
        return 'local', str(random.choice(image_files))

    @staticmethod
    def _local_image_response(image_path: str) -> FileResponse:
        content_type, _ = mimetypes.guess_type(image_path)
        if not content_type or not content_type.startswith('image/'):
            raise HTTPException(status_code=415, detail='不支持的图片类型')
        return FileResponse(
            image_path,
            media_type=content_type,
            headers={
                'Cache-Control': 'no-store',
                'Access-Control-Allow-Origin': '*',
            },
        )

    def _get_random(
        self,
        request: Request,
        type: Optional[str] = Query(default=None, pattern='^(pc|mobile)$'),
    ) -> Response:
        self._ensure_enabled()
        _increment_visit_count()
        source_type, source = self._select_image_source(request, type)
        if source_type == 'network':
            return Response(
                status_code=302,
                headers={
                    'Location': source,
                    'Cache-Control': 'no-store',
                    'Access-Control-Allow-Origin': '*',
                },
            )
        return self._local_image_response(source)

    def _get_preview(self, request: Request, type: Optional[str] = None) -> Response:
        self._ensure_enabled()
        _increment_visit_count()
        source_type, source = self._select_image_source(request, type)
        if source_type == 'local':
            return self._local_image_response(source)

        headers = {'User-Agent': request.headers.get('user-agent', '')}
        with RequestUtils(headers=headers, timeout=15).response_manager(
            method='get',
            url=source,
            allow_redirects=True,
        ) as response:
            if response is None or not response.ok:
                logger.error('获取网络图片预览失败')
                raise HTTPException(status_code=502, detail='网络图片预览加载失败')

            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise HTTPException(status_code=502, detail='网络图片源未返回图片')
            return Response(
                content=response.content,
                media_type=content_type,
                headers={'Cache-Control': 'no-store'},
            )

    def _build_stats(self) -> Dict[str, Any]:
        pc_local = _count_local_images(self._pc_path)
        mobile_local = _count_local_images(self._mobile_path)
        network_pc = (
            count_network_images(self._network_image_url_pc)
            if self._network_image_url_pc
            else 0
        )
        network_mobile = (
            count_network_images(self._network_image_url_mobile)
            if self._network_image_url_mobile
            else 0
        )
        pc_total = pc_local + (network_pc if isinstance(network_pc, int) else 0)
        mobile_total = mobile_local + (
            network_mobile if isinstance(network_mobile, int) else 0
        )
        return {
            'total': pc_total + mobile_total,
            'pc': pc_total,
            'mobile': mobile_total,
            'today': _get_today_visit_count(),
            'detail': {
                'local': {'pc': pc_local, 'mobile': mobile_local},
                'network': {
                    'pc': network_pc if network_pc is not None else '未知',
                    'mobile': network_mobile if network_mobile is not None else '未知',
                },
            },
        }

    def _get_stats(self, _request: Request) -> Dict[str, Any]:
        self._ensure_enabled()
        return self._build_stats()

    def _get_status(self) -> Dict[str, Any]:
        stats = self._build_stats()
        pc_available = bool(self._pc_path or self._network_image_url_pc or self._network_image_url)
        mobile_available = bool(
            self._mobile_path or self._network_image_url_mobile or self._network_image_url
        )
        return {
            'enable': self._enable,
            'api_status': 'available' if self._enable else 'disabled',
            'api_endpoints': {
                'auto': self._enable and pc_available and mobile_available,
                'pc': self._enable and pc_available,
                'mobile': self._enable and mobile_available,
                'stats': self._enable,
            },
            'pc_path': self._pc_path,
            'mobile_path': self._mobile_path,
            'network_image_url_pc': self._network_image_url_pc,
            'network_image_url_mobile': self._network_image_url_mobile,
            'network_image_url': self._network_image_url,
            'pc_count': stats['pc'],
            'mobile_count': stats['mobile'],
            'total_count': stats['total'],
            'today_visits': stats['today'],
            'detail': stats['detail'],
        }

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        return None, self._get_config()

    def get_page(self) -> List[dict]:
        return []

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        return [{'key': 'main_dashboard', 'name': '随机图库状态'}]

    def get_dashboard(self, key: str, **kwargs) -> Optional[
        Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]
    ]:
        if key != 'main_dashboard':
            return None
        return {
            'cols': 12,
            'md': 6,
        }, {
            'refresh': 30,
            'border': True,
            'title': '随机图库状态',
            'subtitle': '图片统计和访问数据',
        }, None

    def stop_service(self):
        _close_legacy_runtime()
