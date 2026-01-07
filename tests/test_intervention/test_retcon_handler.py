"""
RetconHandler单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.loom.intervention.retcon_handler import (
    RetconHandler,
    RetconOperation,
    RetconType,
    RetconResult,
    ConsistencyCheckResult
)


class TestRetconHandler:
    """RetconHandler测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.handler = RetconHandler()
    
    def test_parse_retcon_timeline_adjustment(self):
        """测试解析时间线调整"""
        text = "[RETCON: TIMELINE: 事件A发生在事件B之前]"
        operations = self.handler.parse_retcon(text)
        
        assert len(operations) == 1
        op = operations[0]
        assert op.retcon_type == RetconType.TIMELINE_ADJUSTMENT
        assert op.target == "TIMELINE"
        assert op.content == "事件A发生在事件B之前"
        assert op.raw_text == text
    
    def test_parse_retcon_event_modification(self):
        """测试解析事件修改"""
        text = "[RETCON: EVENT: 战斗结果: 平局改为胜利]"
        operations = self.handler.parse_retcon(text)
        
        assert len(operations) == 1
        op = operations[0]
        assert op.retcon_type == RetconType.EVENT_MODIFICATION
        assert op.target == "战斗结果"
        assert op.content == "平局改为胜利"
    
    def test_parse_retcon_contradiction_resolution(self):
        """测试解析矛盾解决"""
        text = "[RETCON: CONTRADICTION: 角色年龄不一致: 统一为25岁]"
        operations = self.handler.parse_retcon(text)
        
        assert len(operations) == 1
        op = operations[0]
        assert op.retcon_type == RetconType.CONTRADICTION_RESOLUTION
        assert op.target == "角色年龄不一致"
        assert op.content == "统一为25岁"
    
    def test_parse_retcon_fact_correction(self):
        """测试解析事实修正"""
        text = "[RETCON: FACT: 城堡位置: 北改为南]"
        operations = self.handler.parse_retcon(text)
        
        assert len(operations) == 1
        op = operations[0]
        assert op.retcon_type == RetconType.FACT_CORRECTION
        assert op.target == "城堡位置"
        assert op.content == "北改为南"
    
    def test_parse_retcon_multiple_operations(self):
        """测试解析多个操作"""
        text = "[RETCON: TIMELINE: 调整1][RETCON: EVENT: 调整2]"
        operations = self.handler.parse_retcon(text)
        
        assert len(operations) == 2
        types = [op.retcon_type for op in operations]
        assert RetconType.TIMELINE_ADJUSTMENT in types
        assert RetconType.EVENT_MODIFICATION in types
    
    def test_parse_retcon_invalid_format(self):
        """测试解析无效格式"""
        text = "[RETCON: INVALID: 目标: 内容]"
        operations = self.handler.parse_retcon(text)
        
        assert len(operations) == 0
    
    @pytest.mark.asyncio
    async def test_validate_retcon_permission_allowed(self):
        """测试验证Retcon权限（允许）"""
        op = RetconOperation(
            retcon_type=RetconType.EVENT_MODIFICATION,
            target="事件",
            content="修改",
            raw_text="[RETCON: EVENT: 事件: 修改]"
        )
        
        rules_text = "允许修改事件。"
        allowed = await self.handler.validate_retcon_permission(op, rules_text)
        
        assert allowed == True
    
    @pytest.mark.asyncio
    async def test_validate_retcon_permission_denied(self):
        """测试验证Retcon权限（禁止）"""
        op = RetconOperation(
            retcon_type=RetconType.TIMELINE_ADJUSTMENT,
            target="核心时间线",
            content="修改",
            raw_text="[RETCON: TIMELINE: 核心时间线: 修改]"
        )
        
        rules_text = "禁止修改核心时间线。"
        allowed = await self.handler.validate_retcon_permission(op, rules_text)
        
        assert allowed == False
    
    @pytest.mark.asyncio
    async def test_assess_retcon_impact_low(self):
        """测试评估Retcon影响（低）"""
        op = RetconOperation(
            retcon_type=RetconType.FACT_CORRECTION,
            target="次要细节",
            content="修正",
            raw_text="[RETCON: FACT: 次要细节: 修正]"
        )
        
        impact = await self.handler.assess_retcon_impact(op)
        
        assert impact["severity"] == "low"
        assert impact["scope"] == "local"
        assert impact["propagation_risk"] < 30
    
    @pytest.mark.asyncio
    async def test_assess_retcon_impact_high(self):
        """测试评估Retcon影响（高）"""
        op = RetconOperation(
            retcon_type=RetconType.TIMELINE_ADJUSTMENT,
            target="关键事件",
            content="重大修改",
            raw_text="[RETCON: TIMELINE: 关键事件: 重大修改]"
        )
        
        impact = await self.handler.assess_retcon_impact(op)
        
        assert impact["severity"] == "high"
        assert impact["scope"] == "global"
        assert impact["propagation_risk"] > 70
    
    @pytest.mark.asyncio
    async def test_execute_timeline_adjustment(self):
        """测试执行时间线调整"""
        op = RetconOperation(
            retcon_type=RetconType.TIMELINE_ADJUSTMENT,
            target="事件顺序",
            content="A在B之前",
            raw_text="[RETCON: TIMELINE: 事件顺序: A在B之前]"
        )
        
        result = await self.handler._execute_timeline_adjustment(op)
        
        assert result.success == True
        assert result.retcon_type == RetconType.TIMELINE_ADJUSTMENT
        assert "时间线已调整" in result.message
        assert len(result.changes_made) > 0
    
    @pytest.mark.asyncio
    async def test_execute_event_modification(self):
        """测试执行事件修改"""
        op = RetconOperation(
            retcon_type=RetconType.EVENT_MODIFICATION,
            target="战斗结果",
            content="胜利改为失败",
            raw_text="[RETCON: EVENT: 战斗结果: 胜利改为失败]"
        )
        
        result = await self.handler._execute_event_modification(op)
        
        assert result.success == True
        assert result.retcon_type == RetconType.EVENT_MODIFICATION
        assert "事件已修改" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_contradiction_resolution(self):
        """测试执行矛盾解决"""
        op = RetconOperation(
            retcon_type=RetconType.CONTRADICTION_RESOLUTION,
            target="年龄矛盾",
            content="统一为25岁",
            raw_text="[RETCON: CONTRADICTION: 年龄矛盾: 统一为25岁]"
        )
        
        result = await self.handler._execute_contradiction_resolution(op)
        
        assert result.success == True
        assert result.retcon_type == RetconType.CONTRADICTION_RESOLUTION
        assert "矛盾已解决" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_fact_correction(self):
        """测试执行事实修正"""
        op = RetconOperation(
            retcon_type=RetconType.FACT_CORRECTION,
            target="位置错误",
            content="北改为南",
            raw_text="[RETCON: FACT: 位置错误: 北改为南]"
        )
        
        result = await self.handler._execute_fact_correction(op)
        
        assert result.success == True
        assert result.retcon_type == RetconType.FACT_CORRECTION
        assert "事实已修正" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_retcon_operation(self):
        """测试执行Retcon操作"""
        op = RetconOperation(
            retcon_type=RetconType.EVENT_MODIFICATION,
            target="测试事件",
            content="修改",
            raw_text="[RETCON: EVENT: 测试事件: 修改]"
        )
        
        result = await self.handler.execute_retcon_operation(op)
        
        assert result.success == True
        assert result.retcon_type == RetconType.EVENT_MODIFICATION
        assert "执行完成" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_retcon_operations_list(self):
        """测试执行Retcon操作列表"""
        operations = [
            RetconOperation(
                retcon_type=RetconType.FACT_CORRECTION,
                target="细节1",
                content="修正1",
                raw_text="[RETCON: FACT: 细节1: 修正1]"
            ),
            RetconOperation(
                retcon_type=RetconType.EVENT_MODIFICATION,
                target="事件1",
                content="修改1",
                raw_text="[RETCON: EVENT: 事件1: 修改1]"
            )
        ]
        
        results = await self.handler.execute_retcon_operations(operations)
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_check_retcon_consistency_no_conflicts(self):
        """测试检查Retcon一致性（无冲突）"""
        op = RetconOperation(
            retcon_type=RetconType.FACT_CORRECTION,
            target="次要事实",
            content="修正",
            raw_text="[RETCON: FACT: 次要事实: 修正]"
        )
        
        mock_consistency_checker = Mock()
        mock_consistency_checker.check_consistency = AsyncMock(
            return_value=ConsistencyCheckResult(
                is_consistent=True,
                conflicts=[],
                severity="low"
            )
        )
        
        result = await self.handler.check_retcon_consistency(op, mock_consistency_checker)
        
        assert result["is_consistent"] == True
        assert len(result["conflicts"]) == 0
        assert result["severity"] == "low"
    
    @pytest.mark.asyncio
    async def test_check_retcon_consistency_with_conflicts(self):
        """测试检查Retcon一致性（有冲突）"""
        op = RetconOperation(
            retcon_type=RetconType.TIMELINE_ADJUSTMENT,
            target="关键时间线",
            content="重大修改",
            raw_text="[RETCON: TIMELINE: 关键时间线: 重大修改]"
        )
        
        mock_consistency_checker = Mock()
        mock_consistency_checker.check_consistency = AsyncMock(
            return_value=ConsistencyCheckResult(
                is_consistent=False,
                conflicts=["时间线冲突", "因果关系冲突"],
                severity="high"
            )
        )
        
        result = await self.handler.check_retcon_consistency(op, mock_consistency_checker)
        
        assert result["is_consistent"] == False
        assert len(result["conflicts"]) > 0
        assert result["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_resolve_retcon_conflicts_auto(self):
        """测试解决Retcon冲突（自动）"""
        conflicts = ["时间线冲突", "事实矛盾"]
        
        mock_consistency_checker = Mock()
        mock_consistency_checker.resolve_conflict = AsyncMock(
            return_value={"resolved": True, "method": "auto"}
        )
        
        result = await self.handler.resolve_retcon_conflicts(
            conflicts, mock_consistency_checker, "test_session"
        )
        
        assert result["success"] == True
        assert result["conflicts_resolved"] == 2
        assert result["resolution_method"] == "auto"
    
    @pytest.mark.asyncio
    async def test_execute_retcon_with_consistency_check(self):
        """测试带一致性检查的Retcon执行"""
        op = RetconOperation(
            retcon_type=RetconType.EVENT_MODIFICATION,
            target="事件",
            content="修改",
            raw_text="[RETCON: EVENT: 事件: 修改]"
        )
        
        mock_consistency_checker = Mock()
        mock_consistency_checker.check_consistency = AsyncMock(
            return_value=ConsistencyCheckResult(
                is_consistent=True,
                conflicts=[],
                severity="low"
            )
        )
        
        result = await self.handler.execute_retcon_with_consistency_check(
            op, mock_consistency_checker, "test_session"
        )
        
        assert result["success"] == True
        assert result["consistency_check_passed"] == True
        assert "retcon_executed" in result
    
    @pytest.mark.asyncio
    async def test_integrate_with_world_memory(self):
        """测试与WorldMemory集成"""
        mock_world_memory = Mock()
        mock_world_memory.update_timeline = AsyncMock(return_value=True)
        mock_world_memory.update_fact = AsyncMock(return_value=True)
        
        operations = [
            RetconOperation(
                retcon_type=RetconType.TIMELINE_ADJUSTMENT,
                target="时间线",
                content="调整",
                raw_text="[RETCON: TIMELINE: 时间线: 调整]"
            )
        ]
        
        result = await self.handler.integrate_with_world_memory(mock_world_memory, operations)
        
        assert result["success"] == True
        assert result["timeline_updated"] == True
        mock_world_memory.update_timeline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_maintain_canon_consistency(self):
        """测试维护Canon一致性"""
        op = RetconOperation(
            retcon_type=RetconType.FACT_CORRECTION,
            target="事实",
            content="修正",
            raw_text="[RETCON: FACT: 事实: 修正]"
        )
        
        result = await self.handler.maintain_canon_consistency(op)
        
        assert result["canon_preserved"] == True
        assert result["consistency_maintained"] == True
        assert "canon_check" in result
    
    @pytest.mark.asyncio
    async def test_rollback_retcon(self):
        """测试回滚Retcon"""
        op = RetconOperation(
            retcon_type=RetconType.EVENT_MODIFICATION,
            target="事件",
            content="修改",
            raw_text="[RETCON: EVENT: 事件: 修改]"
        )
        
        retcon_result = RetconResult(
            success=True,
            retcon_type=op.retcon_type,
            message="测试",
            changes_made={"event_id": "test"}
        )
        
        rollback_result = await self.handler.rollback_retcon(op, retcon_result)
        
        assert rollback_result["success"] == True
        assert rollback_result["retcon_rolled_back"] == True
        assert "回滚" in rollback_result["message"]
    
    def test_generate_retcon_report(self):
        """测试生成Retcon报告"""
        operations = [
            RetconOperation(
                retcon_type=RetconType.FACT_CORRECTION,
                target="事实1",
                content="修正1",
                raw_text="[RETCON: FACT: 事实1: 修正1]"
            )
        ]
        
        results = [
            RetconResult(
                success=True,
                retcon_type=RetconType.FACT_CORRECTION,
                message="成功",
                changes_made={}
            )
        ]
        
        report = self.handler.generate_retcon_report(operations, results)
        
        assert "Retcon报告" in report
        assert "成功: 1" in report
        assert "失败: 0" in report
        assert "FACT_CORRECTION" in report
    
    @pytest.mark.asyncio
    async def test_handle_retcon_workflow(self):
        """测试完整Retcon工作流"""
        retcon_text = "[RETCON: FACT: 位置: 修正][RETCON: EVENT: 战斗: 修改]"
        
        result = await self.handler.handle_retcon_workflow(retcon_text, "test_session")
        
        assert result["success"] == True
        assert "operations_parsed" in result
        assert "execution_results" in result
        assert "consistency_checks" in result
        assert "report" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])