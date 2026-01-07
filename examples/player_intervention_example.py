"""
玩家干预接口使用示例
展示如何使用LOOM项目的玩家干预层
"""

import asyncio
from src.loom.intervention.player_intervention import PlayerIntervention
from src.loom.intervention.ooc_handler import OOCHandler
from src.loom.intervention.world_editor import WorldEditor
from src.loom.intervention.retcon_handler import RetconHandler


async def example_player_intervention():
    """示例：玩家干预处理"""
    print("=== 玩家干预接口示例 ===\n")
    
    # 初始化组件
    player_intervention = PlayerIntervention()
    ooc_handler = OOCHandler()
    world_editor = WorldEditor()
    retcon_handler = RetconHandler()
    
    # 示例1：包含多种干预的玩家输入
    player_input = """
    探索黑暗森林(OOC: 森林里有什么危险生物？)
    我需要一把剑[EDIT: CREATE: 物品: 魔法剑]
    我记得之前提到过河流[RETCON: FACT: 河流位置: 东改为西]
    [TONE: 恐怖氛围]
    """
    
    print("示例1：解析包含多种干预的玩家输入")
    print(f"玩家输入: {player_input}")
    
    # 解析干预
    parsed = player_intervention.parse_input(player_input)
    print(f"发现干预数量: {len(parsed['interventions'])}")
    print(f"清理后的叙事文本: {parsed['clean_input']}")
    
    for i, interv in enumerate(parsed['interventions'], 1):
        print(f"  干预{i}: {interv.type.value} - {interv.content[:30]}...")
    
    # 示例2：处理OOC注释
    print("\n示例2：处理OOC注释")
    ooc_text = "攻击敌人(OOC: 我想用魔法攻击) /ooc 敌人弱点是什么？"
    ooc_result = ooc_handler.extract_ooc(ooc_text)
    print(f"OOC注释数量: {len(ooc_result.ooc_comments)}")
    for comment in ooc_result.ooc_comments:
        print(f"  OOC: {comment.content}")
    
    # 分类OOC
    categories = ooc_handler.categorize_ooc(ooc_result.ooc_comments)
    print("OOC分类:")
    for category, comments in categories.items():
        if comments:
            print(f"  {category}: {len(comments)}条")
    
    # 示例3：世界编辑
    print("\n示例3：世界编辑")
    edit_text = "[EDIT: CREATE: 角色: 勇敢的骑士][EDIT: STATE: 天气: 晴朗]"
    edit_commands = world_editor.parse_edit_command(edit_text)
    print(f"编辑命令数量: {len(edit_commands)}")
    for cmd in edit_commands:
        print(f"  编辑: {cmd.edit_type.name} - {cmd.target}: {cmd.content}")
    
    # 示例4：Retcon处理
    print("\n示例4：Retcon处理")
    retcon_text = "[RETCON: TIMELINE: 事件顺序调整][RETCON: FACT: 角色年龄: 25改为30]"
    retcon_ops = retcon_handler.parse_retcon(retcon_text)
    print(f"Retcon操作数量: {len(retcon_ops)}")
    for op in retcon_ops:
        print(f"  Retcon: {op.retcon_type.name} - {op.target}: {op.content}")
    
    # 示例5：完整干预处理流程
    print("\n示例5：完整干预处理流程")
    simple_input = "打开宝箱(OOC: 宝箱里有什么？)[EDIT: CREATE: 物品: 金币]"
    
    # 解析
    parsed = player_intervention.parse_input(simple_input)
    
    # 处理干预
    session_context = {"session_id": "example_session", "user_id": "player1"}
    intervention_results = await player_intervention.process_interventions(
        parsed["interventions"], session_context
    )
    
    print(f"处理结果:")
    for result in intervention_results:
        status = "成功" if result.success else "失败"
        print(f"  {result.intervention.type.value}: {status} - {result.narrative_impact}")
    
    # 合并到Prompt
    final_prompt = player_intervention.merge_interventions_into_prompt(
        parsed["clean_input"], intervention_results
    )
    print(f"\n最终Prompt:\n{final_prompt}")
    
    # 示例6：干预优先级
    print("\n示例6：干预优先级排序")
    interventions = parsed["interventions"]
    prioritized = player_intervention.prioritize_interventions(interventions)
    print("按优先级排序:")
    for i, interv in enumerate(prioritized, 1):
        print(f"  {i}. {interv.type.value} (优先级: {interv.priority.name}, 紧急度: {interv.urgency})")
    
    # 示例7：冲突检测
    print("\n示例7：冲突检测")
    conflict_input = "[EDIT: RULE: 核心规则: 修改][RETCON: TIMELINE: 关键事件: 调整]"
    conflict_parsed = player_intervention.parse_input(conflict_input)
    
    if conflict_parsed["conflicts"]:
        print("检测到冲突:")
        for conflict in conflict_parsed["conflicts"]:
            print(f"  {conflict['intervention1']} 与 {conflict['intervention2']}: {conflict['reason']}")
    else:
        print("无冲突")
    
    print("\n=== 示例结束 ===")


async def example_integration():
    """示例：干预层与其他组件集成"""
    print("\n=== 干预层集成示例 ===\n")
    
    # 模拟组件
    class MockSessionManager:
        async def load_session(self, session_id):
            return MockSession()
        
        async def save_session(self, session, force=False):
            return True
    
    class MockSession:
        def __init__(self):
            self.state = {"interventions": []}
            self.metadata = {}
    
    class MockTurnScheduler:
        async def get_turn(self, turn_id):
            return MockTurn()
    
    class MockTurn:
        def __init__(self):
            self.interventions = []
            self.priority = 0
    
    # 初始化
    player_intervention = PlayerIntervention()
    mock_session_manager = MockSessionManager()
    mock_turn_scheduler = MockTurnScheduler()
    
    # 集成示例
    player_input = "探索洞穴(OOC: 洞穴里安全吗？)[EDIT: CREATE: 物品: 火把]"
    
    result = await player_intervention.process_player_input_with_integration(
        player_input,
        mock_session_manager,
        "test_session",
        mock_turn_scheduler,
        "test_turn"
    )
    
    print(f"集成处理结果:")
    print(f"  成功: {result['success']}")
    print(f"  有干预: {result['has_interventions']}")
    print(f"  干预数量: {result['interventions_parsed']}")
    print(f"  会话集成: {result['session_integration']['success']}")
    print(f"  回合集成: {result['turn_integration']['success']}")
    
    print("\n=== 集成示例结束 ===")


def usage_guidelines():
    """使用指南"""
    print("\n=== 玩家干预接口使用指南 ===\n")
    
    print("1. OOC注释格式:")
    print("   - 括号格式: (OOC: 你的注释)")
    print("   - 斜杠格式: /ooc 你的注释")
    print("   - Meta格式: [meta] 你的注释")
    
    print("\n2. 世界编辑格式:")
    print("   - 规则修改: [EDIT: RULE: 规则名: 新内容]")
    print("   - 实体创建: [EDIT: CREATE: 实体类型: 实体描述]")
    print("   - 实体修改: [EDIT: MODIFY: 实体类型: 实体名: 新属性]")
    print("   - 实体删除: [EDIT: DELETE: 实体类型: 实体名]")
    print("   - 状态调整: [EDIT: STATE: 状态名: 新值]")
    
    print("\n3. Retcon格式:")
    print("   - 时间线调整: [RETCON: TIMELINE: 调整描述]")
    print("   - 事件修改: [RETCON: EVENT: 事件名: 新描述]")
    print("   - 矛盾解决: [RETCON: CONTRADICTION: 矛盾描述: 解决方案]")
    print("   - 事实修正: [RETCON: FACT: 事实名: 新值]")
    
    print("\n4. 其他干预格式:")
    print("   - 基调调整: [TONE: 基调描述]")
    print("   - 意图声明: [INTENT: 意图描述]")
    print("   - 元注释: [META: 注释内容]")
    
    print("\n5. 最佳实践:")
    print("   - 将干预放在叙事文本的适当位置")
    print("   - 避免在同一输入中使用冲突的干预类型")
    print("   - 对于重要编辑，先验证权限")
    print("   - 使用Retcon时考虑叙事一致性")
    
    print("\n=== 指南结束 ===")


async def main():
    """主函数"""
    await example_player_intervention()
    await example_integration()
    usage_guidelines()


if __name__ == "__main__":
    asyncio.run(main())