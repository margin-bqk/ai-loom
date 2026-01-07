"""
持久化引擎

提供会话和记忆的持久化存储接口，支持SQLite/DuckDB等后端。
支持异步操作、事务处理、数据迁移和连接池。
"""

import json
import sqlite3
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from contextlib import asynccontextmanager
from enum import Enum

from ..utils.logging_config import get_logger

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
        self._migration_version = 2
        
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SQLitePersistence initialized with db={db_path}, pool_size={pool_size}")
    
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
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity)")
            
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
            
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_created ON turns(created_at)")
            
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
            
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)")
            
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
                        (version, f"migration_v{version}", datetime.now().isoformat())
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
                -- 添加会话统计字段
                ALTER TABLE sessions ADD COLUMN stats TEXT DEFAULT '{}';
            """
        }
        return migrations.get(version)
    
    async def save_session(self, session) -> bool:
        """保存会话到SQLite"""
        try:
            async with self._transaction() as conn:
                session_dict = session.to_dict() if hasattr(session, 'to_dict') else session
                
                await conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (id, name, config, created_at, updated_at, status, current_turn, total_turns, 
                     last_activity, state, metadata, version, stats)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
                    json.dumps(session_dict.get("stats", {}))
                ))
            
            logger.debug(f"Session {session_dict['id']} saved to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_dict.get('id', 'unknown')}: {e}")
            return False
    
    async def load_session(self, session_id: str):
        """从SQLite加载会话"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
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
                    "stats": json.loads(row[12]) if row[12] else {}
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
                cursor = await conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                deleted = cursor.rowcount > 0
            
            logger.info(f"Session {session_id} deleted from database")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def list_sessions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出所有会话"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute("""
                    SELECT id, name, status, current_turn, total_turns, created_at, last_activity 
                    FROM sessions 
                    ORDER BY last_activity DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                rows = await cursor.fetchall()
                
                sessions = []
                for row in rows:
                    sessions.append({
                        "id": row[0],
                        "name": row[1],
                        "status": row[2],
                        "current_turn": row[3],
                        "total_turns": row[4],
                        "created_at": row[5],
                        "last_activity": row[6]
                    })
                
                return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    async def save_turn(self, turn) -> bool:
        """保存回合"""
        try:
            async with self._transaction() as conn:
                turn_dict = turn.to_dict() if hasattr(turn, 'to_dict') else turn
                
                await conn.execute("""
                    INSERT OR REPLACE INTO turns 
                    (id, session_id, turn_number, player_input, status, llm_response, 
                     memories_used, interventions, created_at, started_at, completed_at, 
                     duration_ms, error, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
                    json.dumps(turn_dict.get("metadata", {}))
                ))
            
            logger.debug(f"Turn {turn_dict['id']} saved to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save turn {turn_dict.get('id', 'unknown')}: {e}")
            return False
    
    async def load_turns(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """加载回合"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute("""
                    SELECT * FROM turns 
                    WHERE session_id = ? 
                    ORDER BY turn_number DESC 
                    LIMIT ? OFFSET ?
                """, (session_id, limit, offset))
                
                rows = await cursor.fetchall()
                
                turns = []
                for row in rows:
                    turns.append({
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
                        "metadata": json.loads(row[13]) if row[13] else {}
                    })
                
                return turns
        except Exception as e:
            logger.error(f"Failed to load turns for session {session_id}: {e}")
            return []
    
    async def save_memory(self, memory_entity) -> bool:
        """保存记忆实体"""
        try:
            async with self._transaction() as conn:
                memory_dict = memory_entity.to_dict() if hasattr(memory_entity, 'to_dict') else memory_entity
                
                await conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, session_id, type, content, created_at, updated_at, version, metadata, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_dict["id"],
                    memory_dict["session_id"],
                    memory_dict["type"],
                    json.dumps(memory_dict["content"]),
                    memory_dict["created_at"],
                    memory_dict["updated_at"],
                    memory_dict.get("version", 1),
                    json.dumps(memory_dict.get("metadata", {})),
                    memory_dict.get("embedding")
                ))
            
            logger.debug(f"Memory {memory_dict['id']} saved to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save memory {memory_dict.get('id', 'unknown')}: {e}")
            return False
    
    async def load_memories(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """加载记忆"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute("""
                    SELECT * FROM memories 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (session_id, limit, offset))
                
                rows = await cursor.fetchall()
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": row[0],
                        "session_id": row[1],
                        "type": row[2],
                        "content": json.loads(row[3]),
                        "created_at": row[4],
                        "updated_at": row[5],
                        "version": row[6],
                        "metadata": json.loads(row[7]) if row[7] else {},
                        "embedding": row[8]
                    })
                
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
                
                cursor = await conn.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
                stats["active_sessions"] = (await cursor.fetchone())[0]
                
                # 回合统计
                cursor = await conn.execute("SELECT COUNT(*) FROM turns")
                stats["total_turns"] = (await cursor.fetchone())[0]
                
                # 记忆统计
                cursor = await conn.execute("SELECT COUNT(*) FROM memories")
                stats["total_memories"] = (await cursor.fetchone())[0]
                
                # 数据库大小
                cursor = await conn.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
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
    
    async def search_memories(self, session_id: str, query: str, limit: int = 10) -> List[Dict]:
        """搜索记忆（简单文本搜索）"""
        try:
            async with self._transaction() as conn:
                cursor = await conn.execute("""
                    SELECT * FROM memories
                    WHERE session_id = ? AND (
                        content LIKE ? OR
                        metadata LIKE ? OR
                        type LIKE ?
                    )
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (session_id, f"%{query}%", f"%{query}%", f"%{query}%", limit))
                
                rows = await cursor.fetchall()
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": row[0],
                        "session_id": row[1],
                        "type": row[2],
                        "content": json.loads(row[3]),
                        "created_at": row[4],
                        "updated_at": row[5],
                        "version": row[6],
                        "metadata": json.loads(row[7]) if row[7] else {},
                        "embedding": row[8]
                    })
                
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
                cursor = await conn.execute("""
                    UPDATE sessions
                    SET status = 'archived'
                    WHERE last_activity < ? AND status = 'active'
                """, (cutoff_iso,))
                archived_sessions = cursor.rowcount
                
                # 删除非常旧的归档会话
                cursor = await conn.execute("""
                    DELETE FROM sessions
                    WHERE status = 'archived' AND last_activity < ?
                """, (cutoff_iso,))
                deleted_sessions = cursor.rowcount
                
                logger.info(f"Cleaned up {archived_sessions} archived sessions, deleted {deleted_sessions} old sessions")
                
                return {
                    "archived_sessions": archived_sessions,
                    "deleted_sessions": deleted_sessions
                }
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {"archived_sessions": 0, "deleted_sessions": 0}
    
    async def close(self):
        """关闭所有数据库连接"""
        async with self._pool_lock:
            for conn in self._connection_pool:
                await conn.close()
            self._connection_pool.clear()
        logger.info("Database connections closed")