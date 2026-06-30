"""
夸克网盘 HTTP 客户端
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional

import requests

from app.log import logger


class QuarkClient:
    """
    夸克网盘 HTTP 客户端（Cookie 认证）。
    """

    BASE_URL = "https://drive-pc.quark.cn/1/clouddrive"
    SHARE_BASE_URL = "https://drive.quark.cn/1/clouddrive"
    PAN_CLOUDDRIVE_URL = "https://pan.quark.cn/1/clouddrive"
    ACCOUNT_URL = "https://pan.quark.cn/account"
    QR_LOGIN_URL = "https://uop.quark.cn/cas/ajax"

    DEFAULT_PARAMS = {
        "pr": "ucpro",
        "fr": "pc",
        "uc_param_str": "",
    }

    DEFAULT_HEADERS = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "referer": "https://pan.quark.cn/",
        "origin": "https://pan.quark.cn",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "x-requested-with": "XMLHttpRequest",
        "x-client-version": "3.1.0",
        "x-platform-version": "web",
        "x-platform-type": "web",
        "x-sdk-version": "3.1.0",
        "x-device-model": "web",
        "x-device-name": "Chrome",
        "x-device-platform": "web",
        "x-app-id": "30",
        "x-app-version": "3.1.0",
        "x-app-package": "com.quark.pan",
    }

    def __init__(
        self,
        cookie: str = "",
        on_cookie_refresh: Callable[[str], None] = None,
    ):
        """
        初始化客户端。

        Args:
            cookie: Cookie 字符串，格式 "key1=value1; key2=value2"
            on_cookie_refresh: Cookie 刷新后的回调函数
        """
        self._cookie = (cookie or "").strip()
        self._on_cookie_refresh = on_cookie_refresh
        self._device_id = str(int(time.time() * 1000))
        self._session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)
        self._last_qr_token: str = ""
        self._qr_expires_at: float = 0

    @property
    def cookie(self) -> str:
        return self._cookie

    @property
    def is_logged_in(self) -> bool:
        return bool(self._cookie and "__pus" in self._cookie)

    def get_uid_from_cookie(self) -> str:
        """
        从 Cookie 字符串中提取 __uid 值。
        """
        if not self._cookie:
            return ""
        for part in self._cookie.split(";"):
            part = part.strip()
            if part.startswith("__uid="):
                return part[len("__uid="):]
        return ""

    def _get_timestamp(self) -> int:
        return int(time.time() * 1000)

    def _build_params(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = self.DEFAULT_PARAMS.copy()
        params["__t"] = self._get_timestamp()
        params["__dt"] = 1000
        if extra:
            params.update(extra)
        return params

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = self.DEFAULT_HEADERS.copy()
        headers["x-device-id"] = self._device_id
        if self._cookie:
            headers["cookie"] = self._cookie
        if extra:
            headers.update(extra)
        return headers

    def _update_cookie_from_response(self, response):
        """从响应中提取 __pus/__puus 并刷新 Cookie（与 v2 一致）。"""
        if not response or not hasattr(response, "cookies"):
            return
        cookie_dict = {}
        for item in self._cookie.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookie_dict[key] = value
        updated = False
        for key in ["__puus", "__pus"]:
            if key in response.cookies:
                cookie_dict[key] = response.cookies.get(key)
                updated = True
        if updated:
            self._cookie = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求。
        """
        actual_base = (base_url or self.BASE_URL).rstrip("/")
        full_url = f"{actual_base}/{url.lstrip('/')}"

        request_params = self._build_params(params)
        request_headers = self._build_headers(headers)

        try:
            if method.upper() == "GET":
                response = self._session.get(
                    full_url,
                    params=request_params,
                    headers=request_headers,
                    timeout=timeout,
                )
            elif method.upper() == "POST":
                response = self._session.post(
                    full_url,
                    params=request_params,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout,
                )
            else:
                response = self._session.request(
                    method,
                    full_url,
                    params=request_params,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout,
                )

            # 每次响应后刷新 Cookie（__pus/__puus 可能更新）
            self._update_cookie_from_response(response)

            if response.status_code in (401, 403):
                logger.warning(f"【夸克网盘】认证失败 ({response.status_code}): Cookie 可能已过期")
                return {
                    "status": response.status_code,
                    "code": response.status_code,
                    "message": "认证失败，Cookie 可能已过期",
                    "data": {},
                }

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    # 记录 404 等错误的详细信息（包含 path 字段）
                    logger.warning(
                        f"【夸克网盘】HTTP {response.status_code}: url={full_url}, "
                        f"path={error_data.get('path', '')}, "
                        f"error={error_data.get('error', '')}, "
                        f"message={error_data.get('message', '')}"
                    )
                    return {
                        "status": response.status_code,
                        "code": response.status_code,
                        "message": str(error_data.get("message", "")),
                        "data": error_data,
                    }
                except Exception:
                    return {
                        "status": response.status_code,
                        "code": response.status_code,
                        "message": response.text[:500],
                        "data": {},
                    }

            if not response.text:
                return {"status": 200, "code": 0, "message": "ok", "data": {}}

            result = response.json()

            # 记录 Quark API 层面的非成功状态（便于排查）
            if isinstance(result, dict):
                api_status = result.get("status")
                if api_status not in (200, "200", 2000000, "2000000", 0, "0", None):
                    logger.warning(
                        f"【夸克网盘】API 返回非成功状态: url={url}, "
                        f"status={api_status}, code={result.get('code')}, "
                        f"message={result.get('message', '')}"
                    )

            return result

        except requests.exceptions.RequestException as err:
            logger.error(f"【夸克网盘】请求失败: {url} - {err}")
            return {
                "status": -1,
                "code": -1,
                "message": str(err),
                "data": {},
            }

    # ==================== QR 登录 ====================

    def get_qrcode(self) -> Optional[Dict[str, Any]]:
        """
        获取扫码登录二维码 token 和 URL。
        """
        request_id = str(uuid.uuid4())
        params = {
            "client_id": "532",
            "v": "1.2",
            "request_id": request_id,
        }
        try:
            response = self._session.get(
                f"{self.QR_LOGIN_URL}/getTokenForQrcodeLogin",
                params=params,
                headers=self.DEFAULT_HEADERS,
                timeout=30,
            )
            if response.status_code != 200:
                logger.error(f"【夸克网盘】获取二维码失败: HTTP {response.status_code}")
                return None
            data = response.json()
            if data.get("status") != 2000000:
                logger.error(f"【夸克网盘】获取二维码失败: {data.get('message', '未知错误')}")
                return None

            token = data.get("data", {}).get("members", {}).get("token", "")
            if not token:
                logger.error("【夸克网盘】获取二维码失败: 响应中未找到 token")
                return None

            self._last_qr_token = token
            self._qr_expires_at = time.time() + 300

            qr_url = self._build_qr_url(token)
            return {
                "qr_token": token,
                "qr_url": qr_url,
                "expires_in": 300,
            }
        except Exception as err:
            logger.error(f"【夸克网盘】获取二维码异常: {err}")
            return None

    @staticmethod
    def _build_qr_url(token: str) -> str:
        """
        构造二维码 URL。
        """
        import urllib.parse
        base_url = "https://su.quark.cn/4_eMHBJ"
        params = {
            "token": token,
            "client_id": "532",
            "ssb": "weblogin",
            "uc_param_str": "",
            "uc_biz_str": "S:custom|OPT:SAREA@0|OPT:IMMERSIVE@1|OPT:BACK_BTN_STYLE@0",
        }
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"

    def poll_qrcode(self, qr_token: str) -> Optional[Dict[str, Any]]:
        """
        轮询扫码登录状态。

        Returns:
            dict: 登录成功返回 {"success": True, "cookie": "..."}，等待中返回 {"waiting": True, "message": "..."}，失败返回 {"success": False, "message": "..."}
        """
        request_id = str(uuid.uuid4())
        params = {
            "client_id": "532",
            "v": "1.2",
            "token": qr_token,
            "request_id": request_id,
        }
        try:
            response = self._session.get(
                f"{self.QR_LOGIN_URL}/getServiceTicketByQrcodeToken",
                params=params,
                headers=self.DEFAULT_HEADERS,
                timeout=30,
            )
            if response.status_code != 200:
                return {"waiting": True, "message": "等待扫码中..."}

            data = response.json()
            status = data.get("status")
            message = data.get("message", "")

            if status == 2000000 and message == "ok":
                service_ticket = (
                    data.get("data", {}).get("members", {}).get("service_ticket", "")
                )
                if service_ticket:
                    cookie = self._get_cookies_from_service_ticket(service_ticket)
                    if cookie:
                        self._cookie = cookie
                        if self._on_cookie_refresh:
                            try:
                                self._on_cookie_refresh(cookie)
                            except Exception as err:
                                logger.error(f"【夸克网盘】Cookie 保存回调失败: {err}")
                        return {"success": True, "cookie": cookie, "message": "登录成功"}
                return {"success": False, "message": "获取 service_ticket 失败"}

            fail_statuses = [50004002, 50004003, 50004004]
            if status in fail_statuses or any(
                kw in message.lower() for kw in ["expired", "failed", "error", "timeout", "invalid"]
            ):
                return {"success": False, "message": f"登录失败: {message}"}

            return {"waiting": True, "message": "等待扫码中..."}

        except Exception as err:
            logger.error(f"【夸克网盘】轮询登录状态异常: {err}")
            return {"waiting": True, "message": "等待扫码中..."}

    def _get_cookies_from_service_ticket(self, service_ticket: str) -> str:
        """
        使用 service_ticket 获取用户信息并提取 Cookie。
        """
        try:
            response = self._session.get(
                f"{self.ACCOUNT_URL}/info",
                params={"st": service_ticket, "lw": "scan"},
                headers=self.DEFAULT_HEADERS,
                timeout=30,
            )
            cookies = []
            for cookie in self._session.cookies:
                if cookie.domain and "quark.cn" in cookie.domain:
                    cookies.append(f"{cookie.name}={cookie.value}")
            return "; ".join(cookies)
        except Exception as err:
            logger.error(f"【夸克网盘】获取 Cookie 失败: {err}")
            return ""

    # ==================== 用户信息 ====================

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息。

        注意：account/info 端点位于 pan.quark.cn 域名下，
        不属于 clouddrive API，不能使用 _request() 方法。
        需要带 fr=pc 和 platform=pc 参数才能返回正确的 JSON 格式。
        """
        try:
            # account/info 是 GET 请求，不需要 content-type: application/json
            # QuarkPan 的 APILogin 也不设置 content-type
            headers = self._build_headers()
            headers.pop("content-type", None)
            params = {
                "fr": "pc",
                "platform": "pc",
            }
            response = self._session.get(
                f"{self.ACCOUNT_URL}/info",
                params=params,
                headers=headers,
                timeout=30,
            )
            if response.status_code in (401, 403):
                logger.warning(f"【夸克网盘】获取用户信息认证失败: HTTP {response.status_code}")
                return {
                    "status": 401,
                    "code": 401,
                    "message": "认证失败，Cookie 可能已过期",
                    "data": {},
                }
            if response.status_code >= 400:
                logger.error(f"【夸克网盘】获取用户信息失败: HTTP {response.status_code}, body={response.text[:300]}")
                return {
                    "status": response.status_code,
                    "code": response.status_code,
                    "message": f"HTTP {response.status_code}",
                    "data": {},
                }
            if not response.text:
                return {"status": 200, "code": 0, "message": "ok", "data": {}}

            # 检查响应是否为 JSON（pan.quark.cn 可能返回 HTML）
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                logger.warning("【夸克网盘】account/info 返回 HTML 而非 JSON，Cookie 可能无效")
                return {
                    "status": 401,
                    "code": 401,
                    "message": "Cookie 可能已过期（返回 HTML 登录页）",
                    "data": {},
                }

            result = response.json()
            # Quark account API 使用 status=2000000 表示成功，归一化为 200
            if isinstance(result, dict) and result.get("status") == 2000000:
                result["status"] = 200
            # 如果响应没有 status 字段，但包含 success/data，视为成功
            if isinstance(result, dict) and "status" not in result:
                if result.get("success") is True:
                    result["status"] = 200
                    result.setdefault("code", 0)
                    result.setdefault("message", "ok")
                elif result.get("success") is False:
                    # success=false 表示请求失败，使用 code 作为 status
                    result["status"] = result.get("code", 401)
            return result
        except Exception as err:
            logger.error(f"【夸克网盘】获取用户信息异常: {err}")
            return {"status": -1, "code": -1, "message": str(err), "data": {}}

    def get_member_info(self) -> Dict[str, Any]:
        """
        获取会员与容量信息。

        使用 pan.quark.cn/1/clouddrive/member 端点，
        返回 total_capacity、use_capacity、member_type、identity 等信息。

        注意：pan.quark.cn 域名的 GET 请求不能带 content-type: application/json，
        且需要 platform=pc 参数，否则 API 会返回不完整数据（缺少 identity 数组）。
        与 get_user_info() 保持一致的请求方式。
        """
        try:
            # GET 请求不需要 content-type，移除它（与 get_user_info 保持一致）
            headers = self._build_headers()
            headers.pop("content-type", None)
            params = self._build_params({"platform": "pc"})
            url = f"{self.PAN_CLOUDDRIVE_URL}/member"
            response = self._session.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
            )
            if response.status_code in (401, 403):
                logger.warning(f"【夸克网盘】获取会员信息认证失败: HTTP {response.status_code}")
                return {
                    "status": 401,
                    "code": 401,
                    "message": "认证失败，Cookie 可能已过期",
                    "data": {},
                }
            if response.status_code >= 400:
                logger.error(
                    f"【夸克网盘】获取会员信息失败: HTTP {response.status_code}, "
                    f"body={response.text[:300]}"
                )
                return {
                    "status": response.status_code,
                    "code": response.status_code,
                    "message": f"HTTP {response.status_code}",
                    "data": {},
                }
            if not response.text:
                return {"status": 200, "code": 0, "message": "ok", "data": {}}

            result = response.json()
            return result
        except Exception as err:
            logger.error(f"【夸克网盘】获取会员信息异常: {err}")
            return {"status": -1, "code": -1, "message": str(err), "data": {}}

    def get_capacity(self) -> Dict[str, Any]:
        """
        获取存储空间信息。

        优先使用 pan.quark.cn/1/clouddrive/member 端点（返回 capacity + member 信息），
        如果失败则回退到 drive-pc.quark.cn/1/clouddrive/capacity。
        """
        # 方案1: 使用 member 端点（pan.quark.cn 域名，包含容量数据）
        member_result = self.get_member_info()
        if member_result.get("status") in (200, "200", 2000000, "2000000"):
            # 将 member 响应包装为 capacity 格式
            member_data = member_result.get("data", {})
            if isinstance(member_data, dict) and (
                member_data.get("total_capacity") is not None
                or member_data.get("use_capacity") is not None
            ):
                return member_result

        # 方案2: 回退到 capacity 端点（drive-pc.quark.cn 域名）
        logger.info("【夸克网盘】member 端点未返回容量数据，回退到 capacity 端点")
        result = self._request("GET", "capacity")
        return result

    # ==================== 文件操作 ====================

    def get_file_list(
        self,
        pdir_fid: str = "0",
        page: int = 1,
        size: int = 50,
        sort_field: str = "file_name",
        sort_order: str = "asc",
    ) -> Dict[str, Any]:
        """
        获取文件列表。
        """
        params = {
            "pdir_fid": pdir_fid,
            "_page": page,
            "_size": size,
            "_sort": f"{sort_field}:{sort_order}",
        }
        return self._request("GET", "file/sort", params=params)

    def get_file_info(self, fid: str) -> Dict[str, Any]:
        """
        获取文件详情。

        与 QuarkPan 保持一致：使用 GET 请求，fids 作为 query 参数传递。
        """
        return self._request("GET", "file", params={"fids": fid})

    def create_folder(self, folder_name: str, parent_id: str = "0") -> Dict[str, Any]:
        """
        创建文件夹。
        """
        data = {
            "pdir_fid": parent_id,
            "file_name": folder_name,
            "dir_init_lock": False,
            "dir_path": "",
        }
        return self._request("POST", "file", json_data=data)

    def delete_files(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        删除文件/文件夹（移入回收站）。
        """
        data = {
            "action_type": 2,
            "filelist": file_ids,
            "exclude_fids": [],
        }
        return self._request("POST", "file/delete", json_data=data)

    def get_recycle_list(
        self,
        page: int = 1,
        size: int = 50,
        sort: str = "move_recycle_at:desc",
        category: str = "",
        file_type: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取回收站文件列表。
        """
        params: Dict[str, Any] = {
            "_page": page,
            "_size": size,
            "sort": sort,
            "fetch_pdir_file_name": 1,
        }
        if category:
            params["category"] = category
        if file_type is not None:
            params["file_type"] = file_type
        return self._request("GET", "file/recycle/list", params=params)

    def remove_files_from_recycle(self, record_ids: List[str]) -> Dict[str, Any]:
        """
        从回收站彻底删除文件。
        """
        if not record_ids:
            return {"status": 200, "code": 0, "message": "ok", "data": {}}
        data = {
            "select_mode": 2,
            "record_list": record_ids,
        }
        return self._request("POST", "file/recycle/remove", json_data=data)

    def move_files(
        self, file_ids: List[str], target_folder_id: str
    ) -> Dict[str, Any]:
        """
        移动文件到指定文件夹。
        """
        data = {
            "action_type": 1,
            "to_pdir_fid": target_folder_id,
            "filelist": file_ids,
            "exclude_fids": [],
        }
        return self._request("POST", "file/move", json_data=data)

    def search_files(
        self,
        keyword: str,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """
        搜索文件。
        """
        params = {
            "q": keyword,
            "_page": page,
            "_size": size,
            "_fetch_total": 1,
            "_sort": "file_type:desc,updated_at:desc",
            "_is_hl": 1,
        }
        return self._request("GET", "file/search", params=params)

    def get_download_url(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件下载链接。

        使用 drive-pc.quark.cn 域名（与 file/sort 等所有 API 一致），
        避免跨域名导致的 CDN 鉴权 412。
        参数只保留 pr=ucpro&fr=pc，与 v2 一致。
        """
        return self._request(
            "POST",
            "file/download",
            json_data={"fids": [file_id]},
            params={"pr": "ucpro", "fr": "pc"},
        )

    def get_download_urls(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        批量获取文件下载链接。
        """
        data = {"fids": file_ids}
        return self._request("POST", "file/download", json_data=data)

    # ==================== 任务轮询 ====================

    def get_task_status(self, task_id: str, retry_index: int = 0) -> Dict[str, Any]:
        """
        获取异步任务状态。
        """
        params = {"task_id": task_id, "retry_index": retry_index}
        return self._request("GET", "task", params=params)

    def wait_for_task(self, task_id: str, timeout: int = 60) -> Dict[str, Any]:
        """
        等待异步任务完成。
        """
        start_time = time.time()
        retry_index = 0
        max_retries = timeout

        while retry_index < max_retries and time.time() - start_time < timeout:
            try:
                task_response = self.get_task_status(task_id, retry_index)
                if task_response.get("status") == 200:
                    task_data = task_response.get("data", {})
                    status = task_data.get("status")
                    if status == 2:
                        return task_response
                    elif status == 3:
                        return task_response
                retry_index += 1
                if retry_index < max_retries:
                    time.sleep(1)
            except Exception:
                retry_index += 1
                if retry_index < max_retries:
                    time.sleep(1)

        return {"status": -1, "code": -1, "message": "任务超时", "data": {}}

    # ==================== 分享管理 ====================

    def create_share(
        self,
        file_ids: List[str],
        title: str = "",
        expire_days: int = 0,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建分享链接。
        """
        data = {
            "fid_list": file_ids,
            "title": title,
            "url_type": 2 if password else 1,
            "expired_type": 1 if expire_days == 0 else 2,
        }
        if expire_days > 0:
            data["expired_at"] = int((time.time() + expire_days * 24 * 3600) * 1000)
        if password:
            data["passcode"] = password
        return self._request("POST", "share", json_data=data)

    def get_share_details(self, share_id: str) -> Dict[str, Any]:
        """
        获取分享详细信息（包含 share_url）。
        """
        return self._request(
            "POST", "share/password", json_data={"share_id": share_id}
        )

    def get_my_shares(self, page: int = 1, size: int = 50) -> Dict[str, Any]:
        """
        获取我的分享列表。
        """
        params = {
            "_page": page,
            "_size": size,
            "_order_field": "created_at",
            "_order_type": "desc",
            "_fetch_total": 1,
            "_fetch_notify_follow": 1,
        }
        return self._request("GET", "share/mypage/detail", params=params)

    def delete_share(self, share_id: str) -> Dict[str, Any]:
        """
        删除分享。
        """
        return self._request("POST", "share/delete", json_data={"share_id": share_id})

    # ==================== 转存（已有） ====================

    def get_share_token(self, share_url: str) -> Dict[str, Any]:
        """
        解析分享链接，提取分享 ID 和密码。
        """
        import re
        patterns = [
            r"https://pan\.quark\.cn/s/([a-zA-Z0-9]+).*?密码[：:]?\s*([a-zA-Z0-9]+)",
            r"https://pan\.quark\.cn/s/([a-zA-Z0-9]+)",
            r"quark://share/([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, share_url, re.IGNORECASE)
            if match:
                share_id = match.group(1)
                password = match.group(2) if len(match.groups()) > 1 else None
                if not password:
                    for pw_pattern in [
                        r"密码[：:]?\s*([a-zA-Z0-9]+)",
                        r"提取码[：:]?\s*([a-zA-Z0-9]+)",
                        r"code[：:]?\s*([a-zA-Z0-9]+)",
                    ]:
                        pw_match = re.search(pw_pattern, share_url, re.IGNORECASE)
                        if pw_match:
                            password = pw_match.group(1)
                            break
                return {"share_id": share_id, "password": password}
        return {"share_id": "", "password": None}

    def get_share_token(
        self, share_id: str, password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取分享访问令牌。
        """
        data = {
            "pwd_id": share_id,
            "passcode": password or "",
            "support_visit_limit_private_share": True,
        }
        return self._request(
            "POST", "share/sharepage/token", json_data=data, base_url=self.SHARE_BASE_URL
        )

    def get_share_info(
        self, share_id: str, token: str, pdir_fid: str = "0", page: int = 1, size: int = 50
    ) -> Dict[str, Any]:
        """
        获取分享详细信息。
        """
        params = {
            "pwd_id": share_id,
            "stoken": token,
            "pdir_fid": pdir_fid,
            "force": "0",
            "_page": page,
            "_size": size,
            "_fetch_banner": "1",
            "_fetch_share": "1",
            "_fetch_total": "1",
            "_sort": "file_type:asc,file_name:asc",
        }
        return self._request(
            "GET", "share/sharepage/detail", params=params, base_url=self.SHARE_BASE_URL
        )

    def save_shared_files(
        self,
        share_id: str,
        token: str,
        file_ids: List[str],
        target_folder_id: str = "0",
        pdir_fid: str = "0",
        save_all: bool = False,
        wait_for_completion: bool = True,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """
        转存分享的文件。
        """
        data = {
            "fid_list": file_ids,
            "fid_token_list": [],
            "to_pdir_fid": target_folder_id,
            "pwd_id": share_id,
            "stoken": token,
            "pdir_fid": pdir_fid,
            "pdir_save_all": save_all,
            "exclude_fids": [],
            "scene": "link",
        }
        response = self._request(
            "POST", "share/sharepage/save", json_data=data, base_url=self.SHARE_BASE_URL
        )
        if response.get("status") == 200 and wait_for_completion:
            task_id = response.get("data", {}).get("task_id")
            if task_id:
                task_result = self.wait_for_task(task_id, timeout)
                response["task_result"] = task_result
        return response

    def parse_and_save(
        self,
        share_url: str,
        target_folder_id: str = "0",
        save_all: bool = True,
        wait_for_completion: bool = True,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """
        一站式解析分享链接并转存（与 QuarkPan ShareService.parse_and_save 对齐）。
        """
        parsed = self.parse_share_url(share_url)
        share_id = parsed.get("share_id")
        password = parsed.get("password")
        if not share_id:
            return {
                "status": 400,
                "code": 400,
                "message": "无法解析分享链接",
                "data": {},
            }

        token_resp = self.get_share_token(share_id, password)
        if not isinstance(token_resp, dict) or token_resp.get("status") != 200:
            return {
                "status": token_resp.get("status", 400),
                "code": token_resp.get("code", 400),
                "message": token_resp.get("message", "获取分享令牌失败"),
                "data": {},
            }
        token = (token_resp.get("data") or {}).get("stoken", "")

        share_info = self.get_share_info(share_id, token)
        if not isinstance(share_info, dict) or share_info.get("status") != 200:
            return {
                "status": share_info.get("status", 400),
                "code": share_info.get("code", 400),
                "message": share_info.get("message", "获取分享信息失败"),
                "data": {},
            }
        files = (share_info.get("data") or {}).get("list", [])
        file_ids = [] if save_all else [str(f.get("fid")) for f in files if f.get("fid")]

        result = self.save_shared_files(
            share_id=share_id,
            token=token,
            file_ids=file_ids,
            target_folder_id=target_folder_id,
            pdir_fid="0",
            save_all=save_all,
            wait_for_completion=wait_for_completion,
            timeout=timeout,
        )
        result["share_info"] = {
            "share_id": share_id,
            "file_count": len(files),
            "files": files,
        }
        return result

    # ==================== 上传 ====================

    def pre_upload(
        self,
        file_name: str,
        file_size: int,
        parent_folder_id: str,
        mime_type: str,
    ) -> Dict[str, Any]:
        """
        预上传请求（获取 task_id 和上传参数）。
        """
        current_time = self._get_timestamp()
        data = {
            "ccp_hash_update": True,
            "parallel_upload": True,
            "pdir_fid": parent_folder_id,
            "dir_name": "",
            "size": file_size,
            "file_name": file_name,
            "format_type": mime_type,
            "l_updated_at": current_time,
            "l_created_at": current_time,
        }
        return self._request("POST", "file/upload/pre", json_data=data)

    def update_file_hash(
        self, task_id: str, md5_hash: str, sha1_hash: str
    ) -> Dict[str, Any]:
        """
        更新文件哈希（秒传检测）。
        """
        data = {"task_id": task_id, "md5": md5_hash, "sha1": sha1_hash}
        return self._request("POST", "file/update/hash", json_data=data)

    def get_upload_auth(
        self,
        task_id: str,
        auth_info: str,
        auth_meta: str,
    ) -> Dict[str, Any]:
        """
        获取上传授权。
        """
        data = {
            "task_id": task_id,
            "auth_info": auth_info,
            "auth_meta": auth_meta,
        }
        return self._request("POST", "file/upload/auth", json_data=data)

    def finish_upload(self, task_id: str, obj_key: str = "") -> Dict[str, Any]:
        """
        完成上传。
        """
        data = {"task_id": task_id}
        if obj_key:
            data["obj_key"] = obj_key
        return self._request("POST", "file/upload/finish", json_data=data)

    def get_folder_tree(
        self, folder_id: str = "0", max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        获取目录树。
        """
        params = {"pdir_fid": folder_id, "max_depth": max_depth}
        return self._request("GET", "file/tree", params=params)

    def upload_part_to_oss(
        self,
        upload_url: str,
        data: bytes,
        headers: Dict[str, str],
    ) -> Optional[str]:
        """
        上传分片到 OSS。
        """
        try:
            response = requests.put(upload_url, data=data, headers=headers, timeout=300)
            if response.status_code != 200:
                logger.error(
                    f"【夸克网盘】OSS 上传失败: {response.status_code} {response.text[:200]}"
                )
                return None
            etag = response.headers.get("etag", "").strip('"')
            return etag if etag else None
        except Exception as err:
            logger.error(f"【夸克网盘】OSS 上传异常: {err}")
            return None

    def post_complete_upload(
        self,
        upload_url: str,
        xml_data: str,
        headers: Dict[str, str],
    ) -> bool:
        """
        POST 完成分片合并。
        """
        try:
            response = requests.post(
                upload_url, data=xml_data.encode("utf-8"), headers=headers, timeout=300
            )
            return response.status_code in (200, 203)
        except Exception as err:
            logger.error(f"【夸克网盘】OSS 合并异常: {err}")
            return False
