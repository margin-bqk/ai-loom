"""
摘要生成器

生成记忆摘要，压缩旧记忆，减少记忆膨胀。
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..interpretation.llm_provider import LLMProvider, LLMResponse
from ..utils.logging_config import get_logger
from .world_memory import MemoryEntity, MemoryEntityType

logger = get_logger(__name__)


@dataclass
class SummaryConfig:
    """摘要配置"""

    max_entities_per_summary: int = 20
    summary_interval_days: int = 7
    min_entities_to_summarize: int = 5
    preserve_recent_days: int = 3
    target_summary_length: int = 500
    cache_ttl_hours: int = 24
    summary_strategy: str = (
        "time_based"  # time_based, importance_based, relevance_based
    )
    summary_format: str = "text"  # text, structured, timeline
    importance_threshold: float = 0.7
    enable_cache: bool = True


@dataclass
class MemorySummary:
    """记忆摘要"""

    id: str
    session_id: str
    summary_text: str
    original_entities: List[str]  # 被摘要的实体ID列表
    created_at: datetime
    coverage_period: Dict[str, str]  # 覆盖的时间段
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemorySummarizer:
    """记忆摘要生成器"""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        config: Optional[SummaryConfig] = None,
    ):
        self.llm_provider = llm_provider
        self.config = config or SummaryConfig()
        self.summary_cache: Dict[
            str, Dict[str, Any]
        ] = {}  # cache_key -> {summary, timestamp}
        logger.info(
            f"MemorySummarizer initialized with strategy: {self.config.summary_strategy}"
        )

    async def generate_summary(
        self, entities: List[MemoryEntity], context: Dict[str, Any] = None
    ) -> Optional[MemorySummary]:
        """生成记忆摘要"""
        if not entities:
            logger.warning("No entities to summarize")
            return None

        if len(entities) < self.config.min_entities_to_summarize:
            logger.debug(
                f"Not enough entities to summarize ({len(entities)} < {self.config.min_entities_to_summarize})"
            )
            return None

        try:
            # 准备摘要输入
            summary_input = self._prepare_summary_input(entities, context)

            # 生成摘要
            summary_text = await self._generate_summary_text(summary_input)

            if not summary_text:
                logger.error("Failed to generate summary text")
                return None

            # 创建摘要对象
            summary = MemorySummary(
                id=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                session_id=entities[0].session_id if entities else "unknown",
                summary_text=summary_text,
                original_entities=[e.id for e in entities],
                created_at=datetime.now(),
                coverage_period=self._get_coverage_period(entities),
                metadata={
                    "entities_summarized": len(entities),
                    "entity_types": self._count_entity_types(entities),
                    "generation_method": "llm" if self.llm_provider else "template",
                },
            )

            logger.info(f"Generated summary covering {len(entities)} entities")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None

    def _generate_cache_key(
        self, entities: List[MemoryEntity], context: Optional[Dict[str, Any]]
    ) -> str:
        """生成缓存键"""
        # 基于实体ID和上下文生成哈希
        entity_ids = sorted([e.id for e in entities])
        context_str = json.dumps(context, sort_keys=True) if context else ""

        data = f"{','.join(entity_ids)}:{context_str}:{self.config.summary_strategy}:{self.config.summary_format}"
        return hashlib.md5(data.encode()).hexdigest()

    def _get_cached_summary(self, cache_key: str) -> Optional[MemorySummary]:
        """获取缓存的摘要"""
        if not self.config.enable_cache:
            return None

        if cache_key in self.summary_cache:
            cache_entry = self.summary_cache[cache_key]
            cache_age = datetime.now() - cache_entry["timestamp"]

            # 检查缓存是否过期
            if cache_age < timedelta(hours=self.config.cache_ttl_hours):
                logger.debug(f"Using cached summary for key: {cache_key[:8]}...")
                return cache_entry["summary"]
            else:
                # 缓存过期，删除
                del self.summary_cache[cache_key]

        return None

    def _cache_summary(self, cache_key: str, summary: MemorySummary):
        """缓存摘要"""
        if not self.config.enable_cache:
            return

        self.summary_cache[cache_key] = {
            "summary": summary,
            "timestamp": datetime.now(),
        }
        logger.debug(f"Cached summary for key: {cache_key[:8]}...")

    async def generate_summary_with_cache(
        self, entities: List[MemoryEntity], context: Dict[str, Any] = None
    ) -> Optional[MemorySummary]:
        """生成记忆摘要（带缓存）"""
        if not entities:
            return None

        # 生成缓存键
        cache_key = self._generate_cache_key(entities, context)

        # 检查缓存
        cached_summary = self._get_cached_summary(cache_key)
        if cached_summary:
            return cached_summary

        # 生成新摘要
        summary = await self.generate_summary(entities, context)

        if summary and self.config.enable_cache:
            self._cache_summary(cache_key, summary)

        return summary

    def _select_entities_by_strategy(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """根据策略选择实体"""
        if self.config.summary_strategy == "time_based":
            return self._select_entities_time_based(entities)
        elif self.config.summary_strategy == "importance_based":
            return self._select_entities_importance_based(entities)
        elif self.config.summary_strategy == "relevance_based":
            return self._select_entities_relevance_based(entities)
        else:
            return entities[: self.config.max_entities_per_summary]

    def _select_entities_time_based(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """基于时间选择实体（选择最旧的）"""
        sorted_entities = sorted(entities, key=lambda e: e.created_at)
        return sorted_entities[: self.config.max_entities_per_summary]

    def _select_entities_importance_based(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """基于重要性选择实体"""
        # 计算实体重要性（基于类型、元数据等）
        scored_entities = []
        for entity in entities:
            score = self._calculate_entity_importance(entity)
            scored_entities.append((entity, score))

        # 按重要性排序
        scored_entities.sort(key=lambda x: x[1], reverse=True)

        # 选择重要性高于阈值的实体
        selected = []
        for entity, score in scored_entities:
            if (
                score >= self.config.importance_threshold
                and len(selected) < self.config.max_entities_per_summary
            ):
                selected.append(entity)

        return selected

    def _calculate_entity_importance(self, entity: MemoryEntity) -> float:
        """计算实体重要性"""
        importance = 0.5  # 基础重要性

        # 基于类型的重要性
        type_importance = {
            MemoryEntityType.CHARACTER: 0.8,
            MemoryEntityType.EVENT: 0.7,
            MemoryEntityType.FACT: 0.6,
            MemoryEntityType.LOCATION: 0.5,
            MemoryEntityType.PLOTLINE: 0.9,
            MemoryEntityType.OBJECT: 0.4,
            MemoryEntityType.CONCEPT: 0.5,
            MemoryEntityType.STYLE: 0.3,
        }

        importance = type_importance.get(entity.type, 0.5)

        # 基于元数据调整
        if entity.metadata:
            if "importance" in entity.metadata:
                try:
                    metadata_importance = float(entity.metadata["importance"])
                    importance = (importance + metadata_importance) / 2
                except:
                    pass

        return importance

    def _select_entities_relevance_based(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """基于相关性选择实体（选择相互关联的实体）"""
        # 简化实现：按时间分组
        if not entities:
            return []

        sorted_entities = sorted(entities, key=lambda e: e.created_at)

        # 按时间窗口分组
        groups = []
        current_group = [sorted_entities[0]]

        for i in range(1, len(sorted_entities)):
            time_diff = (
                sorted_entities[i].created_at - sorted_entities[i - 1].created_at
            )
            if time_diff < timedelta(hours=24):  # 24小时内视为相关
                current_group.append(sorted_entities[i])
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [sorted_entities[i]]

        if current_group:
            groups.append(current_group)

        # 选择最大的组
        if groups:
            largest_group = max(groups, key=len)
            return largest_group[: self.config.max_entities_per_summary]

        return sorted_entities[: self.config.max_entities_per_summary]

    async def generate_summary_in_format(
        self,
        entities: List[MemoryEntity],
        summary_format: str = None,
        context: Dict[str, Any] = None,
    ) -> Optional[MemorySummary]:
        """生成指定格式的摘要"""
        if not entities:
            return None

        format_to_use = summary_format or self.config.summary_format

        if format_to_use == "structured":
            return await self._generate_structured_summary(entities, context)
        elif format_to_use == "timeline":
            return await self._generate_timeline_summary(entities, context)
        else:  # text
            return await self.generate_summary(entities, context)

    async def _generate_structured_summary(
        self, entities: List[MemoryEntity], context: Optional[Dict[str, Any]]
    ) -> Optional[MemorySummary]:
        """生成结构化摘要"""
        if not self.llm_provider:
            logger.warning("LLM provider required for structured summaries")
            return await self.generate_summary(entities, context)

        try:
            # 准备结构化摘要输入
            summary_input = self._prepare_summary_input(entities, context)

            prompt = f"""请将以下记忆实体汇总成一个结构化的叙事摘要。摘要应该包含以下部分：
    1. 关键事件时间线
    2. 主要角色及其关系
    3. 重要地点和物品
    4. 剧情发展脉络

    请以JSON格式返回，包含以下字段：
    - timeline: 事件时间线数组
    - characters: 角色信息数组
    - locations: 地点信息数组
    - plot_development: 剧情发展描述
    - summary_text: 整体摘要文本

    记忆实体：
    {summary_input}

    请生成结构化摘要："""

            response = await self.llm_provider.generate(prompt)

            # 尝试解析JSON
            try:
                structured_data = json.loads(response.content.strip())
                summary_text = structured_data.get("summary_text", "结构化摘要生成成功")
            except:
                summary_text = response.content.strip()

            # 创建摘要对象
            summary = MemorySummary(
                id=f"structured_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                session_id=entities[0].session_id if entities else "unknown",
                summary_text=summary_text,
                original_entities=[e.id for e in entities],
                created_at=datetime.now(),
                coverage_period=self._get_coverage_period(entities),
                metadata={
                    "entities_summarized": len(entities),
                    "entity_types": self._count_entity_types(entities),
                    "summary_format": "structured",
                    "structured_data": (
                        structured_data if "structured_data" in locals() else None
                    ),
                },
            )

            logger.info(
                f"Generated structured summary covering {len(entities)} entities"
            )
            return summary

        except Exception as e:
            logger.error(f"Failed to generate structured summary: {e}")
            return await self.generate_summary(entities, context)

    async def _generate_timeline_summary(
        self, entities: List[MemoryEntity], context: Optional[Dict[str, Any]]
    ) -> Optional[MemorySummary]:
        """生成时间线摘要"""
        # 按时间排序
        sorted_entities = sorted(entities, key=lambda e: e.created_at)

        # 构建时间线
        timeline_entries = []
        for entity in sorted_entities:
            time_str = entity.created_at.strftime("%Y-%m-%d %H:%M")

            # 提取关键信息
            content_preview = str(entity.content)
            if len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."

            timeline_entries.append(
                f"{time_str} [{entity.type.value}]: {content_preview}"
            )

        timeline_text = "\n".join(timeline_entries)

        # 创建摘要对象
        summary = MemorySummary(
            id=f"timeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            session_id=entities[0].session_id if entities else "unknown",
            summary_text=f"时间线摘要:\n{timeline_text}",
            original_entities=[e.id for e in entities],
            created_at=datetime.now(),
            coverage_period=self._get_coverage_period(entities),
            metadata={
                "entities_summarized": len(entities),
                "entity_types": self._count_entity_types(entities),
                "summary_format": "timeline",
                "timeline_entries": len(timeline_entries),
            },
        )

        logger.info(f"Generated timeline summary with {len(timeline_entries)} entries")
        return summary

    async def clear_cache(self):
        """清空缓存"""
        self.summary_cache.clear()
        logger.info("Summary cache cleared")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_entries = len(self.summary_cache)
        cache_size = sum(len(str(v)) for v in self.summary_cache.values())

        return {
            "total_entries": total_entries,
            "cache_size_bytes": cache_size,
            "cache_enabled": self.config.enable_cache,
            "cache_ttl_hours": self.config.cache_ttl_hours,
        }

    def _prepare_summary_input(
        self, entities: List[MemoryEntity], context: Optional[Dict[str, Any]]
    ) -> str:
        """准备摘要输入"""
        # 按时间排序
        sorted_entities = sorted(entities, key=lambda e: e.created_at)

        input_parts = []

        # 添加上下文
        if context:
            input_parts.append(f"# 上下文\n")
            for key, value in context.items():
                input_parts.append(f"{key}: {value}")

        # 添加实体信息
        input_parts.append(f"\n# 需要摘要的记忆实体 ({len(sorted_entities)}个)")

        for i, entity in enumerate(sorted_entities):
            entity_text = self._format_entity_for_summary(entity, i + 1)
            input_parts.append(entity_text)

        return "\n".join(input_parts)

    def _format_entity_for_summary(self, entity: MemoryEntity, index: int) -> str:
        """格式化实体用于摘要"""
        time_str = entity.created_at.strftime("%Y-%m-%d %H:%M")

        # 提取关键信息
        content_preview = str(entity.content)
        if len(content_preview) > 100:
            content_preview = content_preview[:100] + "..."

        return f"""
## 实体 {index}: {entity.type.value}
- ID: {entity.id}
- 创建时间: {time_str}
- 内容: {content_preview}
"""

    async def _generate_summary_text(self, summary_input: str) -> Optional[str]:
        """生成摘要文本"""
        # 如果有LLM提供者，使用LLM生成摘要
        if self.llm_provider:
            return await self._generate_summary_with_llm(summary_input)

        # 否则使用模板生成
        return self._generate_summary_with_template(summary_input)

    async def _generate_summary_with_llm(self, summary_input: str) -> Optional[str]:
        """使用LLM生成摘要"""
        prompt = f"""请将以下记忆实体汇总成一个连贯的叙事摘要。摘要应该：
1. 保留关键信息和事件
2. 保持时间顺序
3. 突出重要角色和地点
4. 长度约{self.config.target_summary_length}字

记忆实体：
{summary_input}

请生成摘要："""

        try:
            response = await self.llm_provider.generate(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return None

    def _generate_summary_with_template(self, summary_input: str) -> str:
        """使用模板生成摘要"""
        # 简单模板摘要
        lines = summary_input.split("\n")
        entity_count = 0
        entity_types = {}

        for line in lines:
            if "实体" in line and ":" in line:
                entity_count += 1
            if "类型:" in line:
                entity_type = line.split("类型:")[1].strip()
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        type_summary = ", ".join([f"{k}: {v}" for k, v in entity_types.items()])

        return f"""记忆摘要（自动生成）
覆盖实体数量: {entity_count}
实体类型分布: {type_summary}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

这是一个自动生成的记忆摘要。由于未配置LLM，摘要内容较为简单。建议配置LLM提供者以获得更高质量的摘要。"""

    def _get_coverage_period(self, entities: List[MemoryEntity]) -> Dict[str, str]:
        """获取覆盖时间段"""
        if not entities:
            return {"start": "", "end": ""}

        sorted_entities = sorted(entities, key=lambda e: e.created_at)
        start_time = sorted_entities[0].created_at
        end_time = sorted_entities[-1].created_at

        return {"start": start_time.isoformat(), "end": end_time.isoformat()}

    def _count_entity_types(self, entities: List[MemoryEntity]) -> Dict[str, int]:
        """统计实体类型"""
        type_counts = {}
        for entity in entities:
            entity_type = entity.type.value
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts

    async def should_summarize(self, entities: List[MemoryEntity]) -> bool:
        """判断是否应该生成摘要"""
        if len(entities) < self.config.min_entities_to_summarize:
            return False

        # 检查时间范围
        if len(entities) >= self.config.max_entities_per_summary:
            return True

        # 检查是否超过摘要间隔
        sorted_entities = sorted(entities, key=lambda e: e.created_at)
        oldest = sorted_entities[0].created_at
        newest = sorted_entities[-1].created_at

        time_span = newest - oldest
        if time_span.days >= self.config.summary_interval_days:
            return True

        return False

    async def select_entities_for_summarization(
        self, all_entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """选择需要摘要的实体"""
        if not all_entities:
            return []

        # 排除最近创建的实体
        cutoff_time = datetime.now() - timedelta(days=self.config.preserve_recent_days)
        old_entities = [e for e in all_entities if e.created_at < cutoff_time]

        # 如果旧实体数量不足，返回空列表
        if len(old_entities) < self.config.min_entities_to_summarize:
            return []

        # 根据策略选择实体
        selected = self._select_entities_by_strategy(old_entities)

        logger.debug(
            f"Selected {len(selected)} entities for summarization using {self.config.summary_strategy} strategy"
        )
        return selected

    async def create_summary_entity(self, summary: MemorySummary) -> MemoryEntity:
        """创建摘要实体"""
        return MemoryEntity(
            id=summary.id,
            session_id=summary.session_id,
            type=MemoryEntityType.FACT,
            content={
                "summary_type": "memory_consolidation",
                "text": summary.summary_text,
                "original_entity_count": len(summary.original_entities),
                "coverage_period": summary.coverage_period,
            },
            created_at=summary.created_at,
            updated_at=summary.created_at,
            metadata=summary.metadata,
        )

    async def process_summarization(
        self, world_memory, force: bool = False
    ) -> Optional[MemorySummary]:
        """处理摘要流程"""
        # 获取所有实体
        all_entities = list(world_memory.entities.values())

        if not all_entities:
            logger.info("No entities to summarize")
            return None

        # 选择需要摘要的实体
        if force:
            # 强制摘要：选择最旧的实体
            sorted_entities = sorted(all_entities, key=lambda e: e.created_at)
            entities_to_summarize = sorted_entities[
                : self.config.max_entities_per_summary
            ]
        else:
            entities_to_summarize = await self.select_entities_for_summarization(
                all_entities
            )

        if not entities_to_summarize:
            logger.debug("No entities selected for summarization")
            return None

        # 生成摘要
        context = {
            "session_id": world_memory.session_id,
            "total_entities": len(all_entities),
            "summarization_reason": "forced" if force else "automatic",
        }

        summary = await self.generate_summary(entities_to_summarize, context)

        if summary:
            # 创建摘要实体
            summary_entity = await self.create_summary_entity(summary)

            # 存储摘要实体
            await world_memory.store_entity(summary_entity)

            # 可选：删除被摘要的原始实体
            # 这里不自动删除，让用户决定

            logger.info(
                f"Summarization completed: {len(entities_to_summarize)} entities summarized"
            )

        return summary
