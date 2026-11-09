"""
Proxmox VE REST API 客户端（只读监控）
通过 /api2/json 接口获取节点状态、RRD 监控数据、存储、任务记录等
认证：access/ticket（Cookie + CSRF），票据缓存约 2 小时自动续期
"""
import time
import threading

import requests
import urllib3

from app.log import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VALID_TIMEFRAMES = ("hour", "day", "week", "month", "year")

# 任务类型 -> 展示名
TASK_TYPE_NAMES = {
    "vzdump": "备份", "qmstart": "启动虚拟机", "qmstop": "停止虚拟机",
    "qmreboot": "重启虚拟机", "qmshutdown": "关闭虚拟机", "qmcreate": "创建虚拟机",
    "qmdestroy": "删除虚拟机", "qmmigrate": "迁移虚拟机", "qmclone": "克隆虚拟机",
    "vzcreate": "创建容器", "vzstart": "启动容器", "vzstop": "停止容器",
    "vzshutdown": "关闭容器", "vzdestroy": "删除容器", "vzmigrate": "迁移容器",
    "vzdump_hookscript": "备份脚本", "aptupdate": "更新软件源", "aptupgrade": "系统升级",
    "vncshell": "控制台", "vncproxy": "控制台", "spiceproxy": "控制台",
    "startall": "全部启动", "stopall": "全部停止", "srvstart": "启动服务",
    "srvstop": "停止服务", "storagecfg": "存储配置", "hostsresolve": "Hosts 配置",
    "ceph": "Ceph", " replication": "复制", "jobs": "计划任务",
}


class PveApiClient:
    """PVE REST API 客户端，线程安全，票据自动缓存续期"""

    def __init__(self, host, port=8006, username="root@pam", password="",
                 timeout=12, verify=False):
        self.host = str(host).strip()
        self.port = int(port or 8006)
        if "@" not in username:
            username = f"{username}@pam"
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify = verify
        self._base = f"https://{self.host}:{self.port}/api2/json"
        self._ticket = None
        self._csrf = None
        self._ticket_time = 0
        self._lock = threading.Lock()

    # ---------- 认证 ----------
    def _login(self):
        resp = requests.post(
            f"{self._base}/access/ticket",
            data={"username": self.username, "password": self.password},
            verify=self.verify, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json().get("data") or {}
        self._ticket = data.get("ticket")
        self._csrf = data.get("CSRFPreventionToken")
        self._ticket_time = time.time()
        if not self._ticket:
            raise RuntimeError("PVE 登录失败：未获取到 ticket")

    def _session_get(self, path, params=None):
        with self._lock:
            # 票据有效期约 2 小时，提前 5 分钟续期
            if not self._ticket or time.time() - self._ticket_time > 6900:
                self._login()
            resp = requests.get(
                f"{self._base}{path}", params=params,
                cookies={"PVEAuthCookie": self._ticket},
                verify=self.verify, timeout=self.timeout)
            if resp.status_code == 401:
                # 票据失效，重新登录重试一次
                self._login()
                resp = requests.get(
                    f"{self._base}{path}", params=params,
                    cookies={"PVEAuthCookie": self._ticket},
                    verify=self.verify, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")

    def _session_post(self, path, data=None):
        with self._lock:
            if not self._ticket or time.time() - self._ticket_time > 6900:
                self._login()
            resp = requests.post(
                f"{self._base}{path}", data=data or {},
                cookies={"PVEAuthCookie": self._ticket},
                headers={"CSRFPreventionToken": self._csrf},
                verify=self.verify, timeout=self.timeout)
            if resp.status_code == 401:
                self._login()
                resp = requests.post(
                    f"{self._base}{path}", data=data or {},
                    cookies={"PVEAuthCookie": self._ticket},
                    headers={"CSRFPreventionToken": self._csrf},
                    verify=self.verify, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("data")

    # ---------- 数据接口 ----------
    def _first_node(self):
        nodes = self._session_get("/nodes") or []
        for n in nodes:
            if n.get("status") == "online":
                return n.get("node")
        return nodes[0].get("node") if nodes else None

    def node_status(self, node=None):
        node = node or self._first_node()
        return self._session_get(f"/nodes/{node}/status") or {}

    def rrddata(self, timeframe="hour", node=None):
        if timeframe not in VALID_TIMEFRAMES:
            timeframe = "hour"
        node = node or self._first_node()
        return self._session_get(f"/nodes/{node}/rrddata",
                                 {"timeframe": timeframe, "cf": "AVERAGE"}) or []

    def storages(self, node=None):
        node = node or self._first_node()
        return self._session_get(f"/nodes/{node}/storage") or []

    def recent_tasks(self, limit=15, node=None):
        node = node or self._first_node()
        return self._session_get(f"/nodes/{node}/tasks", {"limit": limit}) or []

    def guest_rrddata(self, vmid, gtype="qemu", timeframe="hour", node=None):
        if timeframe not in VALID_TIMEFRAMES:
            timeframe = "hour"
        node = node or self._first_node()
        return self._session_get(
            f"/nodes/{node}/{gtype}/{vmid}/rrddata",
            {"timeframe": timeframe, "cf": "AVERAGE"}) or []

    def qemu_monitor(self, vmid, command, node=None):
        """向 QEMU monitor 发送命令（如 screendump）"""
        node = node or self._first_node()
        return self._session_post(
            f"/nodes/{node}/qemu/{vmid}/monitor",
            {"command": command}) or {}

    def guest_status(self, vmid, gtype="qemu", node=None):
        node = node or self._first_node()
        return self._session_get(f"/nodes/{node}/{gtype}/{vmid}/status/current") or {}

    # ---------- 聚合 ----------
    def node_monitor(self, timeframe="hour"):
        """节点监控聚合：状态 + RRD 曲线 + 存储 + 最近任务"""
        node = self._first_node()
        status = self.node_status(node)
        rrd = self.rrddata(timeframe, node)
        stores = self.storages(node)
        tasks = self.recent_tasks(15, node)
        cpuinfo = status.get("cpuinfo") or {}
        mem = status.get("memory") or {}
        swap = status.get("swap") or {}
        rootfs = status.get("rootfs") or {}
        return {
            "node": node,
            "pveversion": status.get("pveversion"),
            "kversion": status.get("kversion"),
            "cpu_model": cpuinfo.get("model"),
            "cpu_cores": cpuinfo.get("cores"),
            "cpu_sockets": cpuinfo.get("sockets"),
            "cpu": status.get("cpu", 0),
            "uptime": status.get("uptime", 0),
            "loadavg": status.get("loadavg") or [],
            "memory": {"used": mem.get("used", 0), "total": mem.get("total", 0),
                       "available": mem.get("available", 0)},
            "swap": {"used": swap.get("used", 0), "total": swap.get("total", 0)},
            "rootfs": {"used": rootfs.get("used", 0), "total": rootfs.get("total", 0)},
            "rrd": rrd,
            "storages": [{
                "storage": s.get("storage"), "type": s.get("type"),
                "content": s.get("content"), "active": s.get("active"),
                "used": s.get("used", 0), "total": s.get("total", 0),
                "used_fraction": s.get("used_fraction", 0),
            } for s in stores],
            "tasks": [{
                "upid": t.get("upid"), "type": t.get("type"),
                "desc": TASK_TYPE_NAMES.get(t.get("type"), t.get("type")),
                "status": t.get("status"), "vmid": t.get("id") or t.get("vmid"),
                "user": t.get("user"), "starttime": t.get("starttime"),
                "endtime": t.get("endtime"),
            } for t in tasks],
        }

    def guest_monitor(self, vmid, gtype="qemu", timeframe="hour"):
        """单虚机/容器监控聚合：当前状态 + RRD 曲线"""
        st = self.guest_status(vmid, gtype, None)
        rrd = self.guest_rrddata(vmid, gtype, timeframe, None)
        return {
            "vmid": vmid, "type": gtype,
            "name": st.get("name"), "status": st.get("status"),
            "uptime": st.get("uptime"), "cpus": st.get("cpus"),
            "cpu": st.get("cpu", 0),
            "mem": st.get("mem", 0), "maxmem": st.get("maxmem", 0),
            "netin": st.get("netin", 0), "netout": st.get("netout", 0),
            "disk": st.get("disk", 0), "maxdisk": st.get("maxdisk", 0),
            "rrd": rrd,
        }
