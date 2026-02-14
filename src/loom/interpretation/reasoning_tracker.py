"""
推理跟踪器

实现推理跟踪和可解释性工具，记录推理步骤、决策原因、置信度评分。
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ReasoningStepType(Enum):
    """推理步骤类型"""

    RULE_INTERPRETATION = "rule_interpretation"
    MEMORY_RETRIEVAL = "memory_retrieval"
    CONTEXT_BUILDING = "context_building"
    LLM_GENERATION = "llm_generation"
    CONSISTENCY_CHECK = "consistency_check"
    MEMORY_UPDATE = "memory_update"
    DECISION_MAKING = "decision_making"
    CONSTRAINT_APPLICATION = "constraint_application"
    ERROR_HANDLING = "error_handling"
    OTHER = "other"


class DecisionImportance(Enum):
    """决策重要性"""

    CRITICAL = "critical"  # 关键决策，影响整体叙事
    HIGH = "high"  # 重要决策，影响主要情节
    MEDIUM = "medium"  # 中等决策，影响局部
    LOW = "low"  # 次要决策，影响细节


@dataclass
class ReasoningStep:
    """推理步骤"""

    id: str
    name: str
    step_type: ReasoningStepType
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    substeps: List["ReasoningStep"] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    confidence: Optional[float] = None  # 0-1


@dataclass
class DecisionPoint:
    """决策点"""

    id: str
    step_id: str
    description: str
    alternatives: List[str]
    chosen_alternative: str
    reasoning: str
    importance: DecisionImportance
    confidence: float  # 0-1
    constraints_applied: List[str]
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceAssessment:
    """置信度评估"""

    overall: float  # 0-1
    breakdown: Dict[str, float]  # 各维度置信度
    factors: List[Dict[str, Any]]  # 影响因素
    uncertainty_sources: List[str]  # 不确定性来源


@dataclass
class ReasoningTrace:
    """推理轨迹"""

    trace_id: str
    session_id: str
    turn_number: int
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    steps: List[ReasoningStep] = field(default_factory=list)
    decisions: List[DecisionPoint] = field(default_factory=list)
    confidence_assessment: Optional[ConfidenceAssessment] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasoningTracker:
    """推理跟踪器"""

    def __init__(
        self, session_id: Optional[str] = None, turn_number: Optional[int] = None
    ):
        """
        初始化推理跟踪器

        Args:
            session_id: 会话ID
            turn_number: 回合数
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.turn_number = turn_number or 0
        self.current_trace: Optional[ReasoningTrace] = None
        self.traces: List[ReasoningTrace] = []

        # 性能指标
        self.metrics = {
            "total_steps": 0,
            "total_decisions": 0,
            "total_errors": 0,
            "avg_step_duration": 0.0,
            "avg_confidence": 0.0,
        }

        logger.info(
            f"ReasoningTracker initialized for session {self.session_id}, turn {self.turn_number}"
        )

    def start_trace(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始新的推理轨迹"""
        trace_id = str(uuid.uuid4())
        self.current_trace = ReasoningTrace(
            trace_id=trace_id,
            session_id=self.session_id,
            turn_number=self.turn_number,
            start_time=time.time(),
            metadata=metadata or {},
        )

        logger.debug(f"Started reasoning trace {trace_id}")
        return trace_id

    def end_trace(self, trace_id: Optional[str] = None) -> Optional[ReasoningTrace]:
        """结束推理轨迹"""
        trace = self.current_trace if trace_id is None else self._find_trace(trace_id)
        if not trace:
            logger.warning(f"Trace {trace_id} not found")
            return None

        trace.end_time = time.time()
        trace.total_duration = trace.end_time - trace.start_time

        # 计算置信度评估
        if trace.steps:
            trace.confidence_assessment = self._calculate_confidence_assessment(trace)

        # 添加到历史
        self.traces.append(trace)

        # 更新指标
        self._update_metrics(trace)

        # 重置当前轨迹
        if trace_id is None or trace_id == getattr(
            self.current_trace, "trace_id", None
        ):
            self.current_trace = None

        logger.debug(
            f"Ended reasoning trace {trace.trace_id}, duration: {trace.total_duration:.2f}s"
        )
        return trace

    def start_step(
        self,
        name: str,
        step_type: ReasoningStepType,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """开始推理步骤"""
        if not self.current_trace:
            self.start_trace()

        step_id = str(uuid.uuid4())
        step = ReasoningStep(
            id=step_id,
            name=name,
            step_type=step_type,
            start_time=time.time(),
            input_data=input_data or {},
            metadata=metadata or {},
        )

        self.current_trace.steps.append(step)

        logger.debug(f"Started step {name} ({step_type.value})")
        return step_id

    def end_step(
        self,
        step_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """结束推理步骤"""
        step = self._find_step(step_id)
        if not step:
            logger.warning(f"Step {step_id} not found")
            return False

        step.end_time = time.time()
        step.duration = step.end_time - step.start_time
        step.output_data = output_data or {}
        step.confidence = confidence

        if errors:
            step.errors.extend(errors)

        logger.debug(
            f"Ended step {step.name}, duration: {step.duration:.2f}s, confidence: {confidence}"
        )
        return True

    def add_substep(
        self,
        parent_step_id: str,
        name: str,
        details: Dict[str, Any],
        step_type: ReasoningStepType = ReasoningStepType.OTHER,
    ) -> str:
        """添加子步骤"""
        parent_step = self._find_step(parent_step_id)
        if not parent_step:
            logger.warning(f"Parent step {parent_step_id} not found")
            return ""

        substep_id = str(uuid.uuid4())
        substep = ReasoningStep(
            id=substep_id,
            name=name,
            step_type=step_type,
            start_time=time.time(),
            end_time=time.time(),
            duration=0.0,
            metadata=details,
        )

        parent_step.substeps.append(substep)

        logger.debug(f"Added substep {name} to {parent_step.name}")
        return substep_id

    def record_decision(
        self,
        step_id: str,
        description: str,
        alternatives: List[str],
        chosen_alternative: str,
        reasoning: str,
        importance: DecisionImportance,
        confidence: float,
        constraints_applied: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """记录决策点"""
        if not self.current_trace:
            logger.warning("No active trace to record decision")
            return ""

        decision_id = str(uuid.uuid4())
        decision = DecisionPoint(
            id=decision_id,
            step_id=step_id,
            description=description,
            alternatives=alternatives,
            chosen_alternative=chosen_alternative,
            reasoning=reasoning,
            importance=importance,
            confidence=confidence,
            constraints_applied=constraints_applied or [],
            timestamp=time.time(),
            metadata=metadata or {},
        )

        self.current_trace.decisions.append(decision)

        logger.debug(
            f"Recorded decision: {description}, importance: {importance.value}, confidence: {confidence:.2f}"
        )
        return decision_id

    def record_error(
        self,
        step_id: str,
        error_type: str,
        error_message: str,
        severity: str = "medium",
        recovery_action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """记录错误"""
        step = self._find_step(step_id)
        if not step:
            logger.warning(f"Step {step_id} not found for error recording")
            return False

        error_record = {
            "type": error_type,
            "message": error_message,
            "severity": severity,
            "timestamp": time.time(),
            "recovery_action": recovery_action,
            "metadata": metadata or {},
        }

        step.errors.append(error_record)

        logger.warning(
            f"Recorded error in step {step.name}: {error_type} - {error_message}"
        )
        return True

    def generate_explainability_report(
        self, trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成可解释性报告"""
        trace = self.current_trace if trace_id is None else self._find_trace(trace_id)
        if not trace:
            return {"error": "Trace not found"}

        report = {
            "trace_id": trace.trace_id,
            "session_id": trace.session_id,
            "turn_number": trace.turn_number,
            "timeline": {
                "start_time": datetime.fromtimestamp(trace.start_time).isoformat(),
                "end_time": (
                    datetime.fromtimestamp(trace.end_time).isoformat()
                    if trace.end_time
                    else None
                ),
                "total_duration": trace.total_duration,
            },
            "step_breakdown": self._generate_step_breakdown(trace),
            "decision_analysis": self._analyze_decisions(trace),
            "confidence_analysis": self._analyze_confidence(trace),
            "error_analysis": self._analyze_errors(trace),
            "performance_metrics": self._calculate_performance_metrics(trace),
            "key_insights": self._extract_key_insights(trace),
            "metadata": trace.metadata,
        }

        return report

    def generate_visualization_data(
        self, trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成可视化数据"""
        trace = self.current_trace if trace_id is None else self._find_trace(trace_id)
        if not trace:
            return {"error": "Trace not found"}

        # 步骤时间线数据
        timeline_data = []
        for step in trace.steps:
            timeline_data.append(
                {
                    "id": step.id,
                    "name": step.name,
                    "type": step.step_type.value,
                    "start": step.start_time - trace.start_time,
                    "duration": step.duration or 0,
                    "confidence": step.confidence or 0.5,
                    "has_errors": len(step.errors) > 0,
                }
            )

        # 决策树数据
        decision_tree = []
        for decision in trace.decisions:
            decision_tree.append(
                {
                    "id": decision.id,
                    "step_id": decision.step_id,
                    "description": decision.description,
                    "importance": decision.importance.value,
                    "confidence": decision.confidence,
                    "alternatives_count": len(decision.alternatives),
                    "constraints_count": len(decision.constraints_applied),
                }
            )

        # 置信度雷达图数据
        confidence_radar = []
        if trace.confidence_assessment:
            for dimension, score in trace.confidence_assessment.breakdown.items():
                confidence_radar.append({"dimension": dimension, "score": score})

        return {
            "timeline": timeline_data,
            "decision_tree": decision_tree,
            "confidence_radar": confidence_radar,
            "error_summary": self._generate_error_summary(trace),
            "performance_summary": self._generate_performance_summary(trace),
        }

    def export_trace(self, trace_id: str, format: str = "json") -> Dict[str, Any]:
        """导出推理轨迹"""
        trace = self._find_trace(trace_id)
        if not trace:
            return {"error": "Trace not found"}

        if format == "json":
            return self._export_to_json(trace)
        elif format == "structured":
            return self._export_structured(trace)
        else:
            return {"error": f"Unsupported format: {format}"}

    def get_trace_statistics(self) -> Dict[str, Any]:
        """获取轨迹统计"""
        total_traces = len(self.traces)
        if total_traces == 0:
            return {"total_traces": 0}

        # 计算各种统计
        total_steps = sum(len(trace.steps) for trace in self.traces)
        total_decisions = sum(len(trace.decisions) for trace in self.traces)
        total_errors = sum(
            sum(len(step.errors) for step in trace.steps) for trace in self.traces
        )

        avg_duration = (
            sum(trace.total_duration or 0 for trace in self.traces) / total_traces
        )
        avg_steps_per_trace = total_steps / total_traces
        avg_decisions_per_trace = total_decisions / total_traces

        # 成功率（无错误的轨迹比例）
        successful_traces = sum(
            1
            for trace in self.traces
            if all(len(step.errors) == 0 for step in trace.steps)
        )
        success_rate = successful_traces / total_traces * 100

        return {
            "total_traces": total_traces,
            "total_steps": total_steps,
            "total_decisions": total_decisions,
            "total_errors": total_errors,
            "average_duration": avg_duration,
            "average_steps_per_trace": avg_steps_per_trace,
            "average_decisions_per_trace": avg_decisions_per_trace,
            "success_rate": success_rate,
            "session_id": self.session_id,
            "turn_number": self.turn_number,
        }

    # ========== 辅助方法 ==========

    def _find_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """查找轨迹"""
        if self.current_trace and self.current_trace.trace_id == trace_id:
            return self.current_trace

        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace

        return None

    def _find_step(self, step_id: str) -> Optional[ReasoningStep]:
        """查找步骤"""
        if not self.current_trace:
            return None

        # 在当前轨迹中查找
        for step in self.current_trace.steps:
            if step.id == step_id:
                return step

            # 在子步骤中查找
            for substep in step.substeps:
                if substep.id == step_id:
                    return substep

        return None

    def _calculate_confidence_assessment(
        self, trace: ReasoningTrace
    ) -> ConfidenceAssessment:
        """计算置信度评估"""
        if not trace.steps:
            return ConfidenceAssessment(
                overall=0.5, breakdown={}, factors=[], uncertainty_sources=[]
            )

        # 收集步骤置信度
        step_confidences = [
            step.confidence for step in trace.steps if step.confidence is not None
        ]

        if step_confidences:
            avg_confidence = sum(step_confidences) / len(step_confidences)
        else:
            avg_confidence = 0.5

        # 计算各维度置信度
        breakdown = {}

        # 规则解释维度
        rule_steps = [
            step
            for step in trace.steps
            if step.step_type == ReasoningStepType.RULE_INTERPRETATION
        ]
        if rule_steps:
            rule_confidences = [
                step.confidence for step in rule_steps if step.confidence is not None
            ]
            breakdown["rule_interpretation"] = (
                sum(rule_confidences) / len(rule_confidences)
                if rule_confidences
                else 0.5
            )

        # 记忆检索维度
        memory_steps = [
            step
            for step in trace.steps
            if step.step_type == ReasoningStepType.MEMORY_RETRIEVAL
        ]
        if memory_steps:
            memory_confidences = [
                step.confidence for step in memory_steps if step.confidence is not None
            ]
            breakdown["memory_retrieval"] = (
                sum(memory_confidences) / len(memory_confidences)
                if memory_confidences
                else 0.5
            )

        # LLM生成维度
        llm_steps = [
            step
            for step in trace.steps
            if step.step_type == ReasoningStepType.LLM_GENERATION
        ]
        if llm_steps:
            llm_confidences = [
                step.confidence for step in llm_steps if step.confidence is not None
            ]
            breakdown["llm_generation"] = (
                sum(llm_confidences) / len(llm_confidences) if llm_confidences else 0.5
            )

        # 一致性检查维度
        consistency_steps = [
            step
            for step in trace.steps
            if step.step_type == ReasoningStepType.CONSISTENCY_CHECK
        ]
        if consistency_steps:
            consistency_confidences = [
                step.confidence
                for step in consistency_steps
                if step.confidence is not None
            ]
            breakdown["consistency_check"] = (
                sum(consistency_confidences) / len(consistency_confidences)
                if consistency_confidences
                else 0.5
            )

        # 决策维度
        if trace.decisions:
            decision_confidences = [decision.confidence for decision in trace.decisions]
            breakdown["decision_making"] = sum(decision_confidences) / len(
                decision_confidences
            )

        # 影响因素
        factors = []

        # 步骤完成度
        completed_steps = sum(1 for step in trace.steps if step.end_time is not None)
        completion_rate = completed_steps / len(trace.steps) if trace.steps else 0.0
        factors.append(
            {
                "factor": "step_completion",
                "value": completion_rate,
                "impact": "positive" if completion_rate > 0.8 else "negative",
            }
        )

        # 错误数量
        total_errors = sum(len(step.errors) for step in trace.steps)
        factors.append(
            {
                "factor": "error_count",
                "value": total_errors,
                "impact": "negative" if total_errors > 0 else "neutral",
            }
        )

        # 决策质量
        if trace.decisions:
            avg_decision_confidence = sum(d.confidence for d in trace.decisions) / len(
                trace.decisions
            )
            factors.append(
                {
                    "factor": "decision_confidence",
                    "value": avg_decision_confidence,
                    "impact": (
                        "positive" if avg_decision_confidence > 0.7 else "negative"
                    ),
                }
            )

        # 不确定性来源
        uncertainty_sources = []

        if total_errors > 0:
            uncertainty_sources.append("步骤执行错误")

        low_confidence_steps = [
            step
            for step in trace.steps
            if step.confidence is not None and step.confidence < 0.5
        ]
        if low_confidence_steps:
            uncertainty_sources.append("低置信度步骤")

        if trace.decisions:
            low_confidence_decisions = [
                d for d in trace.decisions if d.confidence < 0.6
            ]
            if low_confidence_decisions:
                uncertainty_sources.append("低置信度决策")

        return ConfidenceAssessment(
            overall=avg_confidence,
            breakdown=breakdown,
            factors=factors,
            uncertainty_sources=uncertainty_sources,
        )

    def _update_metrics(self, trace: ReasoningTrace) -> None:
        """更新指标"""
        self.metrics["total_steps"] += len(trace.steps)
        self.metrics["total_decisions"] += len(trace.decisions)
        self.metrics["total_errors"] += sum(len(step.errors) for step in trace.steps)

        # 更新平均持续时间
        if trace.total_duration:
            total_traces = len(self.traces)
            old_avg = self.metrics["avg_step_duration"]
            new_avg = (
                (old_avg * (total_traces - 1) + trace.total_duration) / total_traces
                if total_traces > 0
                else trace.total_duration
            )
            self.metrics["avg_step_duration"] = new_avg

        # 更新平均置信度
        if trace.confidence_assessment:
            total_traces = len(self.traces)
            old_avg = self.metrics["avg_confidence"]
            new_avg = (
                (old_avg * (total_traces - 1) + trace.confidence_assessment.overall)
                / total_traces
                if total_traces > 0
                else trace.confidence_assessment.overall
            )
            self.metrics["avg_confidence"] = new_avg

    def _generate_step_breakdown(self, trace: ReasoningTrace) -> List[Dict[str, Any]]:
        """生成步骤分解"""
        breakdown = []

        for step in trace.steps:
            step_info = {
                "id": step.id,
                "name": step.name,
                "type": step.step_type.value,
                "start_time": step.start_time - trace.start_time,
                "duration": step.duration or 0,
                "confidence": step.confidence,
                "error_count": len(step.errors),
                "substep_count": len(step.substeps),
                "input_summary": self._summarize_data(step.input_data),
                "output_summary": self._summarize_data(step.output_data),
            }

            # 添加子步骤信息
            if step.substeps:
                step_info["substeps"] = [
                    {
                        "name": substep.name,
                        "type": substep.step_type.value,
                        "details": self._summarize_data(substep.metadata),
                    }
                    for substep in step.substeps
                ]

            # 添加错误信息
            if step.errors:
                step_info["errors"] = [
                    {
                        "type": error["type"],
                        "message": error["message"][:100],
                        "severity": error["severity"],
                    }
                    for error in step.errors[:3]  # 限制数量
                ]

            breakdown.append(step_info)

        return breakdown

    def _analyze_decisions(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """分析决策"""
        if not trace.decisions:
            return {"total_decisions": 0, "analysis": "无决策记录"}

        # 按重要性统计
        importance_counts = {}
        for importance in DecisionImportance:
            importance_counts[importance.value] = sum(
                1 for d in trace.decisions if d.importance == importance
            )

        # 置信度分布
        confidence_ranges = {
            "high": sum(1 for d in trace.decisions if d.confidence >= 0.8),
            "medium": sum(1 for d in trace.decisions if 0.5 <= d.confidence < 0.8),
            "low": sum(1 for d in trace.decisions if d.confidence < 0.5),
        }

        # 约束应用统计
        constraint_usage = {}
        for decision in trace.decisions:
            for constraint in decision.constraints_applied:
                constraint_usage[constraint] = constraint_usage.get(constraint, 0) + 1

        # 关键决策识别
        critical_decisions = [
            d for d in trace.decisions if d.importance == DecisionImportance.CRITICAL
        ]
        key_decisions = []

        for decision in critical_decisions[:5]:  # 限制数量
            key_decisions.append(
                {
                    "description": decision.description,
                    "reasoning": decision.reasoning[:200],
                    "confidence": decision.confidence,
                    "constraints_applied": decision.constraints_applied[:3],
                }
            )

        return {
            "total_decisions": len(trace.decisions),
            "importance_distribution": importance_counts,
            "confidence_distribution": confidence_ranges,
            "constraint_usage": dict(
                sorted(constraint_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "key_decisions": key_decisions,
            "avg_confidence": sum(d.confidence for d in trace.decisions)
            / len(trace.decisions),
            "decision_making_pattern": self._identify_decision_pattern(trace.decisions),
        }

    def _analyze_confidence(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """分析置信度"""
        if not trace.confidence_assessment:
            return {"analysis": "无置信度评估数据"}

        assessment = trace.confidence_assessment

        # 维度分析
        dimension_analysis = []
        for dimension, score in assessment.breakdown.items():
            level = "高" if score >= 0.8 else "中" if score >= 0.5 else "低"
            dimension_analysis.append(
                {"dimension": dimension, "score": score, "level": level}
            )

        # 影响因素分析
        factor_analysis = []
        for factor in assessment.factors:
            factor_analysis.append(
                {
                    "factor": factor["factor"],
                    "value": factor["value"],
                    "impact": factor["impact"],
                }
            )

        # 总体评估
        overall_level = (
            "高"
            if assessment.overall >= 0.8
            else "中"
            if assessment.overall >= 0.5
            else "低"
        )

        return {
            "overall_score": assessment.overall,
            "overall_level": overall_level,
            "dimension_analysis": dimension_analysis,
            "factor_analysis": factor_analysis,
            "uncertainty_sources": assessment.uncertainty_sources,
            "recommendations": self._generate_confidence_recommendations(assessment),
        }

    def _analyze_errors(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """分析错误"""
        all_errors = []
        for step in trace.steps:
            all_errors.extend(step.errors)

        if not all_errors:
            return {"total_errors": 0, "analysis": "无错误记录"}

        # 错误类型统计
        error_types = {}
        error_severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for error in all_errors:
            error_type = error["type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

            severity = error.get("severity", "medium")
            error_severities[severity] = error_severities.get(severity, 0) + 1

        # 错误步骤分布
        error_steps = []
        for step in trace.steps:
            if step.errors:
                error_steps.append(
                    {
                        "step_name": step.name,
                        "step_type": step.step_type.value,
                        "error_count": len(step.errors),
                        "error_types": list(
                            set(error["type"] for error in step.errors)
                        ),
                    }
                )

        # 恢复行动统计
        recovery_actions = {}
        for error in all_errors:
            action = error.get("recovery_action")
            if action:
                recovery_actions[action] = recovery_actions.get(action, 0) + 1

        return {
            "total_errors": len(all_errors),
            "error_type_distribution": error_types,
            "severity_distribution": error_severities,
            "error_steps": error_steps[:5],  # 限制数量
            "recovery_actions": recovery_actions,
            "error_rate": len(all_errors) / len(trace.steps) if trace.steps else 0,
            "recommendations": self._generate_error_recommendations(all_errors),
        }

    def _calculate_performance_metrics(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """计算性能指标"""
        if not trace.steps:
            return {"analysis": "无步骤数据"}

        # 步骤持续时间
        step_durations = [step.duration or 0 for step in trace.steps]

        # 按类型分组持续时间
        type_durations = {}
        for step in trace.steps:
            step_type = step.step_type.value
            duration = step.duration or 0
            if step_type not in type_durations:
                type_durations[step_type] = []
            type_durations[step_type].append(duration)

        # 计算类型平均持续时间
        avg_type_durations = {}
        for step_type, durations in type_durations.items():
            avg_type_durations[step_type] = (
                sum(durations) / len(durations) if durations else 0
            )

        # 瓶颈识别（最耗时的步骤）
        sorted_steps = sorted(trace.steps, key=lambda s: s.duration or 0, reverse=True)
        bottlenecks = []
        for step in sorted_steps[:3]:  # 前3个最耗时的步骤
            if step.duration and step.duration > 1.0:  # 超过1秒
                bottlenecks.append(
                    {
                        "step_name": step.name,
                        "step_type": step.step_type.value,
                        "duration": step.duration,
                        "percentage": (
                            (step.duration / trace.total_duration * 100)
                            if trace.total_duration
                            else 0
                        ),
                    }
                )

        return {
            "total_duration": trace.total_duration,
            "step_count": len(trace.steps),
            "avg_step_duration": sum(step_durations) / len(step_durations),
            "min_step_duration": min(step_durations) if step_durations else 0,
            "max_step_duration": max(step_durations) if step_durations else 0,
            "avg_type_durations": avg_type_durations,
            "bottlenecks": bottlenecks,
            "efficiency_score": self._calculate_efficiency_score(trace),
        }

    def _extract_key_insights(self, trace: ReasoningTrace) -> List[Dict[str, Any]]:
        """提取关键洞察"""
        insights = []

        # 性能洞察
        if trace.total_duration and trace.total_duration > 10.0:
            insights.append(
                {
                    "type": "performance",
                    "title": "推理时间较长",
                    "description": f"总推理时间{trace.total_duration:.1f}秒，可能影响用户体验",
                    "severity": "medium",
                    "suggestion": "考虑优化耗时步骤或添加异步处理",
                }
            )

        # 错误洞察
        total_errors = sum(len(step.errors) for step in trace.steps)
        if total_errors > 3:
            insights.append(
                {
                    "type": "reliability",
                    "title": "错误数量较多",
                    "description": f"共{total_errors}个错误，可能影响推理质量",
                    "severity": "high",
                    "suggestion": "检查错误处理逻辑，增加错误恢复机制",
                }
            )

        # 置信度洞察
        if trace.confidence_assessment and trace.confidence_assessment.overall < 0.6:
            insights.append(
                {
                    "type": "confidence",
                    "title": "总体置信度较低",
                    "description": f"总体置信度{trace.confidence_assessment.overall:.2f}，推理结果可能不可靠",
                    "severity": "high",
                    "suggestion": "检查低置信度步骤，增加验证机制",
                }
            )

        # 决策洞察
        if trace.decisions:
            low_confidence_decisions = [
                d for d in trace.decisions if d.confidence < 0.5
            ]
            if low_confidence_decisions:
                insights.append(
                    {
                        "type": "decision",
                        "title": "存在低置信度决策",
                        "description": f"{len(low_confidence_decisions)}个决策置信度低于0.5",
                        "severity": "medium",
                        "suggestion": "为低置信度决策提供备选方案或人工审核",
                    }
                )

        # 约束应用洞察
        constraint_usage = {}
        for decision in trace.decisions:
            for constraint in decision.constraints_applied:
                constraint_usage[constraint] = constraint_usage.get(constraint, 0) + 1

        if constraint_usage:
            most_used = (
                max(constraint_usage.items(), key=lambda x: x[1])
                if constraint_usage
                else None
            )
            if most_used and most_used[1] > 3:
                insights.append(
                    {
                        "type": "constraint",
                        "title": "约束应用集中",
                        "description": f"约束'{most_used[0]}'被应用{most_used[1]}次",
                        "severity": "low",
                        "suggestion": "检查是否过度依赖特定约束，考虑约束多样性",
                    }
                )

        return insights[:5]  # 限制数量

    def _summarize_data(self, data: Optional[Dict[str, Any]]) -> str:
        """总结数据"""
        if not data:
            return "无数据"

        if isinstance(data, dict):
            # 提取关键信息
            keys = list(data.keys())
            if len(keys) <= 3:
                return f"包含{len(keys)}个字段: {', '.join(keys[:3])}"
            else:
                return f"包含{len(keys)}个字段: {', '.join(keys[:3])}等"
        elif isinstance(data, (list, tuple)):
            return f"列表，{len(data)}个元素"
        else:
            return str(data)[:50] + "..." if len(str(data)) > 50 else str(data)

    def _identify_decision_pattern(self, decisions: List[DecisionPoint]) -> str:
        """识别决策模式"""
        if not decisions:
            return "无决策模式"

        # 分析决策特征
        avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
        avg_alternatives = sum(len(d.alternatives) for d in decisions) / len(decisions)

        if avg_confidence >= 0.8 and avg_alternatives <= 2:
            return "高置信度确定性决策"
        elif avg_confidence >= 0.6 and avg_alternatives <= 3:
            return "中等置信度平衡决策"
        elif avg_confidence < 0.5 and avg_alternatives > 3:
            return "低置信度探索性决策"
        else:
            return "混合决策模式"

    def _generate_confidence_recommendations(
        self, assessment: ConfidenceAssessment
    ) -> List[str]:
        """生成置信度建议"""
        recommendations = []

        if assessment.overall < 0.6:
            recommendations.append("总体置信度较低，建议增加验证步骤")

        # 检查各维度
        for dimension, score in assessment.breakdown.items():
            if score < 0.5:
                recommendations.append(f"{dimension}维度置信度低，建议加强相关处理")

        # 检查不确定性来源
        if assessment.uncertainty_sources:
            if len(assessment.uncertainty_sources) > 2:
                recommendations.append(
                    f"存在多个不确定性来源: {', '.join(assessment.uncertainty_sources[:3])}"
                )

        return recommendations[:3]  # 限制数量

    def _generate_error_recommendations(
        self, errors: List[Dict[str, Any]]
    ) -> List[str]:
        """生成错误建议"""
        if not errors:
            return ["无错误，继续保持"]

        recommendations = []

        # 按类型统计
        error_types = {}
        for error in errors:
            error_type = error["type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # 针对常见错误类型提供建议
        for error_type, count in error_types.items():
            if count >= 2:
                if "timeout" in error_type.lower():
                    recommendations.append(f"超时错误频繁({count}次)，建议增加超时时间或优化处理逻辑")
                elif "memory" in error_type.lower():
                    recommendations.append(f"内存相关错误({count}次)，建议检查内存使用或增加限制")
                elif "network" in error_type.lower():
                    recommendations.append(f"网络错误({count}次)，建议增加重试机制或检查连接")
                else:
                    recommendations.append(f"{error_type}错误频繁({count}次)，建议检查相关逻辑")

        # 严重错误建议
        critical_errors = [
            e for e in errors if e.get("severity") in ["high", "critical"]
        ]
        if critical_errors:
            recommendations.append(f"存在{len(critical_errors)}个严重错误，需要优先处理")

        return recommendations[:3]  # 限制数量

    def _calculate_efficiency_score(self, trace: ReasoningTrace) -> float:
        """计算效率分数"""
        if not trace.total_duration or trace.total_duration == 0:
            return 0.5

        # 基于时间和步骤数量的简单效率计算
        base_score = 0.5

        # 时间效率：越短越好
        if trace.total_duration < 5.0:
            base_score += 0.3
        elif trace.total_duration < 10.0:
            base_score += 0.1
        elif trace.total_duration > 30.0:
            base_score -= 0.2

        # 步骤效率：步骤越少越好（相对）
        if trace.steps:
            avg_step_duration = trace.total_duration / len(trace.steps)
            if avg_step_duration < 1.0:
                base_score += 0.2

        # 错误惩罚
        total_errors = sum(len(step.errors) for step in trace.steps)
        if total_errors > 0:
            base_score -= min(total_errors * 0.1, 0.3)

        return max(0.0, min(base_score, 1.0))

    def _generate_error_summary(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """生成错误摘要"""
        all_errors = []
        for step in trace.steps:
            all_errors.extend(step.errors)

        if not all_errors:
            return {"total": 0, "summary": "无错误"}

        # 按严重程度分组
        by_severity = {}
        for error in all_errors:
            severity = error.get("severity", "medium")
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(error)

        # 按类型分组
        by_type = {}
        for error in all_errors:
            error_type = error["type"]
            by_type[error_type] = by_type.get(error_type, 0) + 1

        return {
            "total": len(all_errors),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_type": by_type,
            "recovery_rate": (
                sum(1 for e in all_errors if e.get("recovery_action")) / len(all_errors)
                if all_errors
                else 0
            ),
        }

    def _generate_performance_summary(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """生成性能摘要"""
        if not trace.steps:
            return {"analysis": "无步骤数据"}

        step_durations = [step.duration or 0 for step in trace.steps]

        return {
            "total_duration": trace.total_duration,
            "step_count": len(trace.steps),
            "avg_step_duration": sum(step_durations) / len(step_durations),
            "bottleneck_steps": [
                {
                    "name": step.name,
                    "duration": step.duration,
                    "percentage": (
                        (step.duration / trace.total_duration * 100)
                        if trace.total_duration and step.duration
                        else 0
                    ),
                }
                for step in sorted(
                    trace.steps, key=lambda s: s.duration or 0, reverse=True
                )[:2]
                if step.duration and step.duration > 1.0
            ],
        }

    def _export_to_json(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """导出为JSON格式"""
        # 简化导出，只包含关键信息
        return {
            "trace_id": trace.trace_id,
            "session_id": trace.session_id,
            "turn_number": trace.turn_number,
            "timeline": {
                "start": trace.start_time,
                "end": trace.end_time,
                "duration": trace.total_duration,
            },
            "steps_summary": [
                {
                    "name": step.name,
                    "type": step.step_type.value,
                    "duration": step.duration,
                    "confidence": step.confidence,
                    "error_count": len(step.errors),
                }
                for step in trace.steps
            ],
            "decisions_summary": [
                {
                    "description": decision.description,
                    "importance": decision.importance.value,
                    "confidence": decision.confidence,
                    "constraints_count": len(decision.constraints_applied),
                }
                for decision in trace.decisions
            ],
            "confidence_assessment": {
                "overall": (
                    trace.confidence_assessment.overall
                    if trace.confidence_assessment
                    else None
                ),
                "breakdown": (
                    trace.confidence_assessment.breakdown
                    if trace.confidence_assessment
                    else {}
                ),
            },
            "metadata": trace.metadata,
        }

    def _export_structured(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """导出结构化格式"""
        # 更详细的导出
        return {
            "header": {
                "trace_id": trace.trace_id,
                "session_id": trace.session_id,
                "turn_number": trace.turn_number,
                "timestamp": {
                    "start": datetime.fromtimestamp(trace.start_time).isoformat(),
                    "end": (
                        datetime.fromtimestamp(trace.end_time).isoformat()
                        if trace.end_time
                        else None
                    ),
                    "duration_seconds": trace.total_duration,
                },
            },
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "type": step.step_type.value,
                    "timing": {
                        "start": step.start_time - trace.start_time,
                        "duration": step.duration,
                    },
                    "data": {
                        "input_keys": (
                            list(step.input_data.keys()) if step.input_data else []
                        ),
                        "output_keys": (
                            list(step.output_data.keys()) if step.output_data else []
                        ),
                    },
                    "confidence": step.confidence,
                    "errors": step.errors,
                    "substeps": [
                        {
                            "name": substep.name,
                            "type": substep.step_type.value,
                            "metadata_keys": (
                                list(substep.metadata.keys())
                                if substep.metadata
                                else []
                            ),
                        }
                        for substep in step.substeps
                    ],
                }
                for step in trace.steps
            ],
            "decisions": [
                {
                    "id": decision.id,
                    "step_id": decision.step_id,
                    "description": decision.description,
                    "alternatives": decision.alternatives,
                    "chosen": decision.chosen_alternative,
                    "reasoning": decision.reasoning,
                    "importance": decision.importance.value,
                    "confidence": decision.confidence,
                    "constraints": decision.constraints_applied,
                    "timestamp": decision.timestamp - trace.start_time,
                }
                for decision in trace.decisions
            ],
            "analysis": {
                "confidence": (
                    {
                        "overall": trace.confidence_assessment.overall,
                        "breakdown": trace.confidence_assessment.breakdown,
                        "factors": trace.confidence_assessment.factors,
                        "uncertainty_sources": trace.confidence_assessment.uncertainty_sources,
                    }
                    if trace.confidence_assessment
                    else None
                ),
                "performance": self._calculate_performance_metrics(trace),
                "errors": self._analyze_errors(trace),
            },
        }

    # ========== 批量处理和高级功能 ==========

    def compare_traces(self, trace_ids: List[str]) -> Dict[str, Any]:
        """比较多个轨迹"""
        traces = [self._find_trace(tid) for tid in trace_ids]
        traces = [t for t in traces if t is not None]

        if len(traces) < 2:
            return {"error": "需要至少2个轨迹进行比较"}

        comparison = {
            "trace_count": len(traces),
            "trace_ids": trace_ids,
            "duration_comparison": self._compare_durations(traces),
            "confidence_comparison": self._compare_confidences(traces),
            "error_comparison": self._compare_errors(traces),
            "decision_comparison": self._compare_decisions(traces),
            "performance_trends": self._analyze_performance_trends(traces),
            "recommendations": self._generate_comparison_recommendations(traces),
        }

        return comparison

    def _compare_durations(self, traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """比较持续时间"""
        durations = [trace.total_duration or 0 for trace in traces]

        return {
            "values": durations,
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "variation": max(durations) - min(durations),
            "trend": (
                "increasing"
                if len(durations) > 1 and durations[-1] > durations[0]
                else "decreasing"
                if durations[-1] < durations[0]
                else "stable"
            ),
        }

    def _compare_confidences(self, traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """比较置信度"""
        confidences = []
        for trace in traces:
            if trace.confidence_assessment:
                confidences.append(trace.confidence_assessment.overall)
            else:
                confidences.append(0.5)  # 默认值

        return {
            "values": confidences,
            "average": sum(confidences) / len(confidences),
            "min": min(confidences),
            "max": max(confidences),
            "trend": (
                "improving"
                if len(confidences) > 1 and confidences[-1] > confidences[0]
                else "declining"
                if confidences[-1] < confidences[0]
                else "stable"
            ),
        }

    def _compare_errors(self, traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """比较错误"""
        error_counts = []
        for trace in traces:
            total_errors = sum(len(step.errors) for step in trace.steps)
            error_counts.append(total_errors)

        return {
            "values": error_counts,
            "total": sum(error_counts),
            "average": sum(error_counts) / len(error_counts),
            "trend": (
                "improving"
                if len(error_counts) > 1 and error_counts[-1] < error_counts[0]
                else "worsening"
                if error_counts[-1] > error_counts[0]
                else "stable"
            ),
        }

    def _compare_decisions(self, traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """比较决策"""
        decision_counts = [len(trace.decisions) for trace in traces]
        decision_confidences = []

        for trace in traces:
            if trace.decisions:
                avg_confidence = sum(d.confidence for d in trace.decisions) / len(
                    trace.decisions
                )
                decision_confidences.append(avg_confidence)
            else:
                decision_confidences.append(0.0)

        return {
            "counts": decision_counts,
            "confidences": decision_confidences,
            "avg_decision_count": sum(decision_counts) / len(decision_counts),
            "avg_decision_confidence": (
                sum(decision_confidences) / len(decision_confidences)
                if decision_confidences
                else 0.0
            ),
        }

    def _analyze_performance_trends(
        self, traces: List[ReasoningTrace]
    ) -> List[Dict[str, Any]]:
        """分析性能趋势"""
        trends = []

        # 按时间排序
        sorted_traces = sorted(traces, key=lambda t: t.start_time)

        if len(sorted_traces) < 2:
            return trends

        # 分析各种趋势
        metrics_to_analyze = [
            ("duration", lambda t: t.total_duration or 0),
            ("step_count", lambda t: len(t.steps)),
            ("error_count", lambda t: sum(len(step.errors) for step in t.steps)),
            ("decision_count", lambda t: len(t.decisions)),
        ]

        for metric_name, extractor in metrics_to_analyze:
            values = [extractor(trace) for trace in sorted_traces]

            # 计算趋势
            if len(values) >= 2:
                first_value = values[0]
                last_value = values[-1]
                change = last_value - first_value
                change_percentage = (
                    (change / first_value * 100) if first_value != 0 else 0
                )

                if abs(change_percentage) > 10:  # 变化超过10%才认为是显著趋势
                    trend_direction = "上升" if change > 0 else "下降"
                    trends.append(
                        {
                            "metric": metric_name,
                            "trend": trend_direction,
                            "change_percentage": abs(change_percentage),
                            "first_value": first_value,
                            "last_value": last_value,
                            "recommendation": f"{metric_name}{trend_direction}{abs(change_percentage):.1f}%，建议关注",
                        }
                    )

        return trends

    def _generate_comparison_recommendations(
        self, traces: List[ReasoningTrace]
    ) -> List[str]:
        """生成比较建议"""
        recommendations = []

        # 分析持续时间
        durations = [trace.total_duration or 0 for trace in traces]
        avg_duration = sum(durations) / len(durations)

        if avg_duration > 10.0:
            recommendations.append(f"平均推理时间{avg_duration:.1f}秒较长，建议优化性能")

        # 分析错误率
        error_counts = [
            sum(len(step.errors) for step in trace.steps) for trace in traces
        ]
        total_errors = sum(error_counts)

        if total_errors > len(traces) * 2:  # 平均每个轨迹超过2个错误
            recommendations.append(
                f"错误较多(平均{total_errors/len(traces):.1f}个/轨迹)，建议加强错误处理"
            )

        # 分析置信度趋势
        confidences = []
        for trace in traces:
            if trace.confidence_assessment:
                confidences.append(trace.confidence_assessment.overall)

        if confidences and len(confidences) >= 2:
            first_conf = confidences[0]
            last_conf = confidences[-1]
            if last_conf < first_conf - 0.1:  # 置信度下降超过0.1
                recommendations.append("置信度呈下降趋势，建议检查推理质量")

        return recommendations[:3]  # 限制数量
