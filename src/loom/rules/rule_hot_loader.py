"""
规则热加载器

提供运行时规则更新功能，支持：
1. 文件变化监视和自动重新加载
2. 会话级规则隔离
3. 版本控制和回滚机制
4. 缓存管理和性能优化
5. 变化通知和事件处理

设计目标：实现无中断的热加载，确保规则更新不影响正在进行的会话。
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ..utils.logging_config import get_logger
from .advanced_markdown_canon import AdvancedMarkdownCanon
from .markdown_canon import MarkdownCanon
from .rule_validator import RuleValidator, ValidationReport

logger = get_logger(__name__)


class ChangeType(Enum):
    """变化类型"""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChange:
    """文件变化"""

    path: Path
    change_type: ChangeType
    timestamp: datetime = field(default_factory=datetime.now)
    old_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonVersion:
    """规则版本"""

    version_id: str
    canon: MarkdownCanon
    timestamp: datetime
    hash: str
    validation_report: Optional[ValidationReport] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """会话状态"""

    session_id: str
    canon_version: str  # 使用的规则版本ID
    created_at: datetime
    last_accessed: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuleHotLoader:
    """规则热加载器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.watched_paths: Set[Path] = set()
        self.file_watchers: Dict[str, Any] = {}  # type: ignore[valid-type]
        self.callbacks: List[Callable] = []
        self.canon_cache: Dict[str, CanonVersion] = {}  # 路径 -> 最新版本
        self.version_history: Dict[str, List[CanonVersion]] = {}  # 路径 -> 版本历史
        self.sessions: Dict[str, SessionState] = {}  # 会话ID -> 会话状态
        self.validator = RuleValidator(self.config.get("validator_config", {}))

        # 性能统计
        self.stats = {
            "total_loads": 0,
            "cache_hits": 0,
            "validation_passes": 0,
            "validation_fails": 0,
            "last_reload": None,
        }

        logger.info("RuleHotLoader initialized")

    def watch(self, path: Path, recursive: bool = True) -> bool:
        """监视规则文件变化"""
        path_str = str(path)

        if path_str in self.file_watchers:
            logger.warning(f"Already watching path: {path}")
            return False

        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            return False

        try:
            # 创建观察者
            observer = Observer()
            handler = CanonFileHandler(self)

            observer.schedule(handler, path_str, recursive=recursive)
            observer.start()

            self.file_watchers[path_str] = observer
            self.watched_paths.add(path)

            logger.info(f"Started watching rules at {path} (recursive={recursive})")
            return True

        except Exception as e:
            logger.error(f"Failed to start watching {path}: {e}")
            return False

    def unwatch(self, path: Path) -> bool:
        """停止监视规则文件"""
        path_str = str(path)

        if path_str not in self.file_watchers:
            logger.warning(f"Not watching path: {path}")
            return False

        try:
            observer = self.file_watchers[path_str]
            observer.stop()
            observer.join()

            del self.file_watchers[path_str]
            self.watched_paths.remove(path)

            logger.info(f"Stopped watching rules at {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop watching {path}: {e}")
            return False

    def register_callback(
        self, callback: Callable[[FileChange, MarkdownCanon], None]
    ) -> None:
        """注册变化回调"""
        self.callbacks.append(callback)
        logger.debug(
            f"Registered change callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}"
        )

    def _handle_file_change(self, event: FileSystemEvent) -> None:
        """处理文件变化"""
        try:
            # event.src_path 可能是 bytes，需要转换为 str
            src_path = (
                event.src_path.decode("utf-8")
                if isinstance(event.src_path, bytes)
                else event.src_path
            )
            path = Path(src_path)

            # 确定变化类型
            if event.event_type == "created":
                change_type = ChangeType.CREATED
            elif event.event_type == "modified":
                change_type = ChangeType.MODIFIED
            elif event.event_type == "deleted":
                change_type = ChangeType.DELETED
            elif event.event_type == "moved":
                change_type = ChangeType.MOVED
                # 对于移动事件，还需要处理目标路径
                dest_path = (
                    Path(event.dest_path) if hasattr(event, "dest_path") else None
                )
            else:
                logger.warning(f"Unknown event type: {event.event_type}")
                return

            # 创建变化记录
            file_change = FileChange(
                path=path,
                change_type=change_type,
                metadata={
                    "event_type": event.event_type,
                    "is_directory": event.is_directory,
                },
            )

            logger.info(f"Rule file changed: {path} ({change_type.value})")

            # 处理变化
            if change_type == ChangeType.MODIFIED:
                self._reload_canon(path)
            elif change_type == ChangeType.DELETED:
                self._remove_canon(path)
            elif change_type == ChangeType.CREATED:
                self._load_canon(path)

            # 通知回调
            canon = self.get_canon(path)
            if canon:
                for callback in self.callbacks:
                    try:
                        callback(file_change, canon)
                    except Exception as e:
                        logger.error(f"Error in change callback: {e}")

        except Exception as e:
            logger.error(f"Error handling file change: {e}")

    def _load_canon(
        self, path: Path, use_cache: bool = True
    ) -> Optional[MarkdownCanon]:
        """加载规则集"""
        cache_key = str(path)

        # 检查缓存
        if use_cache and cache_key in self.canon_cache:
            cached_version = self.canon_cache[cache_key]
            current_hash = self._calculate_file_hash(path)

            if current_hash and cached_version.hash == current_hash:
                self.stats["cache_hits"] += 1
                logger.debug(f"Using cached canon: {path}")
                return cached_version.canon

        try:
            # 读取文件
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # 创建规则集对象
            if self.config.get("use_advanced_parser", True):
                canon = AdvancedMarkdownCanon(path, raw_content=content)
            else:
                canon = MarkdownCanon(path, raw_content=content)

            # 验证规则
            validation_report = self.validator.validate_sync(canon)

            # 计算哈希
            file_hash = self._calculate_file_hash(path) or self._calculate_content_hash(
                content
            )

            # 创建版本
            version_id = f"{path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            version = CanonVersion(
                version_id=version_id,
                canon=canon,
                timestamp=datetime.now(),
                hash=file_hash,
                validation_report=validation_report,
            )

            # 更新缓存和历史
            self.canon_cache[cache_key] = version
            self.version_history.setdefault(cache_key, []).append(version)

            # 限制历史记录数量
            max_history = self.config.get("max_version_history", 10)
            if len(self.version_history[cache_key]) > max_history:
                self.version_history[cache_key] = self.version_history[cache_key][
                    -max_history:
                ]

            # 更新统计
            self.stats["total_loads"] += 1
            if validation_report.is_valid():
                self.stats["validation_passes"] += 1
            else:
                self.stats["validation_fails"] += 1
            self.stats["last_reload"] = datetime.now()

            logger.info(f"Loaded canon from {path} (version: {version_id})")
            logger.info(
                f"  Validation: {'PASS' if validation_report.is_valid() else 'FAIL'} "
                f"(score: {validation_report.validation_score:.2%})"
            )

            return canon

        except Exception as e:
            logger.error(f"Failed to load canon {path}: {e}")
            return None

    def _reload_canon(self, path: Path) -> Optional[MarkdownCanon]:
        """重新加载规则集"""
        logger.info(f"Reloading canon: {path}")
        return self._load_canon(path, use_cache=False)

    def _remove_canon(self, path: Path):
        """移除规则集"""
        cache_key = str(path)

        if cache_key in self.canon_cache:
            del self.canon_cache[cache_key]
            logger.info(f"Removed canon from cache: {path}")

        # 通知会话
        self._notify_sessions_of_removal(path)

    def _notify_sessions_of_removal(self, path: Path):
        """通知会话规则已被移除"""
        for session_id, session in self.sessions.items():
            # 检查会话是否在使用此规则
            # 简化实现：假设会话使用最新版本
            pass

    def get_canon(
        self, path: Path, session_id: Optional[str] = None
    ) -> Optional[MarkdownCanon]:
        """获取规则集（带会话支持）"""
        # 加载或获取缓存的规则
        canon = self._load_canon(path)

        if not canon:
            return None

        # 更新会话状态
        if session_id:
            self._update_session(session_id, path)

        return canon

    def get_canon_with_validation(
        self, path: Path
    ) -> Tuple[Optional[MarkdownCanon], Optional[ValidationReport]]:
        """获取规则集及其验证报告"""
        cache_key = str(path)

        if cache_key in self.canon_cache:
            version = self.canon_cache[cache_key]
            return version.canon, version.validation_report

        # 加载新版本
        canon = self._load_canon(path, use_cache=False)
        if canon and cache_key in self.canon_cache:
            version = self.canon_cache[cache_key]
            return canon, version.validation_report

        return None, None

    def _update_session(self, session_id: str, canon_path: Path):
        """更新会话状态"""
        cache_key = str(canon_path)

        if cache_key not in self.canon_cache:
            return

        version = self.canon_cache[cache_key]

        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.canon_version = version.version_id
            session.last_accessed = datetime.now()
        else:
            session = SessionState(
                session_id=session_id,
                canon_version=version.version_id,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
            )
            self.sessions[session_id] = session

        logger.debug(
            f"Updated session {session_id} to use canon version {version.version_id}"
        )

    def create_session(
        self, session_id: str, initial_canon: Optional[Path] = None
    ) -> bool:
        """创建新会话"""
        if session_id in self.sessions:
            logger.warning(f"Session already exists: {session_id}")
            return False

        session = SessionState(
            session_id=session_id,
            canon_version="",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
        )

        self.sessions[session_id] = session

        # 如果提供了初始规则，加载它
        if initial_canon:
            canon = self.get_canon(initial_canon, session_id)
            if canon:
                logger.info(
                    f"Created session {session_id} with initial canon {initial_canon}"
                )
                return True

        logger.info(f"Created session {session_id}")
        return True

    def get_session_canon(self, session_id: str) -> Optional[MarkdownCanon]:
        """获取会话当前使用的规则集"""
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return None

        session = self.sessions[session_id]

        # 查找规则版本
        for cache_key, version in self.canon_cache.items():
            if version.version_id == session.canon_version:
                return version.canon

        logger.warning(
            f"Canon version not found for session {session_id}: {session.canon_version}"
        )
        return None

    def rollback_session(
        self, session_id: str, version_id: Optional[str] = None
    ) -> bool:
        """回滚会话到指定版本"""
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return False

        session = self.sessions[session_id]

        # 查找可用的版本
        available_versions = []
        for cache_key, versions in self.version_history.items():
            for version in versions:
                available_versions.append((cache_key, version))

        if not available_versions:
            logger.warning("No version history available for rollback")
            return False

        # 如果未指定版本，回滚到上一个版本
        if not version_id:
            # 查找当前版本的上一个版本
            current_version = session.canon_version
            for cache_key, version in available_versions:
                if version.version_id == current_version:
                    # 获取历史记录
                    history = self.version_history.get(cache_key, [])
                    if len(history) > 1:
                        prev_version = history[-2]
                        session.canon_version = prev_version.version_id
                        logger.info(
                            f"Rolled back session {session_id} to version {prev_version.version_id}"
                        )
                        return True

        # 回滚到指定版本
        for cache_key, version in available_versions:
            if version.version_id == version_id:
                session.canon_version = version_id
                logger.info(f"Rolled back session {session_id} to version {version_id}")
                return True

        logger.warning(f"Version not found for rollback: {version_id}")
        return False

    def get_version_history(self, path: Path) -> List[CanonVersion]:
        """获取规则版本历史"""
        cache_key = str(path)
        return self.version_history.get(cache_key, [])

    def compare_versions(
        self, path: Path, version_id1: str, version_id2: str
    ) -> Optional[Dict[str, Any]]:
        """比较两个版本"""
        history = self.get_version_history(path)

        version1 = None
        version2 = None

        for version in history:
            if version.version_id == version_id1:
                version1 = version
            if version.version_id == version_id2:
                version2 = version

        if not version1 or not version2:
            return None

        # 使用验证器进行比较
        return self.validator.compare_versions(version1.canon, version2.canon)

    def _calculate_file_hash(self, path: Path) -> Optional[str]:
        """计算文件哈希"""
        try:
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate file hash for {path}: {e}")
            return None

    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "watched_paths": [str(p) for p in self.watched_paths],
            "cached_canons": len(self.canon_cache),
            "active_sessions": len(self.sessions),
            "total_versions": sum(len(v) for v in self.version_history.values()),
        }

    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """清理旧会话"""
        now = datetime.now()
        sessions_to_remove = []

        for session_id, session in self.sessions.items():
            age = (now - session.last_accessed).total_seconds()
            if age > max_age_seconds:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")

    def stop_all(self):
        """停止所有监视器"""
        for path_str, observer in self.file_watchers.items():
            try:
                observer.stop()
                observer.join()
                logger.info(f"Stopped watcher for {path_str}")
            except Exception as e:
                logger.error(f"Error stopping watcher for {path_str}: {e}")

        self.file_watchers.clear()
        self.watched_paths.clear()
        logger.info("Stopped all watchers")


class CanonFileHandler(FileSystemEventHandler):
    """规则文件变化处理器"""

    def __init__(self, hot_loader: RuleHotLoader):
        self.hot_loader = hot_loader

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            # 处理可能的 bytes 类型
            src_path = (
                event.src_path.decode("utf-8")
                if isinstance(event.src_path, bytes)
                else event.src_path
            )
            if src_path.endswith(".md"):
                self.hot_loader._handle_file_change(event)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            src_path = (
                event.src_path.decode("utf-8")
                if isinstance(event.src_path, bytes)
                else event.src_path
            )
            if src_path.endswith(".md"):
                self.hot_loader._handle_file_change(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            src_path = (
                event.src_path.decode("utf-8")
                if isinstance(event.src_path, bytes)
                else event.src_path
            )
            if src_path.endswith(".md"):
                self.hot_loader._handle_file_change(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            src_path = (
                event.src_path.decode("utf-8")
                if isinstance(event.src_path, bytes)
                else event.src_path
            )
            if src_path.endswith(".md"):
                self.hot_loader._handle_file_change(event)
