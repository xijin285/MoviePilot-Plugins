import random
import re
from typing import Optional

from app.utils.http import RequestUtils

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')


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
