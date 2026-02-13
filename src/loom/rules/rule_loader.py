"""
规则加载器

负责加载规则文件，支持热加载和文件变化监听。
支持目录递归加载、缓存机制、规则依赖关系管理。
"""

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..utils.logging_config import get_logger
from .markdown_canon import MarkdownCanon

logger = get_logger(__name__)


class RuleLoader:
    """规则加载器"""

    def __init__(self, canon_dir: str = "./canon", recursive: bool = True):
        self.canon_dir = Path(canon_dir)
        self.recursive = recursive
        self.canon_cache: Dict[str, MarkdownCanon] = {}
        self.file_hashes: Dict[str, str] = {}
        self.dependencies: Dict[str, Set[str]] = {}  # 规则依赖关系
        self.observer: Optional[Observer] = None
        self.change_callbacks: List[Callable] = []

        # 确保目录存在
        self.canon_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"RuleLoader initialized with canon_dir={canon_dir}, recursive={recursive}"
        )

    def load_canon(self, canon_name: str = "default") -> Optional[MarkdownCanon]:
        """加载规则集"""
        canon_path = self.canon_dir / f"{canon_name}.md"

        if not canon_path.exists():
            logger.warning(f"Canon file not found: {canon_path}")
            return None

        try:
            # 检查缓存
            cache_key = str(canon_path)
            current_hash = self._calculate_file_hash(canon_path)

            if (
                cache_key in self.canon_cache
                and self.file_hashes.get(cache_key) == current_hash
            ):
                logger.debug(f"Using cached canon: {canon_name}")
                return self.canon_cache[cache_key]

            # 加载文件
            with open(canon_path, "r", encoding="utf-8") as f:
                content = f.read()

            canon = MarkdownCanon(path=canon_path, raw_content=content)

            # 提取依赖关系
            self._extract_dependencies(canon)

            # 验证
            errors = canon.validate()
            if errors:
                logger.warning(f"Canon validation errors for {canon_name}: {errors}")

            # 更新缓存
            self.canon_cache[cache_key] = canon
            self.file_hashes[cache_key] = current_hash

            logger.info(f"Loaded canon '{canon_name}' from {canon_path}")
            logger.info(f"  Sections: {list(canon.sections.keys())}")
            logger.info(f"  Metadata: {canon.metadata}")

            return canon

        except Exception as e:
            logger.error(f"Failed to load canon {canon_name}: {e}")
            return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    def get_all_canons(self) -> Dict[str, MarkdownCanon]:
        """获取所有规则集（向后兼容）"""
        return self.load_all_canons()

    def register_change_callback(self, callback: Callable):
        """注册文件变化回调"""
        self.change_callbacks.append(callback)
        logger.debug(f"Registered change callback: {callback.__name__}")

    def start_watching(self):
        """开始监听文件变化"""
        if self.observer is not None:
            logger.warning("Already watching for changes")
            return

        class CanonChangeHandler(FileSystemEventHandler):
            def __init__(self, loader):
                self.loader = loader

            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(".md"):
                    logger.info(f"Canon file modified: {event.src_path}")
                    self.loader._on_file_changed(event.src_path)

        self.observer = Observer()
        handler = CanonChangeHandler(self)
        self.observer.schedule(handler, str(self.canon_dir), recursive=False)
        self.observer.start()

        logger.info(f"Started watching for changes in {self.canon_dir}")

    def stop_watching(self):
        """停止监听文件变化"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Stopped watching for changes")

    def _on_file_changed(self, file_path: str):
        """处理文件变化"""
        # 清除缓存
        cache_key = file_path
        if cache_key in self.canon_cache:
            del self.canon_cache[cache_key]
            del self.file_hashes[cache_key]
            logger.debug(f"Cleared cache for {file_path}")

        # 调用回调
        for callback in self.change_callbacks:
            try:
                callback(file_path)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")

    def create_default_canon(self, canon_name: str = "default") -> bool:
        """创建默认规则集"""
        canon_path = self.canon_dir / f"{canon_name}.md"

        if canon_path.exists():
            logger.warning(f"Canon file already exists: {canon_path}")
            return False

        default_content = """# 世界观 (World)

这是你的世界的基本设定。描述世界的物理法则、历史背景、主要种族、文化特点等。

# 叙事基调 (Tone)

描述故事的风格和情绪。是黑暗奇幻、轻松喜剧、硬核科幻还是其他风格？

# 冲突解决 (Conflict)

定义如何解决故事中的冲突。是偏向现实主义、戏剧性还是规则化？

# 权限边界 (Permissions)

定义玩家可以做什么，不可以做什么。哪些类型的干预是允许的？

# 因果关系 (Causality)

定义时间、死亡、因果关系等形而上学规则。

# 元信息 (Meta)

version: 1.0.0
author: LOOM User
created: 2025-01-01
"""

        try:
            with open(canon_path, "w", encoding="utf-8") as f:
                f.write(default_content)

            logger.info(f"Created default canon at {canon_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create default canon: {e}")
            return False

    def load_canon_from_path(self, file_path: Path) -> Optional[MarkdownCanon]:
        """从指定路径加载规则集"""
        try:
            cache_key = str(file_path)
            current_hash = self._calculate_file_hash(file_path)

            # 检查缓存
            if (
                cache_key in self.canon_cache
                and self.file_hashes.get(cache_key) == current_hash
            ):
                logger.debug(f"Using cached canon from {file_path}")
                return self.canon_cache[cache_key]

            # 加载文件
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            canon = MarkdownCanon(path=file_path, raw_content=content)

            # 提取依赖关系（在验证之前，因为即使验证失败也可能有依赖）
            self._extract_dependencies(canon)

            # 验证
            errors = canon.validate()
            if errors:
                logger.warning(f"Canon validation errors for {file_path}: {errors}")

            # 更新缓存
            self.canon_cache[cache_key] = canon
            self.file_hashes[cache_key] = current_hash

            logger.info(f"Loaded canon from {file_path}")
            return canon

        except Exception as e:
            logger.error(f"Failed to load canon from {file_path}: {e}")
            return None

    def _extract_dependencies(self, canon: MarkdownCanon):
        """提取规则依赖关系"""
        cache_key = str(canon.path)
        self.dependencies[cache_key] = set()

        # 从元数据中提取依赖
        if "depends_on" in canon.metadata:
            deps = canon.metadata["depends_on"]
            if isinstance(deps, str):
                deps = [deps]

            for dep in deps:
                self.dependencies[cache_key].add(dep)

        # 从内容中提取引用（如"参见：xxx"）
        content = canon.get_full_text()
        import re

        ref_patterns = [
            r"参见[:：]\s*([^\n]+)",
            r"参考[:：]\s*([^\n]+)",
            r"依赖[:：]\s*([^\n]+)",
        ]

        for pattern in ref_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.dependencies[cache_key].add(match.strip())

    def load_all_canons(self) -> Dict[str, MarkdownCanon]:
        """加载所有规则集（支持递归）"""
        canons = {}

        # 构建文件搜索模式
        if self.recursive:
            md_files = list(self.canon_dir.rglob("*.md"))
        else:
            md_files = list(self.canon_dir.glob("*.md"))

        for md_file in md_files:
            # 计算相对路径作为规则名
            rel_path = md_file.relative_to(self.canon_dir)
            canon_name = str(rel_path.with_suffix("")).replace("\\", "/")

            canon = self.load_canon_from_path(md_file)
            if canon:
                canons[canon_name] = canon

        logger.info(f"Loaded {len(canons)} canons from {self.canon_dir}")
        return canons

    def get_dependency_tree(self, canon_name: str = None) -> Dict[str, Any]:
        """获取依赖树"""
        if canon_name:
            # 获取指定规则的依赖树
            canon_path = self.canon_dir / f"{canon_name}.md"
            cache_key = str(canon_path)

            if cache_key not in self.dependencies:
                # 尝试加载规则以提取依赖
                canon = self.load_canon(canon_name)
                if not canon:
                    return {"error": f"Canon {canon_name} not found"}

            deps = self.dependencies.get(cache_key, set())
            return {
                "canon": canon_name,
                "dependencies": list(deps),
                "dependents": self._find_dependents(cache_key),
            }
        else:
            # 获取所有规则的依赖图
            return {
                "dependencies": {k: list(v) for k, v in self.dependencies.items()},
                "has_circular": self._check_circular_dependencies(),
            }

    def _find_dependents(self, canon_path: str) -> List[str]:
        """查找依赖此规则的其他规则"""
        dependents = []
        for other_path, deps in self.dependencies.items():
            if canon_path in deps:
                # 提取规则名
                path_obj = Path(other_path)
                if path_obj.is_relative_to(self.canon_dir):
                    rel_path = path_obj.relative_to(self.canon_dir)
                    canon_name = str(rel_path.with_suffix("")).replace("\\", "/")
                    dependents.append(canon_name)

        return dependents

    def _check_circular_dependencies(self) -> bool:
        """检查循环依赖"""
        visited = set()
        recursion_stack = set()

        def dfs(node: str) -> bool:
            if node in recursion_stack:
                return True  # 发现循环
            if node in visited:
                return False

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in self.dependencies.get(node, set()):
                # 将依赖名转换为路径
                neighbor_path = str(self.canon_dir / f"{neighbor}.md")
                if dfs(neighbor_path):
                    return True

            recursion_stack.remove(node)
            return False

        for node in self.dependencies:
            if dfs(node):
                return True

        return False

    def validate_all(self) -> Dict[str, List[str]]:
        """验证所有规则集"""
        results = {}
        canons = self.load_all_canons()

        for name, canon in canons.items():
            errors = canon.validate()
            if errors:
                results[name] = errors

        return results

    def export_cache_info(self) -> Dict[str, Any]:
        """导出缓存信息"""
        return {
            "cached_files": len(self.canon_cache),
            "cache_keys": list(self.canon_cache.keys()),
            "file_hashes": self.file_hashes,
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
        }

    def clear_cache(self, canon_name: str = None):
        """清空缓存"""
        if canon_name:
            canon_path = self.canon_dir / f"{canon_name}.md"
            cache_key = str(canon_path)
            if cache_key in self.canon_cache:
                del self.canon_cache[cache_key]
                del self.file_hashes[cache_key]
                if cache_key in self.dependencies:
                    del self.dependencies[cache_key]
                logger.info(f"Cleared cache for {canon_name}")
        else:
            self.canon_cache.clear()
            self.file_hashes.clear()
            self.dependencies.clear()
            logger.info("Cleared all cache")

    def get_canon_stats(self) -> Dict[str, Any]:
        """获取规则集统计信息"""
        stats = {
            "canon_dir": str(self.canon_dir),
            "recursive": self.recursive,
            "cached_canons": len(self.canon_cache),
            "available_files": [],
            "dependency_graph_size": len(self.dependencies),
        }

        # 查找所有文件
        if self.recursive:
            md_files = list(self.canon_dir.rglob("*.md"))
        else:
            md_files = list(self.canon_dir.glob("*.md"))

        for md_file in md_files:
            rel_path = md_file.relative_to(self.canon_dir)
            canon_name = str(rel_path.with_suffix("")).replace("\\", "/")

            stats["available_files"].append(
                {
                    "name": canon_name,
                    "path": str(md_file),
                    "size": md_file.stat().st_size if md_file.exists() else 0,
                    "cached": str(md_file) in self.canon_cache,
                }
            )

        return stats
