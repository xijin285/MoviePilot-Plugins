#!/usr/bin/env python3
"""
MoviePilot V3 插件仓库自检。

检查项：
1、package.v3.json 与 plugins.v3/ 一一对应，目录名、类名、版本号、显示名一致；
2、V3 源码不得残留 V3 兼容层未覆盖的旧宿主导入路径；
3、Vue 联邦插件的 dist/assets/remoteEntry.js 必须随仓库提交；
4、所有 Python 文件可编译；
5、相对导入（from .xxx import）必须能解析到插件目录内的实际文件——
   防止「删除本地模块（如 compat.py）后仍有文件引用它」导致宿主加载失败。

用法：python scripts/validate_v3_plugins.py
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V3_DIR = ROOT / "plugins.v3"
V3_INDEX = ROOT / "package.v3.json"

# V3 兼容层（app/runtime/compat/manifest.py）已映射的旧路径，插件可继续导入
COMPAT_MAPPED_PREFIXES = {
    "app.log",
    "app.plugins",
    "app.utils.http",
    "app.core.config",
    "app.core.event",
    "app.core.cache",
    "app.core.meta",
    "app.core.metainfo",
    "app.chain.media",
    "app.db.site_oper",
    "app.db.plugindata_oper",
    "app.helper.sites",
    "app.helper.cookiecloud",
    "app.helper.storage",
    "app.schemas",
}

# V3 中仍物理存在的旧模块（未被 compat 映射，但路径有效）
PHYSICAL_LEGACY_PREFIXES = {
    "app.modules.filemanager.storages",
}

# 明确不可用的旧路径：V3 已删除且 compat 未映射
FORBIDDEN_PREFIXES = {
    "app.logs",  # 注意是复数，V3 只有 app.log
}

IMPORT_RE = re.compile(r"^\s*(?:from\s+(app[\w.]*)\s+import|import\s+(app[\w.]*))", re.M)


def is_allowed(path: str) -> bool:
    if path == "app" or path.startswith("app.sdk"):
        return True
    for prefix in FORBIDDEN_PREFIXES:
        if path == prefix or path.startswith(prefix + "."):
            return False
    for prefix in PHYSICAL_LEGACY_PREFIXES | COMPAT_MAPPED_PREFIXES:
        if path == prefix or path.startswith(prefix + "."):
            return True
    return False


def plugin_meta(init_file: Path) -> dict:
    """从 __init__.py 的类属性里读取插件身份信息。"""
    source = init_file.read_text(encoding="utf-8")
    meta = {}
    for attr in ("plugin_name", "plugin_version"):
        match = re.search(rf"^\s{{4}}{attr}\s*=\s*['\"]([^'\"]+)['\"]", source, re.M)
        if match:
            meta[attr] = match.group(1)
    match = re.search(r"^\s*class\s+(\w+)\s*\(\s*_PluginBase\s*\)", source, re.M)
    if match:
        meta["class_name"] = match.group(1)
    meta["is_vue"] = bool(re.search(r"return\s+['\"]vue['\"]", source))
    return meta


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not V3_INDEX.exists():
        print("❌ 缺少 package.v3.json")
        return 1

    index = json.loads(V3_INDEX.read_text(encoding="utf-8"))
    index_ids = {pid.lower(): pid for pid in index}

    # 1) 索引 -> 目录
    for pid, entry in index.items():
        plugin_dir = V3_DIR / pid.lower()
        init_file = plugin_dir / "__init__.py"
        if not init_file.exists():
            errors.append(f"{pid}: package.v3.json 有条目，但 {plugin_dir} 缺少 __init__.py")
            continue

        meta = plugin_meta(init_file)
        if meta.get("class_name", "").lower() != pid.lower():
            errors.append(
                f"{pid}: 类名 {meta.get('class_name')!r} 与市场 ID 不一致（插件分身/配置前缀会错位）"
            )
        if meta.get("plugin_version") != entry.get("version"):
            errors.append(
                f"{pid}: 源码 plugin_version={meta.get('plugin_version')!r} "
                f"≠ 市场 version={entry.get('version')!r}"
            )
        if entry.get("name") and meta.get("plugin_name") != entry["name"]:
            warnings.append(
                f"{pid}: 市场名 {entry['name']!r} 与 plugin_name {meta.get('plugin_name')!r} 不同（仅展示差异）"
            )
        if not entry.get("system_version"):
            warnings.append(f"{pid}: 未声明 system_version，V3 不会做宿主版本准入")

        # 3) Vue 联邦产物
        if meta.get("is_vue"):
            entry_file = plugin_dir / "dist" / "assets" / "remoteEntry.js"
            if not entry_file.exists():
                errors.append(f"{pid}: Vue 联邦插件缺少 dist/assets/remoteEntry.js（安装后页面会白屏）")

    # 2) 目录 -> 索引 + 导入审计
    if V3_DIR.exists():
        for plugin_dir in sorted(p for p in V3_DIR.iterdir() if p.is_dir()):
            if plugin_dir.name.lower() not in index_ids:
                warnings.append(f"{plugin_dir.name}: 目录存在但未登记到 package.v3.json")

            for py_file in plugin_dir.rglob("*.py"):
                if "node_modules" in py_file.parts:
                    continue
                rel = py_file.relative_to(ROOT)
                try:
                    source = py_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue

                for match in IMPORT_RE.finditer(source):
                    module = match.group(1) or match.group(2)
                    if module and not is_allowed(module):
                        errors.append(f"{rel}: 导入了 V3 不可用的宿主路径 {module}")

                # 4) 语法编译（不落盘，避免产生 __pycache__）
                try:
                    compile(source, str(py_file), "exec")
                except SyntaxError as err:
                    errors.append(f"{rel}: 语法错误 第 {err.lineno} 行 {err.msg}")

                # 5) 相对导入必须能解析到插件目录内的实际文件
                try:
                    tree = ast.parse(source)
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if not (isinstance(node, ast.ImportFrom) and node.level):
                        continue
                    base = py_file.parent
                    for _ in range(node.level - 1):
                        base = base.parent
                    target = base
                    if node.module:
                        for part in node.module.split("."):
                            target = target / part
                    candidates = [
                        target.with_suffix(".py"),
                        target / "__init__.py",
                    ]
                    if not any(c.is_file() for c in candidates):
                        names = ", ".join(n.name for n in node.names)
                        errors.append(
                            f"{rel}: 相对导入无法解析 "
                            f"from {'.' * node.level}{node.module or ''} import {names}"
                            f"（{'、'.join(str(c.relative_to(plugin_dir)) for c in candidates)} 均不存在）"
                        )

    for warning in warnings:
        print(f"⚠️  {warning}")
    for error in errors:
        print(f"❌ {error}")

    if errors:
        print(f"\n校验失败：{len(errors)} 个错误，{len(warnings)} 个提示")
        return 1

    print(f"✅ 校验通过：{len(index)} 个 V3 插件，{len(warnings)} 个提示")
    return 0


if __name__ == "__main__":
    sys.exit(main())
