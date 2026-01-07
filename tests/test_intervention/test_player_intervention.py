"""
PlayerIntervention单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.loom.intervention.player_intervention import (
    PlayerIntervention,
    Intervention,
    InterventionType,
    InterventionPriority,
    InterventionResult
)


class TestPlayerIntervention:
    """PlayerIntervention测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.intervention = PlayerIntervention()
    
    def test_parse_input_no_interventions(self):
        """测试无干预的输入解析"""
        text = "这是一个普通的叙事输入。"
        result = self.intervention.parse_input(text)
        
        assert result["has_interventions"] == False
        assert result["clean_input"] == text
        assert len(result["interventions"]) == 0
        assert len(result["conflicts"]) == 0
    
    def test_parse_input_ooc_intervention(self):
        """测试OOC干预解析"""
        text = "我想去城堡。(OOC: 城堡里有什么？)"
        result = self.intervention.parse_input(text)
        
        assert result["has_interventions"] == True
        assert "我想去城堡。" in result["clean_input"]
        assert len(result["interventions"]) == 1
        
        interv = result["interventions"][0]
        assert interv.type == InterventionType.OOC
        assert interv.content == "城堡里有什么？"
        assert interv.priority == InterventionPriority.BACKGROUND
    
    def test_parse_input_world_edit_intervention(self):
        """测试世界编辑干预解析"""
        text = "探索森林[EDIT: 天气: 晴朗]"
        result = self.intervention.parse_input(text)
        
        assert result["has_interventions"] == True
        assert "探索森林" in result["clean_input"]
        assert len(result["interventions"]) == 1
        
        interv = result["interventions"][0]
        assert interv.type == InterventionType.WORLD_EDIT
        assert interv.content == "天气: 晴朗"
        assert interv.priority == InterventionPriority.HIGH
    
    def test_parse_input_multiple_interventions(self):
        """测试多个干预解析"""
        text = "攻击敌人[EDIT: 敌人: 虚弱](OOC: 我想用魔法)"
        result = self.intervention.parse_input(text)
        
        assert result["has_interventions"] == True
        assert "攻击敌人" in result["clean_input"]
        assert len(result["interventions"]) == 2
        
        # 检查干预类型
        types = [interv.type for interv in result["interventions"]]
        assert InterventionType.WORLD_EDIT in types
        assert InterventionType.OOC in types
    
    def test_parse_input_conflict_detection(self):
        """测试冲突检测"""
        text = "[EDIT: 规则: 修改][RETCON: 历史: 改变]"
        result = self.intervention.parse_input(text)
        
        assert len(result["conflicts"]) > 0
        conflict = result["conflicts"][0]
        assert "冲突" in conflict["reason"] or "Retcon" in conflict["reason"]
    
    def test_prioritize_interventions(self):
        """测试干预优先级排序"""
        interventions = [
            Intervention(
                type=InterventionType.OOC,
                content="注释",
                raw_text="(OOC: 注释)",
                priority=InterventionPriority.BACKGROUND,
                urgency=0
            ),
            Intervention(
                type=InterventionType.RETCON,
                content="修改历史",
                raw_text="[RETCON: 修改历史]",
                priority=InterventionPriority.HIGH,
                urgency=50
            ),
            Intervention(
                type=InterventionType.INTENT_DECLARE,
                content="意图",
                raw_text="[INTENT: 意图]",
                priority=InterventionPriority.LOW,
                urgency=10
            )
        ]
        
        prioritized = self.intervention.prioritize_interventions(interventions)
        
        # 检查排序：RETCON应该在最前面（优先级最高）
        assert prioritized[0].type == InterventionType.RETCON
        # OOC应该在最后面（优先级最低）
        assert prioritized[-1].type == InterventionType.OOC
    
    @pytest.mark.asyncio
    async def test_process_ooc_intervention(self):
        """测试处理OOC干预"""
        intervention = Intervention(
            type=InterventionType.OOC,
            content="这个角色应该更勇敢",
            raw_text="(OOC: 这个角色应该更勇敢)",
            priority=InterventionPriority.BACKGROUND
        )
        
        session_context = {"session_id": "test_session"}
        result = await self.intervention._process_single_intervention(intervention, session_context)
        
        assert result.success == True
        assert "OOC注释不影响叙事" in result.narrative_impact
        assert len(result.actions_taken) == 1
        assert result.actions_taken[0]["action"] == "log_ooc"
    
    @pytest.mark.asyncio
    async def test_process_world_edit_intervention(self):
        """测试处理世界编辑干预"""
        intervention = Intervention(
            type=InterventionType.WORLD_EDIT,
            content="天气: 晴朗",
            raw_text="[EDIT: 天气: 晴朗]",
            priority=InterventionPriority.HIGH
        )
        
        session_context = {"session_id": "test_session"}
        result = await self.intervention._process_single_intervention(intervention, session_context)
        
        assert result.success == True
        assert "世界编辑" in result.narrative_impact
        assert len(result.actions_taken) == 1
        assert result.actions_taken[0]["action"] == "world_edit"
    
    @pytest.mark.asyncio
    async def test_process_retcon_intervention(self):
        """测试处理Retcon干预"""
        intervention = Intervention(
            type=InterventionType.RETCON,
            content="修改历史事件",
            raw_text="[RETCON: 修改历史事件]",
            priority=InterventionPriority.HIGH
        )
        
        session_context = {"session_id": "test_session"}
        result = await self.intervention._process_single_intervention(intervention, session_context)
        
        assert result.success == True
        assert "Retcon" in result.narrative_impact
        assert len(result.warnings) > 0
        assert "谨慎使用" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_process_interventions_list(self):
        """测试处理干预列表"""
        interventions = [
            Intervention(
                type=InterventionType.OOC,
                content="注释1",
                raw_text="(OOC: 注释1)",
                priority=InterventionPriority.BACKGROUND
            ),
            Intervention(
                type=InterventionType.WORLD_EDIT,
                content="目标: 修改",
                raw_text="[EDIT: 目标: 修改]",
                priority=InterventionPriority.HIGH
            )
        ]
        
        session_context = {"session_id": "test_session"}
        results = await self.intervention.process_interventions(interventions, session_context)
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    def test_merge_interventions_into_prompt(self):
        """测试将干预合并到Prompt"""
        clean_input = "叙事文本"
        intervention_results = [
            InterventionResult(
                success=True,
                intervention=Intervention(
                    type=InterventionType.WORLD_EDIT,
                    content="天气: 晴朗",
                    raw_text="[EDIT: 天气: 晴朗]",
                    priority=InterventionPriority.HIGH
                ),
                narrative_impact="世界编辑",
                actions_taken=[]
            ),
            InterventionResult(
                success=True,
                intervention=Intervention(
                    type=InterventionType.OOC,
                    content="注释",
                    raw_text="(OOC: 注释)",
                    priority=InterventionPriority.BACKGROUND
                ),
                narrative_impact="OOC注释",
                actions_taken=[]
            )
        ]
        
        prompt = self.intervention.merge_interventions_into_prompt(clean_input, intervention_results)
        
        assert "叙事文本" in prompt
        assert "玩家干预" in prompt
        assert "WORLD_EDIT" in prompt
        # OOC注释不应该出现在合并后的Prompt中
        assert "OOC" not in prompt
    
    @pytest.mark.asyncio
    async def test_validate_permission_allowed(self):
        """测试验证权限（允许）"""
        intervention = Intervention(
            type=InterventionType.WORLD_EDIT,
            content="测试",
            raw_text="[EDIT: 测试]",
            priority=InterventionPriority.HIGH
        )
        
        rules_text = "允许编辑世界状态。"
        allowed = await self.intervention.validate_permission(intervention, rules_text)
        
        assert allowed == True
    
    @pytest.mark.asyncio
    async def test_validate_permission_denied(self):
        """测试验证权限（禁止）"""
        intervention = Intervention(
            type=InterventionType.WORLD_EDIT,
            content="测试",
            raw_text="[EDIT: 测试]",
            priority=InterventionPriority.HIGH
        )
        
        rules_text = "禁止编辑世界状态。"
        allowed = await self.intervention.validate_permission(intervention, rules_text)
        
        assert allowed == False
    
    def test_audit_intervention(self):
        """测试干预审计"""
        intervention = Intervention(
            type=InterventionType.WORLD_EDIT,
            content="测试内容",
            raw_text="[EDIT: 测试内容]",
            priority=InterventionPriority.HIGH
        )
        
        result = InterventionResult(
            success=True,
            intervention=intervention,
            narrative_impact="测试影响",
            actions_taken=[{"action": "test"}]
        )
        
        audit = asyncio.run(self.intervention.audit_intervention(intervention, result, "test_user"))
        
        assert audit["user_id"] == "test_user"
        assert audit["intervention_type"] == "world_edit"
        assert audit["success"] == True
        assert "timestamp" in audit
    
    @pytest.mark.asyncio
    async def test_integrate_with_session_manager(self):
        """测试与SessionManager集成"""
        mock_session_manager = Mock()
        mock_session = Mock()
        mock_session.state = {}
        mock_session.metadata = {}
        mock_session_manager.load_session = AsyncMock(return_value=mock_session)
        mock_session_manager.save_session = AsyncMock(return_value=True)
        
        interventions = [
            Intervention(
                type=InterventionType.OOC,
                content="测试",
                raw_text="(OOC: 测试)",
                priority=InterventionPriority.BACKGROUND
            )
        ]
        
        result = await self.intervention.integrate_with_session(
            mock_session_manager, "test_session", interventions
        )
        
        assert result["success"] == True
        assert result["interventions_added"] == 1
        mock_session_manager.save_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_player_input_with_integration(self):
        """测试完整处理玩家输入"""
        mock_session_manager = Mock()
        mock_session = Mock()
        mock_session.state = {}
        mock_session.metadata = {}
        mock_session_manager.load_session = AsyncMock(return_value=mock_session)
        mock_session_manager.save_session = AsyncMock(return_value=True)
        
        mock_turn_scheduler = Mock()
        mock_turn = Mock()
        mock_turn.interventions = []
        mock_turn.priority = 0
        mock_turn_scheduler.get_turn = AsyncMock(return_value=mock_turn)
        mock_turn_scheduler.persistence = None
        
        text = "测试输入[EDIT: 目标: 修改]"
        
        result = await self.intervention.process_player_input_with_integration(
            text, mock_session_manager, "test_session", 
            mock_turn_scheduler, "test_turn"
        )
        
        assert result["success"] == True
        assert result["has_interventions"] == True
        assert "session_integration" in result
        assert "turn_integration" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])