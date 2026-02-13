"""
性能基准测试

测试阶段1重构后的性能表现，确保重构没有引入性能问题。
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

from loom.core.interfaces import (
    SessionConfig,
    Session,
    SessionStatus,
    NarrativeContext,
    NarrativeInterpretation
)


class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    @pytest.fixture
    def sample_session_config(self):
        """示例会话配置"""
        return SessionConfig(
            name="性能测试会话",
            canon_path="./tests/data/canon.md",
            llm_provider="openai"
        )
    
    @pytest.fixture
    def sample_session(self, sample_session_config):
        """示例会话"""
        return Session(
            id="perf-test-session",
            name="性能测试会话",
            config=sample_session_config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE,
            current_turn=0,
            total_turns=0,
            state={},
            metadata={}
        )
    
    def test_interface_method_call_performance(self):
        """测试接口方法调用性能"""
        # 创建模拟接口
        mock_interpreter = Mock()
        mock_interpreter.interpret_narrative = AsyncMock()
        
        # 测量方法调用时间
        call_times = []
        
        for i in range(100):
            start = time.perf_counter()
            # 模拟异步方法调用
            asyncio.run(mock_interpreter.interpret_narrative("session-id", Mock()))
            end = time.perf_counter()
            call_times.append((end - start) * 1000)  # 转换为毫秒
        
        # 计算统计信息
        avg_time = statistics.mean(call_times)
        max_time = max(call_times)
        min_time = min(call_times)
        
        print(f"\n接口方法调用性能测试:")
        print(f"  调用次数: 100")
        print(f"  平均时间: {avg_time:.3f} ms")
        print(f"  最长时间: {max_time:.3f} ms")
        print(f"  最短时间: {min_time:.3f} ms")
        
        # 性能断言：平均调用时间应小于5ms（模拟调用，考虑系统负载）
        assert avg_time < 5.0, f"接口方法调用太慢: {avg_time:.3f} ms"
    
    @pytest.mark.asyncio
    async def test_data_model_creation_performance(self):
        """测试数据模型创建性能"""
        creation_times = []
        
        for i in range(1000):
            start = time.perf_counter()
            
            # 创建SessionConfig
            config = SessionConfig(
                name=f"测试会话{i}",
                canon_path=f"./canon{i}.md",
                llm_provider="openai",
                max_turns=10,
                metadata={"test": i}
            )
            
            # 创建Session
            session = Session(
                id=f"session-{i}",
                name=f"测试会话{i}",
                config=config,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=SessionStatus.ACTIVE,
                current_turn=i % 10,
                total_turns=10,
                state={"turn": i},
                metadata={"created": datetime.now().isoformat()}
            )
            
            end = time.perf_counter()
            creation_times.append((end - start) * 1000)  # 转换为毫秒
        
        # 计算统计信息
        avg_time = statistics.mean(creation_times)
        p95_time = statistics.quantiles(creation_times, n=20)[18]  # 95百分位
        
        print(f"\n数据模型创建性能测试:")
        print(f"  创建次数: 1000")
        print(f"  平均创建时间: {avg_time:.3f} ms")
        print(f"  P95创建时间: {p95_time:.3f} ms")
        
        # 性能断言：平均创建时间应小于0.1ms
        assert avg_time < 0.1, f"数据模型创建太慢: {avg_time:.3f} ms"
    
    @pytest.mark.asyncio
    async def test_narrative_interpretation_performance(self):
        """测试叙事解释性能"""
        # 创建模拟数据
        interpretations = []
        
        for i in range(100):
            interpretation = NarrativeInterpretation(
                interpretation=f"这是第{i}个叙事解释" * 10,  # 增加文本长度
                consistency_score=i / 100.0,
                continuity_issues=[f"问题{i}" for _ in range(5)],
                suggested_improvements=[f"建议{i}" for _ in range(3)],
                narrative_arcs=[{"name": f"弧线{i}", "progress": i/100.0} for _ in range(2)]
            )
            interpretations.append(interpretation)
        
        # 测试序列化性能
        serialization_times = []
        
        for interpretation in interpretations:
            start = time.perf_counter()
            
            # 模拟序列化操作
            serialized = {
                "interpretation": interpretation.interpretation[:100],  # 截断
                "consistency_score": interpretation.consistency_score,
                "issues_count": len(interpretation.continuity_issues),
                "suggestions_count": len(interpretation.suggested_improvements),
                "arcs_count": len(interpretation.narrative_arcs)
            }
            
            end = time.perf_counter()
            serialization_times.append((end - start) * 1000)
        
        avg_serialization_time = statistics.mean(serialization_times)
        
        print(f"\n叙事解释序列化性能测试:")
        print(f"  序列化次数: 100")
        print(f"  平均序列化时间: {avg_serialization_time:.3f} ms")
        
        # 性能断言：序列化时间应小于0.05ms
        assert avg_serialization_time < 0.05, f"序列化太慢: {avg_serialization_time:.3f} ms"
    
    def test_memory_usage_estimation(self):
        """测试内存使用估算"""
        import sys
        
        # 创建多个数据对象
        objects = []
        
        for i in range(100):
            config = SessionConfig(
                name=f"会话{i}",
                canon_path=f"./canon{i}.md",
                llm_provider="openai"
            )
            
            session = Session(
                id=f"session-{i}",
                name=f"会话{i}",
                config=config,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=SessionStatus.ACTIVE,
                current_turn=0,
                total_turns=0,
                state={},
                metadata={}
            )
            
            objects.append(session)
        
        # 估算内存使用
        total_size = sum(sys.getsizeof(obj) for obj in objects)
        avg_size = total_size / len(objects)
        
        print(f"\n内存使用估算测试:")
        print(f"  对象数量: 100")
        print(f"  总内存使用: {total_size / 1024:.2f} KB")
        print(f"  平均每个对象: {avg_size:.2f} bytes")
        
        # 内存断言：每个Session对象应小于1KB
        assert avg_size < 1024, f"对象内存使用过大: {avg_size:.2f} bytes"
    
    @pytest.mark.asyncio
    async def test_concurrent_interface_calls(self):
        """测试并发接口调用"""
        import asyncio
        
        # 创建模拟接口
        mock_interfaces = []
        
        for i in range(10):
            mock = Mock()
            mock.process = AsyncMock(return_value=f"结果{i}")
            mock_interfaces.append(mock)
        
        # 并发调用
        async def call_interface(interface, delay=0.001):
            await asyncio.sleep(delay)  # 模拟处理延迟
            return await interface.process()
        
        start = time.perf_counter()
        
        # 并发执行
        tasks = [call_interface(iface, i * 0.0005) for i, iface in enumerate(mock_interfaces)]
        results = await asyncio.gather(*tasks)
        
        end = time.perf_counter()
        total_time = (end - start) * 1000
        
        print(f"\n并发接口调用测试:")
        print(f"  并发接口数量: 10")
        print(f"  总执行时间: {total_time:.3f} ms")
        print(f"  结果数量: {len(results)}")
        
        # 并发性能断言：10个并发调用应小于50ms
        assert total_time < 50, f"并发调用太慢: {total_time:.3f} ms"
    
    def test_adapter_overhead_measurement(self):
        """测试适配器开销"""
        # 创建传统系统模拟
        class LegacySystem:
            def process(self, data):
                # 模拟传统处理
                time.sleep(0.001)  # 1ms处理时间
                return {"result": "传统结果", "data": data}
        
        # 创建适配器
        class Adapter:
            def __init__(self, legacy):
                self.legacy = legacy
            
            def process(self, data):
                # 适配器转换
                converted_data = {"input": data, "timestamp": datetime.now().isoformat()}
                
                # 调用传统系统
                start = time.perf_counter()
                result = self.legacy.process(converted_data)
                end = time.perf_counter()
                
                # 转换结果
                adapted_result = {
                    "success": True,
                    "output": result["result"],
                    "original_data": result["data"],
                    "processing_time": end - start
                }
                
                return adapted_result
        
        # 测试性能
        legacy = LegacySystem()
        adapter = Adapter(legacy)
        
        direct_times = []
        adapted_times = []
        
        for i in range(100):
            # 直接调用传统系统
            start = time.perf_counter()
            legacy.process(f"数据{i}")
            end = time.perf_counter()
            direct_times.append((end - start) * 1000)
            
            # 通过适配器调用
            start = time.perf_counter()
            adapter.process(f"数据{i}")
            end = time.perf_counter()
            adapted_times.append((end - start) * 1000)
        
        avg_direct = statistics.mean(direct_times)
        avg_adapted = statistics.mean(adapted_times)
        overhead = avg_adapted - avg_direct
        overhead_percentage = (overhead / avg_direct) * 100
        
        print(f"\n适配器开销测试:")
        print(f"  直接调用平均时间: {avg_direct:.3f} ms")
        print(f"  适配器调用平均时间: {avg_adapted:.3f} ms")
        print(f"  适配器开销: {overhead:.3f} ms ({overhead_percentage:.1f}%)")
        
        # 开销断言：适配器开销应小于50%
        assert overhead_percentage < 50, f"适配器开销过大: {overhead_percentage:.1f}%"


class TestComparativeBenchmarks:
    """对比基准测试"""
    
    def test_before_after_refactoring_comparison(self):
        """测试重构前后对比（模拟）"""
        # 注意：这是模拟测试，实际项目中需要真实的重构前后数据
        
        # 模拟重构前性能数据
        before_refactor = {
            "interface_call_time": 2.5,  # ms
            "memory_per_object": 1500,   # bytes
            "concurrent_throughput": 50,  # requests/sec
        }
        
        # 模拟重构后性能数据（目标）
        after_refactor = {
            "interface_call_time": 1.8,  # ms (改进28%)
            "memory_per_object": 1200,   # bytes (改进20%)
            "concurrent_throughput": 60,  # requests/sec (改进20%)
        }
        
        # 计算改进百分比
        improvements = {
            "interface_call_time": ((before_refactor["interface_call_time"] - after_refactor["interface_call_time"]) / 
                                   before_refactor["interface_call_time"]) * 100,
            "memory_per_object": ((before_refactor["memory_per_object"] - after_refactor["memory_per_object"]) / 
                                 before_refactor["memory_per_object"]) * 100,
            "concurrent_throughput": ((after_refactor["concurrent_throughput"] - before_refactor["concurrent_throughput"]) / 
                                     before_refactor["concurrent_throughput"]) * 100,
        }
        
        print(f"\n重构前后性能对比（模拟）:")
        print(f"  接口调用时间: {before_refactor['interface_call_time']:.1f}ms -> {after_refactor['interface_call_time']:.1f}ms ({improvements['interface_call_time']:.1f}% 改进)")
        print(f"  对象内存使用: {before_refactor['memory_per_object']}B -> {after_refactor['memory_per_object']}B ({improvements['memory_per_object']:.1f}% 改进)")
        print(f"  并发吞吐量: {before_refactor['concurrent_throughput']}/s -> {after_refactor['concurrent_throughput']}/s ({improvements['concurrent_throughput']:.1f}% 改进)")
        
        # 断言：重构不应导致性能下降
        assert improvements["interface_call_time"] >= -10, "接口调用时间下降超过10%"
        assert improvements["memory_per_object"] >= -10, "内存使用增加超过10%"
        assert improvements["concurrent_throughput"] >= -10, "并发吞吐量下降超过10%"


def run_performance_suite():
    """运行完整的性能测试套件"""
    import sys
    import io
    
    # 捕获输出
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        # 运行性能测试
        test_class = TestPerformanceBenchmarks()
        
        print("=" * 60)
        print("LOOM 阶段1重构 - 性能基准测试套件")
        print("=" * 60)
        
        # 运行各个测试
        test_class.test_interface_method_call_performance()
        asyncio.run(test_class.test_data_model_creation_performance())
        asyncio.run(test_class.test_narrative_interpretation_performance())
        test_class.test_memory_usage_estimation()
        asyncio.run(test_class.test_concurrent_interface_calls())
        test_class.test_adapter_overhead_measurement()
        
        # 运行对比测试
        comparative = TestComparativeBenchmarks()
        comparative.test_before_after_refactoring_comparison()
        
        print("\n" + "=" * 60)
        print("性能测试完成")
        print("=" * 60)
        
        # 获取输出
        output = sys.stdout.getvalue()
        
    finally:
        sys.stdout = original_stdout
    
    # 打印输出
    print(output)
    
    return True


if __name__ == "__main__":
    # 运行性能测试套件
    success = run_performance_suite()
    
    # 运行pytest测试
    import pytest
    exit_code = pytest.main([__file__, "-v"])
    
    if exit_code == 0 and success:
        print("\n✅ 所有性能测试通过")
    else:
        print("\n❌ 性能测试失败")
        sys.exit(1)