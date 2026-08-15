import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.utils.http import RequestUtils

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
# 单源（随机图床等一次返回一张）预览时的最大请求次数，避免等待过久
MAX_SOURCE_REQUESTS = 6
# 候选图片收集并发数
COLLECT_WORKERS = 3


def is_url(value):
    return isinstance(value, str) and value.strip().startswith(('http://', 'https://'))


def is_image_url(url):
    return url.lower().endswith(IMG_EXTS)


def get_urls_from_text(text):
    """从文本中提取所有图片 URL。"""
    urls = re.findall(r'https?://[^\s,\"]+', text)
    return [url for url in urls if is_image_url(url)]


def _request(method: str, url: str, allow_redirects: bool = True):
    return RequestUtils(timeout=5).request(
        method=method,
        url=url,
        allow_redirects=allow_redirects,
    )


def get_network_image_url(config_value):
    """识别配置内容并返回一个可用的网络图片地址。"""
    if not config_value:
        return None

    if ',' in config_value:
        candidates = [
            value.strip()
            for value in config_value.split(',')
            if is_url(value.strip())
        ]
        if candidates:
            return random.choice(candidates)

    url = config_value.strip()
    if not is_url(url):
        return None
    if is_image_url(url):
        return url

    response = None
    try:
        response = _request('head', url)
        if response and response.headers.get('Content-Type', '').startswith('image/'):
            return response.url
    finally:
        if response is not None:
            response.close()

    try:
        response = RequestUtils(timeout=5).get_res(url)
        if not response:
            return url
        content_type = response.headers.get('Content-Type', '')
        if content_type.startswith('image/'):
            return response.url
        if 'json' in content_type:
            data = response.json()
            if isinstance(data, dict):
                for key in ('url', 'image', 'img', 'src'):
                    value = data.get(key)
                    if isinstance(value, str) and is_image_url(value):
                        return value
            elif isinstance(data, list):
                images = [
                    value
                    for value in data
                    if isinstance(value, str) and is_image_url(value)
                ]
                if images:
                    return random.choice(images)
        if 'text' in content_type:
            urls = get_urls_from_text(response.text)
            if urls:
                return random.choice(urls)
    finally:
        if response is not None:
            response.close()

    return url


def collect_network_image_urls(config_value, limit=20):
    """从网络图片源配置中批量收集图片 URL。

    支持逗号分隔的多个直链/API、txt 文本、JSON API、随机图床 API。
    多个候选源并发收集，随机图床源限制请求次数以保证响应速度。
    :return: 去重后的图片 URL 列表
    """
    if not config_value or not isinstance(config_value, str):
        return []
    candidates = [value.strip() for value in config_value.split(',') if is_url(value.strip())]
    if not candidates:
        return []

    urls = []
    seen = set()

    def _add(url):
        if url not in seen:
            seen.add(url)
            urls.append(url)

    with ThreadPoolExecutor(max_workers=COLLECT_WORKERS) as executor:
        futures = []
        for candidate in candidates:
            if len(urls) >= limit:
                break
            if is_image_url(candidate):
                _add(candidate)
                continue
            futures.append(executor.submit(_collect_from_source, candidate, limit))
        for future in as_completed(futures):
            for url in future.result():
                _add(url)
                if len(urls) >= limit:
                    break
    return urls[:limit]


def _collect_from_source(url, limit):
    """从单个 API/文本源收集图片 URL，支持随机图床多次请求去重。"""
    if limit <= 0:
        return []
    first = _parse_source_urls(url)
    if not first:
        return []
    if len(first) > 1:
        return first[:limit]

    results = []
    seen = set()
    for _ in range(min(limit, MAX_SOURCE_REQUESTS)):
        batch = _parse_source_urls(url)
        new_found = False
        for item in batch:
            if item not in seen:
                seen.add(item)
                results.append(item)
                new_found = True
        if not new_found or len(results) >= limit:
            break
    return results[:limit]


def _parse_source_urls(url):
    """请求并解析单个源，返回其中的图片 URL 列表。"""
    response = None
    try:
        response = RequestUtils(timeout=3).get_res(url)
        if not response:
            return []
        content_type = response.headers.get('Content-Type', '')
        if content_type.startswith('image/'):
            return [response.url]
        if 'json' in content_type:
            data = response.json()
            found = []
            if isinstance(data, dict):
                for key in ('url', 'image', 'img', 'src', 'images', 'imgs'):
                    value = data.get(key)
                    if isinstance(value, str) and is_image_url(value):
                        found.append(value)
                    elif isinstance(value, list):
                        found.extend(item for item in value if isinstance(item, str) and is_image_url(item))
            elif isinstance(data, list):
                found.extend(item for item in data if isinstance(item, str) and is_image_url(item))
            if found:
                return found
            return get_urls_from_text(str(data))
        if 'text' in content_type:
            return get_urls_from_text(response.text)
    except Exception:
        return []
    finally:
        if response is not None:
            response.close()
    return []


def count_network_images(config_value):
    """网络图片源数量无法可靠预知。"""
    if not config_value:
        return 0
    return None


def _count_from_url(url) -> Optional[int]:
    response = None
    try:
        response = RequestUtils(timeout=5).get_res(url)
        if not response:
            return None
        content_type = response.headers.get('Content-Type', '')
        if content_type.startswith('image/'):
            return 1
        if 'json' in content_type:
            data = response.json()
            if isinstance(data, dict):
                for key in ('url', 'image', 'img', 'src', 'images', 'imgs'):
                    value = data.get(key)
                    if isinstance(value, str) and is_image_url(value):
                        return 1
                    if isinstance(value, list):
                        return len([
                            item
                            for item in value
                            if isinstance(item, str) and is_image_url(item)
                        ])
                return len(get_urls_from_text(str(data)))
            if isinstance(data, list):
                return len([
                    item
                    for item in data
                    if isinstance(item, str) and is_image_url(item)
                ])
        if 'text' in content_type:
            return len(get_urls_from_text(response.text))
    finally:
        if response is not None:
            response.close()
    return None
