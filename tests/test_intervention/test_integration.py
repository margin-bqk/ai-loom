"""
干预层集成测试
测试玩家干预接口与核心运行时层、规则层、解释层、世界记忆层的集成
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.loom.intervention.player_intervention import PlayerIntervention, Intervention, InterventionType
from src.loom.intervention.ooc_handler import OOCHandler
from src.loom.intervention.world_editor import WorldEditor
from src.loom.intervention.retcon_handler import RetconHandler

from src.loom.core.session_manager import SessionManager
from src.loom.core.turn_scheduler import TurnScheduler
from src.loom.core.prompt_assembler import PromptAssembler
from src.loom.rules.rule_loader import RuleLoader
from src.loom.memory.world_memory import WorldMemory
from src.loom.interpretation.consistency_checker import ConsistencyChecker


class TestInterventionIntegration:
    """干预层集成测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.player_intervention = PlayerIntervention()
        self.ooc_handler = OOCHandler()
        self.world_editor = WorldEditor()
        self.retcon_handler = RetconHandler()
    
    @pytest.mark.asyncio
    async def test_player_intervention_with_session_manager(self):
        """测试PlayerIntervention与SessionManager集成"""
        # 创建模拟SessionManager
        mock_session_manager = Mock(spec=SessionManager)
        mock_session = Mock()
        mock_session.state = {"interventions": []}
        mock_session.metadata = {"session_id": "test_session"}
        mock_session_manager.load_session = AsyncMock(return_value=mock_session)
        mock_session_manager.save_session = AsyncMock(return_value=True)
        
        # 测试干预处理
        text = "叙事文本(OOC: 测试注释)"
        result = await self.player_intervention.process_player_input_with_integration(
            text, mock_session_manager, "test_session", None, None
        )
        
        assert result["success"] == True
        assert result["has_interventions"] == True
        assert "session_integration" in result
        mock_session_manager.save_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_player_intervention_with_turn_scheduler(self):
        """测试PlayerIntervention与TurnScheduler集成"""
        # 创建模拟TurnScheduler
        mock_turn_scheduler = Mock(spec=TurnScheduler)
        mock_turn = Mock()
        mock_turn.interventions = []
        mock_turn.priority = 0
        mock_turn_scheduler.get_turn = AsyncMock(return_value=mock_turn)
        mock_turn_scheduler.persistence = None
        
        # 创建干预
        interventions = [
            Intervention(
                type=InterventionType.OOC,
                content="测试",
                raw_text="(OOC: 测试)",
                priority=0
            )
        ]
        
        result = await self.player_intervention.integrate_with_turn(
            mock_turn_scheduler, "test_turn", interventions
        )
        
        assert result["success"] == True
        assert result["interventions_added"] == 1
        mock_turn_scheduler.get_turn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ooc_handler_with_prompt_assembler(self):
        """测试OOCHandler与PromptAssembler集成"""
        # 创建模拟PromptAssembler
        mock_prompt_assembler = Mock(spec=PromptAssembler)
        mock_prompt_assembler.add_context = AsyncMock(return_value=True)
        
        # 解析OOC注释
        text = "叙事文本(OOC: 角色应该更勇敢)"
        comments = self.ooc_handler.parse_ooc(text)
        
        # 集成到PromptAssembler
        result = await self.ooc_handler.integrate_with_prompt_assembler(
            mock_prompt_assembler, comments, "test_session"
        )
        
        assert result["success"] == True
        assert result["ooc_context_added"] == 1
        mock_prompt_assembler.add_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_world_editor_with_rule_loader(self):
        """测试WorldEditor与RuleLoader集成"""
        # 创建模拟RuleLoader
        mock_rule_loader = Mock(spec=RuleLoader)
        mock_rule_loader.reload_rules = AsyncMock(return_value=True)
        
        # 创建编辑命令
        edit_text = "[EDIT: RULE: 测试规则: 新内容]"
        commands = self.world_editor.parse_edit_command(edit_text)
        
        # 集成到RuleLoader
        result = await self.world_editor.integrate_with_rule_loader(
            mock_rule_loader, commands[0]
        )
        
        assert result["success"] == True
        assert result["rules_reloaded"] == True
        mock_rule_loader.reload_rules.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_world_editor_with_world_memory(self):
        """测试WorldEditor与WorldMemory集成"""
        # 创建模拟WorldMemory
        mock_world_memory = Mock(spec=WorldMemory)
        mock_world_memory.add_entity = AsyncMock(return_value=True)
        mock_world_memory.update_state = AsyncMock(return_value=True)
        
        # 创建编辑命令
        edit_text = "[EDIT: CREATE: 角色: 新角色]"
        commands = self.world_editor.parse_edit_command(edit_text)
        
        # 集成到WorldMemory
        result = await self.world_editor.integrate_with_world_memory(
            mock_world_memory, commands
        )
        
        assert result["success"] == True
        assert result["entities_created"] == 1
        mock_world_memory.add_entity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retcon_handler_with_consistency_checker(self):
        """测试RetconHandler与ConsistencyChecker集成"""
        # 创建模拟ConsistencyChecker
        mock_consistency_checker = Mock(spec=ConsistencyChecker)
        mock_consistency_checker.check_consistency = AsyncMock(
            return_value={
                "is_consistent": True,
                "conflicts": [],
                "severity": "low"
            }
        )
        
        # 创建Retcon操作
        retcon_text = "[RETCON: FACT: 位置: 修正]"
        operations = self.retcon_handler.parse_retcon(retcon_text)
        
        # 检查一致性
        result = await self.retcon_handler.check_retcon_consistency(
            operations[0], mock_consistency_checker
        )
        
        assert result["is_consistent"] == True
        assert len(result["conflicts"]) == 0
        mock_consistency_checker.check_consistency.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retcon_handler_with_world_memory(self):
        """测试RetconHandler与WorldMemory集成"""
        # 创建模拟WorldMemory
        mock_world_memory = Mock(spec=WorldMemory)
        mock_world_memory.update_timeline = AsyncMock(return_value=True)
        mock_world_memory.update_fact = AsyncMock(return_value=True)
        
        # 创建Retcon操作
        retcon_text = "[RETCON: TIMELINE: 事件顺序: 调整]"
        operations = self.retcon_handler.parse_retcon(retcon_text)
        
        # 集成到WorldMemory
        result = await self.retcon_handler.integrate_with_world_memory(
            mock_world_memory, operations
        )
        
        assert result["success"] == True
        assert result["timeline_updated"] == True
        mock_world_memory.update_timeline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_full_intervention_workflow(self):
        """测试完整干预工作流"""
        # 创建模拟组件
        mock_session_manager = Mock(spec=SessionManager)
        mock_session = Mock()
        mock_session.state = {}
        mock_session.metadata = {}
        mock_session_manager.load_session = AsyncMock(return_value=mock_session)
        mock_session_manager.save_session = AsyncMock(return_value=True)
        
        mock_turn_scheduler = Mock(spec=TurnScheduler)
        mock_turn = Mock()
        mock_turn.interventions = []
        mock_turn.priority = 0
        mock_turn_scheduler.get_turn = AsyncMock(return_value=mock_turn)
        
        mock_prompt_assembler = Mock(spec=PromptAssembler)
        mock_prompt_assembler.add_context = AsyncMock(return_value=True)
        
        mock_rule_loader = Mock(spec=RuleLoader)
        mock_rule_loader.reload_rules = AsyncMock(return_value=True)
        
        mock_world_memory = Mock(spec=WorldMemory)
        mock_world_memory.add_entity = AsyncMock(return_value=True)
        mock_world_memory.update_state = AsyncMock(return_value=True)
        
        mock_consistency_checker = Mock(spec=ConsistencyChecker)
        mock_consistency_checker.check_consistency = AsyncMock(
            return_value={"is_consistent": True, "conflicts": []}
        )
        
        # 模拟玩家输入包含多种干预
        player_input = """
        探索森林(OOC: 森林里有什么生物？)
        [EDIT: CREATE: 角色: 勇敢的探险家]
        [RETCON: FACT: 之前提到的河流位置: 东改为西]
        """
        
        # 步骤1: PlayerIntervention解析和处理
        parse_result = self.player_intervention.parse_input(player_input)
        assert parse_result["has_interventions"] == True
        
        # 步骤2: 处理干预
        session_context = {"session_id": "test_session"}
        intervention_results = await self.player_intervention.process_interventions(
            parse_result["interventions"], session_context
        )
        assert len(intervention_results) > 0
        
        # 步骤3: 与SessionManager集成
        session_result = await self.player_intervention.integrate_with_session(
            mock_session_manager, "test_session", parse_result["interventions"]
        )
        assert session_result["success"] == True
        
        # 步骤4: 与TurnScheduler集成
        turn_result = await self.player_intervention.integrate_with_turn(
            mock_turn_scheduler, "test_turn", parse_result["interventions"]
        )
        assert turn_result["success"] == True
        
        # 步骤5: OOC处理与PromptAssembler集成
        ooc_comments = self.ooc_handler.parse_ooc(player_input)
        if ooc_comments:
            ooc_result = await self.ooc_handler.integrate_with_prompt_assembler(
                mock_prompt_assembler, ooc_comments, "test_session"
            )
            assert ooc_result["success"] == True
        
        # 步骤6: 世界编辑与RuleLoader/WorldMemory集成
        edit_commands = self.world_editor.parse_edit_command(player_input)
        if edit_commands:
            for cmd in edit_commands:
                if cmd.edit_type.name == "RULE_MODIFICATION":
                    rule_result = await self.world_editor.integrate_with_rule_loader(
                        mock_rule_loader, cmd
                    )
                    assert rule_result["success"] == True
                else:
                    world_result = await self.world_editor.integrate_with_world_memory(
                        mock_world_memory, [cmd]
                    )
                    assert world_result["success"] == True
        
        # 步骤7: Retcon处理与ConsistencyChecker集成
        retcon_operations = self.retcon_handler.parse_retcon(player_input)
        if retcon_operations:
            for op in retcon_operations:
                consistency_result = await self.retcon_handler.check_retcon_consistency(
                    op, mock_consistency_checker
                )
                assert consistency_result["is_consistent"] == True
        
        # 验证所有模拟组件都被调用
        assert mock_session_manager.save_session.called
        assert mock_turn_scheduler.get_turn.called
        if ooc_comments:
            assert mock_prompt_assembler.add_context.called
        if any(cmd.edit_type.name == "RULE_MODIFICATION" for cmd in edit_commands):
            assert mock_rule_loader.reload_rules.called
        if any(cmd.edit_type.name in ["ENTITY_CREATION", "ENTITY_MODIFICATION", "ENTITY_DELETION", "STATE_ADJUSTMENT"] 
               for cmd in edit_commands):
            assert mock_world_memory.add_entity.called or mock_world_memory.update_state.called
        if retcon_operations:
            assert mock_consistency_checker.check_consistency.called
    
    @pytest.mark.asyncio
    async def test_intervention_priority_and_conflict_resolution(self):
        """测试干预优先级和冲突解决"""
        # 创建包含冲突干预的输入
        player_input = """
        [EDIT: RULE: 核心规则: 修改]
        [RETCON: TIMELINE: 关键事件: 调整]
        (OOC: 这会有冲突吗？)
        """
        
        # 解析输入
        parse_result = self.player_intervention.parse_input(player_input)
        
        # 检查冲突
        assert len(parse_result["conflicts"]) > 0
        
        # 优先级排序
        prioritized = self.player_intervention.prioritize_interventions(
            parse_result["interventions"]
        )
        
        # RETCON应该优先级最高
        retcon_interventions = [i for i in prioritized if i.type == InterventionType.RETCON]
        if retcon_interventions:
            # 检查RETCON是否在列表前面
            retcon_index = prioritized.index(retcon_interventions[0])
            ooc_interventions = [i for i in prioritized if i.type == InterventionType.OOC]
            if ooc_interventions:
                ooc_index = prioritized.index(ooc_interventions[0])
                assert retcon_index < ooc_index
    
    @pytest.mark.asyncio
    async def test_error_handling_in_integration(self):
        """测试集成中的错误处理"""
        # 模拟组件抛出异常
        mock_session_manager = Mock(spec=SessionManager)
        mock_session_manager.load_session = AsyncMock(side_effect=Exception("模拟错误"))
        
        # 应该优雅处理错误
        try:
            result = await self.player_intervention.process_player_input_with_integration(
                "测试", mock_session_manager, "test_session", None, None
            )
            # 即使有错误，也应该返回结果
            assert "error" in result or result["success"] == False
        except Exception:
            # 如果异常传播，测试失败
            pytest.fail("集成应该处理组件异常")
    
    @pytest.mark.asyncio
    async def test_performance_of_intervention_processing(self):
        """测试干预处理性能"""
        import time
        
        # 创建大量干预的输入
        player_input = " ".join([f"(OOC: 注释{i})" for i in range(10)]) + \
                      " ".join([f"[EDIT: CREATE: 角色{i}: 内容]" for i in range(10)])
        
        start_time = time.time()
        
        # 解析
        parse_result = self.player_intervention.parse_input(player_input)
        
        # 处理
        session_context = {"session_id": "test_session"}
        await self.player_intervention.process_interventions(
            parse_result["interventions"], session_context
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 性能检查：处理20个干预应该在合理时间内
        assert processing_time < 2.0, f"干预处理时间过长: {processing_time}秒"
        
        print(f"处理20个干预用时: {processing_time:.3f}秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])