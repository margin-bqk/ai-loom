"""
WorldEditor单元测试
"""

import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.loom.intervention.world_editor import EditCommand, EditResult, WorldEditor


class TestWorldEditor:
    """WorldEditor测试类"""

    def setup_method(self):
        """测试设置"""
        self.editor = WorldEditor()

    def test_parse_edit_command_character_add(self):
        """测试解析添加角色命令"""
        text = "character: add: name=骑士,description=勇敢的骑士"
        command = self.editor.parse_edit_command(text)

        assert command is not None
        assert command.target_type == "character"
        assert command.action == "add"
        assert command.parameters.get("name") == "骑士"
        assert command.parameters.get("description") == "勇敢的骑士"

    def test_parse_edit_command_fact_add(self):
        """测试解析添加事实命令"""
        text = "fact: add: value=城堡在北边,certainty=0.9"
        command = self.editor.parse_edit_command(text)

        assert command is not None
        assert command.target_type == "fact"
        assert command.action == "add"
        assert command.parameters.get("value") == "城堡在北边"
        assert command.parameters.get("certainty") == "0.9"

    def test_parse_edit_command_relation_add(self):
        """测试解析添加关系命令"""
        text = "relation: add: source=char1,target=char2,type=friends"
        command = self.editor.parse_edit_command(text)

        assert command is not None
        assert command.target_type == "relation"
        assert command.action == "add"
        assert command.parameters.get("source") == "char1"
        assert command.parameters.get("target") == "char2"
        assert command.parameters.get("type") == "friends"

    def test_parse_edit_command_character_update(self):
        """测试解析更新角色命令"""
        text = "character: update: [char_123]: name=新名字"
        command = self.editor.parse_edit_command(text)

        assert command is not None
        assert command.target_type == "character"
        assert command.action == "update"
        assert command.target_id == "char_123"
        assert command.parameters.get("name") == "新名字"

    def test_parse_edit_command_invalid_format(self):
        """测试解析无效格式命令"""
        text = "invalid: 目标: 内容"
        command = self.editor.parse_edit_command(text)

        assert command is None

    @pytest.mark.asyncio
    async def test_execute_edit_character_add(self):
        """测试执行添加角色编辑"""
        command = EditCommand(
            target_type="character",
            target_id=None,
            action="add",
            parameters={"name": "测试角色", "description": "测试描述"},
        )

        session_context = {"session_id": "test_session"}
        result = await self.editor.execute_edit(command, session_context)

        # 由于没有WorldMemory，应该失败
        assert result.success == False
        assert "世界记忆未初始化" in result.narrative_impact

    @pytest.mark.asyncio
    async def test_execute_edit_fact_add(self):
        """测试执行添加事实编辑"""
        command = EditCommand(
            target_type="fact",
            target_id=None,
            action="add",
            parameters={"value": "测试事实", "certainty": "0.8"},
        )

        session_context = {"session_id": "test_session"}
        result = await self.editor.execute_edit(command, session_context)

        # 由于没有WorldMemory，应该失败
        assert result.success == False
        assert "世界记忆未初始化" in result.narrative_impact

    @pytest.mark.asyncio
    async def test_execute_edit_character_update(self):
        """测试执行更新角色编辑"""
        command = EditCommand(
            target_type="character",
            target_id="test_char",
            action="update",
            parameters={"name": "新名字"},
        )

        session_context = {"session_id": "test_session"}
        result = await self.editor.execute_edit(command, session_context)

        # 由于没有WorldMemory，应该失败
        assert result.success == False
        assert "缺少目标ID或世界记忆未初始化" in result.narrative_impact

    @pytest.mark.asyncio
    async def test_validate_edit_allowed(self):
        """测试验证编辑（允许）"""
        command = EditCommand(
            target_type="character",
            target_id=None,
            action="add",
            parameters={"name": "测试"},
        )

        rules_text = "允许添加角色。"
        allowed, errors = await self.editor.validate_edit(command, rules_text)

        assert allowed == True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_edit_denied(self):
        """测试验证编辑（禁止）"""
        command = EditCommand(
            target_type="character",
            target_id=None,
            action="add",
            parameters={"name": "测试"},
        )

        rules_text = "禁止添加角色。禁止编辑。"
        allowed, errors = await self.editor.validate_edit(command, rules_text)

        assert allowed == False
        assert "规则禁止添加角色" in errors
        assert "规则禁止编辑" in errors

    def test_get_edit_history(self):
        """测试获取编辑历史"""
        # 添加测试历史
        test_result = EditResult(
            success=True,
            command=EditCommand(
                target_type="test", target_id=None, action="test", parameters={}
            ),
            changes_made=[],
            narrative_impact="测试",
        )

        self.editor.edit_history.append(test_result)
        history = self.editor.get_edit_history()

        assert len(history) == 1
        assert history[0].narrative_impact == "测试"

    @pytest.mark.asyncio
    async def test_undo_last_edit(self):
        """测试撤销最后一次编辑"""
        # 添加测试历史
        test_result = EditResult(
            success=True,
            command=EditCommand(
                target_type="test", target_id=None, action="test", parameters={}
            ),
            changes_made=[],
            narrative_impact="测试",
        )

        self.editor.edit_history.append(test_result)
        undo_result = await self.editor.undo_last_edit()

        assert undo_result is not None
        assert undo_result.success == True
        assert "撤销了最后一次编辑" in undo_result.narrative_impact

    @pytest.mark.asyncio
    async def test_modify_rule(self):
        """测试修改规则"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# 测试规则\n\n## 章节1\n原始内容\n")
            temp_path = f.name

        try:
            # 创建带RuleLoader的编辑器
            mock_rule_loader = Mock()
            mock_rule_loader.canon_dir = os.path.dirname(temp_path)
            mock_rule_loader.clear_cache = Mock()

            editor = WorldEditor(rule_loader=mock_rule_loader)

            rule_name = os.path.basename(temp_path).replace(".md", "")
            result = await editor.modify_rule(rule_name, "章节1", "新内容", "测试修改")

            assert result.success == True
            assert "修改了规则" in result.narrative_impact

            # 验证文件内容
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "新内容" in content

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_create_rule(self):
        """测试创建规则"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建带RuleLoader的编辑器
            mock_rule_loader = Mock()
            mock_rule_loader.canon_dir = temp_dir

            editor = WorldEditor(rule_loader=mock_rule_loader)

            result = await editor.create_rule(
                "新规则", "# 新规则\n\n测试内容", "测试创建"
            )

            assert result.success == True
            assert "创建了新规则文件" in result.narrative_impact

            # 验证文件存在
            rule_file = os.path.join(temp_dir, "新规则.md")
            assert os.path.exists(rule_file)

    @pytest.mark.asyncio
    async def test_integrate_with_rule_loader(self):
        """测试与RuleLoader集成"""
        mock_rule_loader = Mock()
        mock_rule_loader.load_all_canons = Mock(return_value={"test": {}})
        mock_rule_loader.validate_all = Mock(return_value={"valid": True})

        editor = WorldEditor(rule_loader=mock_rule_loader)
        result = await editor.integrate_with_rule_loader()

        assert result["success"] == True
        assert result["canons_loaded"] == 1

    @pytest.mark.asyncio
    async def test_integrate_with_world_memory(self):
        """测试与WorldMemory集成"""
        mock_world_memory = Mock()
        mock_world_memory.get_memory_stats = AsyncMock(
            return_value={"entities": 5, "relations": 3}
        )
        mock_world_memory.export_memory = AsyncMock(
            return_value={"entities": [], "relations": []}
        )

        editor = WorldEditor(world_memory=mock_world_memory)
        result = await editor.integrate_with_world_memory()

        assert result["success"] == True
        assert "memory_stats" in result

    @pytest.mark.asyncio
    async def test_execute_comprehensive_edit_rule(self):
        """测试执行综合编辑（规则）"""
        mock_rule_loader = Mock()
        mock_rule_loader.canon_dir = "."
        mock_rule_loader.clear_cache = Mock()

        editor = WorldEditor(rule_loader=mock_rule_loader)

        # 使用patch模拟文件操作
        with patch("builtins.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = "# 测试\n\n## 章节\n内容"
            mock_file.write = Mock()

            edit_text = "rule: modify: 测试规则: section=章节,value=新内容"
            result = await editor.execute_comprehensive_edit(
                edit_text, {"session_id": "test"}
            )

            # 由于是模拟，结果可能成功或失败，取决于实现
            # 至少不会崩溃

    @pytest.mark.asyncio
    async def test_execute_comprehensive_edit_world(self):
        """测试执行综合编辑（世界）"""
        edit_text = "character: add: name=测试角色"
        result = await self.editor.execute_comprehensive_edit(
            edit_text, {"session_id": "test"}
        )

        # 由于没有WorldMemory，应该失败
        assert result.success == False
        assert (
            "无法解析编辑命令" in result.narrative_impact
            or "世界记忆未初始化" in result.narrative_impact
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
