"""
记忆摘要生成器 (MemorySummarizer)

增强版记忆摘要生成器，支持基于LLM的摘要算法、重要性评分、摘要优化和增量更新。

设计目标：
1. 支持多种摘要生成策略（时间、重要性、相关性）
2. 集成LLM提供高质量摘要
3. 支持摘要缓存和增量更新
4. 提供重要性评分和摘要优化
5. 支持多种摘要格式（文本、结构化、时间线）
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..interpretation.llm_provider import LLMProvider, LLMResponse
from ..utils.async_helpers import async_retry
from ..utils.logging_config import get_logger
from .interfaces import MemorySummarizer as BaseMemorySummarizer
from .world_memory import MemoryEntity, MemoryEntityType

logger = get_logger(__name__)


class SummaryStrategy(Enum):
    """摘要生成策略"""

    TIME_BASED = "time_based"  # 基于时间（最旧的实体）
    IMPORTANCE_BASED = "importance_based"  # 基于重要性
    RELEVANCE_BASED = "relevance_based"  # 基于相关性
    HYBRID = "hybrid"  # 混合策略


class SummaryFormat(Enum):
    """摘要格式"""

    TEXT = "text"  # 纯文本摘要
    STRUCTURED = "structured"  # 结构化摘要（JSON）
    TIMELINE = "timeline"  # 时间线格式
    BULLET_POINTS = "bullet_points"  # 要点列表


@dataclass
class SummaryConfig:
    """摘要配置"""

    max_entities_per_summary: int = 20
    summary_interval_days: int = 7
    min_entities_to_summarize: int = 5
    preserve_recent_days: int = 3
    target_summary_length: int = 500
    cache_ttl_hours: int = 24
    summary_strategy: SummaryStrategy = SummaryStrategy.TIME_BASED
    summary_format: SummaryFormat = SummaryFormat.TEXT
    importance_threshold: float = 0.7
    enable_cache: bool = True
    enable_incremental: bool = True
    max_cache_size: int = 100
    llm_model: str = "gpt-3.5-turbo"
    temperature: float = 0.3

    def __post_init__(self):
        """后初始化处理，将字符串转换为枚举值"""
        # 如果summary_strategy是字符串，转换为SummaryStrategy枚举
        if isinstance(self.summary_strategy, str):
            try:
                self.summary_strategy = SummaryStrategy(self.summary_strategy.lower())
            except ValueError:
                # 如果无法转换，使用默认值
                self.summary_strategy = SummaryStrategy.TIME_BASED
                logger.warning(
                    f"Unsupported summary strategy string: {self.summary_strategy}, using default: {self.summary_strategy}"
                )

        # 如果summary_format是字符串，转换为SummaryFormat枚举
        if isinstance(self.summary_format, str):
            try:
                self.summary_format = SummaryFormat(self.summary_format.lower())
            except ValueError:
                # 如果无法转换，使用默认值
                self.summary_format = SummaryFormat.TEXT
                logger.warning(
                    f"Unsupported summary format string: {self.summary_format}, using default: {self.summary_format}"
                )


@dataclass
class EnhancedMemorySummary:
    """增强记忆摘要"""

    id: str
    session_id: str
    summary_text: str
    original_entities: List[str]  # 被摘要的实体ID列表
    created_at: datetime
    coverage_period: Dict[str, str]  # 覆盖的时间段
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_scores: Dict[str, float] = field(default_factory=dict)  # 实体重要性分数
    summary_format: SummaryFormat = SummaryFormat.TEXT
    version: int = 1


@dataclass
class ImportanceScore:
    """重要性评分"""

    entity_id: str
    score: float
    factors: Dict[str, float]  # 评分因素
    explanation: Optional[str] = None


class MemorySummarizer(BaseMemorySummarizer):
    """增强记忆摘要生成器

    提供完整的记忆摘要功能，包括：
    1. 基于LLM的摘要生成
    2. 实体重要性评分
    3. 摘要缓存和增量更新
    4. 多种摘要格式支持
    5. 摘要优化和压缩
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """初始化记忆摘要生成器

        Args:
            llm_provider: LLM提供者
            config: 配置字典
        """
        self.llm_provider = llm_provider
        self.config = SummaryConfig(**config) if config else SummaryConfig()

        # 摘要缓存
        self.summary_cache: Dict[str, Dict[str, Any]] = (
            {}
        )  # cache_key -> {summary, timestamp}

        # 重要性评分缓存
        self.importance_cache: Dict[str, ImportanceScore] = {}

        logger.info(
            f"MemorySummarizer initialized with strategy: {self.config.summary_strategy.value}"
        )

    async def summarize_entities(self, entities: List[MemoryEntity]) -> str:
        """生成实体摘要

        Args:
            entities: 记忆实体列表

        Returns:
            摘要文本
        """
        if not entities:
            return "没有可摘要的实体"

        # 选择要摘要的实体
        selected_entities = self._select_entities_for_summary(entities)

        # 生成摘要
        summary = await self.generate_summary(selected_entities)

        if summary:
            return summary.summary_text
        else:
            return "摘要生成失败"

    async def generate_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """生成时间线

        Args:
            session_id: 会话ID

        Returns:
            时间线事件列表
        """
        # 这个方法需要从存储中获取实体
        # 这里返回空列表，实际实现需要集成存储
        return []

    async def generate_summary(
        self, entities: List[MemoryEntity], context: Dict[str, Any] = None
    ) -> Optional[EnhancedMemorySummary]:
        """生成记忆摘要

        Args:
            entities: 记忆实体列表
            context: 上下文信息

        Returns:
            增强记忆摘要对象
        """
        if not entities:
            logger.warning("No entities to summarize")
            return None

        if len(entities) < self.config.min_entities_to_summarize:
            logger.debug(
                f"Not enough entities to summarize ({len(entities)} < {self.config.min_entities_to_summarize})"
            )
            return None

        try:
            # 检查缓存
            cache_key = self._generate_cache_key(entities, context)
            cached_summary = self._get_cached_summary(cache_key)
            if cached_summary:
                return cached_summary

            # 计算重要性评分
            importance_scores = await self._calculate_importance_scores(entities)

            # 准备摘要输入
            summary_input = self._prepare_summary_input(
                entities, context, importance_scores
            )

            # 根据格式生成摘要
            if self.config.summary_format == SummaryFormat.STRUCTURED:
                summary_text = await self._generate_structured_summary(summary_input)
            elif self.config.summary_format == SummaryFormat.TIMELINE:
                summary_text = await self._generate_timeline_summary(entities)
            elif self.config.summary_format == SummaryFormat.BULLET_POINTS:
                summary_text = await self._generate_bullet_points_summary(summary_input)
            else:  # TEXT
                summary_text = await self._generate_text_summary(summary_input)

            if not summary_text:
                logger.error("Failed to generate summary text")
                return None

            # 创建摘要对象
            summary = EnhancedMemorySummary(
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
                    "summary_strategy": self.config.summary_strategy.value,
                    "summary_format": self.config.summary_format.value,
                },
                importance_scores={
                    score.entity_id: score.score for score in importance_scores
                },
                summary_format=self.config.summary_format,
            )

            # 缓存摘要
            self._cache_summary(cache_key, summary)

            logger.info(f"Generated summary covering {len(entities)} entities")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None

    async def generate_incremental_summary(
        self, new_entities: List[MemoryEntity], previous_summary: EnhancedMemorySummary
    ) -> EnhancedMemorySummary:
        """生成增量摘要

        Args:
            new_entities: 新增实体
            previous_summary: 之前的摘要

        Returns:
            更新后的摘要
        """
        if not self.config.enable_incremental:
            # 如果不支持增量，重新生成完整摘要
            all_entities = await self._get_entities_by_ids(
                previous_summary.original_entities
            )
            all_entities.extend(new_entities)
            return await self.generate_summary(all_entities)

        try:
            # 准备增量摘要提示
            prompt = self._build_incremental_summary_prompt(
                new_entities, previous_summary
            )

            # 使用LLM生成增量摘要
            if self.llm_provider:
                response = await self.llm_provider.generate(prompt)
                new_summary_text = response.content.strip()
            else:
                # 简单合并
                new_summary_text = f"{previous_summary.summary_text}\n\n新增内容:\n"
                for entity in new_entities:
                    new_summary_text += f"- {self._entity_to_text(entity)[:100]}...\n"

            # 更新摘要
            updated_summary = EnhancedMemorySummary(
                id=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                session_id=previous_summary.session_id,
                summary_text=new_summary_text,
                original_entities=previous_summary.original_entities
                + [e.id for e in new_entities],
                created_at=datetime.now(),
                coverage_period={
                    "start": previous_summary.coverage_period.get("start", ""),
                    "end": datetime.now().isoformat(),
                },
                metadata={
                    **previous_summary.metadata,
                    "incremental_update": True,
                    "new_entities_count": len(new_entities),
                    "previous_summary_id": previous_summary.id,
                },
                importance_scores=previous_summary.importance_scores,
                summary_format=previous_summary.summary_format,
                version=previous_summary.version + 1,
            )

            logger.info(
                f"Generated incremental summary with {len(new_entities)} new entities"
            )
            return updated_summary

        except Exception as e:
            logger.error(f"Failed to generate incremental summary: {e}")
            # 回退到完整重新生成
            all_entities = await self._get_entities_by_ids(
                previous_summary.original_entities
            )
            all_entities.extend(new_entities)
            return await self.generate_summary(all_entities)

    async def optimize_summary(
        self, summary: EnhancedMemorySummary, target_length: Optional[int] = None
    ) -> EnhancedMemorySummary:
        """优化摘要（压缩或扩展）

        Args:
            summary: 原始摘要
            target_length: 目标长度（字符数）

        Returns:
            优化后的摘要
        """
        if not self.llm_provider:
            return summary

        target_len = target_length or self.config.target_summary_length

        try:
            prompt = f"""请优化以下摘要，使其长度大约为{target_len}个字符：
            
            原始摘要：
            {summary.summary_text}
            
            请生成优化后的摘要，保持关键信息不变："""

            response = await self.llm_provider.generate(prompt)
            optimized_text = response.content.strip()

            # 创建优化后的摘要
            optimized_summary = EnhancedMemorySummary(
                id=f"{summary.id}_optimized",
                session_id=summary.session_id,
                summary_text=optimized_text,
                original_entities=summary.original_entities,
                created_at=datetime.now(),
                coverage_period=summary.coverage_period,
                metadata={
                    **summary.metadata,
                    "optimized": True,
                    "original_length": len(summary.summary_text),
                    "optimized_length": len(optimized_text),
                },
                importance_scores=summary.importance_scores,
                summary_format=summary.summary_format,
                version=summary.version,
            )

            logger.info(
                f"Optimized summary from {len(summary.summary_text)} to {len(optimized_text)} characters"
            )
            return optimized_summary

        except Exception as e:
            logger.error(f"Failed to optimize summary: {e}")
            return summary

    async def calculate_entity_importance(
        self, entity: MemoryEntity
    ) -> ImportanceScore:
        """计算实体重要性

        Args:
            entity: 记忆实体

        Returns:
            重要性评分
        """
        # 检查缓存
        if entity.id in self.importance_cache:
            return self.importance_cache[entity.id]

        # 计算重要性分数
        factors = self._calculate_importance_factors(entity)
        total_score = sum(factors.values()) / len(factors) if factors else 0.5

        # 如果有LLM，可以获取解释
        explanation = None
        if self.llm_provider:
            try:
                prompt = f"""请分析以下记忆实体的重要性：
                
                实体类型：{entity.type.value}
                内容：{json.dumps(entity.content, ensure_ascii=False)[:200]}
                
                请简要解释这个实体的重要性："""

                response = await self.llm_provider.generate(prompt)
                explanation = response.content.strip()
            except:
                pass

        score = ImportanceScore(
            entity_id=entity.id,
            score=total_score,
            factors=factors,
            explanation=explanation,
        )

        # 缓存结果
        self.importance_cache[entity.id] = score

        return score

    def _calculate_importance_factors(self, entity: MemoryEntity) -> Dict[str, float]:
        """计算重要性因素"""
        factors = {}

        # 1. 类型重要性
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
        factors["type"] = type_importance.get(entity.type, 0.5)

        # 2. 内容丰富度
        content_complexity = self._calculate_content_complexity(entity.content)
        factors["content_complexity"] = content_complexity

        # 3. 时间新鲜度（越新越重要）
        if hasattr(entity, "created_at"):
            age_days = (datetime.now() - entity.created_at).days
            recency = max(0, 1.0 - (age_days / 30.0))  # 30天内线性衰减
            factors["recency"] = recency

        # 4. 元数据重要性
        if entity.metadata and "importance" in entity.metadata:
            try:
                metadata_importance = float(entity.metadata["importance"])
                factors["metadata"] = metadata_importance
            except:
                factors["metadata"] = 0.5

        return factors

    def _calculate_content_complexity(self, content: Any) -> float:
        """计算内容复杂度"""
        if isinstance(content, str):
            # 基于长度和多样性
            length_score = min(len(content) / 500.0, 1.0)  # 500字符为满分
            # 简单估算多样性（唯一词比例）
            words = content.split()
            if words:
                unique_ratio = len(set(words)) / len(words)
            else:
                unique_ratio = 0.5
            return (length_score + unique_ratio) / 2

        elif isinstance(content, dict):
            # 基于键值对数量
            size = len(content)
            complexity = min(size / 10.0, 1.0)  # 10个键值对为满分
            return complexity

        elif isinstance(content, list):
            # 基于列表长度
            length = len(content)
            complexity = min(length / 5.0, 1.0)  # 5个元素为满分
            return complexity

        else:
            return 0.5

    def _select_entities_for_summary(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """选择要摘要的实体"""
        if self.config.summary_strategy == SummaryStrategy.TIME_BASED:
            return self._select_entities_time_based(entities)
        elif self.config.summary_strategy == SummaryStrategy.IMPORTANCE_BASED:
            return self._select_entities_importance_based(entities)
        elif self.config.summary_strategy == SummaryStrategy.RELEVANCE_BASED:
            return self._select_entities_relevance_based(entities)
        elif self.config.summary_strategy == SummaryStrategy.HYBRID:
            return self._select_entities_hybrid(entities)
        else:
            return entities[: self.config.max_entities_per_summary]

    def _select_entities_time_based(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """基于时间选择实体（选择最旧的）"""
        # 排除最近N天的实体
        cutoff_date = datetime.now() - timedelta(days=self.config.preserve_recent_days)
        old_entities = [e for e in entities if e.created_at < cutoff_date]

        # 按时间排序（最旧的在前）
        sorted_entities = sorted(old_entities, key=lambda e: e.created_at)
        return sorted_entities[: self.config.max_entities_per_summary]

    def _select_entities_importance_based(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """基于重要性选择实体"""
        # 计算所有实体的重要性
        scored_entities = []
        for entity in entities:
            # 这里简化处理，实际应该调用calculate_entity_importance
            importance = self._calculate_importance_factors(entity)
            avg_score = (
                sum(importance.values()) / len(importance) if importance else 0.5
            )
            scored_entities.append((entity, avg_score))

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

    def _select_entities_hybrid(
        self, entities: List[MemoryEntity]
    ) -> List[MemoryEntity]:
        """混合策略选择实体"""
        # 结合时间和重要性
        time_based = self._select_entities_time_based(entities)
        importance_based = self._select_entities_importance_based(entities)

        # 合并并去重
        combined = list({e.id: e for e in time_based + importance_based}.values())
        return combined[: self.config.max_entities_per_summary]

    def _generate_cache_key(
        self, entities: List[MemoryEntity], context: Optional[Dict[str, Any]]
    ) -> str:
        """生成缓存键"""
        # 基于实体ID和上下文生成哈希
        entity_ids = sorted([e.id for e in entities])
        context_str = json.dumps(context, sort_keys=True) if context else ""

        data = f"{','.join(entity_ids)}:{context_str}:{self.config.summary_strategy.value}:{self.config.summary_format.value}"
        return hashlib.md5(data.encode()).hexdigest()

    def _get_cached_summary(self, cache_key: str) -> Optional[EnhancedMemorySummary]:
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

    def _cache_summary(self, cache_key: str, summary: EnhancedMemorySummary):
        """缓存摘要"""
        if not self.config.enable_cache:
            return

        self.summary_cache[cache_key] = {
            "summary": summary,
            "timestamp": datetime.now(),
        }

        # 限制缓存大小
        if len(self.summary_cache) > self.config.max_cache_size:
            # 删除最旧的缓存
            oldest_key = min(
                self.summary_cache.keys(),
                key=lambda k: self.summary_cache[k]["timestamp"],
            )
            del self.summary_cache[oldest_key]

        logger.debug(f"Cached summary for key: {cache_key[:8]}...")

    async def _calculate_importance_scores(
        self, entities: List[MemoryEntity]
    ) -> List[ImportanceScore]:
        """计算重要性评分列表"""
        scores = []
        for entity in entities:
            score = await self.calculate_entity_importance(entity)
            scores.append(score)
        return scores

    def _prepare_summary_input(
        self,
        entities: List[MemoryEntity],
        context: Optional[Dict[str, Any]],
        importance_scores: List[ImportanceScore],
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
            # 查找重要性评分
            importance = next(
                (s for s in importance_scores if s.entity_id == entity.id), None
            )
            importance_str = f" (重要性: {importance.score:.2f})" if importance else ""

            entity_text = self._format_entity_for_summary(entity, i + 1, importance_str)
            input_parts.append(entity_text)

        return "\n".join(input_parts)

    def _format_entity_for_summary(
        self, entity: MemoryEntity, index: int, importance_str: str = ""
    ) -> str:
        """格式化实体用于摘要"""
        time_str = entity.created_at.strftime("%Y-%m-%d %H:%M")

        # 提取关键信息
        content_preview = str(entity.content)
        if len(content_preview) > 100:
            content_preview = content_preview[:100] + "..."

        return f"""
## 实体 {index}: {entity.type.value}{importance_str}
- ID: {entity.id}
- 创建时间: {time_str}
- 内容: {content_preview}
"""

    async def _generate_text_summary(self, summary_input: str) -> Optional[str]:
        """生成文本摘要"""
        if not self.llm_provider:
            return self._generate_template_summary(summary_input)

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
            return self._generate_template_summary(summary_input)

    async def _generate_structured_summary(self, summary_input: str) -> str:
        """生成结构化摘要"""
        if not self.llm_provider:
            return "需要LLM提供者来生成结构化摘要"

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

        try:
            response = await self.llm_provider.generate(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Structured summary generation failed: {e}")
            return await self._generate_text_summary(summary_input)

    async def _generate_timeline_summary(self, entities: List[MemoryEntity]) -> str:
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
        return f"时间线摘要:\n{timeline_text}"

    async def _generate_bullet_points_summary(self, summary_input: str) -> str:
        """生成要点列表摘要"""
        if not self.llm_provider:
            # 简单提取
            lines = summary_input.split("\n")
            bullet_points = []
            for line in lines:
                if "实体" in line and ":" in line:
                    bullet_points.append(f"- {line.strip()}")
            return "\n".join(bullet_points)

        prompt = f"""请将以下记忆实体汇总成要点列表格式的摘要：

记忆实体：
{summary_input}

请生成要点列表摘要，每个要点应该简洁明了："""

        try:
            response = await self.llm_provider.generate(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Bullet points summary generation failed: {e}")
            return await self._generate_text_summary(summary_input)

    def _generate_template_summary(self, summary_input: str) -> str:
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

    def _build_incremental_summary_prompt(
        self, new_entities: List[MemoryEntity], previous_summary: EnhancedMemorySummary
    ) -> str:
        """构建增量摘要提示"""
        new_entities_text = "\n".join(
            [f"- {self._entity_to_text(entity)}" for entity in new_entities]
        )

        return f"""基于以下已有摘要和新增记忆，生成更新后的摘要：

已有摘要：
{previous_summary.summary_text}

新增记忆：
{new_entities_text}

请生成更新后的完整摘要，保持连贯性和一致性。"""

    def _entity_to_text(self, entity: MemoryEntity) -> str:
        """将实体转换为文本"""
        content_str = str(entity.content)
        if len(content_str) > 100:
            content_str = content_str[:100] + "..."
        return f"[{entity.type.value}] {content_str}"

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

    async def _get_entities_by_ids(self, entity_ids: List[str]) -> List[MemoryEntity]:
        """根据ID获取实体（需要具体实现）"""
        # 这个方法需要从存储中获取实体
        # 这里返回空列表，实际实现需要集成存储
        return []

    async def clear_cache(self):
        """清空缓存"""
        self.summary_cache.clear()
        self.importance_cache.clear()
        logger.info("Summary and importance caches cleared")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "summary_cache_entries": len(self.summary_cache),
            "importance_cache_entries": len(self.importance_cache),
            "cache_enabled": self.config.enable_cache,
            "cache_ttl_hours": self.config.cache_ttl_hours,
            "max_cache_size": self.config.max_cache_size,
        }

    async def should_summarize(self, entities: List[MemoryEntity]) -> bool:
        """判断是否应该生成摘要"""
        if len(entities) < self.config.min_entities_to_summarize:
            return False

        # 检查时间范围
        if self.config.summary_strategy == SummaryStrategy.TIME_BASED:
            # 检查是否有足够多的旧实体
            cutoff_date = datetime.now() - timedelta(
                days=self.config.preserve_recent_days
            )
            old_entities = [e for e in entities if e.created_at < cutoff_date]
            return len(old_entities) >= self.config.min_entities_to_summarize

        return True
