"""
RetconHandler单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from loom.intervention.retcon_handler import (
    RetconHandler,
    RetconOperation,
    RetconResult
)


class TestRetconHandler:
    """RetconHandler测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.handler = RetconHandler()
    
    def test_parse_retcon_command_modify_fact(self):
        """测试解析修改事实命令"""
        text = "modify_fact: [entity_123]: 城堡在北边 -> 城堡在南边 (地图错误)"
        operation = self.handler.parse_retcon_command(text)
        
        assert operation is not None
        assert operation.type == "modify_fact"
        assert operation.target_id == "entity_123"
        assert operation.changes.get("old") == "城堡在北边"
        assert operation.changes.get("new") == "城堡在南边"
        assert operation.justification == "地图错误"
    
    def test_parse_retcon_command_add_memory(self):
        """测试解析添加记忆命令"""
        text = "add_memory: 新记忆: 国王曾经访问过东方 (补充背景)"
        operation = self.handler.parse_retcon_command(text)
        
        assert operation is not None
        assert operation.type == "add_memory"
        assert operation.changes.get("content") == "国王曾经访问过东方"
        assert operation.justification == "补充背景"
    
    def test_parse_retcon_command_remove_memory(self):
        """测试解析移除记忆命令"""
        text = "remove_memory: [memory_456]: 记忆有误 (信息不准确)"
        operation = self.handler.parse_retcon_command(text)
        
        assert operation is not None
        assert operation.type == "remove_memory"
        assert operation.target_id == "memory_456"
        assert operation.changes.get("reason") == "记忆有误"
        assert operation.justification == "信息不准确"
    
    def test_parse_retcon_command_alter_timeline(self):
        """测试解析修改时间线命令"""
        text = "alter_timeline: 战斗时间: 早晨:夜晚 (时间线调整)"
        operation = self.handler.parse_retcon_command(text)
        
        assert operation is not None
        assert operation.type == "alter_timeline"
        assert operation.changes.get("event") == "早晨"
        assert operation.changes.get("new_time") == "夜晚"
        assert operation.justification == "时间线调整"
    
    def test_parse_retcon_command_invalid_format(self):
        """测试解析无效格式"""
        text = "invalid: 目标: 内容"
        operation = self.handler.parse_retcon_command(text)
        
        assert operation is None
    
    @pytest.mark.asyncio
    async def test_execute_retcon_modify_fact(self):
        """测试执行修改事实Retcon"""
        operation = RetconOperation(
            type="modify_fact",
            target_id="test_entity",
            changes={"old": "旧事实", "new": "新事实"},
            justification="测试修改",
            timestamp=datetime.now()
        )
        
        session_context = {"session_id": "test_session"}
        result = await self.handler.execute_retcon(operation, session_context)
        
        # 由于没有WorldMemory，应该失败
        assert result.success == False
        assert "缺少目标ID或世界记忆未初始化" in result.narrative_impact
    
    @pytest.mark.asyncio
    async def test_execute_retcon_add_memory(self):
        """测试执行添加记忆Retcon"""
        operation = RetconOperation(
            type="add_memory",
            target_id=None,
            changes={"content": "测试记忆内容"},
            justification="测试添加",
            timestamp=datetime.now()
        )
        
        session_context = {"session_id": "test_session"}
        result = await self.handler.execute_retcon(operation, session_context)
        
        # 由于没有WorldMemory，应该失败
        assert result.success == False
        assert "世界记忆未初始化" in result.narrative_impact
    
    @pytest.mark.asyncio
    async def test_validate_retcon_allowed(self):
        """测试验证Retcon（允许）"""
        operation = RetconOperation(
            type="modify_fact",
            target_id="test",
            changes={"new_value": "测试"},
            justification="充分的理由，至少十个字符以上",
            timestamp=datetime.now()
        )
        
        rules_text = "允许修改事实。"
        allowed, errors = await self.handler.validate_retcon(operation, rules_text)
        
        assert allowed == True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_retcon_denied(self):
        """测试验证Retcon（禁止）"""
        operation = RetconOperation(
            type="modify_fact",
            target_id="test",
            changes={"new_value": "测试"},
            justification="理由",
            timestamp=datetime.now()
        )
        
        rules_text = "禁止修改历史。禁止Retcon。"
        allowed, errors = await self.handler.validate_retcon(operation, rules_text)
        
        assert allowed == False
        assert "规则禁止修改历史" in errors
        assert "规则禁止Retcon" in errors
    
    @pytest.mark.asyncio
    async def test_check_retcon_consistency(self):
        """测试检查Retcon一致性"""
        operation = RetconOperation(
            type="modify_fact",
            target_id="test",
            changes={"old": "旧", "new": "新"},
            justification="测试",
            timestamp=datetime.now()
        )
        
        mock_consistency_checker = Mock()
        mock_consistency_checker.check = Mock(return_value={
            "score": 0.8,
            "issues": [],
            "success": True
        })
        
        result = await self.handler.check_retcon_consistency(
            operation, mock_consistency_checker, "规则文本"
        )
        
        assert result["success"] == True
        assert result["consistency_score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_execute_retcon_with_consistency_check(self):
        """测试带一致性检查的Retcon执行"""
        operation = RetconOperation(
            type="modify_fact",
            target_id="test",
            changes={"old": "旧", "new": "新"},
            justification="充分的理由，至少十个字符以上",
            timestamp=datetime.now()
        )
        
        mock_consistency_checker = Mock()
        mock_consistency_checker.check = Mock(return_value={
            "score": 0.9,
            "issues": [],
            "success": True,
            "critical_issues_count": 0
        })
        
        session_context = {"session_id": "test_session"}
        result = await self.handler.execute_retcon_with_consistency_check(
            operation, session_context, mock_consistency_checker, "规则文本"
        )
        
        # 由于没有WorldMemory，应该失败，但一致性检查会通过
        assert result.success == False
        assert "缺少目标ID或世界记忆未初始化" in result.narrative_impact
    
    def test_get_retcon_history(self):
        """测试获取Retcon历史"""
        # 添加一些测试历史
        test_result = RetconResult(
            success=True,
            operation=RetconOperation(
                type="test",
                target_id=None,
                changes={},
                justification="测试",
                timestamp=datetime.now()
            ),
            narrative_impact="测试",
            consistency_issues=[]
        )
        
        self.handler.retcon_history.append(test_result)
        history = self.handler.get_retcon_history()
        
        assert len(history) == 1
        assert history[0].narrative_impact == "测试"
    
    def test_get_available_versions(self):
        """测试获取可用版本"""
        # 添加测试快照
        self.handler.version_snapshots["test_v1"] = {
            "timestamp": "2025-01-01T00:00:00",
            "entities": [],
            "relations": []
        }
        
        versions = self.handler.get_available_versions()
        
        assert len(versions) == 1
        assert versions[0]["id"] == "test_v1"
    
    @pytest.mark.asyncio
    async def test_rollback_to_version(self):
        """测试回滚到版本"""
        # 添加测试快照
        self.handler.version_snapshots["test_v1"] = {
            "timestamp": "2025-01-01T00:00:00",
            "entities": [],
            "relations": []
        }
        
        success = await self.handler.rollback_to_version("test_v1")
        
        # 由于没有WorldMemory，应该失败
        assert success == False
    
    @pytest.mark.asyncio
    async def test_resolve_retcon_conflicts(self):
        """测试解决Retcon冲突"""
        operation = RetconOperation(
            type="modify_fact",
            target_id="test",
            changes={"old": "旧", "new": "新"},
            justification="测试",
            timestamp=datetime.now()
        )
        
        conflicts = [
            {"type": "memory_conflict", "memory_id": "mem1", "description": "冲突1"}
        ]
        
        result = await self.handler.resolve_retcon_conflicts(operation, conflicts)
        
        assert result["success"] == False  # 没有WorldMemory
        assert result["conflicts_total"] == 1
        assert result["conflicts_unresolved"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])