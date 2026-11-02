"""
MoviePilot V2 / V3 双版本兼容层。

MoviePilot V3 把宿主能力收敛到 `app.sdk` 稳定出口，并对 `app.utils.*`、
`app.plugins` 等旧路径提供兼容映射；但 `app.logs` 等历史路径并不在兼容清单内。
这里统一按「V3 SDK 优先、V2 旧路径兜底」的顺序导入，使同一份插件代码可以同时
运行在 V2 与 V3 宿主上。

新增宿主依赖时请只在此文件集中处理，业务代码不要直接导入 app.* 旧路径。
"""

# ============ 运行版本判定 ============
try:  # MoviePilot V3 起提供 app.sdk 稳定 SDK
    import app.sdk  # noqa: F401

    IS_V3 = True
except Exception:  # pragma: no cover - V2 宿主没有 app.sdk
    IS_V3 = False

# ============ 日志 ============
try:  # V3 稳定出口
    from app.sdk.logging import logger
except ImportError:
    try:  # V2
        from app.log import logger
    except ImportError:  # 部分分支版本使用 app.logs
        from app.logs import logger

# ============ 插件基类 ============
try:  # V3
    from app.sdk.plugin import _PluginBase
except ImportError:  # V2
    from app.plugins import _PluginBase

# ============ HTTP 工具 ============
try:  # V3
    from app.sdk.network import RequestUtils
except ImportError:  # V2
    from app.utils.http import RequestUtils

# ============ 插件运行时（仅用于清理旧版独立服务登记） ============
try:
    import app.plugins as plugin_runtime
except ImportError:  # pragma: no cover - 理论上不会发生
    plugin_runtime = None


__all__ = [
    "IS_V3",
    "RequestUtils",
    "_PluginBase",
    "logger",
    "plugin_runtime",
]
