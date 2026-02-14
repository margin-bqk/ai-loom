# Interactive Example

## 概述

本文档提供 LOOM 交互式叙事功能的完整示例，展示如何处理玩家干预、动态世界修改、实时决策和分支叙事。通过本示例，您将学习如何：

1. 解析和处理玩家干预指令
2. 实现动态世界编辑和 Retcon（追溯修改）
3. 管理分支叙事和多重时间线
4. 处理玩家与叙事的实时交互
5. 创建自适应叙事系统

## 玩家干预系统

### 1. 干预类型解析

基于 `examples/player_intervention_example.py` 的干预系统：

```python
# examples/intervention_parser.py
from enum import Enum
from typing import Dict, List, Optional, Tuple
import re

class InterventionType(Enum):
    """干预类型枚举"""
    OOC = "ooc"               # 戏外注释
    EDIT = "edit"             # 世界编辑
    RETCON = "retcon"         # 追溯修改
    TONE = "tone"             # 基调调整
    INTENT = "intent"         # 意图声明
    META = "meta"             # 元注释
    RULE = "rule"             # 规则修改
    STATE = "state"           # 状态调整

class InterventionPriority(Enum):
    """干预优先级"""
    CRITICAL = 5    # 必须立即处理（如安全、规则冲突）
    HIGH = 4        # 重要叙事影响
    MEDIUM = 3      # 中等影响
    LOW = 2         # 轻微影响
    INFO = 1        # 信息性

class InterventionParser:
    """玩家干预解析器"""

    def __init__(self):
        # 定义干预模式
        self.patterns = {
            InterventionType.OOC: [
                r'\(OOC:\s*(.*?)\)',           # (OOC: 注释)
                r'/ooc\s+(.*)',                # /ooc 注释
                r'\[meta\]\s*(.*)',            # [meta] 注释
                r'//\s*(.*)$'                  # // 注释
            ],
            InterventionType.EDIT: [
                r'\[EDIT:\s*(CREATE|MODIFY|DELETE|STATE):\s*(.*?):\s*(.*?)\]',
                r'\[EDIT:\s*(RULE):\s*(.*?):\s*(.*?)\]'
            ],
            InterventionType.RETCON: [
                r'\[RETCON:\s*(TIMELINE|EVENT|FACT|CONTRADICTION):\s*(.*?):\s*(.*?)\]'
            ],
            InterventionType.TONE: [
                r'\[TONE:\s*(.*?)\]'
            ],
            InterventionType.INTENT: [
                r'\[INTENT:\s*(.*?)\]'
            ]
        }

        # 干预优先级映射
        self.priority_map = {
            InterventionType.RETCON: InterventionPriority.HIGH,
            InterventionType.EDIT: InterventionPriority.MEDIUM,
            InterventionType.RULE: InterventionPriority.CRITICAL,
            InterventionType.OOC: InterventionPriority.LOW,
            InterventionType.TONE: InterventionPriority.MEDIUM,
            InterventionType.INTENT: InterventionPriority.INFO,
            InterventionType.STATE: InterventionPriority.MEDIUM,
            InterventionType.META: InterventionPriority.INFO
        }

    def parse_input(self, player_input: str) -> Dict:
        """
        解析玩家输入，提取干预指令

        Args:
            player_input: 玩家原始输入

        Returns:
            解析结果字典
        """
        result = {
            "original_input": player_input,
            "clean_input": player_input,
            "interventions": [],
            "conflicts": [],
            "has_interventions": False
        }

        # 存储找到的干预
        interventions_found = []

        # 按类型解析
        for interv_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, player_input, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    # 提取干预内容
                    groups = match.groups()
                    content = self._extract_content(interv_type, groups)

                    # 创建干预对象
                    intervention = {
                        "type": interv_type,
                        "priority": self.priority_map[interv_type],
                        "content": content,
                        "raw_match": match.group(0),
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    }

                    interventions_found.append(intervention)

        if interventions_found:
            result["has_interventions"] = True

            # 按位置排序
            interventions_found.sort(key=lambda x: x["start_pos"])

            # 清理原始输入（移除干预标记）
            clean_input = player_input
            for interv in reversed(interventions_found):  # 从后往前移除
                clean_input = (
                    clean_input[:interv["start_pos"]] +
                    clean_input[interv["end_pos"]:]
                )

            result["clean_input"] = clean_input.strip()
            result["interventions"] = interventions_found

            # 检查冲突
            result["conflicts"] = self._check_conflicts(interventions_found)

        return result

    def _extract_content(self, interv_type: InterventionType, groups: Tuple) -> Dict:
        """根据干预类型提取内容"""
        if interv_type == InterventionType.OOC:
            return {"comment": groups[0]}

        elif interv_type == InterventionType.EDIT:
            if len(groups) >= 3:
                return {
                    "edit_type": groups[0].upper(),
                    "target": groups[1],
                    "content": groups[2]
                }

        elif interv_type == InterventionType.RETCON:
            if len(groups) >= 3:
                return {
                    "retcon_type": groups[0].upper(),
                    "target": groups[1],
                    "content": groups[2]
                }

        elif interv_type == InterventionType.TONE:
            return {"tone_description": groups[0]}

        elif interv_type == InterventionType.INTENT:
            return {"intent_description": groups[0]}

        return {"raw_groups": groups}

    def _check_conflicts(self, interventions: List[Dict]) -> List[Dict]:
        """检查干预冲突"""
        conflicts = []

        # 检查编辑和Retcon冲突
        edits = [i for i in interventions if i["type"] in [InterventionType.EDIT, InterventionType.RETCON]]

        for i in range(len(edits)):
            for j in range(i + 1, len(edits)):
                conflict = self._check_specific_conflict(edits[i], edits[j])
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _check_specific_conflict(self, interv1: Dict, interv2: Dict) -> Optional[Dict]:
        """检查特定干预对之间的冲突"""
        # 相同目标的编辑冲突
        if (interv1["type"] == InterventionType.EDIT and
            interv2["type"] == InterventionType.EDIT):
            content1 = interv1["content"]
            content2 = interv2["content"]

            if content1.get("target") == content2.get("target"):
                return {
                    "intervention1": interv1["type"].value,
                    "intervention2": interv2["type"].value,
                    "reason": f"对同一目标'{content1['target']}'的冲突编辑",
                    "target": content1["target"]
                }

        # Retcon与编辑的时间线冲突
        if (interv1["type"] == InterventionType.RETCON and
            interv2["type"] == InterventionType.EDIT):
            return {
                "intervention1": interv1["type"].value,
                "intervention2": interv2["type"].value,
                "reason": "时间线修改与实时编辑可能冲突",
                "suggestion": "先处理Retcon，再应用编辑"
            }

        return None

# 使用示例
if __name__ == "__main__":
    parser = InterventionParser()

    # 测试复杂输入
    test_input = """
    探索黑暗森林(OOC: 森林里有什么危险生物？)
    我需要一把剑[EDIT: CREATE: 物品: 魔法剑]
    我记得之前提到过河流[RETCON: FACT: 河流位置: 东改为西]
    [TONE: 恐怖氛围]
    """

    result = parser.parse_input(test_input)

    print("原始输入:")
    print(test_input)
    print("\n解析结果:")
    print(f"清理后输入: {result['clean_input']}")
    print(f"发现干预: {len(result['interventions'])}个")

    for i, interv in enumerate(result['interventions'], 1):
        print(f"\n干预{i}:")
        print(f"  类型: {interv['type'].value}")
        print(f"  优先级: {interv['priority'].value}")
        print(f"  内容: {interv['content']}")

    if result['conflicts']:
        print(f"\n发现冲突: {len(result['conflicts'])}个")
        for conflict in result['conflicts']:
            print(f"  {conflict['intervention1']} vs {conflict['intervention2']}: {conflict['reason']}")
```

### 2. 干预处理器

```python
# examples/intervention_handler.py
import asyncio
from typing import Dict, List, Any
from datetime import datetime

class InterventionHandler:
    """干预处理器"""

    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.parser = InterventionParser()

        # 注册处理函数
        self.handlers = {
            InterventionType.OOC: self._handle_ooc,
            InterventionType.EDIT: self._handle_edit,
            InterventionType.RETCON: self._handle_retcon,
            InterventionType.TONE: self._handle_tone,
            InterventionType.INTENT: self._handle_intent,
            InterventionType.RULE: self._handle_rule,
            InterventionType.STATE: self._handle_state,
            InterventionType.META: self._handle_meta
        }

    async def process_player_input(self,
                                  session_id: str,
                                  player_input: str,
                                  context: Dict[str, Any] = None) -> Dict:
        """
        处理玩家输入，包括干预

        Args:
            session_id: 会话ID
            player_input: 玩家输入
            context: 上下文信息

        Returns:
            处理结果
        """
        # 解析输入
        parsed = self.parser.parse_input(player_input)

        # 加载会话
        session = await self.session_manager.load_session(session_id)

        # 处理干预
        intervention_results = []
        if parsed["has_interventions"]:
            intervention_results = await self._process_interventions(
                session, parsed["interventions"], context
            )

        # 合并到最终提示
        final_prompt = self._merge_interventions_into_prompt(
            parsed["clean_input"], intervention_results
        )

        # 添加回合
        turn = await session.add_turn(final_prompt)

        # 保存会话
        await self.session_manager.save_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "turn_id": turn.turn_id,
            "original_input": player_input,
            "clean_input": parsed["clean_input"],
            "interventions_parsed": len(parsed["interventions"]),
            "interventions_processed": len(intervention_results),
            "final_response": turn.response,
            "intervention_details": intervention_results
        }

    async def _process_interventions(self,
                                    session,
                                    interventions: List[Dict],
                                    context: Dict) -> List[Dict]:
        """处理干预列表"""
        results = []

        # 按优先级排序
        sorted_interventions = sorted(
            interventions,
            key=lambda x: x["priority"].value,
            reverse=True
        )

        for intervention in sorted_interventions:
            try:
                # 获取处理函数
                handler = self.handlers.get(intervention["type"])
                if not handler:
                    results.append({
                        "intervention": intervention,
                        "success": False,
                        "error": f"未找到处理函数: {intervention['type']}",
                        "narrative_impact": "无"
                    })
                    continue

                # 执行处理
                result = await handler(session, intervention, context)

                results.append({
                    "intervention": intervention,
                    "success": True,
                    "result": result,
                    "narrative_impact": result.get("narrative_impact", "已处理"),
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                results.append({
                    "intervention": intervention,
                    "success": False,
                    "error": str(e),
                    "narrative_impact": "处理失败",
                    "timestamp": datetime.now().isoformat()
                })

        return results

    async def _handle_ooc(self, session, intervention: Dict, context: Dict) -> Dict:
        """处理OOC注释"""
        content = intervention["content"]
        comment = content.get("comment", "")

        # 记录OOC注释
        if "ooc_comments" not in session.metadata:
            session.metadata["ooc_comments"] = []

        session.metadata["ooc_comments"].append({
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
            "turn_context": context.get("turn_context", "")
        })

        # 分类OOC
        ooc_type = self._categorize_ooc(comment)

        return {
            "action": "recorded_ooc",
            "comment": comment,
            "category": ooc_type,
            "narrative_impact": "记录玩家意图，可能影响后续叙事"
        }

    async def _handle_edit(self, session, intervention: Dict, context: Dict) -> Dict:
        """处理世界编辑"""
        content = intervention["content"]
        edit_type = content.get("edit_type")
        target = content.get("target")
        edit_content = content.get("content")

        # 验证编辑权限
        if not self._check_edit_permission(session, edit_type, target, context):
            return {
                "action": "edit_rejected",
                "reason": "权限不足",
                "narrative_impact": "编辑被拒绝"
            }

        # 执行编辑
        if edit_type == "CREATE":
            result = await self._execute_create(session, target, edit_content)
        elif edit_type == "MODIFY":
            result = await self._execute_modify(session, target, edit_content)
        elif edit_type == "DELETE":
            result = await self._execute_delete(session, target, edit_content)
        elif edit_type == "STATE":
            result = await self._execute_state(session, target, edit_content)
        elif edit_type == "RULE":
            result = await self._execute_rule(session, target, edit_content)
        else:
            result = {"error": f"未知编辑类型: {edit_type}"}

        # 记录编辑历史
        self._record_edit_history(session, intervention, result)

        return {
            "action": f"edit_{edit_type.lower()}",
            "target": target,
            "content": edit_content,
            "result": result,
            "narrative_impact": f"修改了{target}: {edit_content}"
        }

    async def _handle_retcon(self, session, intervention: Dict, context: Dict) -> Dict:
        """处理Retcon"""
        content = intervention["content"]
        retcon_type = content.get("retcon_type")
        target = content.get("target")
        retcon_content = content.get("content")

        # 验证Retcon权限（通常比编辑更严格）
        if not self._check_retcon_permission(session, retcon_type, target, context):
            return {
                "action": "retcon_rejected",
                "reason": "Retcon权限不足",
                "narrative_impact": "时间线修改被拒绝"
            }

        # 执行Retcon
        if retcon_type == "TIMELINE":
            result = await self._execute_timeline_retcon(session, target, retcon_content)
        elif retcon_type == "EVENT":
            result = await self._execute_event_retcon(session, target, retcon_content)
        elif retcon_type == "FACT":
            result = await self._execute_fact_retcon(session, target, retcon_content)
        elif retcon_type == "CONTRADICTION":
            result = await self._execute_contradiction_retcon(session, target, retcon_content)
        else:
            result = {"error": f"未知Retcon类型: {retcon_type}"}

        # 记录Retcon历史
        self._record_retcon_history(session, intervention, result)

        return {
            "action": f"retcon_{retcon_type.lower()}",
            "target": target,
            "content": retcon_content,
            "result": result,
            "narrative_impact": f"追溯修改了{target}: {retcon_content}"
        }

    async def _handle_tone(self, session, intervention: Dict, context: Dict) -> Dict:
        """处理基调调整"""
        content = intervention["content"]
        tone_description = content.get("tone_description", "")

        # 更新会话基调
        if "tone_settings" not in session.metadata:
            session.metadata["tone_settings"] = {}

        # 解析基调描述
        tone_elements = self._parse_tone_description(tone_description)
        session.metadata["tone_settings"].update(tone_elements)

        return {
            "action": "tone_adjusted",
            "tone_description": tone_description,
            "tone_elements": tone_elements,
            "narrative_impact": f"调整叙事基调为: {tone_description}"
        }

    async def _handle_intent(self, session, intervention: Dict, context: Dict) -> Dict:
        """处理意图声明"""
