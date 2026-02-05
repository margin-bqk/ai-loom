"""
记忆一致性检查器 (MemoryConsistencyChecker)

检查记忆冲突、时间线一致性、实体关系一致性，确保世界记忆的逻辑连贯性。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from .world_memory import (
    MemoryEntity,
    MemoryEntityType,
    MemoryRelation,
    MemoryRelationType,
)
from .interfaces import ConsistencyError
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ConsistencyIssueType(Enum):
    """一致性问题类型"""

    TEMPORAL_CONFLICT = "temporal_conflict"
    FACT_CONTRADICTION = "fact_contradiction"
    RELATIONSHIP_INCONSISTENCY = "relationship_inconsistency"
    ENTITY_DUPLICATE = "entity_duplicate"
    LOGICAL_CONTRADICTION = "logical_contradiction"


class ConsistencySeverity(Enum):
    """一致性严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ConsistencyIssue:
    """一致性问题"""

    issue_id: str
    issue_type: ConsistencyIssueType
    severity: ConsistencySeverity
    description: str
    affected_entities: List[str]
    conflicting_data: Dict[str, Any]
    detected_at: datetime
    suggested_fixes: List[Dict[str, Any]] = field(default_factory=list)
    resolved: bool = False


@dataclass
class ConsistencyCheckResult:
    """一致性检查结果"""

    check_id: str
    session_id: str
    issues_found: int
    issues: List[ConsistencyIssue]
    check_duration: float
    checked_at: datetime


class MemoryConsistencyChecker:
    """记忆一致性检查器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.issues_history: Dict[str, ConsistencyIssue] = {}

    async def check_consistency(
        self, entities: List[MemoryEntity], relations: List[MemoryRelation] = None
    ) -> ConsistencyCheckResult:
        """检查记忆一致性"""
        import time

        start_time = time.time()

        try:
            check_id = f"check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session_id = entities[0].session_id if entities else "unknown"

            issues = []

            # 检查重复实体
            issues.extend(await self._check_duplicates(entities))

            # 检查时间冲突
            issues.extend(await self._check_temporal_conflicts(entities))

            # 检查事实矛盾
            issues.extend(await self._check_fact_contradictions(entities))

            # 检查关系一致性
            if relations:
                issues.extend(
                    await self._check_relationship_consistency(entities, relations)
                )

            # 记录到历史
            for issue in issues:
                self.issues_history[issue.issue_id] = issue

            duration = time.time() - start_time

            return ConsistencyCheckResult(
                check_id=check_id,
                session_id=session_id,
                issues_found=len(issues),
                issues=issues,
                check_duration=duration,
                checked_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Consistency check failed: {e}")
            import time

            return ConsistencyCheckResult(
                check_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                session_id="error",
                issues_found=0,
                issues=[],
                check_duration=time.time() - start_time,
                checked_at=datetime.now(),
            )

    async def _check_duplicates(
        self, entities: List[MemoryEntity]
    ) -> List[ConsistencyIssue]:
        """检查重复实体"""
        issues = []
        seen_hashes = {}

        for entity in entities:
            content_hash = self._hash_entity_content(entity)

            if content_hash in seen_hashes:
                duplicate = seen_hashes[content_hash]

                issue = ConsistencyIssue(
                    issue_id=f"duplicate_{entity.id}_{duplicate.id}",
                    issue_type=ConsistencyIssueType.ENTITY_DUPLICATE,
                    severity=ConsistencySeverity.MEDIUM,
                    description=f"实体 {entity.id} 和 {duplicate.id} 内容重复",
                    affected_entities=[entity.id, duplicate.id],
                    conflicting_data={
                        "content_hash": content_hash,
                        "entity1_created": entity.created_at.isoformat(),
                        "entity2_created": duplicate.created_at.isoformat(),
                    },
                    detected_at=datetime.now(),
                    suggested_fixes=[
                        {
                            "action": "merge",
                            "description": "合并重复实体",
                            "parameters": {"keep_older": True},
                        }
                    ],
                )
                issues.append(issue)
            else:
                seen_hashes[content_hash] = entity

        return issues

    def _hash_entity_content(self, entity: MemoryEntity) -> str:
        """哈希实体内容"""
        content_str = (
            json.dumps(entity.content, sort_keys=True)
            if isinstance(entity.content, dict)
            else str(entity.content)
        )
        data = f"{entity.type.value}:{content_str}"
        return hashlib.md5(data.encode()).hexdigest()

    async def _check_temporal_conflicts(
        self, entities: List[MemoryEntity]
    ) -> List[ConsistencyIssue]:
        """检查时间冲突"""
        issues = []

        # 按类型分组
        entities_by_type = {}
        for entity in entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity)

        # 检查每种类型的时间冲突
        for entity_type, type_entities in entities_by_type.items():
            # 按时间排序
            sorted_entities = sorted(type_entities, key=lambda e: e.created_at)

            for i in range(len(sorted_entities) - 1):
                e1 = sorted_entities[i]
                e2 = sorted_entities[i + 1]

                # 检查时间是否太接近（24小时内）
                time_diff = abs((e1.created_at - e2.created_at).total_seconds())
                if time_diff < 24 * 3600:  # 24小时
                    issue = ConsistencyIssue(
                        issue_id=f"temporal_{e1.id}_{e2.id}",
                        issue_type=ConsistencyIssueType.TEMPORAL_CONFLICT,
                        severity=ConsistencySeverity.MEDIUM,
                        description=f"实体 {e1.id} 和 {e2.id} 时间冲突（24小时内）",
                        affected_entities=[e1.id, e2.id],
                        conflicting_data={
                            "time_diff_hours": time_diff / 3600,
                            "entity_type": entity_type.value,
                        },
                        detected_at=datetime.now(),
                        suggested_fixes=[
                            {
                                "action": "adjust_timing",
                                "description": "调整实体时间",
                                "parameters": {"offset_hours": 24},
                            }
                        ],
                    )
                    issues.append(issue)

        return issues

    async def _check_fact_contradictions(
        self, entities: List[MemoryEntity]
    ) -> List[ConsistencyIssue]:
        """检查事实矛盾"""
        issues = []

        # 查找相同类型的实体
        entities_by_type = {}
        for entity in entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity)

        # 检查每种类型的事实矛盾
        for entity_type, type_entities in entities_by_type.items():
            # 对于角色类型，检查状态矛盾
            if entity_type == MemoryEntityType.CHARACTER:
                for entity in type_entities:
                    if isinstance(entity.content, dict):
                        status = entity.content.get("status")
                        if status == "dead":
                            # 检查是否有后续事件涉及这个角色
                            later_events = [
                                e
                                for e in entities
                                if e.type == MemoryEntityType.EVENT
                                and e.created_at > entity.created_at
                                and isinstance(e.content, dict)
                                and entity.id in str(e.content.get("participants", []))
                            ]

                            if later_events:
                                issue = ConsistencyIssue(
                                    issue_id=f"logical_dead_{entity.id}",
                                    issue_type=ConsistencyIssueType.LOGICAL_CONTRADICTION,
                                    severity=ConsistencySeverity.HIGH,
                                    description=f"角色 {entity.id} 已死亡但参与了后续事件",
                                    affected_entities=[entity.id]
                                    + [e.id for e in later_events],
                                    conflicting_data={
                                        "character_status": "dead",
                                        "later_events": [e.id for e in later_events],
                                    },
                                    detected_at=datetime.now(),
                                    suggested_fixes=[
                                        {
                                            "action": "update_status",
                                            "description": "更新角色状态",
                                            "parameters": {"new_status": "alive"},
                                        }
                                    ],
                                )
                                issues.append(issue)

        return issues

    async def _check_relationship_consistency(
        self, entities: List[MemoryEntity], relations: List[MemoryRelation]
    ) -> List[ConsistencyIssue]:
        """检查关系一致性"""
        issues = []

        # 构建实体ID集合
        entity_ids = {entity.id for entity in entities}

        for relation in relations:
            # 检查关系引用是否有效
            if relation.source_id not in entity_ids:
                issue = ConsistencyIssue(
                    issue_id=f"relation_source_{relation.source_id}",
                    issue_type=ConsistencyIssueType.RELATIONSHIP_INCONSISTENCY,
                    severity=ConsistencySeverity.HIGH,
                    description=f"关系引用不存在的源实体: {relation.source_id}",
                    affected_entities=[relation.source_id],
                    conflicting_data={
                        "relation_type": relation.relation_type.value,
                        "source_id": relation.source_id,
                        "target_id": relation.target_id,
                    },
                    detected_at=datetime.now(),
                    suggested_fixes=[
                        {
                            "action": "remove_relation",
                            "description": "删除无效关系",
                            "parameters": {},
                        }
                    ],
                )
                issues.append(issue)

            if relation.target_id not in entity_ids:
                issue = ConsistencyIssue(
                    issue_id=f"relation_target_{relation.target_id}",
                    issue_type=ConsistencyIssueType.RELATIONSHIP_INCONSISTENCY,
                    severity=ConsistencySeverity.HIGH,
                    description=f"关系引用不存在的目标实体: {relation.target_id}",
                    affected_entities=[relation.target_id],
                    conflicting_data={
                        "relation_type": relation.relation_type.value,
                        "source_id": relation.source_id,
                        "target_id": relation.target_id,
                    },
                    detected_at=datetime.now(),
                    suggested_fixes=[
                        {
                            "action": "remove_relation",
                            "description": "删除无效关系",
                            "parameters": {},
                        }
                    ],
                )
                issues.append(issue)

        return issues

    async def get_unresolved_issues(self) -> List[ConsistencyIssue]:
        """获取未解决的问题"""
        return [issue for issue in self.issues_history.values() if not issue.resolved]

    async def mark_issue_resolved(self, issue_id: str):
        """标记问题为已解决"""
        if issue_id in self.issues_history:
            self.issues_history[issue_id].resolved = True
            logger.info(f"Marked issue {issue_id} as resolved")

    async def clear_old_issues(self, days_old: int = 30):
        """清理旧问题"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        old_issues = [
            issue_id
            for issue_id, issue in self.issues_history.items()
            if issue.detected_at < cutoff_date and issue.resolved
        ]

        for issue_id in old_issues:
            del self.issues_history[issue_id]

        logger.info(f"Cleared {len(old_issues)} old issues")
