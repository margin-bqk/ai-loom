"""
Retcon处理

处理追溯性修改（Retcon），管理历史版本和一致性。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json

from ..memory.world_memory import WorldMemory, MemoryEntity
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RetconOperation:
    """Retcon操作"""
    type: str  # "modify_fact", "add_memory", "remove_memory", "alter_timeline"
    target_id: Optional[str]
    changes: Dict[str, Any]
    justification: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetconResult:
    """Retcon结果"""
    success: bool
    operation: RetconOperation
    narrative_impact: str
    consistency_issues: List[str]
    version_created: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class RetconHandler:
    """Retcon处理器"""
    
    def __init__(self, world_memory: Optional[WorldMemory] = None):
        self.world_memory = world_memory
        self.retcon_history: List[RetconResult] = []
        self.version_snapshots: Dict[str, Dict[str, Any]] = {}
        logger.info("RetconHandler initialized")
    
    def parse_retcon_command(self, retcon_text: str) -> Optional[RetconOperation]:
        """解析Retcon命令"""
        # 简单解析：格式为 "操作类型: 目标: 修改内容 (理由)"
        parts = retcon_text.split(':', 2)
        if len(parts) < 3:
            logger.warning(f"Invalid retcon command format: {retcon_text}")
            return None
        
        operation_type = parts[0].strip().lower()
        target = parts[1].strip()
        rest = parts[2].strip()
        
        # 验证操作类型
        valid_operations = ["modify_fact", "add_memory", "remove_memory", "alter_timeline"]
        if operation_type not in valid_operations:
            logger.warning(f"Invalid retcon operation type: {operation_type}")
            return None
        
        # 分离修改内容和理由
        if '(' in rest and ')' in rest:
            change_text = rest[:rest.find('(')].strip()
            justification = rest[rest.find('(')+1:rest.find(')')].strip()
        else:
            change_text = rest
            justification = "玩家请求"
        
        # 解析修改内容
        changes = self._parse_changes(change_text, operation_type)
        
        operation = RetconOperation(
            type=operation_type,
            target_id=self._extract_target_id(target),
            changes=changes,
            justification=justification,
            timestamp=datetime.now(),
            metadata={"raw_text": retcon_text, "target_description": target}
        )
        
        logger.debug(f"Parsed retcon operation: {operation_type} for {target}")
        return operation
    
    def _parse_changes(self, change_text: str, operation_type: str) -> Dict[str, Any]:
        """解析修改内容"""
        changes = {}
        
        if operation_type == "modify_fact":
            # 事实修改: "原内容 -> 新内容"
            if '->' in change_text:
                old, new = change_text.split('->', 1)
                changes["old"] = old.strip()
                changes["new"] = new.strip()
            else:
                changes["new_value"] = change_text
        
        elif operation_type == "add_memory":
            # 添加记忆: "内容"
            changes["content"] = change_text
        
        elif operation_type == "remove_memory":
            # 移除记忆: "理由"
            changes["reason"] = change_text
        
        elif operation_type == "alter_timeline":
            # 修改时间线: "事件: 新时间"
            if ':' in change_text:
                event, new_time = change_text.split(':', 1)
                changes["event"] = event.strip()
                changes["new_time"] = new_time.strip()
            else:
                changes["alteration"] = change_text
        
        return changes
    
    def _extract_target_id(self, target: str) -> Optional[str]:
        """从目标字符串中提取ID"""
        # 查找ID模式 [ID]
        import re
        id_pattern = r'\[(.*?)\]'
        match = re.search(id_pattern, target)
        if match:
            return match.group(1)
        
        return None
    
    async def execute_retcon(self, operation: RetconOperation, session_context: Dict[str, Any]) -> RetconResult:
        """执行Retcon操作"""
        try:
            # 创建版本快照
            version_id = await self._create_snapshot(session_context.get("session_id", "unknown"))
            
            # 执行操作
            handler_name = f"_handle_{operation.type}"
            handler = getattr(self, handler_name, None)
            
            if not handler:
                return RetconResult(
                    success=False,
                    operation=operation,
                    narrative_impact=f"不支持的操作类型: {operation.type}",
                    consistency_issues=[],
                    errors=[f"Unsupported operation type: {operation.type}"]
                )
            
            result = await handler(operation, session_context)
            result.version_created = version_id
            
            # 检查一致性
            consistency_issues = await self._check_consistency(operation, result)
            result.consistency_issues = consistency_issues
            
            self.retcon_history.append(result)
            
            logger.info(f"Executed retcon: {operation.type} - Success: {result.success}")
            if consistency_issues:
                logger.warning(f"Retcon consistency issues: {consistency_issues}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing retcon: {e}")
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="执行Retcon时发生错误",
                consistency_issues=[],
                errors=[str(e)]
            )
    
    async def _handle_modify_fact(self, operation: RetconOperation, session_context: Dict[str, Any]) -> RetconResult:
        """修改事实"""
        if not self.world_memory or not operation.target_id:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="缺少目标ID或世界记忆未初始化",
                consistency_issues=[],
                errors=["Missing target ID or WorldMemory not initialized"]
            )
        
        # 检索实体
        entity = await self.world_memory.retrieve_entity(operation.target_id)
        if not entity:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact=f"未找到实体: {operation.target_id}",
                consistency_issues=[],
                errors=[f"Entity not found: {operation.target_id}"]
            )
        
        # 应用修改
        old_content = str(entity.content)
        new_content = operation.changes.get("new", operation.changes.get("new_value", ""))
        
        # 简化修改：更新实体内容
        updates = {"statement": new_content, "retconned": True, "original": old_content}
        
        updated_entity = await self.world_memory.update_entity(operation.target_id, updates)
        
        if updated_entity:
            return RetconResult(
                success=True,
                operation=operation,
                narrative_impact=f"修改了事实: {old_content[:50]}... -> {new_content[:50]}...",
                consistency_issues=[],
                warnings=["事实修改可能影响叙事一致性"]
            )
        else:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="修改事实失败",
                consistency_issues=[],
                errors=["Failed to update fact entity"]
            )
    
    async def _handle_add_memory(self, operation: RetconOperation, session_context: Dict[str, Any]) -> RetconResult:
        """添加记忆"""
        if not self.world_memory:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="世界记忆未初始化",
                consistency_issues=[],
                errors=["WorldMemory not initialized"]
            )
        
        from ..memory.world_memory import MemoryEntity, MemoryEntityType
        import uuid
        
        memory_id = operation.target_id or str(uuid.uuid4())
        content = operation.changes.get("content", "新增记忆")
        
        # 创建记忆实体
        entity = MemoryEntity(
            id=memory_id,
            session_id=session_context.get("session_id", "unknown"),
            type=MemoryEntityType.FACT,
            content={
                "statement": content,
                "source": "retcon",
                "retconned": True,
                "justification": operation.justification
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        success = await self.world_memory.store_entity(entity)
        
        if success:
            return RetconResult(
                success=True,
                operation=operation,
                narrative_impact=f"添加了追溯性记忆: {content[:50]}...",
                consistency_issues=[],
                warnings=["追溯性添加记忆可能影响时间线一致性"]
            )
        else:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="添加记忆失败",
                consistency_issues=[],
                errors=["Failed to store memory entity"]
            )
    
    async def _handle_remove_memory(self, operation: RetconOperation, session_context: Dict[str, Any]) -> RetconResult:
        """移除记忆"""
        if not self.world_memory or not operation.target_id:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="缺少目标ID或世界记忆未初始化",
                consistency_issues=[],
                errors=["Missing target ID or WorldMemory not initialized"]
            )
        
        # 标记为移除而非实际删除
        entity = await self.world_memory.retrieve_entity(operation.target_id)
        if not entity:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact=f"未找到实体: {operation.target_id}",
                consistency_issues=[],
                errors=[f"Entity not found: {operation.target_id}"]
            )
        
        # 更新实体标记为移除
        updates = {
            "retconned": True,
            "removed": True,
            "removal_reason": operation.changes.get("reason", operation.justification),
            "removed_at": datetime.now().isoformat()
        }
        
        updated_entity = await self.world_memory.update_entity(operation.target_id, updates)
        
        if updated_entity:
            return RetconResult(
                success=True,
                operation=operation,
                narrative_impact=f"移除了记忆: {operation.target_id}",
                consistency_issues=[],
                warnings=["记忆移除可能创建叙事漏洞"]
            )
        else:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="移除记忆失败",
                consistency_issues=[],
                errors=["Failed to update entity for removal"]
            )
    
    async def _handle_alter_timeline(self, operation: RetconOperation, session_context: Dict[str, Any]) -> RetconResult:
        """修改时间线"""
        # 时间线修改是复杂操作，这里简化处理
        event = operation.changes.get("event", "未知事件")
        new_time = operation.changes.get("new_time", "新时间")
        
        return RetconResult(
            success=True,
            operation=operation,
            narrative_impact=f"修改了时间线: {event} -> {new_time}",
            consistency_issues=["时间线修改可能导致严重的不一致性"],
            warnings=["时间线修改是高风险操作，可能破坏叙事连贯性"]
        )
    
    async def _create_snapshot(self, session_id: str) -> str:
        """创建版本快照"""
        version_id = f"retcon_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if self.world_memory:
            snapshot = await self.world_memory.export_memory()
            self.version_snapshots[version_id] = snapshot
            logger.debug(f"Created snapshot: {version_id}")
        else:
            self.version_snapshots[version_id] = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "note": "WorldMemory not available"
            }
        
        return version_id
    
    async def _check_consistency(self, operation: RetconOperation, result: RetconResult) -> List[str]:
        """检查一致性"""
        issues = []
        
        # 检查Retcon的合理性
        if operation.type == "modify_fact":
            if "->" not in operation.metadata.get("raw_text", "") and "new_value" not in operation.changes:
                issues.append("事实修改格式不明确")
        
        if operation.type == "remove_memory":
            if not operation.justification or len(operation.justification) < 5:
                issues.append("移除记忆的理由不充分")
        
        if operation.type == "alter_timeline":
            issues.append("时间线修改需要额外的一致性检查")
        
        # 检查是否创建了矛盾
        if "矛盾" in operation.justification or "冲突" in operation.justification:
            issues.append("Retcon理由表明存在矛盾")
        
        return issues
    
    async def rollback_to_version(self, version_id: str) -> bool:
        """回滚到指定版本"""
        if version_id not in self.version_snapshots:
            logger.error(f"Version not found: {version_id}")
            return False
        
        snapshot = self.version_snapshots[version_id]
        
        if self.world_memory:
            # 清空当前记忆
            self.world_memory.entities.clear()
            self.world_memory.relations.clear()
            
            # 导入快照
            success = await self.world_memory.import_memory(snapshot)
            
            if success:
                logger.info(f"Rolled back to version: {version_id}")
                
                # 记录回滚操作
                rollback_operation = RetconOperation(
                    type="rollback",
                    target_id=None,
                    changes={"version": version_id},
                    justification="系统回滚",
                    timestamp=datetime.now()
                )
                
                rollback_result = RetconResult(
                    success=True,
                    operation=rollback_operation,
                    narrative_impact=f"回滚到版本: {version_id}",
                    consistency_issues=[],
                    version_created=f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                self.retcon_history.append(rollback_result)
                
                return True
            else:
                logger.error(f"Failed to import snapshot: {version_id}")
                return False
        else:
            logger.warning(f"Cannot rollback without WorldMemory")
            return False
    
    def get_retcon_history(self, limit: int = 20) -> List[RetconResult]:
        """获取Retcon历史"""
        return self.retcon_history[-limit:] if self.retcon_history else []
    
    def get_available_versions(self) -> List[Dict[str, Any]]:
        """获取可用版本"""
        versions = []
        
        for version_id, snapshot in self.version_snapshots.items():
            versions.append({
                "id": version_id,
                "timestamp": snapshot.get("timestamp", "unknown"),
                "entity_count": len(snapshot.get("entities", [])),
                "relation_count": len(snapshot.get("relations", []))
            })
        
        return sorted(versions, key=lambda x: x["timestamp"], reverse=True)
    
    async def validate_retcon(self, operation: RetconOperation, rules_text: str) -> Tuple[bool, List[str]]:
        """验证Retcon是否允许"""
        errors = []
        
        # 检查规则限制
        if "禁止Retcon" in rules_text:
            errors.append("规则禁止Retcon")
        
        if "禁止修改历史" in rules_text and operation.type in ["modify_fact", "alter_timeline"]:
            errors.append("规则禁止修改历史")
        
        if "禁止移除记忆" in rules_text and operation.type == "remove_memory":
            errors.append("规则禁止移除记忆")
        
        # 检查理由是否充分
        if len(operation.justification) < 10:
            errors.append("Retcon理由不充分（至少10个字符）")
        
        return len(errors) == 0, errors
    
    # 与ConsistencyChecker集成的方法
    
    async def check_retcon_consistency(self, operation: RetconOperation, consistency_checker, rules_text: str,
                                      memories: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """检查Retcon操作的一致性"""
        if not consistency_checker:
            return {
                "success": False,
                "error": "ConsistencyChecker not provided",
                "consistency_score": 0.0,
                "issues": []
            }
        
        try:
            # 模拟Retcon后的响应
            simulated_response = self._simulate_retcon_effect(operation)
            
            # 检查一致性
            if memories:
                # 使用记忆检查
                result = consistency_checker.check_with_memories(
                    simulated_response,
                    memories,
                    constraints=[]
                )
            else:
                # 使用规则检查
                result = consistency_checker.check(
                    simulated_response,
                    rules_text,
                    constraints=[]
                )
            
            # 分析结果
            issues = result.get("issues", [])
            score = result.get("score", 0.0)
            
            # 提取关键问题
            critical_issues = [issue for issue in issues if issue.get("severity") in ["high", "medium"]]
            
            return {
                "success": True,
                "consistency_score": score,
                "issues_count": len(issues),
                "critical_issues_count": len(critical_issues),
                "issues": issues[:5],  # 限制返回数量
                "simulated_response": simulated_response[:500],  # 限制长度
                "recommendation": self._generate_consistency_recommendation(score, critical_issues)
            }
            
        except Exception as e:
            logger.error(f"Failed to check retcon consistency: {e}")
            return {
                "success": False,
                "error": str(e),
                "consistency_score": 0.0,
                "issues": []
            }
    
    def _simulate_retcon_effect(self, operation: RetconOperation) -> str:
        """模拟Retcon操作的效果"""
        if operation.type == "modify_fact":
            old_content = operation.changes.get("old", "原有事实")
            new_content = operation.changes.get("new", "新事实")
            return f"Retcon操作：将事实从'{old_content}'修改为'{new_content}'。理由：{operation.justification}"
        
        elif operation.type == "add_memory":
            content = operation.changes.get("content", "新记忆")
            return f"Retcon操作：添加新记忆'{content}'。理由：{operation.justification}"
        
        elif operation.type == "remove_memory":
            reason = operation.changes.get("reason", "移除理由")
            return f"Retcon操作：移除记忆。理由：{reason}。原始理由：{operation.justification}"
        
        elif operation.type == "alter_timeline":
            event = operation.changes.get("event", "事件")
            new_time = operation.changes.get("new_time", "新时间")
            return f"Retcon操作：修改时间线，将事件'{event}'的时间调整为'{new_time}'。理由：{operation.justification}"
        
        else:
            return f"Retcon操作：{operation.type} - {operation.justification}"
    
    def _generate_consistency_recommendation(self, score: float, critical_issues: List[Dict[str, Any]]) -> str:
        """生成一致性建议"""
        if score >= 0.8:
            return "Retcon操作一致性良好，可以执行"
        elif score >= 0.6:
            return "Retcon操作存在一些一致性问题，建议调整后执行"
        elif score >= 0.4:
            return "Retcon操作存在较多一致性问题，需要谨慎考虑"
        else:
            return "Retcon操作一致性很差，不建议执行"
    
    async def resolve_retcon_conflicts(self, operation: RetconOperation, conflicts: List[Dict[str, Any]],
                                      world_memory: Optional[WorldMemory] = None) -> Dict[str, Any]:
        """解决Retcon冲突"""
        if not conflicts:
            return {
                "success": True,
                "conflicts_resolved": 0,
                "message": "无冲突需要解决"
            }
        
        resolved_conflicts = []
        unresolved_conflicts = []
        
        for conflict in conflicts:
            conflict_type = conflict.get("type", "unknown")
            
            if conflict_type == "memory_conflict" and world_memory:
                # 尝试解决记忆冲突
                resolution = await self._resolve_memory_conflict(operation, conflict, world_memory)
                if resolution["success"]:
                    resolved_conflicts.append({
                        **conflict,
                        "resolution": resolution
                    })
                else:
                    unresolved_conflicts.append({
                        **conflict,
                        "resolution_failed": True
                    })
            else:
                # 标记为需要手动解决
                unresolved_conflicts.append({
                    **conflict,
                    "requires_manual_resolution": True
                })
        
        return {
            "success": len(unresolved_conflicts) == 0,
            "conflicts_total": len(conflicts),
            "conflicts_resolved": len(resolved_conflicts),
            "conflicts_unresolved": len(unresolved_conflicts),
            "resolved_conflicts": resolved_conflicts,
            "unresolved_conflicts": unresolved_conflicts,
            "recommendation": self._generate_conflict_resolution_recommendation(resolved_conflicts, unresolved_conflicts)
        }
    
    async def _resolve_memory_conflict(self, operation: RetconOperation, conflict: Dict[str, Any],
                                      world_memory: WorldMemory) -> Dict[str, Any]:
        """解决记忆冲突"""
        try:
            # 获取冲突的记忆ID
            memory_id = conflict.get("memory_id")
            if not memory_id:
                return {"success": False, "error": "No memory ID provided"}
            
            # 检索记忆
            memory_entity = await world_memory.retrieve_entity(memory_id)
            if not memory_entity:
                return {"success": False, "error": f"Memory not found: {memory_id}"}
            
            # 根据Retcon类型解决冲突
            if operation.type == "modify_fact":
                # 更新记忆内容
                updates = {
                    "retconned": True,
                    "original_content": memory_entity.content,
                    "retcon_justification": operation.justification,
                    "retcon_operation": operation.type
                }
                
                updated_entity = await world_memory.update_entity(memory_id, updates)
                if updated_entity:
                    return {
                        "success": True,
                        "action": "memory_updated",
                        "memory_id": memory_id,
                        "message": "记忆已更新以解决冲突"
                    }
                else:
                    return {"success": False, "error": "Failed to update memory"}
            
            elif operation.type == "remove_memory":
                # 标记记忆为已移除
                updates = {
                    "removed": True,
                    "removal_reason": operation.justification,
                    "removed_by_retcon": True
                }
                
                updated_entity = await world_memory.update_entity(memory_id, updates)
                if updated_entity:
                    return {
                        "success": True,
                        "action": "memory_marked_removed",
                        "memory_id": memory_id,
                        "message": "记忆已标记为移除"
                    }
                else:
                    return {"success": False, "error": "Failed to mark memory as removed"}
            
            else:
                return {"success": False, "error": f"Unsupported operation type for conflict resolution: {operation.type}"}
                
        except Exception as e:
            logger.error(f"Failed to resolve memory conflict: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_conflict_resolution_recommendation(self, resolved: List[Dict[str, Any]],
                                                    unresolved: List[Dict[str, Any]]) -> str:
        """生成冲突解决建议"""
        if not unresolved:
            return "所有冲突已成功解决"
        
        unresolved_types = {}
        for conflict in unresolved:
            conflict_type = conflict.get("type", "unknown")
            unresolved_types[conflict_type] = unresolved_types.get(conflict_type, 0) + 1
        
        type_summary = ", ".join([f"{k}({v})" for k, v in unresolved_types.items()])
        
        if len(unresolved) == 1:
            return f"有1个{type_summary}冲突需要手动解决"
        else:
            return f"有{len(unresolved)}个冲突需要手动解决（{type_summary}）"
    
    async def execute_retcon_with_consistency_check(self, operation: RetconOperation, session_context: Dict[str, Any],
                                                   consistency_checker, rules_text: str,
                                                   memories: List[Dict[str, Any]] = None) -> RetconResult:
        """执行带一致性检查的Retcon操作"""
        # 检查一致性
        consistency_check = await self.check_retcon_consistency(
            operation, consistency_checker, rules_text, memories
        )
        
        if not consistency_check["success"]:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="Retcon一致性检查失败",
                consistency_issues=["一致性检查失败: " + consistency_check.get("error", "未知错误")],
                errors=[consistency_check.get("error", "一致性检查失败")]
            )
        
        # 检查一致性分数
        consistency_score = consistency_check.get("consistency_score", 0.0)
        critical_issues_count = consistency_check.get("critical_issues_count", 0)
        
        if consistency_score < 0.5 or critical_issues_count > 2:
            return RetconResult(
                success=False,
                operation=operation,
                narrative_impact="Retcon操作一致性太差，拒绝执行",
                consistency_issues=consistency_check.get("issues", []),
                warnings=["Retcon一致性分数过低，建议修改操作"],
                errors=["一致性检查失败: 分数过低"]
            )
        
        # 执行Retcon
        result = await self.execute_retcon(operation, session_context)
        
        # 添加一致性检查信息
        result.consistency_issues.extend([
            f"一致性分数: {consistency_score:.2f}",
            f"关键问题数: {critical_issues_count}"
        ])
        
        # 添加警告（如果一致性不够好）
        if consistency_score < 0.8:
            result.warnings.append(f"Retcon一致性一般（{consistency_score:.2f}），可能影响叙事连贯性")
        
        return result