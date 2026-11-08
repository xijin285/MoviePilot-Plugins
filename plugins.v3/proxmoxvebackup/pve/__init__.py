"""
PVE操作模块
提供PVE主机状态查询、容器管理等功能
"""
from .client import (
    get_pve_status,
    get_container_status,
    get_qemu_status,
    clean_pve_tmp_files,
    clean_pve_logs,
    list_template_images,
    download_template_image,
    delete_template_image,
    upload_template_image,
    download_template_image_from_url
)

__all__ = [
    'get_pve_status',
    'get_container_status',
    'get_qemu_status',
    'clean_pve_tmp_files',
    'clean_pve_logs',
    'list_template_images',
    'download_template_image',
    'delete_template_image',
    'upload_template_image',
    'download_template_image_from_url'
]

