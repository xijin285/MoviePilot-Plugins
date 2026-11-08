"""通知模块"""
from typing import Optional, List, Any
from datetime import datetime
from app.log import logger
from app.schemas import NotificationType

DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━"


def _fmt_size(num: Any) -> str:
    """字节数转可读大小"""
    try:
        n = float(num or 0)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(n)} B"
            return f"{n:.1f} {unit}"
        n /= 1024
    return ""


def _fmt_targets(targets: Optional[List[Any]]) -> str:
    """备份落点清单转可读文案，如「本地磁盘 + 网盘·夸克 + WebDAV」"""
    labels: List[str] = []
    for item in targets or []:
        if isinstance(item, dict):
            kind = str(item.get("kind") or "").strip()
            raw = str(item.get("label") or "").strip()
            if kind == "local":
                label = "本地磁盘"
            elif kind == "webdav":
                label = "WebDAV"
            elif kind == "cloud":
                label = f"网盘·{raw}" if raw else "网盘"
            else:
                label = raw or kind
        else:
            label = str(item).strip()
        if label and label not in labels:
            labels.append(label)
    return " + ".join(labels)


class NotificationManager:
    """通知管理器类"""

    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name

    # ---------- 内部构造 ----------

    @staticmethod
    def _line(icon: str, key: str, value: str) -> str:
        return f"{icon} {key}：{value}\n"

    def _build(self, *, action: str, success: bool, status_text: str,
               rows: List[str], footer: str, tail: str) -> str:
        """统一拼装通知正文

        :param action: 动作名（备份 / 恢复 / 清理历史记录）
        :param success: 是否成功
        :param status_text: 状态行文案
        :param rows: 明细行（已含 emoji 前缀与换行）
        :param footer: 结尾提示语
        :param tail: 尾部一句话（如「备份已成功完成」）
        """
        if success:
            text = f"{DIVIDER}\n"
            text += self._line("✅", "状态", status_text)
        else:
            bad_divider = "❌" + DIVIDER[1:-1] + "❌"
            text = f"{bad_divider}\n"
            text += self._line("❗", "状态", status_text)

        if rows:
            text += "\n" + "".join(rows)

        text += "\n"
        text += f"{bad_divider if not success else DIVIDER}\n"
        text += f"🕗 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += tail
        if footer:
            text += f"\n{footer}"
        return text

    def _send(self, title: str, text: str, kind: str):
        try:
            self.plugin.post_message(mtype=NotificationType.Plugin, title=title, text=text)
            logger.info(f"{self.plugin_name} 发送{kind}通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送{kind}通知失败: {e}")

    # ---------- 对外接口 ----------

    def send_backup_notification(self, success: bool, message: str = "", filename: Optional[str] = None,
                                 notification_style: int = 0, notify: bool = True,
                                 targets: Optional[List[Any]] = None,
                                 failed: Optional[List[Any]] = None,
                                 size: Any = 0, elapsed: Any = 0):
        """发送备份通知

        :param targets: 本次备份的落点清单，如 [{"kind": "local", "label": "本地磁盘"}]
        :param size: 备份文件大小（字节）
        :param elapsed: 耗时（秒）
        """
        if not notify:
            return

        title = f"🛠️ {self.plugin_name} · 备份{'成功' if success else '失败'}"
        rows: List[str] = []
        router = str(getattr(self.plugin, '_original_ikuai_url', '') or '-')
        rows.append(self._line("🔗", "路由", router))
        if filename:
            rows.append(self._line("📄", "文件", filename))

        target_text = _fmt_targets(targets)
        if target_text:
            rows.append(self._line("💾", "落点", target_text))
        failed_text = "、".join([str(x) for x in (failed or []) if str(x).strip()])
        if failed_text:
            rows.append(self._line("⚠️", "未成功", failed_text))

        meta: List[str] = []
        size_text = _fmt_size(size)
        if size_text:
            rows.append(self._line("📦", "大小", size_text))
        try:
            sec = float(elapsed or 0)
        except (TypeError, ValueError):
            sec = 0
        if sec > 0:
            rows.append(self._line("⏱️", "耗时", f"{sec:g} 秒"))

        if message:
            rows.append(self._line("📋", "详情", message.strip()))

        tail = "\n✨ 备份已成功完成" if success else "\n💡 请检查路由器连通性、账号密码与备份目标配置"
        text = self._build(
            action="备份",
            success=success,
            status_text="备份成功" if success else "备份失败",
            rows=rows,
            footer="",
            tail=tail,
        )
        self._send(title, text, "备份")

    def send_restore_notification(self, success: bool, message: str = "", filename: str = "",
                                  notification_style: int = 0, notify: bool = True,
                                  source: str = "", elapsed: Any = 0, restore_point: str = ""):
        """发送恢复通知"""
        if not notify:
            return

        title = f"🛠️ {self.plugin_name} · 恢复{'成功' if success else '失败'}"
        rows: List[str] = []
        rows.append(self._line("🔗", "路由", str(getattr(self.plugin, '_original_ikuai_url', '') or '-')))
        if filename:
            rows.append(self._line("📄", "文件", filename))
        if source:
            rows.append(self._line("💾", "来源", source))
        if restore_point:
            rows.append(self._line("🛟", "恢复点", restore_point))
        try:
            rsec = float(elapsed or 0)
        except (TypeError, ValueError):
            rsec = 0
        if rsec > 0:
            rows.append(self._line("⏱️", "耗时", f"{rsec:g} 秒"))
        if message:
            rows.append(self._line("📋", "详情", message.strip()))

        tail = "\n✨ 配置已恢复，请确认网络是否正常" if success else "\n💡 恢复失败，路由配置未变更"
        text = self._build(
            action="恢复",
            success=success,
            status_text="恢复成功" if success else "恢复失败",
            rows=rows,
            footer="",
            tail=tail,
        )
        self._send(title, text, "恢复")

    def send_clear_history_notification(self, success: bool, message: str,
                                        notification_style: int = 0, notify: bool = True):
        """发送清理历史记录通知"""
        if not notify:
            return

        title = f"🛠️ {self.plugin_name} · 清理历史记录"
        rows: List[str] = []
        if message:
            rows.append(self._line("📋", "详情", message.strip()))

        text = self._build(
            action="清理",
            success=success,
            status_text="清理成功" if success else "清理失败",
            rows=rows,
            footer="",
            tail="",
        )
        self._send(title, text, "清理历史记录")
