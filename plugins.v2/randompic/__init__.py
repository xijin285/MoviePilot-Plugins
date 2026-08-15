import hashlib
import mimetypes
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response

from PIL import Image

import app.plugins as plugin_runtime
from app.log import logger
from app.plugins import _PluginBase
from app.utils.http import RequestUtils

from .network_image_provider import (
    collect_network_image_urls,
    count_network_images,
    get_network_image_url,
)

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
    plugin_version = '2.3.1'
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
        self._download_count: int = 20
        self._download_lock = threading.Lock()
        self._download_status: Dict[str, Any] = {}

    def _default_paths(self) -> Tuple[str, str]:
        """返回默认 PC/Mobile 目录（插件数据目录下）。"""
        base = self.get_data_path()
        return str(base / 'PC'), str(base / 'Mobile')

    def init_plugin(self, config: Optional[Dict[str, Any]] = None):
        _close_legacy_runtime()
        if not config:
            return
        default_pc, default_mobile = self._default_paths()
        self._enable = bool(config.get('enable'))
        self._pc_path = config.get('pc_path') or default_pc
        self._mobile_path = config.get('mobile_path') or default_mobile
        self._network_image_url_pc = config.get('network_image_url_pc')
        self._network_image_url_mobile = config.get('network_image_url_mobile')
        self._network_image_url = config.get('network_image_url')
        try:
            self._download_count = max(1, int(config.get('download_count') or 20))
        except (TypeError, ValueError):
            self._download_count = 20

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
                'path': '/preview/save',
                'endpoint': self._save_preview_image,
                'methods': ['POST'],
                'auth': 'bear',
                'summary': '保存预览图片到本地目录并自动分类',
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
            {
                'path': '/download/candidates',
                'endpoint': self._get_download_candidates,
                'methods': ['GET'],
                'auth': 'bear',
                'summary': '获取候选下载图片列表',
            },
            {
                'path': '/download',
                'endpoint': self._start_download,
                'methods': ['POST'],
                'auth': 'bear',
                'summary': '下载网络图片并按横竖屏分类保存到本地',
            },
            {
                'path': '/download/status',
                'endpoint': self._get_download_status,
                'methods': ['GET'],
                'auth': 'bear',
                'summary': '获取下载任务状态',
            },
        ]
        # v3 兼容：保持插件自定义响应格式（纯 dict），
        # 绕过宿主 ResponseAPIRoute 的统一 envelope 自动包装
        for _api in apis:
            if isinstance(_api, dict) and "openapi_extra" not in _api:
                _api["openapi_extra"] = {"x-moviepilot-raw-response": True}
        return apis

    def _get_config(self) -> Dict[str, Any]:
        default_pc, default_mobile = self._default_paths()
        return {
            'enable': self._enable,
            'pc_path': self._pc_path or default_pc,
            'mobile_path': self._mobile_path or default_mobile,
            'default_pc_path': default_pc,
            'default_mobile_path': default_mobile,
            'network_image_url_pc': self._network_image_url_pc,
            'network_image_url_mobile': self._network_image_url_mobile,
            'network_image_url': self._network_image_url,
            'download_count': self._download_count,
        }

    def _save_config(self, data: dict) -> dict:
        try:
            enable = bool(data.get('enable'))
            pc_path = data.get('pc_path')
            mobile_path = data.get('mobile_path')
            network_image_url_pc = data.get('network_image_url_pc')
            network_image_url_mobile = data.get('network_image_url_mobile')
            network_image_url = data.get('network_image_url')
            try:
                download_count = max(1, int(data.get('download_count') or 20))
            except (TypeError, ValueError):
                download_count = 20

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
            self._download_count = download_count
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
        default_pc, default_mobile = self._default_paths()
        pc_path = self._pc_path or default_pc
        mobile_path = self._mobile_path or default_mobile
        # 是否用户自定义（非空且不等于默认路径）
        pc_path_custom = bool(self._pc_path) and str(self._pc_path) != str(default_pc)
        mobile_path_custom = bool(self._mobile_path) and str(self._mobile_path) != str(default_mobile)
        pc_available = bool(pc_path or self._network_image_url_pc or self._network_image_url)
        mobile_available = bool(
            mobile_path or self._network_image_url_mobile or self._network_image_url
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
            'pc_path': pc_path,
            'pc_path_custom': pc_path_custom,
            'mobile_path': mobile_path,
            'mobile_path_custom': mobile_path_custom,
            'network_image_url_pc': self._network_image_url_pc,
            'network_image_url_mobile': self._network_image_url_mobile,
            'network_image_url': self._network_image_url,
            'pc_count': stats['pc'],
            'mobile_count': stats['mobile'],
            'total_count': stats['total'],
            'today_visits': stats['today'],
            'detail': stats['detail'],
        }

    def _get_download_candidates(
        self,
        source: str = Query(default='both', pattern='^(both|pc|mobile)$'),
        count: int = Query(default=30, ge=1, le=100),
    ) -> Dict[str, Any]:
        self._ensure_enabled()
        urls = self._collect_download_urls(source, count)
        return {'success': True, 'data': {'urls': urls, 'total': len(urls)}}

    def _start_download(self, data: dict) -> dict:
        self._ensure_enabled()

        selected_urls = data.get('urls')
        if isinstance(selected_urls, list) and selected_urls:
            urls = [
                url.strip()
                for url in selected_urls
                if isinstance(url, str) and url.strip().startswith(('http://', 'https://'))
            ]
            if not urls:
                return {'success': False, 'msg': '未选择有效的图片地址'}
            count = len(urls)
            source_type = 'both'
        else:
            urls = None
            try:
                count = int(data.get('count') or self._download_count or 20)
            except (TypeError, ValueError):
                count = self._download_count
            source_type = data.get('source') or 'both'
            if count < 1 or count > 500:
                return {'success': False, 'msg': '下载数量需在 1-500 之间'}
            if source_type not in ('both', 'pc', 'mobile'):
                return {'success': False, 'msg': '不支持的下载源'}

        has_local = bool(self._pc_path or self._mobile_path)
        if not has_local:
            return {'success': False, 'msg': '请先配置本地图片目录'}
        if not urls and not (
            self._network_image_url_pc or self._network_image_url_mobile or self._network_image_url
        ):
            return {'success': False, 'msg': '请先配置网络图片地址'}

        with self._download_lock:
            if self._download_status.get('running'):
                return {'success': False, 'msg': '下载任务进行中，请稍后再试'}
            self._download_status = {
                'running': True,
                'total': 0,
                'done': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'pc_saved': 0,
                'mobile_saved': 0,
                'message': '正在启动下载任务...',
            }

        thread = threading.Thread(
            target=self._download_worker,
            args=(count, source_type, urls),
            daemon=True,
        )
        thread.start()
        return {'success': True, 'msg': '下载任务已启动'}

    def _get_download_status(self) -> Dict[str, Any]:
        with self._download_lock:
            return dict(self._download_status)

    def _download_worker(
        self,
        count: int,
        source_type: str,
        selected_urls: Optional[List[str]] = None,
    ) -> None:
        try:
            if selected_urls:
                urls = selected_urls
            else:
                urls = self._collect_download_urls(source_type, count)
            if not urls:
                with self._download_lock:
                    self._download_status.update(
                        {'running': False, 'message': '未从网络源解析到图片地址'}
                    )
                return

            total = min(count, len(urls))
            with self._download_lock:
                self._download_status.update({'total': total, 'message': '开始下载图片...'})

            for url in urls[:total]:
                with self._download_lock:
                    self._download_status['done'] += 1
                try:
                    saved = self._download_and_save(url)
                    with self._download_lock:
                        if saved == 'pc':
                            self._download_status['pc_saved'] += 1
                            self._download_status['success'] += 1
                        elif saved == 'mobile':
                            self._download_status['mobile_saved'] += 1
                            self._download_status['success'] += 1
                        elif saved == 'exists':
                            self._download_status['skipped'] += 1
                        else:
                            self._download_status['failed'] += 1
                except Exception as err:
                    logger.warning(f'下载图片失败 {url} - {err}')
                    with self._download_lock:
                        self._download_status['failed'] += 1
        finally:
            with self._download_lock:
                self._download_status['running'] = False
                self._download_status['message'] = '下载任务已完成'

    def _collect_download_urls(self, source_type: str, count: int) -> List[str]:
        sources = []
        if source_type in ('both', 'pc'):
            sources.append(self._network_image_url_pc)
        if source_type in ('both', 'mobile'):
            sources.append(self._network_image_url_mobile)
        if source_type == 'both':
            sources.append(self._network_image_url)

        collected = []
        with ThreadPoolExecutor(max_workers=len(sources) or 1) as executor:
            futures = [
                executor.submit(collect_network_image_urls, str(source), count)
                for source in sources
                if source and str(source).strip()
            ]
            for future in as_completed(futures):
                collected.extend(future.result())
                if len(collected) >= count:
                    break

        seen = set()
        deduped = []
        for url in collected:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped

    def _download_and_save(self, url: str) -> str:
        """下载单张图片，按实际宽高比分类保存到本地目录。

        :return: pc / mobile / exists / invalid
        """
        with RequestUtils(timeout=15).response_manager(
            method='get',
            url=url,
            allow_redirects=True,
        ) as response:
            if response is None or not response.ok:
                return 'invalid'
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return 'invalid'
            return self._classify_and_save_content(response.content, content_type)

    def _classify_and_save_content(self, content: bytes, content_type: str) -> str:
        """按实际宽高比将图片字节分类保存到本地目录。

        :return: pc / mobile / exists / invalid
        """
        try:
            with Image.open(BytesIO(content)) as img:
                width, height = img.size
        except Exception as err:
            logger.warning(f'解析图片尺寸失败 - {err}')
            return 'invalid'

        is_landscape = width >= height
        target_path = self._pc_path if is_landscape else self._mobile_path
        if not target_path or not str(target_path).strip():
            return 'invalid'
        target_dir = Path(target_path)
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logger.warning(f'创建目录失败 {target_dir} - {err}')
            return 'invalid'

        ext = mimetypes.guess_extension(content_type.split(';')[0].strip()) or '.jpg'
        if ext.lower() not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            ext = '.jpg'
        filename = f'{hashlib.md5(content).hexdigest()[:12]}{ext}'
        filepath = target_dir / filename
        if filepath.exists():
            return 'exists'
        try:
            filepath.write_bytes(content)
        except Exception as err:
            logger.warning(f'保存图片失败 {filepath} - {err}')
            return 'invalid'
        return 'pc' if is_landscape else 'mobile'

    def _save_preview_image(self, file: UploadFile = File(...)) -> Dict[str, Any]:
        """将预览的图片字节保存到本地目录，自动按横竖屏分类。"""
        self._ensure_enabled()
        try:
            content = file.file.read()
            content_type = file.content_type or mimetypes.guess_type(file.filename or '')[0] or ''
        except Exception as err:
            logger.error(f'读取上传预览图片失败: {err}')
            return {'success': False, 'msg': '读取上传图片失败'}
        finally:
            try:
                file.file.close()
            except Exception:
                pass

        if not content:
            return {'success': False, 'msg': '上传内容为空'}

        result = self._classify_and_save_content(content, content_type)
        if result == 'invalid':
            return {'success': False, 'msg': '图片解析或保存失败'}
        if result == 'exists':
            return {'success': True, 'msg': '图片已存在，自动跳过'}
        category = '横屏' if result == 'pc' else '竖屏'
        return {'success': True, 'msg': f'已保存为{category}图片'}

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
