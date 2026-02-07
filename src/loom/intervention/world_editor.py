"""
世界编辑器

处理玩家对世界状态的直接编辑。
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import os
from pathlib import Path

from ..memory.world_memory import WorldMemory, MemoryEntity, MemoryEntityType
from ..rules.rule_loader import RuleLoader
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EditCommand:
    """编辑命令"""

    target_type: str  # "entity", "property", "relation", "rule"
    target_id: Optional[str]  # 目标ID
    action: str  # "add", "update", "delete", "modify"
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EditResult:
    """编辑结果"""

    success: bool
    command: EditCommand
    changes_made: List[Dict[str, Any]]
    narrative_impact: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class WorldEditor:
    """世界编辑器"""

    def __init__(
        self,
        world_memory: Optional[WorldMemory] = None,
        rule_loader: Optional[RuleLoader] = None,
    ):
        self.world_memory = world_memory
        self.rule_loader = rule_loader
        self.edit_history: List[EditResult] = []
        logger.info("WorldEditor initialized")

    def parse_edit_command(self, edit_text: str) -> Optional[EditCommand]:
        """解析编辑命令文本"""
        # 简单解析：格式为 "目标: 动作: 参数"
        parts = edit_text.split(":", 2)
        if len(parts) < 3:
            logger.warning(f"Invalid edit command format: {edit_text}")
            return None

        target = parts[0].strip()
        action = parts[1].strip()
        param_text = parts[2].strip()

        # 解析参数
        parameters = self._parse_parameters(param_text)

        # 确定目标类型
        target_type = self._infer_target_type(target)

        # 从参数文本中提取目标ID
        target_id = self._extract_target_id(param_text)

        command = EditCommand(
            target_type=target_type,
            target_id=target_id,
            action=action,
            parameters=parameters,
            metadata={"raw_text": edit_text},
        )

        logger.debug(
            f"Parsed edit command: {target_type}.{action}, target_id: {target_id}"
        )
        return command

    def _parse_parameters(self, param_text: str) -> Dict[str, Any]:
        """解析参数文本"""
        parameters = {}

        # 首先提取ID（如果存在）
        id_pattern = r"\[(.*?)\]"
        import re

        id_match = re.search(id_pattern, param_text)
        if id_match:
            # 从参数文本中移除ID部分
            id_part = id_match.group(0)
            param_text_without_id = param_text.replace(id_part, "").strip()

            # 如果ID后面有冒号，移除它
            if param_text_without_id.startswith(":"):
                param_text_without_id = param_text_without_id[1:].strip()
        else:
            param_text_without_id = param_text

        # 简单键值对解析
        # 格式: key1=value1, key2=value2
        pairs = param_text_without_id.split(",")
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                parameters[key.strip()] = value.strip()

        # 如果没有明确的键值对，将整个文本作为"value"参数
        if not parameters and param_text_without_id:
            parameters["value"] = param_text_without_id

        return parameters

    def _infer_target_type(self, target: str) -> str:
        """推断目标类型"""
        target_lower = target.lower()

        if any(word in target_lower for word in ["角色", "人物", "character"]):
            return "character"
        elif any(word in target_lower for word in ["地点", "位置", "location"]):
            return "location"
        elif any(word in target_lower for word in ["事实", "信息", "fact"]):
            return "fact"
        elif any(word in target_lower for word in ["关系", "关联", "relation"]):
            return "relation"
        elif any(word in target_lower for word in ["规则", "设定", "rule"]):
            return "rule"
        else:
            return "entity"

    def _extract_target_id(self, target: str) -> Optional[str]:
        """从目标字符串中提取ID"""
        # 查找ID模式
        id_pattern = r"\[(.*?)\]"
        match = re.search(id_pattern, target)
        if match:
            return match.group(1)

        # 如果没有明确ID，返回None
        return None

    async def execute_edit(
        self, command: EditCommand, session_context: Dict[str, Any]
    ) -> EditResult:
        """执行编辑命令"""
        try:
            handler_name = f"_handle_{command.target_type}_{command.action}"
            handler = getattr(self, handler_name, None)

            if not handler:
                return EditResult(
                    success=False,
                    command=command,
                    changes_made=[],
                    narrative_impact=f"不支持的操作: {command.target_type}.{command.action}",
                    errors=[
                        f"Unsupported operation: {command.target_type}.{command.action}"
                    ],
                )

            result = await handler(command, session_context)
            self.edit_history.append(result)

            logger.info(
                f"Executed edit: {command.target_type}.{command.action} - Success: {result.success}"
            )

            return result

        except Exception as e:
            logger.error(f"Error executing edit command: {e}")
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="执行编辑时发生错误",
                errors=[str(e)],
            )

    async def _handle_character_add(
        self, command: EditCommand, session_context: Dict[str, Any]
    ) -> EditResult:
        """添加角色"""
        if not self.world_memory:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="世界记忆未初始化",
                errors=["WorldMemory not initialized"],
            )

        # 创建角色实体
        from ..memory.world_memory import MemoryEntity, MemoryEntityType
        import uuid
        from datetime import datetime

        character_id = command.target_id or str(uuid.uuid4())
        character_name = command.parameters.get("name", f"角色_{character_id[:8]}")

        entity = MemoryEntity(
            id=character_id,
            session_id=session_context.get("session_id", "unknown"),
            type=MemoryEntityType.CHARACTER,
            content={
                "name": character_name,
                "description": command.parameters.get("description", ""),
                "attributes": self._parse_attributes(command.parameters),
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 存储实体
        success = await self.world_memory.store_entity(entity)

        if success:
            return EditResult(
                success=True,
                command=command,
                changes_made=[
                    {
                        "action": "add_character",
                        "entity_id": character_id,
                        "name": character_name,
                    }
                ],
                narrative_impact=f"添加了新角色: {character_name}",
                warnings=["角色已添加，但需要进一步描述以融入叙事"],
            )
        else:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="添加角色失败",
                errors=["Failed to store character entity"],
            )

    async def _handle_character_update(
        self, command: EditCommand, session_context: Dict[str, Any]
    ) -> EditResult:
        """更新角色"""
        if not self.world_memory or not command.target_id:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="缺少目标ID或世界记忆未初始化",
                errors=["Missing target ID or WorldMemory not initialized"],
            )

        # 检索现有实体
        entity = await self.world_memory.retrieve_entity(command.target_id)
        if not entity or entity.type != MemoryEntityType.CHARACTER:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact=f"未找到角色实体: {command.target_id}",
                errors=[f"Character entity not found: {command.target_id}"],
            )

        # 准备更新
        updates = {}
        if "name" in command.parameters:
            updates["name"] = command.parameters["name"]
        if "description" in command.parameters:
            updates["description"] = command.parameters["description"]

        # 更新实体
        updated_entity = await self.world_memory.update_entity(
            command.target_id, updates
        )

        if updated_entity:
            return EditResult(
                success=True,
                command=command,
                changes_made=[
                    {
                        "action": "update_character",
                        "entity_id": command.target_id,
                        "updates": updates,
                    }
                ],
                narrative_impact=f"更新了角色: {command.parameters.get('name', command.target_id)}",
                warnings=["角色更新可能影响叙事一致性"],
            )
        else:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="更新角色失败",
                errors=["Failed to update character entity"],
            )

    async def _handle_fact_add(
        self, command: EditCommand, session_context: Dict[str, Any]
    ) -> EditResult:
        """添加事实"""
        if not self.world_memory:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="世界记忆未初始化",
                errors=["WorldMemory not initialized"],
            )

        from ..memory.world_memory import MemoryEntity, MemoryEntityType
        import uuid
        from datetime import datetime

        fact_id = command.target_id or str(uuid.uuid4())
        fact_content = command.parameters.get(
            "value", command.parameters.get("content", "新事实")
        )

        entity = MemoryEntity(
            id=fact_id,
            session_id=session_context.get("session_id", "unknown"),
            type=MemoryEntityType.FACT,
            content={
                "statement": fact_content,
                "source": "player_edit",
                "certainty": float(command.parameters.get("certainty", 1.0)),
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        success = await self.world_memory.store_entity(entity)

        if success:
            return EditResult(
                success=True,
                command=command,
                changes_made=[
                    {
                        "action": "add_fact",
                        "entity_id": fact_id,
                        "content": fact_content,
                    }
                ],
                narrative_impact=f"添加了新事实: {fact_content[:50]}...",
                warnings=["直接添加事实可能影响叙事一致性"],
            )
        else:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="添加事实失败",
                errors=["Failed to store fact entity"],
            )

    async def _handle_relation_add(
        self, command: EditCommand, session_context: Dict[str, Any]
    ) -> EditResult:
        """添加关系"""
        if not self.world_memory:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="世界记忆未初始化",
                errors=["WorldMemory not initialized"],
            )

        from ..memory.world_memory import MemoryRelation, MemoryRelationType

        source_id = command.parameters.get("source")
        target_id = command.parameters.get("target")
        relation_type_str = command.parameters.get("type", "related_to")

        if not source_id or not target_id:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="缺少源或目标实体ID",
                errors=["Missing source or target entity ID"],
            )

        try:
            relation_type = MemoryRelationType(relation_type_str)
        except ValueError:
            relation_type = MemoryRelationType.RELATED_TO

        relation = MemoryRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=float(command.parameters.get("strength", 1.0)),
        )

        success = await self.world_memory.add_relation(relation)

        if success:
            return EditResult(
                success=True,
                command=command,
                changes_made=[
                    {
                        "action": "add_relation",
                        "source": source_id,
                        "target": target_id,
                        "type": relation_type.value,
                    }
                ],
                narrative_impact=f"添加了关系: {source_id} -> {target_id} ({relation_type.value})",
            )
        else:
            return EditResult(
                success=False,
                command=command,
                changes_made=[],
                narrative_impact="添加关系失败",
                errors=["Failed to add relation"],
            )

    def _parse_attributes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """解析属性"""
        attributes = {}

        for key, value in parameters.items():
            if key.startswith("attr_"):
                attr_name = key[5:]  # 移除"attr_"前缀
                attributes[attr_name] = value

        return attributes

    async def validate_edit(
        self, command: EditCommand, rules_text: str
    ) -> Tuple[bool, List[str]]:
        """验证编辑是否允许"""
        errors = []

        # 检查规则限制
        if "禁止编辑" in rules_text and command.action in ["add", "update", "delete"]:
            errors.append("规则禁止编辑")

        if (
            "禁止添加角色" in rules_text
            and command.target_type == "character"
            and command.action == "add"
        ):
            errors.append("规则禁止添加角色")

        if (
            "禁止修改事实" in rules_text
            and command.target_type == "fact"
            and command.action == "update"
        ):
            errors.append("规则禁止修改事实")

        return len(errors) == 0, errors

    def get_edit_history(self, limit: int = 20) -> List[EditResult]:
        """获取编辑历史"""
        return self.edit_history[-limit:] if self.edit_history else []

    async def undo_last_edit(self) -> Optional[EditResult]:
        """撤销最后一次编辑"""
        if not self.edit_history:
            return None

        last_edit = self.edit_history[-1]
        # 简化实现：记录撤销操作
        undo_result = EditResult(
            success=True,
            command=last_edit.command,
            changes_made=[
                {
                    "action": "undo",
                    "original_edit": last_edit.command.metadata.get("raw_text", ""),
                }
            ],
            narrative_impact="撤销了最后一次编辑",
            warnings=["撤销操作可能不完全恢复原始状态"],
        )

        self.edit_history.append(undo_result)
        logger.info(
            f"Undid last edit: {last_edit.command.target_type}.{last_edit.command.action}"
        )

        return undo_result

    # 规则修改方法

    async def modify_rule(
        self,
        rule_path: str,
        section: str,
        new_content: str,
        justification: str = "玩家编辑",
    ) -> EditResult:
        """修改规则文件"""
        if not self.rule_loader:
            return EditResult(
                success=False,
                command=EditCommand(
                    target_type="rule",
                    target_id=rule_path,
                    action="modify",
                    parameters={"section": section, "new_content": new_content},
                ),
                changes_made=[],
                narrative_impact="规则加载器未初始化",
                errors=["RuleLoader not initialized"],
            )

        try:
            # 构建规则文件路径
            canon_dir = Path(self.rule_loader.canon_dir)
            rule_file = canon_dir / f"{rule_path}.md"

            if not rule_file.exists():
                # 尝试直接使用路径
                rule_file = Path(rule_path)
                if not rule_file.exists():
                    return EditResult(
                        success=False,
                        command=EditCommand(
                            target_type="rule",
                            target_id=rule_path,
                            action="modify",
                            parameters={"section": section, "new_content": new_content},
                        ),
                        changes_made=[],
                        narrative_impact=f"规则文件不存在: {rule_path}",
                        errors=[f"Rule file not found: {rule_path}"],
                    )

            # 读取现有内容
            with open(rule_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 备份原始内容
            backup_content = content

            # 修改指定章节
            # 简单实现：查找章节标题并替换内容
            section_pattern = rf"^#+\s*{section}\s*$"
            import re

            lines = content.split("\n")
            modified = False

            for i, line in enumerate(lines):
                if re.match(section_pattern, line, re.IGNORECASE):
                    # 找到章节，替换从下一行到下一个章节标题之间的内容
                    j = i + 1
                    while j < len(lines) and not re.match(r"^#+\s*\w", lines[j]):
                        j += 1

                    # 替换内容
                    new_section_content = f"{line}\n\n{new_content}\n"
                    lines[i:j] = [new_section_content]
                    modified = True
                    break

            if not modified:
                # 如果章节不存在，添加到文件末尾
                lines.append(f"\n\n## {section}\n\n{new_content}")

            new_content_full = "\n".join(lines)

            # 写入文件
            with open(rule_file, "w", encoding="utf-8") as f:
                f.write(new_content_full)

            # 清除规则加载器缓存
            self.rule_loader.clear_cache(rule_path)

            # 创建编辑命令
            command = EditCommand(
                target_type="rule",
                target_id=rule_path,
                action="modify",
                parameters={
                    "section": section,
                    "new_content": new_content,
                    "justification": justification,
                },
                metadata={
                    "rule_file": str(rule_file),
                    "backup_size": len(backup_content),
                    "new_size": len(new_content_full),
                },
            )

            result = EditResult(
                success=True,
                command=command,
                changes_made=[
                    {
                        "action": "modify_rule",
                        "rule_path": rule_path,
                        "section": section,
                        "content_length": len(new_content),
                        "backup_created": True,
                    }
                ],
                narrative_impact=f"修改了规则 {rule_path} 的章节 '{section}'",
                warnings=["规则修改可能需要重新加载才能生效"],
            )

            self.edit_history.append(result)
            logger.info(f"Modified rule {rule_path}, section '{section}'")

            return result

        except Exception as e:
            logger.error(f"Failed to modify rule: {e}")
            return EditResult(
                success=False,
                command=EditCommand(
                    target_type="rule",
                    target_id=rule_path,
                    action="modify",
                    parameters={"section": section, "new_content": new_content},
                ),
                changes_made=[],
                narrative_impact="修改规则时发生错误",
                errors=[str(e)],
            )

    async def create_rule(
        self, rule_path: str, content: str, justification: str = "玩家创建"
    ) -> EditResult:
        """创建新规则文件"""
        if not self.rule_loader:
            return EditResult(
                success=False,
                command=EditCommand(
                    target_type="rule",
                    target_id=rule_path,
                    action="create",
                    parameters={"content": content},
                ),
                changes_made=[],
                narrative_impact="规则加载器未初始化",
                errors=["RuleLoader not initialized"],
            )

        try:
            canon_dir = Path(self.rule_loader.canon_dir)
            rule_file = canon_dir / f"{rule_path}.md"

            if rule_file.exists():
                return EditResult(
                    success=False,
                    command=EditCommand(
                        target_type="rule",
                        target_id=rule_path,
                        action="create",
                        parameters={"content": content},
                    ),
                    changes_made=[],
                    narrative_impact=f"规则文件已存在: {rule_path}",
                    errors=[f"Rule file already exists: {rule_path}"],
                )

            # 确保目录存在
            rule_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(rule_file, "w", encoding="utf-8") as f:
                f.write(content)

            # 创建编辑命令
            command = EditCommand(
                target_type="rule",
                target_id=rule_path,
                action="create",
                parameters={"content": content, "justification": justification},
                metadata={"rule_file": str(rule_file), "file_size": len(content)},
            )

            result = EditResult(
                success=True,
                command=command,
                changes_made=[
                    {
                        "action": "create_rule",
                        "rule_path": rule_path,
                        "content_length": len(content),
                    }
                ],
                narrative_impact=f"创建了新规则文件: {rule_path}",
                warnings=["新规则需要验证和集成"],
            )

            self.edit_history.append(result)
            logger.info(f"Created rule file {rule_path}")

            return result

        except Exception as e:
            logger.error(f"Failed to create rule: {e}")
            return EditResult(
                success=False,
                command=EditCommand(
                    target_type="rule",
                    target_id=rule_path,
                    action="create",
                    parameters={"content": content},
                ),
                changes_made=[],
                narrative_impact="创建规则时发生错误",
                errors=[str(e)],
            )

    async def integrate_with_rule_loader(
        self, rule_loader: Optional[RuleLoader] = None
    ) -> Dict[str, Any]:
        """与RuleLoader集成"""
        loader = rule_loader or self.rule_loader
        if not loader:
            return {"success": False, "error": "RuleLoader not available"}

        try:
            # 重新加载所有规则以应用修改
            canons = loader.load_all_canons()

            # 验证所有规则
            validation_results = loader.validate_all()

            return {
                "success": True,
                "canons_loaded": len(canons),
                "validation_results": validation_results,
                "cache_cleared": True,
            }

        except Exception as e:
            logger.error(f"Failed to integrate with RuleLoader: {e}")
            return {"success": False, "error": str(e)}

    async def integrate_with_world_memory(
        self, world_memory: Optional[WorldMemory] = None
    ) -> Dict[str, Any]:
        """与WorldMemory集成"""
        memory = world_memory or self.world_memory
        if not memory:
            return {"success": False, "error": "WorldMemory not available"}

        try:
            # 获取记忆统计
            stats = await memory.get_memory_stats()

            # 导出记忆（用于备份）
            export_data = await memory.export_memory()

            return {
                "success": True,
                "memory_stats": stats,
                "entities_count": len(export_data.get("entities", [])),
                "relations_count": len(export_data.get("relations", [])),
                "export_available": True,
            }

        except Exception as e:
            logger.error(f"Failed to integrate with WorldMemory: {e}")
            return {"success": False, "error": str(e)}

    async def execute_comprehensive_edit(
        self, edit_text: str, session_context: Dict[str, Any]
    ) -> EditResult:
        """执行综合编辑（支持规则和世界编辑）"""
        # 解析编辑命令
        command = self.parse_edit_command(edit_text)
        if not command:
            return EditResult(
                success=False,
                command=EditCommand(
                    target_type="unknown",
                    target_id=None,
                    action="parse",
                    parameters={"raw_text": edit_text},
                ),
                changes_made=[],
                narrative_impact="无法解析编辑命令",
                errors=["Failed to parse edit command"],
            )

        # 根据目标类型执行
        if command.target_type == "rule":
            # 规则编辑
            section = command.parameters.get("section", "general")
            content = command.parameters.get(
                "value", command.parameters.get("content", "")
            )

            if command.action == "modify":
                return await self.modify_rule(
                    command.target_id or "default", section, content, "玩家编辑"
                )
            elif command.action == "create":
                return await self.create_rule(
                    command.target_id or "new_rule", content, "玩家创建"
                )
            else:
                return EditResult(
                    success=False,
                    command=command,
                    changes_made=[],
                    narrative_impact=f"不支持的规则操作: {command.action}",
                    errors=[f"Unsupported rule operation: {command.action}"],
                )
        else:
            # 世界编辑（使用现有方法）
            return await self.execute_edit(command, session_context)
