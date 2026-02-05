"""
解释层 (LLM推理)

职责：每回合重新解释规则，推导符合规则的叙事结果。
包含基础组件和增强组件。
"""

from .rule_interpreter import RuleInterpreter
from .llm_provider import LLMProvider, LLMResponse
from .reasoning_pipeline import ReasoningPipeline, ReasoningContext, ReasoningResult
from .consistency_checker import ConsistencyChecker, ConsistencyIssue, ConsistencyReport

# 增强组件
from .enhanced_reasoning_pipeline import (
    EnhancedReasoningPipeline,
    EnhancedReasoningResult,
)
from .enhanced_context_builder import (
    EnhancedContextBuilder,
    ContextOptimizationStrategy,
    ContextQualityMetrics,
)
from .enhanced_consistency_checker import (
    EnhancedConsistencyChecker,
    DeepConsistencyIssue,
    DeepConsistencyReport,
    ConsistencyCategory,
)
from .reasoning_tracker import (
    ReasoningTracker,
    ReasoningStepType,
    DecisionImportance,
    ReasoningTrace,
)

# LLM Provider增强组件
from .enhanced_provider_manager import (
    EnhancedProviderManager,
    ProviderHealthMonitor,
    ProviderLoadBalancer,
    FallbackStrategy,
    ProviderPriority,
    ProviderHealth,
    ProviderMetrics,
)
from .cost_optimizer import (
    CostOptimizer,
    BudgetAlertLevel,
    CostRecord,
    BudgetLimit,
    ProviderPricing,
)
from .local_model_provider import (
    LocalModelProvider,
    LocalModelManager,
    LocalModelInfo,
    LocalModelType,
    ModelPerformanceMetrics,
)

# 性能监控组件
from .performance_monitor import (
    PerformanceMonitor,
    Metric,
    MetricType,
    Alert,
    AlertSeverity,
    PerformanceReport,
    MetricsStore,
    AlertManager,
    SystemMetricsCollector,
    PrometheusExporter,
    get_performance_monitor,
)
from .benchmark_framework import (
    BenchmarkFramework,
    BenchmarkRunner,
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkType,
    BenchmarkStatus,
    ComparisonResult,
    BenchmarkResultsStore,
    get_benchmark_framework,
)
from .resource_analyzer import (
    ResourceAnalyzer,
    ResourceUsage,
    ResourceType,
    ResourceIssue,
    ResourceIssueType,
    ResourceAnalysisReport,
    MemoryAnalyzer,
    CPUAnalyzer,
    DiskAnalyzer,
    ThreadAnalyzer,
    get_resource_analyzer,
)

__all__ = [
    # 基础组件
    "RuleInterpreter",
    "LLMProvider",
    "LLMResponse",
    "ReasoningPipeline",
    "ReasoningContext",
    "ReasoningResult",
    "ConsistencyChecker",
    "ConsistencyIssue",
    "ConsistencyReport",
    # 增强推理管道
    "EnhancedReasoningPipeline",
    "EnhancedReasoningResult",
    # 增强上下文构建器
    "EnhancedContextBuilder",
    "ContextOptimizationStrategy",
    "ContextQualityMetrics",
    # 增强一致性检查器
    "EnhancedConsistencyChecker",
    "DeepConsistencyIssue",
    "DeepConsistencyReport",
    "ConsistencyCategory",
    # 推理跟踪器
    "ReasoningTracker",
    "ReasoningStepType",
    "DecisionImportance",
    "ReasoningTrace",
    # LLM Provider增强组件
    "EnhancedProviderManager",
    "ProviderHealthMonitor",
    "ProviderLoadBalancer",
    "FallbackStrategy",
    "ProviderPriority",
    "ProviderHealth",
    "ProviderMetrics",
    "CostOptimizer",
    "BudgetAlertLevel",
    "CostRecord",
    "BudgetLimit",
    "ProviderPricing",
    "LocalModelProvider",
    "LocalModelManager",
    "LocalModelInfo",
    "LocalModelType",
    "ModelPerformanceMetrics",
    # 性能监控组件
    "PerformanceMonitor",
    "Metric",
    "MetricType",
    "Alert",
    "AlertSeverity",
    "PerformanceReport",
    "MetricsStore",
    "AlertManager",
    "SystemMetricsCollector",
    "PrometheusExporter",
    "get_performance_monitor",
    # 基准测试框架
    "BenchmarkFramework",
    "BenchmarkRunner",
    "BenchmarkConfig",
    "BenchmarkResult",
    "BenchmarkType",
    "BenchmarkStatus",
    "ComparisonResult",
    "BenchmarkResultsStore",
    "get_benchmark_framework",
    # 资源分析器
    "ResourceAnalyzer",
    "ResourceUsage",
    "ResourceType",
    "ResourceIssue",
    "ResourceIssueType",
    "ResourceAnalysisReport",
    "MemoryAnalyzer",
    "CPUAnalyzer",
    "DiskAnalyzer",
    "ThreadAnalyzer",
    "get_resource_analyzer",
]
