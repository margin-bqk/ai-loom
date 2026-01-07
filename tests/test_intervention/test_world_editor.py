"""
WorldEditor单元测试
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from src.loom.intervention.world_editor import (
    WorldEditor,
    EditCommand,
    EditType,
    EditResult,
    EditValidation
)


class TestWorldEditor:
    """WorldEditor测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.editor = WorldEditor()
    
    def test_parse_edit_command_rule_modification(self):
        """测试解析规则修改命令"""
        text = "[EDIT: RULE: 天气规则: 晴天概率=80%]"
        commands = self.editor.parse_edit_command(text)
        
        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.edit_type == EditType.RULE_MODIFICATION
        assert cmd.target == "天气规则"
        assert cmd.content == "晴天概率=80%"
        assert cmd.raw_text == text
    
    def test_parse_edit_command_entity_creation(self):
        """测试解析实体创建命令"""
        text = "[EDIT: CREATE: 角色: 勇敢的骑士]"
        commands = self.editor.parse_edit_command(text)
        
        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.edit_type == EditType.ENTITY_CREATION
        assert cmd.target == "角色"
        assert cmd.content == "勇敢的骑士"
    
    def test_parse_edit_command_entity_modification(self):
        """测试解析实体修改命令"""
        text = "[EDIT: MODIFY: 角色: 骑士: 健康=100]"
        commands = self.editor.parse_edit_command(text)
        
        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.edit_type == EditType.ENTITY_MODIFICATION
        assert cmd.target == "角色"
        assert cmd.content == "骑士: 健康=100"
    
    def test_parse_edit_command_entity_deletion(self):
        """测试解析实体删除命令"""
        text = "[EDIT: DELETE: 物品: 旧剑]"
        commands = self.editor.parse_edit_command(text)
        
        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.edit_type == EditType.ENTITY_DELETION
        assert cmd.target == "物品"
        assert cmd.content == "旧剑"
    
    def test_parse_edit_command_state_adjustment(self):
        """测试解析状态调整命令"""
        text = "[EDIT: STATE: 世界状态: 时间=正午]"
        commands = self.editor.parse_edit_command(text)
        
        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.edit_type == EditType.STATE_ADJUSTMENT
        assert cmd.target == "世界状态"
        assert cmd.content == "时间=正午"
    
    def test_parse_edit_command_multiple_commands(self):
        """测试解析多个命令"""
        text = "[EDIT: RULE: 规则1][EDIT: CREATE: 实体1]"
        commands = self.editor.parse_edit_command(text)
        
        assert len(commands) == 2
        types = [cmd.edit_type for cmd in commands]
        assert EditType.RULE_MODIFICATION in types
        assert EditType.ENTITY_CREATION in types
    
    def test_parse_edit_command_invalid_format(self):
        """测试解析无效格式命令"""
        text = "[EDIT: INVALID: 目标: 内容]"
        commands = self.editor.parse_edit_command(text)
        
        # 应该返回空列表或标记为无效
        assert len(commands) == 0
    
    @pytest.mark.asyncio
    async def test_validate_edit_permission_allowed(self):
        """测试验证编辑权限（允许）"""
        cmd = EditCommand(
            edit_type=EditType.RULE_MODIFICATION,
            target="天气规则",
            content="修改",
            raw_text="[EDIT: RULE: 天气规则: 修改]"
        )
        
        rules_text = "允许修改天气规则。"
        validation = await self.editor.validate_edit(cmd, rules_text)
        
        assert validation.allowed == True
        assert validation.reason == "权限验证通过"
    
    @pytest.mark.asyncio
    async def test_validate_edit_permission_denied(self):
        """测试验证编辑权限（禁止）"""
        cmd = EditCommand(
            edit_type=EditType.RULE_MODIFICATION,
            target="核心规则",
            content="修改",
            raw_text="[EDIT: RULE: 核心规则: 修改]"
        )
        
        rules_text = "禁止修改核心规则。"
        validation = await self.editor.validate_edit(cmd, rules_text)
        
        assert validation.allowed == False
        assert "禁止" in validation.reason
    
    @pytest.mark.asyncio
    async def test_validate_edit_consistency_check(self):
        """测试验证编辑一致性"""
        cmd = EditCommand(
            edit_type=EditType.ENTITY_CREATION,
            target="角色",
            content="重复角色",
            raw_text="[EDIT: CREATE: 角色: 重复角色]"
        )
        
        world_state = {"角色": ["重复角色"]}
        validation = await self.editor.validate_edit(cmd, "", world_state)
        
        assert validation.allowed == False
        assert "已存在" in validation.reason
    
    @pytest.mark.asyncio
    async def test_execute_rule_modification(self):
        """测试执行规则修改"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# 原始规则\n原始内容\n")
            temp_path = f.name
        
        try:
            cmd = EditCommand(
                edit_type=EditType.RULE_MODIFICATION,
                target=temp_path,
                content="新内容",
                raw_text="[EDIT: RULE: 文件: 新内容]"
            )
            
            result = await self.editor._execute_rule_modification(cmd)
            
            assert result.success == True
            assert "规则文件已修改" in result.message
            
            # 验证文件内容
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "新内容" in content
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_execute_entity_creation(self):
        """测试执行实体创建"""
        mock_world_memory = Mock()
        mock_world_memory.add_entity = AsyncMock(return_value=True)
        
        cmd = EditCommand(
            edit_type=EditType.ENTITY_CREATION,
            target="角色",
            content="勇敢的骑士",
            raw_text="[EDIT: CREATE: 角色: 勇敢的骑士]"
        )
        
        result = await self.editor._execute_entity_creation(cmd, mock_world_memory)
        
        assert result.success == True
        assert "实体已创建" in result.message
        mock_world_memory.add_entity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_entity_modification(self):
        """测试执行实体修改"""
        mock_world_memory = Mock()
        mock_world_memory.update_entity = AsyncMock(return_value=True)
        
        cmd = EditCommand(
            edit_type=EditType.ENTITY_MODIFICATION,
            target="角色",
            content="骑士: 健康=100",
            raw_text="[EDIT: MODIFY: 角色: 骑士: 健康=100]"
        )
        
        result = await self.editor._execute_entity_modification(cmd, mock_world_memory)
        
        assert result.success == True
        assert "实体已修改" in result.message
        mock_world_memory.update_entity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_entity_deletion(self):
        """测试执行实体删除"""
        mock_world_memory = Mock()
        mock_world_memory.remove_entity = AsyncMock(return_value=True)
        
        cmd = EditCommand(
            edit_type=EditType.ENTITY_DELETION,
            target="物品",
            content="旧剑",
            raw_text="[EDIT: DELETE: 物品: 旧剑]"
        )
        
        result = await self.editor._execute_entity_deletion(cmd, mock_world_memory)
        
        assert result.success == True
        assert "实体已删除" in result.message
        mock_world_memory.remove_entity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_state_adjustment(self):
        """测试执行状态调整"""
        mock_world_memory = Mock()
        mock_world_memory.update_state = AsyncMock(return_value=True)
        
        cmd = EditCommand(
            edit_type=EditType.STATE_ADJUSTMENT,
            target="世界状态",
            content="时间=正午",
            raw_text="[EDIT: STATE: 世界状态: 时间=正午]"
        )
        
        result = await self.editor._execute_state_adjustment(cmd, mock_world_memory)
        
        assert result.success == True
        assert "状态已调整" in result.message
        mock_world_memory.update_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_edit_command(self):
        """测试执行编辑命令"""
        cmd = EditCommand(
            edit_type=EditType.RULE_MODIFICATION,
            target="测试规则",
            content="测试内容",
            raw_text="[EDIT: RULE: 测试规则: 测试内容]"
        )
        
        result = await self.editor.execute_edit_command(cmd)
        
        assert result.success == True
        assert result.edit_type == EditType.RULE_MODIFICATION
        assert "执行完成" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_edit_commands_list(self):
        """测试执行编辑命令列表"""
        commands = [
            EditCommand(
                edit_type=EditType.ENTITY_CREATION,
                target="角色",
                content="角色1",
                raw_text="[EDIT: CREATE: 角色: 角色1]"
            ),
            EditCommand(
                edit_type=EditType.STATE_ADJUSTMENT,
                target="状态",
                content="值=1",
                raw_text="[EDIT: STATE: 状态: 值=1]"
            )
        ]
        
        results = await self.editor.execute_edit_commands(commands)
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_integrate_with_rule_loader(self):
        """测试与RuleLoader集成"""
        mock_rule_loader = Mock()
        mock_rule_loader.reload_rules = AsyncMock(return_value=True)
        
        cmd = EditCommand(
            edit_type=EditType.RULE_MODIFICATION,
            target="规则文件.md",
            content="新规则",
            raw_text="[EDIT: RULE: 规则文件.md: 新规则]"
        )
        
        result = await self.editor.integrate_with_rule_loader(mock_rule_loader, cmd)
        
        assert result["success"] == True
        assert result["rules_reloaded"] == True
        mock_rule_loader.reload_rules.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integrate_with_world_memory(self):
        """测试与WorldMemory集成"""
        mock_world_memory = Mock()
        mock_world_memory.add_entity = AsyncMock(return_value=True)
        mock_world_memory.update_state = AsyncMock(return_value=True)
        
        commands = [
            EditCommand(
                edit_type=EditType.ENTITY_CREATION,
                target="角色",
                content="新角色",
                raw_text="[EDIT: CREATE: 角色: 新角色]"
            )
        ]
        
        result = await self.editor.integrate_with_world_memory(mock_world_memory, commands)
        
        assert result["success"] == True
        assert result["entities_created"] == 1
        mock_world_memory.add_entity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_comprehensive_edit(self):
        """测试执行综合编辑"""
        mock_rule_loader = Mock()
        mock_rule_loader.reload_rules = AsyncMock(return_value=True)
        
        mock_world_memory = Mock()
        mock_world_memory.add_entity = AsyncMock(return_value=True)
        
        edit_text = "[EDIT: CREATE: 角色: 骑士][EDIT: RULE: 规则.md: 修改]"
        
        result = await self.editor.execute_comprehensive_edit(
            edit_text, mock_rule_loader, mock_world_memory, "test_session"
        )
        
        assert result["success"] == True
        assert result["commands_executed"] == 2
        assert "rule_loader_integration" in result
        assert "world_memory_integration" in result
    
    @pytest.mark.asyncio
    async def test_rollback_edit(self):
        """测试回滚编辑"""
        cmd = EditCommand(
            edit_type=EditType.ENTITY_CREATION,
            target="角色",
            content="测试角色",
            raw_text="[EDIT: CREATE: 角色: 测试角色]"
        )
        
        edit_result = EditResult(
            success=True,
            edit_type=cmd.edit_type,
            message="测试",
            changes_made={"entity_id": "test"}
        )
        
        rollback_result = await self.editor.rollback_edit(cmd, edit_result)
        
        assert rollback_result["success"] == True
        assert rollback_result["edit_rolled_back"] == True
        assert "回滚" in rollback_result["message"]
    
    def test_generate_edit_summary(self):
        """测试生成编辑摘要"""
        commands = [
            EditCommand(
                edit_type=EditType.ENTITY_CREATION,
                target="角色",
                content="角色1",
                raw_text="[EDIT: CREATE: 角色: 角色1]"
            ),
            EditCommand(
                edit_type=EditType.RULE_MODIFICATION,
                target="规则",
                content="修改",
                raw_text="[EDIT: RULE: 规则: 修改]"
            )
        ]
        
        results = [
            EditResult(
                success=True,
                edit_type=EditType.ENTITY_CREATION,
                message="成功",
                changes_made={}
            ),
            EditResult(
                success=False,
                edit_type=EditType.RULE_MODIFICATION,
                message="失败",
                changes_made={}
            )
        ]
        
        summary = self.editor.generate_edit_summary(commands, results)
        
        assert "编辑摘要" in summary
        assert "成功: 1" in summary
        assert "失败: 1" in summary
        assert "ENTITY_CREATION" in summary
        assert "RULE_MODIFICATION" in summary
    
    @pytest.mark.asyncio
    async def test_validate_world_edit_permissions(self):
        """测试验证世界编辑权限"""
        edit_text = "[EDIT: CREATE: 角色: 测试]"
        rules_text = "允许创建角色。"
        
        validation = await self.editor.validate_world_edit_permissions(edit_text, rules_text)
        
        assert validation["overall_allowed"] == True
        assert len(validation["command_validations"]) > 0
        assert validation["command_validations"][0]["allowed"] == True
    
    @pytest.mark.asyncio
    async def test_handle_edit_workflow(self):
        """测试完整编辑工作流"""
        edit_text = "[EDIT: CREATE: 角色: 骑士][EDIT: STATE: 世界: 时间=正午]"
        
        result = await self.editor.handle_edit_workflow(edit_text, "test_session")
        
        assert result["success"] == True
        assert "commands_parsed" in result
        assert "execution_results" in result
        assert "summary" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])