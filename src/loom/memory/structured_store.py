"""
结构化存储

提供关系型数据库存储接口，支持SQLite等后端。
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .world_memory import MemoryEntity, MemoryEntityType, MemoryRelation, MemoryRelationType
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StructuredStore:
    """结构化存储"""
    
    def __init__(self, db_path: str = "loom_memory.db", enable_cache: bool = True, cache_ttl: int = 300):
        self.db_path = Path(db_path)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl  # 缓存TTL（秒）
        self.query_cache = {}  # 查询缓存
        self.cache_timestamps = {}  # 缓存时间戳
        self._ensure_tables()
        logger.info(f"StructuredStore initialized with db={db_path}, cache={'enabled' if enable_cache else 'disabled'}")
    
    def _ensure_tables(self):
        """确保表存在"""
        def create_tables():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 实体表 - 存储角色、地点、物品等
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_entities (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    metadata TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # 关系表 - 实体间关系
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_relations (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (source_id, target_id, relation_type),
                    FOREIGN KEY (source_id) REFERENCES memory_entities (id),
                    FOREIGN KEY (target_id) REFERENCES memory_entities (id)
                )
            """)
            
            # 事实表 - 存储事件、状态变化等
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_facts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    fact_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source_entity_id TEXT,
                    target_entity_id TEXT,
                    confidence REAL DEFAULT 1.0,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_entity_id) REFERENCES memory_entities (id),
                    FOREIGN KEY (target_entity_id) REFERENCES memory_entities (id)
                )
            """)
            
            # 剧情线表 - 故事线、任务、目标
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plotlines (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,  -- active, completed, abandoned, paused
                    priority INTEGER DEFAULT 1,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # 剧情线-实体关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plotline_entities (
                    plotline_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    role TEXT NOT NULL,  -- protagonist, antagonist, location, etc.
                    significance REAL DEFAULT 0.5,
                    metadata TEXT NOT NULL,
                    PRIMARY KEY (plotline_id, entity_id, role),
                    FOREIGN KEY (plotline_id) REFERENCES plotlines (id),
                    FOREIGN KEY (entity_id) REFERENCES memory_entities (id)
                )
            """)
            
            # 版本控制表 - 数据版本历史
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entity_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    changed_fields TEXT NOT NULL,  -- JSON array of changed field names
                    changed_by TEXT,  -- user/system identifier
                    change_reason TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (entity_id) REFERENCES memory_entities (id),
                    UNIQUE(entity_id, version)
                )
            """)
            
            # 记忆关联表 - 实体-事实关联
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entity_fact_associations (
                    entity_id TEXT NOT NULL,
                    fact_id TEXT NOT NULL,
                    association_type TEXT NOT NULL,  -- involved_in, caused_by, affected_by, etc.
                    relevance REAL DEFAULT 0.5,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (entity_id, fact_id, association_type),
                    FOREIGN KEY (entity_id) REFERENCES memory_entities (id),
                    FOREIGN KEY (fact_id) REFERENCES memory_facts (id)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_session ON memory_entities (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON memory_entities (type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_active ON memory_entities (is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON memory_relations (source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON memory_relations (target_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_session ON memory_facts (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_timestamp ON memory_facts (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_type ON memory_facts (fact_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_plotlines_session ON plotlines (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_plotlines_status ON plotlines (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_versions_entity ON entity_versions (entity_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_associations_entity ON entity_fact_associations (entity_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_associations_fact ON entity_fact_associations (fact_id)")
            
            conn.commit()
            conn.close()
        
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self.executor, create_tables)
    
    async def store_entity(self, entity: MemoryEntity) -> bool:
        """存储实体"""
        def store():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_entities 
                (id, session_id, type, content, created_at, updated_at, version, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.id,
                entity.session_id,
                entity.type.value,
                json.dumps(entity.content, ensure_ascii=False),
                entity.created_at.isoformat(),
                entity.updated_at.isoformat(),
                entity.version,
                json.dumps(entity.metadata, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            return True
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, store)
            return True
        except Exception as e:
            logger.error(f"Failed to store entity {entity.id}: {e}")
            return False
    
    async def retrieve_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """检索实体"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM memory_entities WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return MemoryEntity(
                id=row[0],
                session_id=row[1],
                type=MemoryEntityType(row[2]),
                content=json.loads(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                version=row[6],
                metadata=json.loads(row[7])
            )
        
        try:
            loop = asyncio.get_event_loop()
            entity = await loop.run_in_executor(self.executor, retrieve)
            return entity
        except Exception as e:
            logger.error(f"Failed to retrieve entity {entity_id}: {e}")
            return None
    
    async def retrieve_entities_by_type(self, session_id: str, entity_type: MemoryEntityType, limit: int = 100) -> List[MemoryEntity]:
        """按类型检索实体"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM memory_entities 
                WHERE session_id = ? AND type = ? 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (session_id, entity_type.value, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            entities = []
            for row in rows:
                entities.append(MemoryEntity(
                    id=row[0],
                    session_id=row[1],
                    type=MemoryEntityType(row[2]),
                    content=json.loads(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5]),
                    version=row[6],
                    metadata=json.loads(row[7])
                ))
            
            return entities
        
        try:
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(self.executor, retrieve)
            return entities
        except Exception as e:
            logger.error(f"Failed to retrieve entities by type: {e}")
            return []
    
    async def search_entities(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[MemoryEntity]:
        """搜索实体"""
        def search():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 简单关键词搜索
            sql = """
                SELECT * FROM memory_entities 
                WHERE content LIKE ? 
                ORDER BY updated_at DESC 
                LIMIT ?
            """
            
            cursor.execute(sql, (f"%{query}%", limit))
            rows = cursor.fetchall()
            conn.close()
            
            entities = []
            for row in rows:
                entities.append(MemoryEntity(
                    id=row[0],
                    session_id=row[1],
                    type=MemoryEntityType(row[2]),
                    content=json.loads(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5]),
                    version=row[6],
                    metadata=json.loads(row[7])
                ))
            
            return entities
        
        try:
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(self.executor, search)
            return entities
        except Exception as e:
            logger.error(f"Failed to search entities: {e}")
            return []
    
    async def store_relation(self, relation: MemoryRelation) -> bool:
        """存储关系"""
        def store():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_relations 
                (source_id, target_id, relation_type, strength, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                relation.source_id,
                relation.target_id,
                relation.relation_type.value,
                relation.strength,
                json.dumps(relation.metadata, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            return True
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, store)
            return True
        except Exception as e:
            logger.error(f"Failed to store relation: {e}")
            return False
    
    async def retrieve_relations(self, entity_id: str, relation_type: Optional[MemoryRelationType] = None) -> List[MemoryRelation]:
        """检索关系"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if relation_type:
                cursor.execute("""
                    SELECT * FROM memory_relations 
                    WHERE (source_id = ? OR target_id = ?) AND relation_type = ?
                """, (entity_id, entity_id, relation_type.value))
            else:
                cursor.execute("""
                    SELECT * FROM memory_relations 
                    WHERE source_id = ? OR target_id = ?
                """, (entity_id, entity_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            relations = []
            for row in rows:
                relations.append(MemoryRelation(
                    source_id=row[0],
                    target_id=row[1],
                    relation_type=MemoryRelationType(row[2]),
                    strength=row[3],
                    metadata=json.loads(row[4])
                ))
            
            return relations
        
        try:
            loop = asyncio.get_event_loop()
            relations = await loop.run_in_executor(self.executor, retrieve)
            return relations
        except Exception as e:
            logger.error(f"Failed to retrieve relations: {e}")
            return []
    
    async def delete_entity(self, entity_id: str) -> bool:
        """删除实体"""
        def delete():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM memory_entities WHERE id = ?", (entity_id,))
            cursor.execute("DELETE FROM memory_relations WHERE source_id = ? OR target_id = ?", (entity_id, entity_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(self.executor, delete)
            return success
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            return False
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计"""
        def get_stats():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 实体统计
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM memory_entities 
                WHERE session_id = ? 
                GROUP BY type
            """, (session_id,))
            
            entity_stats = {}
            for row in cursor.fetchall():
                entity_stats[row[0]] = row[1]
            
            # 关系统计
            cursor.execute("""
                SELECT relation_type, COUNT(*) as count 
                FROM memory_relations 
                WHERE source_id IN (SELECT id FROM memory_entities WHERE session_id = ?)
                GROUP BY relation_type
            """, (session_id,))
            
            relation_stats = {}
            for row in cursor.fetchall():
                relation_stats[row[0]] = row[1]
            
            conn.close()
            
            return {
                "session_id": session_id,
                "entity_count": sum(entity_stats.values()),
                "entity_stats": entity_stats,
                "relation_count": sum(relation_stats.values()),
                "relation_stats": relation_stats
            }
        
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(self.executor, get_stats)
            return stats
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def store_fact(self, fact_data: Dict[str, Any]) -> str:
        """存储事实"""
        def store():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            fact_id = fact_data.get("id", str(uuid.uuid4()))
            timestamp = fact_data.get("timestamp", datetime.now().isoformat())
            
            cursor.execute("""
                INSERT INTO memory_facts
                (id, session_id, fact_type, content, timestamp, source_entity_id,
                 target_entity_id, confidence, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fact_id,
                fact_data["session_id"],
                fact_data["fact_type"],
                json.dumps(fact_data["content"], ensure_ascii=False),
                timestamp,
                fact_data.get("source_entity_id"),
                fact_data.get("target_entity_id"),
                fact_data.get("confidence", 1.0),
                json.dumps(fact_data.get("metadata", {}), ensure_ascii=False),
                datetime.now().isoformat()
            ))
            
            # 存储关联
            for entity_id in fact_data.get("related_entities", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO entity_fact_associations
                    (entity_id, fact_id, association_type, relevance, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    fact_id,
                    fact_data.get("association_type", "involved_in"),
                    fact_data.get("relevance", 0.5),
                    json.dumps({}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            return fact_id
        
        try:
            loop = asyncio.get_event_loop()
            fact_id = await loop.run_in_executor(self.executor, store)
            return fact_id
        except Exception as e:
            logger.error(f"Failed to store fact: {e}")
            return None
    
    async def retrieve_facts(self, session_id: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """检索事实"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM memory_facts WHERE session_id = ?"
            params = [session_id]
            
            if filters:
                if "fact_type" in filters:
                    query += " AND fact_type = ?"
                    params.append(filters["fact_type"])
                if "start_time" in filters:
                    query += " AND timestamp >= ?"
                    params.append(filters["start_time"])
                if "end_time" in filters:
                    query += " AND timestamp <= ?"
                    params.append(filters["end_time"])
                if "source_entity_id" in filters:
                    query += " AND source_entity_id = ?"
                    params.append(filters["source_entity_id"])
                if "target_entity_id" in filters:
                    query += " AND target_entity_id = ?"
                    params.append(filters["target_entity_id"])
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            facts = []
            for row in rows:
                facts.append({
                    "id": row[0],
                    "session_id": row[1],
                    "fact_type": row[2],
                    "content": json.loads(row[3]),
                    "timestamp": row[4],
                    "source_entity_id": row[5],
                    "target_entity_id": row[6],
                    "confidence": row[7],
                    "metadata": json.loads(row[8]),
                    "created_at": row[9]
                })
            
            return facts
        
        try:
            loop = asyncio.get_event_loop()
            facts = await loop.run_in_executor(self.executor, retrieve)
            return facts
        except Exception as e:
            logger.error(f"Failed to retrieve facts: {e}")
            return []
    
    async def create_plotline(self, plotline_data: Dict[str, Any]) -> str:
        """创建剧情线"""
        def create():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            plotline_id = plotline_data.get("id", str(uuid.uuid4()))
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO plotlines
                (id, session_id, title, description, status, priority,
                 start_time, end_time, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plotline_id,
                plotline_data["session_id"],
                plotline_data["title"],
                plotline_data["description"],
                plotline_data.get("status", "active"),
                plotline_data.get("priority", 1),
                plotline_data.get("start_time", now),
                plotline_data.get("end_time"),
                json.dumps(plotline_data.get("metadata", {}), ensure_ascii=False),
                now,
                now
            ))
            
            # 添加关联实体
            for entity_assoc in plotline_data.get("entities", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO plotline_entities
                    (plotline_id, entity_id, role, significance, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    plotline_id,
                    entity_assoc["entity_id"],
                    entity_assoc.get("role", "participant"),
                    entity_assoc.get("significance", 0.5),
                    json.dumps(entity_assoc.get("metadata", {}), ensure_ascii=False)
                ))
            
            conn.commit()
            conn.close()
            return plotline_id
        
        try:
            loop = asyncio.get_event_loop()
            plotline_id = await loop.run_in_executor(self.executor, create)
            return plotline_id
        except Exception as e:
            logger.error(f"Failed to create plotline: {e}")
            return None
    
    async def get_plotlines(self, session_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取剧情线"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM plotlines
                    WHERE session_id = ? AND status = ?
                    ORDER BY priority DESC, created_at DESC
                """, (session_id, status))
            else:
                cursor.execute("""
                    SELECT * FROM plotlines
                    WHERE session_id = ?
                    ORDER BY priority DESC, created_at DESC
                """, (session_id,))
            
            rows = cursor.fetchall()
            
            plotlines = []
            for row in rows:
                # 获取关联实体
                cursor.execute("""
                    SELECT entity_id, role, significance, metadata
                    FROM plotline_entities
                    WHERE plotline_id = ?
                """, (row[0],))
                
                entities = []
                for entity_row in cursor.fetchall():
                    entities.append({
                        "entity_id": entity_row[0],
                        "role": entity_row[1],
                        "significance": entity_row[2],
                        "metadata": json.loads(entity_row[3])
                    })
                
                plotlines.append({
                    "id": row[0],
                    "session_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "status": row[4],
                    "priority": row[5],
                    "start_time": row[6],
                    "end_time": row[7],
                    "metadata": json.loads(row[8]),
                    "created_at": row[9],
                    "updated_at": row[10],
                    "entities": entities
                })
            
            conn.close()
            return plotlines
        
        try:
            loop = asyncio.get_event_loop()
            plotlines = await loop.run_in_executor(self.executor, retrieve)
            return plotlines
        except Exception as e:
            logger.error(f"Failed to get plotlines: {e}")
            return []
    
    async def update_plotline(self, plotline_id: str, updates: Dict[str, Any]) -> bool:
        """更新剧情线"""
        def update():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建更新语句
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key == "metadata":
                    set_clauses.append("metadata = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "entities":
                    continue  # 单独处理
                else:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            params.append(plotline_id)
            
            cursor.execute(f"""
                UPDATE plotlines
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, params)
            
            # 更新关联实体
            if "entities" in updates:
                # 先删除现有关联
                cursor.execute("DELETE FROM plotline_entities WHERE plotline_id = ?", (plotline_id,))
                
                # 添加新关联
                for entity_assoc in updates["entities"]:
                    cursor.execute("""
                        INSERT INTO plotline_entities
                        (plotline_id, entity_id, role, significance, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        plotline_id,
                        entity_assoc["entity_id"],
                        entity_assoc.get("role", "participant"),
                        entity_assoc.get("significance", 0.5),
                        json.dumps(entity_assoc.get("metadata", {}), ensure_ascii=False)
                    ))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(self.executor, update)
            return success
        except Exception as e:
            logger.error(f"Failed to update plotline: {e}")
            return False
    
    async def save_entity_version(self, entity: MemoryEntity, changed_fields: List[str],
                                 changed_by: Optional[str] = None, reason: Optional[str] = None) -> bool:
        """保存实体版本"""
        def save():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO entity_versions
                (entity_id, version, content, changed_fields, changed_by, change_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.id,
                entity.version,
                json.dumps(entity.content, ensure_ascii=False),
                json.dumps(changed_fields, ensure_ascii=False),
                changed_by,
                reason,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, save)
            return True
        except Exception as e:
            logger.error(f"Failed to save entity version: {e}")
            return False
    
    async def get_entity_versions(self, entity_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取实体版本历史"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM entity_versions
                WHERE entity_id = ?
                ORDER BY version DESC
                LIMIT ?
            """, (entity_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            versions = []
            for row in rows:
                versions.append({
                    "id": row[0],
                    "entity_id": row[1],
                    "version": row[2],
                    "content": json.loads(row[3]),
                    "changed_fields": json.loads(row[4]),
                    "changed_by": row[5],
                    "change_reason": row[6],
                    "created_at": row[7]
                })
            
            return versions
        
        try:
            loop = asyncio.get_event_loop()
            versions = await loop.run_in_executor(self.executor, retrieve)
            return versions
        except Exception as e:
            logger.error(f"Failed to get entity versions: {e}")
            return []
    
    async def get_related_facts(self, entity_id: str, association_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取相关事实"""
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if association_type:
                cursor.execute("""
                    SELECT f.* FROM memory_facts f
                    JOIN entity_fact_associations a ON f.id = a.fact_id
                    WHERE a.entity_id = ? AND a.association_type = ?
                    ORDER BY f.timestamp DESC
                """, (entity_id, association_type))
            else:
                cursor.execute("""
                    SELECT f.* FROM memory_facts f
                    JOIN entity_fact_associations a ON f.id = a.fact_id
                    WHERE a.entity_id = ?
                    ORDER BY f.timestamp DESC
                """, (entity_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            facts = []
            for row in rows:
                facts.append({
                    "id": row[0],
                    "session_id": row[1],
                    "fact_type": row[2],
                    "content": json.loads(row[3]),
                    "timestamp": row[4],
                    "source_entity_id": row[5],
                    "target_entity_id": row[6],
                    "confidence": row[7],
                    "metadata": json.loads(row[8]),
                    "created_at": row[9]
                })
            
            return facts
        
        try:
            loop = asyncio.get_event_loop()
            facts = await loop.run_in_executor(self.executor, retrieve)
            return facts
        except Exception as e:
            logger.error(f"Failed to get related facts: {e}")
            return []
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """生成缓存键"""
        import hashlib
        import pickle
        
        data = {
            "method": method,
            "args": args,
            "kwargs": kwargs
        }
        
        try:
            data_bytes = pickle.dumps(data)
        except:
            data_bytes = str(data).encode()
        
        return hashlib.md5(data_bytes).hexdigest()
    
    def _get_cached_result(self, cache_key: str):
        """获取缓存结果"""
        if not self.enable_cache:
            return None
        
        if cache_key in self.query_cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            current_time = datetime.now().timestamp()
            
            if current_time - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                return self.query_cache[cache_key]
            else:
                # 缓存过期
                del self.query_cache[cache_key]
                del self.cache_timestamps[cache_key]
        
        return None
    
    def _set_cached_result(self, cache_key: str, result):
        """设置缓存结果"""
        if not self.enable_cache:
            return
        
        self.query_cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.now().timestamp()
        logger.debug(f"Cached result for key: {cache_key[:8]}...")
    
    def clear_cache(self):
        """清空缓存"""
        self.query_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Query cache cleared")
    
    async def retrieve_entity(self, entity_id: str) -> Optional[MemoryEntity]:
        """检索实体"""
        # 检查缓存
        if self.enable_cache:
            cache_key = self._get_cache_key("retrieve_entity", entity_id)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM memory_entities WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return MemoryEntity(
                id=row[0],
                session_id=row[1],
                type=MemoryEntityType(row[2]),
                content=json.loads(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                version=row[6],
                metadata=json.loads(row[7])
            )
        
        try:
            loop = asyncio.get_event_loop()
            entity = await loop.run_in_executor(self.executor, retrieve)
            
            # 缓存结果
            if self.enable_cache and entity is not None:
                cache_key = self._get_cache_key("retrieve_entity", entity_id)
                self._set_cached_result(cache_key, entity)
            
            return entity
        except Exception as e:
            logger.error(f"Failed to retrieve entity {entity_id}: {e}")
            return None
    
    async def retrieve_entities_by_type(self, session_id: str, entity_type: MemoryEntityType, limit: int = 100) -> List[MemoryEntity]:
        """按类型检索实体"""
        # 检查缓存
        if self.enable_cache:
            cache_key = self._get_cache_key("retrieve_entities_by_type", session_id, entity_type.value, limit)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        def retrieve():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM memory_entities
                WHERE session_id = ? AND type = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (session_id, entity_type.value, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            entities = []
            for row in rows:
                entities.append(MemoryEntity(
                    id=row[0],
                    session_id=row[1],
                    type=MemoryEntityType(row[2]),
                    content=json.loads(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5]),
                    version=row[6],
                    metadata=json.loads(row[7])
                ))
            
            return entities
        
        try:
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(self.executor, retrieve)
            
            # 缓存结果
            if self.enable_cache:
                cache_key = self._get_cache_key("retrieve_entities_by_type", session_id, entity_type.value, limit)
                self._set_cached_result(cache_key, entities)
            
            return entities
        except Exception as e:
            logger.error(f"Failed to retrieve entities by type: {e}")
            return []
    
    async def store_entity(self, entity: MemoryEntity) -> bool:
        """存储实体"""
        def store():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_entities
                (id, session_id, type, content, created_at, updated_at, version, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.id,
                entity.session_id,
                entity.type.value,
                json.dumps(entity.content, ensure_ascii=False),
                entity.created_at.isoformat(),
                entity.updated_at.isoformat(),
                entity.version,
                json.dumps(entity.metadata, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            return True
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(self.executor, store)
            
            # 清除相关缓存
            if success and self.enable_cache:
                self._invalidate_entity_cache(entity.id, entity.session_id, entity.type)
            
            return success
        except Exception as e:
            logger.error(f"Failed to store entity {entity.id}: {e}")
            return False
    
    def _invalidate_entity_cache(self, entity_id: str, session_id: str, entity_type: MemoryEntityType):
        """使实体相关缓存失效"""
        # 清除实体检索缓存
        entity_cache_key = self._get_cache_key("retrieve_entity", entity_id)
        if entity_cache_key in self.query_cache:
            del self.query_cache[entity_cache_key]
            del self.cache_timestamps[entity_cache_key]
        
        # 清除按类型检索缓存
        type_cache_key = self._get_cache_key("retrieve_entities_by_type", session_id, entity_type.value, 100)
        if type_cache_key in self.query_cache:
            del self.query_cache[type_cache_key]
            del self.cache_timestamps[type_cache_key]
        
        # 清除会话统计缓存
        stats_cache_key = self._get_cache_key("get_session_stats", session_id)
        if stats_cache_key in self.query_cache:
            del self.query_cache[stats_cache_key]
            del self.cache_timestamps[stats_cache_key]
    
    async def cleanup_old_sessions(self, days_old: int = 30):
        """清理旧会话"""
        def cleanup():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # 标记旧会话实体为不活跃
            cursor.execute("""
                UPDATE memory_entities
                SET is_active = 0
                WHERE session_id IN (
                    SELECT DISTINCT session_id
                    FROM memory_entities
                    WHERE created_at < ?
                    GROUP BY session_id
                    HAVING MAX(created_at) < ?
                )
            """, (cutoff_date, cutoff_date))
            
            logger.info(f"Marked old sessions (older than {days_old} days) as inactive")
            
            conn.commit()
            conn.close()
            return True
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, cleanup)
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return False