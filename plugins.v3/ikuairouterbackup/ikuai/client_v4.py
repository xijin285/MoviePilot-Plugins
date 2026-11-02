"""爱快 v4 REST 客户端（API 令牌 / Bearer 认证）

专用于爱快 iKuai OS 4.x 的 /api/v4.0 REST 接口，通过「登录管理 → 个人 API 令牌」
生成的令牌认证（Authorization: Bearer <token>）。

注意：v4 令牌只能做"控制面"操作（备份列表/创建/删除/恢复/监控），
官方当前固件没有暴露备份文件"下载"端点，备份文件下载仍需走 v3 密码会话
（/Action/login → sess_key → /Action/download），由 IkuaiClient 内部处理。
"""
import time
from datetime import datetime
from typing import Optional, Dict, List
from urllib.parse import urljoin, quote

import urllib3
import requests

# 禁用爱快路由器自签名证书的 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.log import logger


class IkuaiClientV4:
    """爱快 iKuai OS 4.x REST 客户端（Bearer 令牌）"""

    def __init__(self, url: str, token: str, plugin_name: str = ""):
        """
        :param url: 爱快路由器地址（如 https://192.168.5.56）
        :param token: 个人 API 令牌字符串
        :param plugin_name: 插件名称
        """
        self.url = url.rstrip('/')
        self.token = token.strip()
        self.plugin_name = plugin_name
        self.api_base = "/api/v4.0"
        self.session = None
        self._init_session()

    def _init_session(self):
        """初始化 Session，禁用自签名证书验证"""
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        })

    def _request(self, method: str, path: str, body: dict = None) -> Optional[dict]:
        """
        发起 v4 REST 请求，统一解析 {\"code\":0,\"message\":\"Success\",\"results\":...} 信封。
        :return: results 内容（无 results 时返回完整响应字典）；失败返回 None
        """
        url = urljoin(self.url, self.api_base + path)
        try:
            resp = self.session.request(method, url, json=body, timeout=20)
            resp.raise_for_status()
            res_json = resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} v4 [{method} {path}] 请求失败: {e}")
            return None
        except ValueError:
            logger.error(f"{self.plugin_name} v4 [{method} {path}] 响应非JSON: {getattr(resp, 'text', '')[:200]}")
            return None

        # v4 统一响应格式
        if res_json.get("code") == 0 and str(res_json.get("message", "")).lower() in ["success", "ok", "成功"]:
            results = res_json.get("results")
            if isinstance(results, dict) and results:
                return results
            # 无 results 或 results 为空：说明操作成功但没有额外内容（如创建/删除备份）
            return res_json
        else:
            err_msg = res_json.get("message") or res_json.get("ErrMsg") or "未知错误"
            logger.error(f"{self.plugin_name} v4 [{method} {path}] 失败: {res_json}")
            # 把错误信息挂到返回的 dict，便于上层区分"删除动作成功但缺返回"的情况
            res_json["_error"] = True
            return res_json

    def validate(self) -> bool:
        """校验令牌是否有效（调用监控接口），成功即认为令牌有效且具备读取权限。"""
        results = self._request("GET", "/monitoring/system")
        return bool(results and not results.get("_error") and results.get("sysinfo") is not None)

    def get_backup_list(self) -> Optional[List[Dict]]:
        """
        获取备份文件列表。v4 记录字段：id/timestamp(Unix秒)/filename/filesize/version/backtype。
        为兼容下游按 date 排序，会把 timestamp 转为可读 date 字符串补进记录。
        """
        results = self._request("GET", "/system/backup")
        if not results or results.get("_error"):
            return None
        backup_info = results.get("backup_info") or []
        normalized = []
        for item in backup_info:
            if not isinstance(item, dict):
                continue
            entry = dict(item)
            ts = entry.get("timestamp")
            if ts and not entry.get("date"):
                try:
                    entry["date"] = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, OSError):
                    entry["date"] = ""
            normalized.append(entry)
        logger.info(f"{self.plugin_name} v4 成功获取到 {len(normalized)} 条备份记录。")
        return normalized

    def create_backup(self) -> Optional[dict]:
        """触发创建备份。v4: POST /system/backup body {}。"""
        return self._request("POST", "/system/backup", {})

    def delete_backup(self, filename: str) -> Optional[dict]:
        """删除备份。v4: DELETE /system/backup?srcfile=<文件名>（必须用 query 参数）。"""
        path = f"/system/backup?srcfile={quote(filename)}"
        return self._request("DELETE", path)

    def get_system_info(self) -> Optional[Dict]:
        """获取系统状态（CPU/内存/在线用户/流量/版本）。v4: GET /monitoring/system"""
        results = self._request("GET", "/monitoring/system")
        if not results or results.get("_error"):
            return None
        sysinfo = results.get("sysinfo") or {}
        info = {}
        cpu_list = sysinfo.get("cpu", [])
        if cpu_list:
            try:
                info["cpu_usage"] = float(str(cpu_list[-1]).replace("%", ""))
            except (ValueError, TypeError):
                info["cpu_usage"] = 0.0
        memory = sysinfo.get("memory", {})
        if memory and memory.get("used"):
            try:
                info["mem_usage"] = float(str(memory["used"]).replace("%", ""))
            except (ValueError, TypeError):
                info["mem_usage"] = 0.0
        if sysinfo.get("uptime") is not None:
            info["uptime"] = sysinfo["uptime"]
        online_user = sysinfo.get("online_user", {})
        if online_user:
            info["online_users"] = online_user.get("count", 0)
            info["online_wired"] = online_user.get("count_wired", 0)
            info["online_wireless"] = online_user.get("count_wireless", 0)
        stream = sysinfo.get("stream", {})
        if stream:
            info["connect_num"] = stream.get("connect_num", 0)
            info["upload_speed"] = stream.get("upload", 0)
            info["download_speed"] = stream.get("download", 0)
        verinfo = sysinfo.get("verinfo", {})
        if verinfo:
            info["version"] = verinfo.get("verstring", "")
            info["build_date"] = str(verinfo.get("build_date", ""))
            info["arch"] = verinfo.get("arch", "")
        info["hostname"] = sysinfo.get("hostname", "")
        return info
