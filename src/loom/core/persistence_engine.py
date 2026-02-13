"""
持久化引擎

提供会话和记忆的持久化存储接口，支持SQLite/DuckDB等后端。
支持异步操作、事务处理、数据迁移和连接池。
"""

import json
import sqlite3
import aiosqlite
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from contextlib import asynccontextmanager
from enum import Enum
import yaml

from ..utils.logging_config import get_logger
from .interfaces import NarrativeArchive

logger = get_logger(__name__)


class DatabaseBackend(Enum):
    """数据库后端类型"""

    SQLITE = "sqlite"
    DUCKDB = "duckdb"
    POSTGRESQL = "postgresql"


class PersistenceEngine:
    """持久化引擎基类"""

    async def save_session(self, session) -> bool:
        """保存会话"""
        raise NotImplementedError

    async def load_session(self, session_id: str):
        """加载会话"""
        raise NotImplementedError

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        raise NotImplementedError

    async def list_sessions(self) -> Dict[str, Any]:
        """列出所有会话"""
        raise NotImplementedError

    async def save_turn(self, turn) -> bool:
        """保存回合"""
        raise NotImplementedError

    async def load_turns(self, session_id: str, limit: int = 100) -> List[Dict]:
        """加载回合"""
        raise NotImplementedError

    async def save_memory(self, memory_entity) -> bool:
        """保存记忆实体"""
        raise NotImplementedError

    async def load_memories(self, session_id: str, limit: int = 100) -> List[Dict]:
        """加载记忆"""
        raise NotImplementedError

    async def execute_migration(self, migration_script: str) -> bool:
        """执行数据迁移"""
        raise NotImplementedError

    async def backup(self, backup_path: str) -> bool:
        """备份数据库"""
        raise NotImplementedError

    async def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        raise NotImplementedError


class SQLitePersistence(PersistenceEngine):
    """SQLite持久化引擎（使用aiosqlite进行异步操作）"""

    def __init__(self, db_path: str = "loom.db", pool_size: int = 5):
        self.db_path = Path(db_path)
        self.pool_size = pool_size
        self._connection_pool: List[aiosqlite.Connection] = []
        self._pool_lock = asyncio.Lock()
        self._migration_version = 3

        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"SQLitePersistence initialized with db={db_path}, pool_size={pool_size}"
        )

    async def initialize(self):
        """初始化数据库连接和表结构"""
        await self._ensure_tables()
        await self._check_migrations()

    async def _get_connection(self) -> aiosqlite.Connection:
        """从连接池获取连接"""
        async with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()

        # 创建新连接
        conn = await aiosqlite.connect(self.db_path)
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    async def _return_connection(self, conn: aiosqlite.Connection):
        """归还连接到池中"""
        async with self._pool_lock:
            if len(self._connection_pool) < self.pool_size:
                self._connection_pool.append(conn)
            else:
                await conn.close()

    @asynccontextmanager
    async def _transaction(self):
        """事务上下文管理器"""
        conn = await self._get_connection()
        try:
            await conn.execute("BEGIN")
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await self._return_connection(conn)

    async def _ensure_tables(self):
        """确保表存在"""
        async with self._transaction() as conn:
            # 会话表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_turn INTEGER DEFAULT 0,
                    total_turns INTEGER DEFAULT 0,
                    last_activity TEXT NOT NULL,
                    state TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    stats TEXT DEFAULT '{}'
                )
            """)

            # 创建索引
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity)"
            )

            # 回合表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    player_input TEXT NOT NULL,
                    status TEXT NOT NULL,
                    llm_response TEXT,
                    memories_used TEXT,
                    interventions TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration_ms INTEGER,
                    error TEXT,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
                    UNIQUE(session_id, turn_number)
                )
            """)

            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_created ON turns(created_at)"
            )

            # 记忆表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    metadata TEXT NOT NULL,
                    embedding BLOB,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)

            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)"
            )

            # 叙事档案表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS narrative_archives (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    narrative_timeline TEXT NOT NULL,
                    key_characters TEXT NOT NULL,
                    plot_arcs TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)

            # 叙事档案版本表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS archive_versions (
                    id TEXT PRIMARY KEY,
                    archive_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT DEFAULT 'system',
                    FOREIGN KEY (archive_id) REFERENCES narrative_archives (id) ON DELETE CASCADE,
                    UNIQUE(archive_id, version)
                )
            """)

            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_archives_session ON narrative_archives(session_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_archives_created ON narrative_archives(created_at)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_archive_versions_archive ON archive_versions(archive_id)"
            )

            # 迁移版本表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)

        logger.info("Database tables ensured")

    async def _check_migrations(self):
        """检查并执行数据迁移"""
        async with self._transaction() as conn:
            # 检查当前版本
            cursor = await conn.execute("SELECT MAX(version) FROM migrations")
            row = await cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            # 执行待迁移
            migrations_to_apply = []
            for version in range(current_version + 1, self._migration_version + 1):
                migration = self._get_migration_script(version)
                if migration:
                    migrations_to_apply.append((version, migration))

            for version, migration in migrations_to_apply:
                try:
                    await conn.executescript(migration)
                    await conn.execute(
                        "INSERT INTO migrations (version, name, applied_at) VALUES (?, ?, ?)",
                        (version, f"migration_v{version}", datetime.now().isoformat()),
                    )
                    logger.info(f"Applied migration v{version}")
                except Exception as e:
                    logger.error(f"Failed to apply migration v{version}: {e}")
                    raise

    def _get_migration_script(self, version: int) -> Optional[str]:
        """获取迁移脚本"""
        migrations = {
            1: """
                -- 初始版本，表已创建
            """,
            2: """
                -- 版本2：无操作（stats列已在表创建时添加）
                -- 此版本仅用于版本号递增
            """,
            3: """
                -- 添加叙事档案支持
                CREATE TABLE IF NOT EXISTS narrative_archives (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    narrative_timeline TEXT NOT NULL,
                    key_characters TEXT NOT NULL,
                    plot_arcs TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    metadata TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS archive_versions (
                    id TEXT PRIMARY KEY,
                    archive_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT DEFAULT 'system',
                    FOREIGN KEY (archive_id) REFERENCES narrative_archives (id) ON DELETE CASCADE,
                    UNIQUE(archive_id, version)
                );
                
                CREATE INDEX IF NOT EXISTS idx_archives_session ON narrative_archives(session_id);
                CREATE INDEX IF NOT EXISTS idx_archives_created ON narrative_archives(created_at);
                CREATE INDEX IF NOT EXISTS idx_archive_versions_archive ON archive_versions(archive_id);
            """,
        }
        return migrations.get(version)

    async def save_session(self, session) -> bool:
        """保存会话到SQLite"""
        try:
            async with self._transaction() as conn:
                session_dict = (
                    session.to_dict() if hasattr(session, "to_dict") else session
                )

                await conn.execute(
                    """
                    INSERT OR REPLACE INTO sessions 
                    (id, name, config, created_at, updated_at, status, current_turn, total_turns, 
                     last_activity, state, metadata, version, stats)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_dict["id"],
                        session_dict["name"],
                        json.dumps(session_dict["config"]),
                        session_dict["created_at"],
                        session_dict["updated_at"],
                        session_dict["status"],
                        session_dict["current_turn"],
                        session_dict["total_turns"],
                        session_dict["last_activity"],
                        json.dumps(session_dict["state"]),
                        json.dumps(session_dict["metadata"]),
                        1,
                        json.dumps(session_dict.get("stats", {})),
                    ),
                )

            logger.debug(f"Session {session_dict['id']} saved to database")
            return True
        except Exception as e:
            logger.error(
                f"Failed to save session {session_dict.get('id', 'unknown')}: {e}"
            )
            return False

    async def load_session(self, session_id: str):
        """从SQLite加载会话"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM sessions WHERE id = ?", (session_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                # 转换为字典
                session_data = {
                    "id": row[0],
                    "name": row[1],
                    "config": json.loads(row[2]),
                    "created_at": row[3],
                    "updated_at": row[4],
                    "status": row[5],
                    "current_turn": row[6],
                    "total_turns": row[7],
                    "last_activity": row[8],
                    "state": json.loads(row[9]),
                    "metadata": json.loads(row[10]),
                    "version": row[11],
                    "stats": json.loads(row[12]) if row[12] else {},
                }

            logger.debug(f"Session {session_id} loaded from database")
            return session_data
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    "DELETE FROM sessions WHERE id = ?", (session_id,)
                )
                deleted = cursor.rowcount > 0

            logger.info(f"Session {session_id} deleted from database")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    async def list_sessions(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出所有会话"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    """
                    SELECT id, name, status, current_turn, total_turns, created_at, last_activity 
                    FROM sessions 
                    ORDER BY last_activity DESC 
                    LIMIT ? OFFSET ?
                """,
                    (limit, offset),
                )

                rows = await cursor.fetchall()

                sessions = []
                for row in rows:
                    sessions.append(
                        {
                            "id": row[0],
                            "name": row[1],
                            "status": row[2],
                            "current_turn": row[3],
                            "total_turns": row[4],
                            "created_at": row[5],
                            "last_activity": row[6],
                        }
                    )

                return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    async def save_turn(self, turn) -> bool:
        """保存回合"""
        try:
            async with self._transaction() as conn:
                turn_dict = turn.to_dict() if hasattr(turn, "to_dict") else turn

                await conn.execute(
                    """
                    INSERT OR REPLACE INTO turns 
                    (id, session_id, turn_number, player_input, status, llm_response, 
                     memories_used, interventions, created_at, started_at, completed_at, 
                     duration_ms, error, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        turn_dict["id"],
                        turn_dict["session_id"],
                        turn_dict["turn_number"],
                        turn_dict["player_input"],
                        turn_dict["status"],
                        turn_dict.get("llm_response"),
                        json.dumps(turn_dict.get("memories_used", [])),
                        json.dumps(turn_dict.get("interventions", [])),
                        turn_dict["created_at"],
                        turn_dict.get("started_at"),
                        turn_dict.get("completed_at"),
                        turn_dict.get("duration_ms"),
                        turn_dict.get("error"),
                        json.dumps(turn_dict.get("metadata", {})),
                    ),
                )

            logger.debug(f"Turn {turn_dict['id']} saved to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save turn {turn_dict.get('id', 'unknown')}: {e}")
            return False

    async def load_turns(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        """加载回合"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    """
                    SELECT * FROM turns 
                    WHERE session_id = ? 
                    ORDER BY turn_number DESC 
                    LIMIT ? OFFSET ?
                """,
                    (session_id, limit, offset),
                )

                rows = await cursor.fetchall()

                turns = []
                for row in rows:
                    turns.append(
                        {
                            "id": row[0],
                            "session_id": row[1],
                            "turn_number": row[2],
                            "player_input": row[3],
                            "status": row[4],
                            "llm_response": row[5],
                            "memories_used": json.loads(row[6]) if row[6] else [],
                            "interventions": json.loads(row[7]) if row[7] else [],
                            "created_at": row[8],
                            "started_at": row[9],
                            "completed_at": row[10],
                            "duration_ms": row[11],
                            "error": row[12],
                            "metadata": json.loads(row[13]) if row[13] else {},
                        }
                    )

                return turns
        except Exception as e:
            logger.error(f"Failed to load turns for session {session_id}: {e}")
            return []

    async def save_memory(self, memory_entity) -> bool:
        """保存记忆实体"""
        try:
            async with self._transaction() as conn:
                memory_dict = (
                    memory_entity.to_dict()
                    if hasattr(memory_entity, "to_dict")
                    else memory_entity
                )

                await conn.execute(
                    """
                    INSERT OR REPLACE INTO memories 
                    (id, session_id, type, content, created_at, updated_at, version, metadata, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        memory_dict["id"],
                        memory_dict["session_id"],
                        memory_dict["type"],
                        json.dumps(memory_dict["content"]),
                        memory_dict["created_at"],
                        memory_dict["updated_at"],
                        memory_dict.get("version", 1),
                        json.dumps(memory_dict.get("metadata", {})),
                        memory_dict.get("embedding"),
                    ),
                )

            logger.debug(f"Memory {memory_dict['id']} saved to database")
            return True
        except Exception as e:
            logger.error(
                f"Failed to save memory {memory_dict.get('id', 'unknown')}: {e}"
            )
            return False

    async def load_memories(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        """加载记忆"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    """
                    SELECT * FROM memories 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """,
                    (session_id, limit, offset),
                )

                rows = await cursor.fetchall()

                memories = []
                for row in rows:
                    memories.append(
                        {
                            "id": row[0],
                            "session_id": row[1],
                            "type": row[2],
                            "content": json.loads(row[3]),
                            "created_at": row[4],
                            "updated_at": row[5],
                            "version": row[6],
                            "metadata": json.loads(row[7]) if row[7] else {},
                            "embedding": row[8],
                        }
                    )

                return memories
        except Exception as e:
            logger.error(f"Failed to load memories for session {session_id}: {e}")
            return []

    async def execute_migration(self, migration_script: str) -> bool:
        """执行数据迁移"""
        try:
            async with self._transaction() as conn:
                await conn.executescript(migration_script)
            logger.info("Migration executed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to execute migration: {e}")
            return False

    async def backup(self, backup_path: str) -> bool:
        """备份数据库"""
        try:
            import shutil

            backup_path_obj = Path(backup_path)
            backup_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # 关闭所有连接
            async with self._pool_lock:
                for conn in self._connection_pool:
                    await conn.close()
                self._connection_pool.clear()

            # 复制数据库文件
            shutil.copy(self.db_path, backup_path_obj)

            # 重新初始化连接池
            await self.initialize()

            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            async with self._transaction() as conn:
                stats = {}

                # 会话统计
                cursor = await conn.execute("SELECT COUNT(*) FROM sessions")
                stats["total_sessions"] = (await cursor.fetchone())[0]

                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE status = 'active'"
                )
                stats["active_sessions"] = (await cursor.fetchone())[0]

                # 回合统计
                cursor = await conn.execute("SELECT COUNT(*) FROM turns")
                stats["total_turns"] = (await cursor.fetchone())[0]

                # 记忆统计
                cursor = await conn.execute("SELECT COUNT(*) FROM memories")
                stats["total_memories"] = (await cursor.fetchone())[0]

                # 数据库大小
                cursor = await conn.execute(
                    "SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()"
                )
                db_size = await cursor.fetchone()
                stats["database_size_bytes"] = db_size[0] if db_size else 0

                # 最近活动
                cursor = await conn.execute("SELECT MAX(last_activity) FROM sessions")
                last_activity = await cursor.fetchone()
                stats["last_activity"] = last_activity[0] if last_activity[0] else None

                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    async def search_memories(
        self, session_id: str, query: str, limit: int = 10
    ) -> List[Dict]:
        """搜索记忆（简单文本搜索）"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    """
                    SELECT * FROM memories
                    WHERE session_id = ? AND (
                        content LIKE ? OR
                        metadata LIKE ? OR
                        type LIKE ?
                    )
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    (session_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
                )

                rows = await cursor.fetchall()

                memories = []
                for row in rows:
                    memories.append(
                        {
                            "id": row[0],
                            "session_id": row[1],
                            "type": row[2],
                            "content": json.loads(row[3]),
                            "created_at": row[4],
                            "updated_at": row[5],
                            "version": row[6],
                            "metadata": json.loads(row[7]) if row[7] else {},
                            "embedding": row[8],
                        }
                    )

                return memories
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """清理旧数据"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()

            async with self._transaction() as conn:
                # 归档旧会话
                cursor = await conn.execute(
                    """
                    UPDATE sessions
                    SET status = 'archived'
                    WHERE last_activity < ? AND status = 'active'
                """,
                    (cutoff_iso,),
                )
                archived_sessions = cursor.rowcount

                # 删除非常旧的归档会话
                cursor = await conn.execute(
                    """
                    DELETE FROM sessions
                    WHERE status = 'archived' AND last_activity < ?
                """,
                    (cutoff_iso,),
                )
                deleted_sessions = cursor.rowcount

                logger.info(
                    f"Cleaned up {archived_sessions} archived sessions, deleted {deleted_sessions} old sessions"
                )

                return {
                    "archived_sessions": archived_sessions,
                    "deleted_sessions": deleted_sessions,
                }
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {"archived_sessions": 0, "deleted_sessions": 0}

    # 叙事档案相关方法
    async def save_narrative_archive(self, archive: NarrativeArchive) -> bool:
        """保存叙事档案"""
        try:
            async with self._transaction() as conn:
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO narrative_archives
                    (id, session_id, title, summary, narrative_timeline, key_characters,
                     plot_arcs, created_at, updated_at, version, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        archive.id,
                        archive.session_id,
                        archive.title,
                        archive.summary,
                        json.dumps(archive.narrative_timeline),
                        json.dumps(archive.key_characters),
                        json.dumps(archive.plot_arcs),
                        archive.created_at.isoformat(),
                        archive.updated_at.isoformat(),
                        archive.version,
                        json.dumps(archive.metadata),
                    ),
                )

            logger.debug(f"Narrative archive {archive.id} saved to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save narrative archive {archive.id}: {e}")
            return False

    async def load_narrative_archive(
        self, archive_id: str
    ) -> Optional[NarrativeArchive]:
        """加载叙事档案"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM narrative_archives WHERE id = ?", (archive_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                archive_data = {
                    "id": row[0],
                    "session_id": row[1],
                    "title": row[2],
                    "summary": row[3],
                    "narrative_timeline": json.loads(row[4]),
                    "key_characters": json.loads(row[5]),
                    "plot_arcs": json.loads(row[6]),
                    "created_at": datetime.fromisoformat(row[7]),
                    "updated_at": datetime.fromisoformat(row[8]),
                    "version": row[9],
                    "metadata": json.loads(row[10]) if row[10] else {},
                }

            logger.debug(f"Narrative archive {archive_id} loaded from database")
            return NarrativeArchive(**archive_data)
        except Exception as e:
            logger.error(f"Failed to load narrative archive {archive_id}: {e}")
            return None

    async def list_narrative_archives(
        self, session_id: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[NarrativeArchive]:
        """列出叙事档案"""
        try:
            async with self._transaction() as conn:
                query = """
                    SELECT * FROM narrative_archives
                    WHERE 1=1
                """
                params = []

                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

                archives = []
                for row in rows:
                    try:
                        archive_data = {
                            "id": row[0],
                            "session_id": row[1],
                            "title": row[2],
                            "summary": row[3],
                            "narrative_timeline": json.loads(row[4]),
                            "key_characters": json.loads(row[5]),
                            "plot_arcs": json.loads(row[6]),
                            "created_at": datetime.fromisoformat(row[7]),
                            "updated_at": datetime.fromisoformat(row[8]),
                            "version": row[9],
                            "metadata": json.loads(row[10]) if row[10] else {},
                        }
                        archives.append(NarrativeArchive(**archive_data))
                    except Exception as e:
                        logger.error(f"Failed to parse archive data for {row[0]}: {e}")

                return archives
        except Exception as e:
            logger.error(f"Failed to list narrative archives: {e}")
            return []

    async def export_to_markdown(self, archive_id: str, output_path: str) -> bool:
        """导出叙事档案为Markdown格式"""
        try:
            archive = await self.load_narrative_archive(archive_id)
            if not archive:
                logger.error(f"Archive {archive_id} not found")
                return False

            # 创建Markdown内容
            md_content = []
            md_content.append(f"# {archive.title}")
            md_content.append(f"")
            md_content.append(f"**会话ID**: {archive.session_id}")
            md_content.append(f"**创建时间**: {archive.created_at}")
            md_content.append(f"**更新时间**: {archive.updated_at}")
            md_content.append(f"**版本**: {archive.version}")
            md_content.append(f"")

            md_content.append("## 摘要")
            md_content.append(archive.summary)
            md_content.append("")

            md_content.append("## 关键角色")
            for character in archive.key_characters:
                md_content.append(f"### {character.get('name', '未知角色')}")
                md_content.append(f"- **角色**: {character.get('role', '未知')}")
                md_content.append(
                    f"- **描述**: {character.get('description', '无描述')}"
                )
                if "traits" in character:
                    md_content.append(f"- **特质**: {', '.join(character['traits'])}")
                md_content.append("")

            md_content.append("## 叙事时间线")
            for i, event in enumerate(archive.narrative_timeline):
                md_content.append(f"### 事件 {i+1}: {event.get('title', '未命名事件')}")
                md_content.append(f"- **时间**: {event.get('timestamp', '未知时间')}")
                md_content.append(f"- **类型**: {event.get('type', '未知类型')}")
                md_content.append(f"- **描述**: {event.get('description', '无描述')}")
                md_content.append("")

            md_content.append("## 情节弧线")
            for i, arc in enumerate(archive.plot_arcs):
                md_content.append(f"### 弧线 {i+1}: {arc.get('name', '未命名弧线')}")
                md_content.append(f"- **状态**: {arc.get('status', '未知')}")
                md_content.append(f"- **进度**: {arc.get('progress', 0) * 100:.0f}%")
                md_content.append(f"- **描述**: {arc.get('description', '无描述')}")
                md_content.append("")

            # 写入文件
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))

            logger.info(f"Narrative archive {archive_id} exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export narrative archive {archive_id}: {e}")
            return False

    async def import_from_markdown(
        self, markdown_path: str, session_id: str
    ) -> Optional[NarrativeArchive]:
        """从Markdown导入叙事档案"""
        try:
            # 读取Markdown文件
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单解析Markdown（实际实现需要更复杂的解析）
            lines = content.split("\n")

            # 提取标题
            title = ""
            summary = ""
            key_characters = []
            narrative_timeline = []
            plot_arcs = []

            current_section = None
            current_character = None
            current_event = None
            current_arc = None

            for line in lines:
                line = line.strip()
                if line.startswith("# "):
                    title = line[2:].strip()
                elif line.startswith("## 摘要"):
                    current_section = "summary"
                elif line.startswith("## 关键角色"):
                    current_section = "characters"
                elif line.startswith("## 叙事时间线"):
                    current_section = "timeline"
                elif line.startswith("## 情节弧线"):
                    current_section = "arcs"
                elif line.startswith("### "):
                    # 子标题
                    if current_section == "characters":
                        if current_character:
                            key_characters.append(current_character)
                        current_character = {"name": line[4:].strip()}
                    elif current_section == "timeline":
                        if current_event:
                            narrative_timeline.append(current_event)
                        current_event = {"title": line[4:].strip()}
                    elif current_section == "arcs":
                        if current_arc:
                            plot_arcs.append(current_arc)
                        current_arc = {"name": line[4:].strip()}
                elif line.startswith("- **"):
                    # 属性行
                    if line.startswith("- **角色**:"):
                        if current_character:
                            current_character["role"] = line.split(":", 1)[1].strip()
                    elif line.startswith("- **描述**:"):
                        if current_section == "summary":
                            summary = line.split(":", 1)[1].strip()
                        elif current_character:
                            current_character["description"] = line.split(":", 1)[
                                1
                            ].strip()
                        elif current_event:
                            current_event["description"] = line.split(":", 1)[1].strip()
                        elif current_arc:
                            current_arc["description"] = line.split(":", 1)[1].strip()

            # 添加最后一个项目
            if current_character:
                key_characters.append(current_character)
            if current_event:
                narrative_timeline.append(current_event)
            if current_arc:
                plot_arcs.append(current_arc)

            # 创建档案对象
            import uuid
            from datetime import datetime

            archive = NarrativeArchive(
                id=str(uuid.uuid4()),
                session_id=session_id,
                title=title or "导入的叙事档案",
                summary=summary or "从Markdown文件导入",
                narrative_timeline=narrative_timeline,
                key_characters=key_characters,
                plot_arcs=plot_arcs,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version=1,
                metadata={
                    "source": markdown_path,
                    "imported_at": datetime.now().isoformat(),
                },
            )

            # 保存到数据库
            success = await self.save_narrative_archive(archive)
            if success:
                logger.info(
                    f"Narrative archive imported from {markdown_path} as {archive.id}"
                )
                return archive

            return None
        except Exception as e:
            logger.error(
                f"Failed to import narrative archive from {markdown_path}: {e}"
            )
            return None

    async def create_archive_version(
        self, archive_id: str, description: str
    ) -> Optional[str]:
        """创建档案版本"""
        try:
            archive = await self.load_narrative_archive(archive_id)
            if not archive:
                logger.error(f"Archive {archive_id} not found")
                return None

            # 获取当前最大版本号
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    "SELECT MAX(version) FROM archive_versions WHERE archive_id = ?",
                    (archive_id,),
                )
                row = await cursor.fetchone()
                next_version = (row[0] or 0) + 1

                # 创建版本记录
                version_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO archive_versions
                    (id, archive_id, version, description, content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        version_id,
                        archive_id,
                        next_version,
                        description,
                        json.dumps(
                            {
                                "title": archive.title,
                                "summary": archive.summary,
                                "narrative_timeline": archive.narrative_timeline,
                                "key_characters": archive.key_characters,
                                "plot_arcs": archive.plot_arcs,
                                "metadata": archive.metadata,
                            }
                        ),
                        datetime.now().isoformat(),
                    ),
                )

                # 更新档案版本号
                archive.version = next_version
                archive.updated_at = datetime.now()
                await self.save_narrative_archive(archive)

            logger.info(f"Created version {next_version} for archive {archive_id}")
            return version_id
        except Exception as e:
            logger.error(f"Failed to create version for archive {archive_id}: {e}")
            return None

    async def rollback_archive_version(self, archive_id: str, version: int) -> bool:
        """回滚到指定版本"""
        try:
            # 加载指定版本
            async with self._transaction() as conn:
                cursor = await conn.execute(
                    "SELECT content FROM archive_versions WHERE archive_id = ? AND version = ?",
                    (archive_id, version),
                )
                row = await cursor.fetchone()

                if not row:
                    logger.error(
                        f"Version {version} not found for archive {archive_id}"
                    )
                    return False

                version_content = json.loads(row[0])

                # 更新档案
                archive = await self.load_narrative_archive(archive_id)
                if not archive:
                    logger.error(f"Archive {archive_id} not found")
                    return False

                archive.title = version_content.get("title", archive.title)
                archive.summary = version_content.get("summary", archive.summary)
                archive.narrative_timeline = version_content.get(
                    "narrative_timeline", archive.narrative_timeline
                )
                archive.key_characters = version_content.get(
                    "key_characters", archive.key_characters
                )
                archive.plot_arcs = version_content.get("plot_arcs", archive.plot_arcs)
                archive.metadata = version_content.get("metadata", archive.metadata)
                archive.updated_at = datetime.now()

                # 保存回滚后的档案
                success = await self.save_narrative_archive(archive)
                if success:
                    logger.info(
                        f"Rolled back archive {archive_id} to version {version}"
                    )
                    return True

            return False
        except Exception as e:
            logger.error(
                f"Failed to rollback archive {archive_id} to version {version}: {e}"
            )
            return False

    async def close(self):
        """关闭所有数据库连接"""
        async with self._pool_lock:
            for conn in self._connection_pool:
                await conn.close()
            self._connection_pool.clear()
        logger.info("Database connections closed")
