"""
回合调度器

管理异步回合队列和并发，确保回合按顺序处理。
支持回合依赖关系、超时重试、错误处理和与SessionManager集成。
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class TurnStatus(Enum):
    """回合状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"


@dataclass
class Turn:
    """回合实体"""

    id: str
    session_id: str
    turn_number: int
    player_input: str
    status: TurnStatus = TurnStatus.PENDING
    llm_response: Optional[str] = None
    memories_used: List[str] = field(default_factory=list)
    interventions: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # 依赖的回合ID
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    priority: int = 0  # 优先级，越高越先处理
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "turn_number": self.turn_number,
            "player_input": self.player_input,
            "status": self.status.value,
            "llm_response": self.llm_response,
            "memories_used": self.memories_used,
            "interventions": self.interventions,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Turn":
        """从字典创建回合"""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            turn_number=data["turn_number"],
            player_input=data["player_input"],
            status=TurnStatus(data["status"]),
            llm_response=data.get("llm_response"),
            memories_used=data.get("memories_used", []),
            interventions=data.get("interventions", []),
            dependencies=data.get("dependencies", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 30),
            priority=data.get("priority", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            duration_ms=data.get("duration_ms"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class TurnScheduler:
    """回合调度器"""

    def __init__(
        self, max_concurrent: int = 3, session_manager=None, persistence_engine=None
    ):
        self.max_concurrent = max_concurrent
        self.session_manager = session_manager
        self.persistence = persistence_engine

        # 队列和状态跟踪
        self.pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_turns: Dict[str, Turn] = {}
        self.completed_turns: Dict[str, Turn] = {}
        self.failed_turns: Dict[str, Turn] = {}

        # 依赖关系跟踪
        self.dependency_graph: Dict[str, Set[str]] = {}  # turn_id -> 依赖的turn_ids
        self.reverse_dependency: Dict[str, Set[str]] = (
            {}
        )  # turn_id -> 依赖于它的turn_ids

        # 并发控制
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._processing_task: Optional[asyncio.Task] = None
        self._is_running = False

        # 回调函数
        self._on_turn_started: List[Callable] = []
        self._on_turn_completed: List[Callable] = []
        self._on_turn_failed: List[Callable] = []

        logger.info(f"TurnScheduler initialized with max_concurrent={max_concurrent}")

    async def start(self):
        """启动调度器"""
        if self._is_running:
            logger.warning("TurnScheduler is already running")
            return

        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_queue())
        logger.info("TurnScheduler started")

    async def stop(self):
        """停止调度器"""
        if not self._is_running:
            return

        self._is_running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        # 保存状态
        await self._save_state()

        logger.info("TurnScheduler stopped")

    async def submit_turn(self, turn: Turn) -> str:
        """提交回合到队列"""
        # 检查依赖关系
        if turn.dependencies:
            # 构建依赖图
            self.dependency_graph[turn.id] = set(turn.dependencies)
            for dep_id in turn.dependencies:
                if dep_id not in self.reverse_dependency:
                    self.reverse_dependency[dep_id] = set()
                self.reverse_dependency[dep_id].add(turn.id)

            # 检查依赖是否已完成
            all_deps_completed = True
            for dep_id in turn.dependencies:
                if dep_id in self.active_turns or dep_id not in self.completed_turns:
                    all_deps_completed = False
                    break

            if not all_deps_completed:
                logger.debug(
                    f"Turn {turn.id} waiting for dependencies: {turn.dependencies}"
                )
                return turn.id

        # 添加到队列（使用负优先级，因为PriorityQueue是最小堆）
        await self.pending_queue.put((-turn.priority, time.time(), turn))
        logger.debug(f"Turn {turn.id} submitted to queue (priority: {turn.priority})")

        # 保存到持久化存储
        if self.persistence:
            await self.persistence.save_turn(turn)

        return turn.id

    async def _process_queue(self):
        """处理队列中的回合"""
        while self._is_running:
            try:
                # 获取下一个回合
                priority, timestamp, turn = await self.pending_queue.get()

                # 检查依赖关系
                if turn.dependencies:
                    deps_ready = await self._check_dependencies(turn.id)
                    if not deps_ready:
                        # 放回队列，稍后重试
                        await asyncio.sleep(0.1)
                        await self.pending_queue.put((priority, timestamp, turn))
                        self.pending_queue.task_done()
                        continue

                async with self.semaphore:
                    await self._process_turn(turn)

                self.pending_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Queue processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                await asyncio.sleep(1)  # 避免紧密循环

    async def _process_turn(self, turn: Turn):
        """处理单个回合"""
        turn_id = turn.id
        session_id = turn.session_id

        try:
            # 更新状态
            self.active_turns[turn_id] = turn
            turn.status = TurnStatus.PROCESSING
            turn.started_at = datetime.now()

            # 触发回调
            await self._notify_turn_started(turn)

            logger.info(
                f"Processing turn {turn_id} (session {session_id}, turn #{turn.turn_number})"
            )

            # 获取会话
            session = None
            if self.session_manager:
                session = await self.session_manager.load_session(session_id)

            # 执行回合处理（这里应该调用实际的回合处理逻辑）
            result = await self._execute_turn(turn, session)

            # 更新回合状态
            turn.completed_at = datetime.now()
            if turn.started_at:
                duration = (turn.completed_at - turn.started_at).total_seconds() * 1000
                turn.duration_ms = int(duration)

            turn.status = TurnStatus.COMPLETED
            turn.llm_response = result.get("response") if result else None

            # 移动到完成列表
            self.completed_turns[turn_id] = turn
            del self.active_turns[turn_id]

            # 触发依赖完成
            await self._handle_dependencies_completed(turn_id)

            # 触发回调
            await self._notify_turn_completed(turn)

            logger.debug(f"Turn {turn_id} completed in {turn.duration_ms}ms")

            # 保存到持久化存储
            if self.persistence:
                await self.persistence.save_turn(turn)

            # 更新会话
            if session and self.session_manager:
                session.increment_turn()
                await self.session_manager.save_session(session)

        except asyncio.TimeoutError:
            await self._handle_turn_timeout(turn)
        except Exception as e:
            await self._handle_turn_error(turn, e)

    async def _execute_turn(self, turn: Turn, session) -> Dict[str, Any]:
        """执行回合处理逻辑"""
        # 这里应该集成实际的回合处理逻辑
        # 暂时模拟处理
        try:
            # 模拟处理时间
            await asyncio.sleep(0.5)

            # 返回模拟结果
            return {
                "response": f"Processed turn #{turn.turn_number} for session {turn.session_id}",
                "memories_used": [],
                "interventions_processed": len(turn.interventions),
            }
        except Exception as e:
            logger.error(f"Error executing turn {turn.id}: {e}")
            raise

    async def _handle_turn_timeout(self, turn: Turn):
        """处理回合超时"""
        turn.status = TurnStatus.TIMEOUT
        turn.error = f"Timeout after {turn.timeout_seconds} seconds"
        turn.completed_at = datetime.now()

        # 检查重试
        if turn.retry_count < turn.max_retries:
            turn.retry_count += 1
            turn.status = TurnStatus.RETRYING
            logger.info(
                f"Retrying turn {turn.id} ({turn.retry_count}/{turn.max_retries})"
            )

            # 重新提交到队列
            await self.submit_turn(turn)
        else:
            # 标记为失败
            await self._handle_turn_error(turn, Exception(turn.error))

    async def _handle_turn_error(self, turn: Turn, error: Exception):
        """处理回合错误"""
        turn.status = TurnStatus.FAILED
        turn.error = str(error)
        turn.completed_at = datetime.now()

        self.failed_turns[turn.id] = turn
        if turn.id in self.active_turns:
            del self.active_turns[turn.id]

        logger.error(f"Turn {turn.id} failed: {error}")

        # 触发回调
        await self._notify_turn_failed(turn)

        # 保存到持久化存储
        if self.persistence:
            await self.persistence.save_turn(turn)

    async def _check_dependencies(self, turn_id: str) -> bool:
        """检查依赖关系是否满足"""
        if turn_id not in self.dependency_graph:
            return True

        deps = self.dependency_graph[turn_id]
        for dep_id in deps:
            if dep_id not in self.completed_turns:
                return False

        return True

    async def _handle_dependencies_completed(self, turn_id: str):
        """处理依赖完成"""
        if turn_id in self.reverse_dependency:
            for dependent_id in self.reverse_dependency[turn_id]:
                # 检查是否所有依赖都已完成
                if dependent_id in self.dependency_graph:
                    all_deps_completed = True
                    for dep_id in self.dependency_graph[dependent_id]:
                        if dep_id not in self.completed_turns:
                            all_deps_completed = False
                            break

                    if all_deps_completed:
                        logger.debug(
                            f"All dependencies completed for turn {dependent_id}"
                        )

    async def _save_state(self):
        """保存调度器状态"""
        # 可以扩展为保存到持久化存储
        pass

    async def _notify_turn_started(self, turn: Turn):
        """通知回合开始"""
        for callback in self._on_turn_started:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(turn)
                else:
                    callback(turn)
            except Exception as e:
                logger.error(f"Error in turn started callback: {e}")

    async def _notify_turn_completed(self, turn: Turn):
        """通知回合完成"""
        for callback in self._on_turn_completed:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(turn)
                else:
                    callback(turn)
            except Exception as e:
                logger.error(f"Error in turn completed callback: {e}")

    async def _notify_turn_failed(self, turn: Turn):
        """通知回合失败"""
        for callback in self._on_turn_failed:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(turn)
                else:
                    callback(turn)
            except Exception as e:
                logger.error(f"Error in turn failed callback: {e}")

    # 公共API

    async def get_turn_status(self, turn_id: str) -> Optional[TurnStatus]:
        """获取回合状态"""
        if turn_id in self.active_turns:
            return self.active_turns[turn_id].status
        elif turn_id in self.completed_turns:
            return self.completed_turns[turn_id].status
        elif turn_id in self.failed_turns:
            return self.failed_turns[turn_id].status

        # 从持久化存储查询
        if self.persistence:
            turns = await self.persistence.load_turns("", limit=1)  # 需要实现按ID查询
            for turn_data in turns:
                if turn_data["id"] == turn_id:
                    return TurnStatus(turn_data["status"])

        return None

    async def get_turn(self, turn_id: str) -> Optional[Turn]:
        """获取回合详情"""
        if turn_id in self.active_turns:
            return self.active_turns[turn_id]
        elif turn_id in self.completed_turns:
            return self.completed_turns[turn_id]
        elif turn_id in self.failed_turns:
            return self.failed_turns[turn_id]

        # 从持久化存储查询
        if self.persistence:
            turns = await self.persistence.load_turns("", limit=1)
            for turn_data in turns:
                if turn_data["id"] == turn_id:
                    return Turn.from_dict(turn_data)

        return None

    async def cancel_turn(self, turn_id: str) -> bool:
        """取消回合"""
        if turn_id in self.active_turns:
            turn = self.active_turns[turn_id]
            turn.status = TurnStatus.CANCELLED
            turn.completed_at = datetime.now()

            # 从活跃列表移除
            del self.active_turns[turn_id]
            self.failed_turns[turn_id] = turn

            logger.info(f"Cancelled turn {turn_id}")

            # 保存到持久化存储
            if self.persistence:
                await self.persistence.save_turn(turn)

            return True

        return False

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.pending_queue.qsize()

    def get_active_count(self) -> int:
        """获取活跃回合数"""
        return len(self.active_turns)

    def get_completed_count(self) -> int:
        """获取已完成回合数"""
        return len(self.completed_turns)

    def get_failed_count(self) -> int:
        """获取失败回合数"""
        return len(self.failed_turns)

    def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        return {
            "queue_size": self.get_queue_size(),
            "active_turns": self.get_active_count(),
            "completed_turns": self.get_completed_count(),
            "failed_turns": self.get_failed_count(),
            "max_concurrent": self.max_concurrent,
            "is_running": self._is_running,
        }

    def register_turn_started_callback(self, callback: Callable):
        """注册回合开始回调"""
        self._on_turn_started.append(callback)

    def register_turn_completed_callback(self, callback: Callable):
        """注册回合完成回调"""
        self._on_turn_completed.append(callback)

    def register_turn_failed_callback(self, callback: Callable):
        """注册回合失败回调"""
        self._on_turn_failed.append(callback)

    async def wait_for_turn(
        self, turn_id: str, timeout: Optional[float] = None
    ) -> Optional[Turn]:
        """等待回合完成"""
        start_time = time.time()

        while True:
            turn = await self.get_turn(turn_id)
            if turn and turn.status in [
                TurnStatus.COMPLETED,
                TurnStatus.FAILED,
                TurnStatus.CANCELLED,
            ]:
                return turn

            if timeout and (time.time() - start_time) > timeout:
                return None

            await asyncio.sleep(0.1)

    async def cleanup_old_turns(self, max_age_hours: int = 24):
        """清理旧回合数据"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        # 清理内存中的旧回合
        turns_to_remove = []
        for turn_id, turn in self.completed_turns.items():
            if turn.completed_at and turn.completed_at < cutoff_time:
                turns_to_remove.append(turn_id)

        for turn_id in turns_to_remove:
            del self.completed_turns[turn_id]

        logger.info(
            f"Cleaned up {len(turns_to_remove)} old completed turns from memory"
        )

        # 清理失败的回合
        turns_to_remove = []
        for turn_id, turn in self.failed_turns.items():
            if turn.completed_at and turn.completed_at < cutoff_time:
                turns_to_remove.append(turn_id)

        for turn_id in turns_to_remove:
            del self.failed_turns[turn_id]

        logger.info(f"Cleaned up {len(turns_to_remove)} old failed turns from memory")

        return len(turns_to_remove)

    async def get_session_turns(self, session_id: str, limit: int = 100) -> List[Turn]:
        """获取会话的回合列表"""
        turns = []

        # 从内存中获取
        for turn in (
            list(self.completed_turns.values())
            + list(self.active_turns.values())
            + list(self.failed_turns.values())
        ):
            if turn.session_id == session_id:
                turns.append(turn)

        # 按回合号排序
        turns.sort(key=lambda t: t.turn_number, reverse=True)

        # 限制数量
        turns = turns[:limit]

        # 如果数量不足，从持久化存储获取
        if len(turns) < limit and self.persistence:
            turn_data_list = await self.persistence.load_turns(
                session_id, limit=limit - len(turns)
            )
            for turn_data in turn_data_list:
                # 避免重复
                if not any(t.id == turn_data["id"] for t in turns):
                    turns.append(Turn.from_dict(turn_data))

        return turns

    def create_turn(
        self, session_id: str, turn_number: int, player_input: str, **kwargs
    ) -> Turn:
        """创建新的回合对象"""
        turn_id = str(uuid.uuid4())

        return Turn(
            id=turn_id,
            session_id=session_id,
            turn_number=turn_number,
            player_input=player_input,
            **kwargs,
        )
