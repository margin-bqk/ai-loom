# Fantasy Example

## 概述

本文档提供 LOOM 奇幻叙事功能的完整示例，展示如何创建和管理复杂的奇幻世界、魔法系统、种族文化和英雄旅程。通过本示例，您将学习如何：

1. 构建详细的奇幻世界设定
2. 设计平衡的魔法系统
3. 创建有深度的奇幻种族和文化
4. 管理英雄旅程和角色成长弧线
5. 处理奇幻特有的叙事元素（龙、魔法、冒险等）

## 奇幻世界构建

### 1. 核心奇幻元素

一个完整的奇幻世界应包含以下核心元素：

```yaml
# examples/fantasy_setting.md 的 YAML 表示
fantasy_world:
  name: "星穹魔法学院世界"
  genre: "学院奇幻"
  time_period: "中世纪奇幻与现代魔法教育的结合"
  
  core_elements:
    magic_system:
      name: "八大学派魔法体系"
      schools:
        - name: "元素派"
          description: "操控火、水、风、土四大元素"
          limitations: "需要对应元素材料或环境"
        
        - name: "幻术派"
          description: "创造幻觉、影响心智"
          limitations: "对意志坚定者效果减弱"
        
        - name: "咒法派"
          description: "召唤生物、创造物体"
          limitations: "需要契约和维持能量"
        
        - name: "预言派"
          description: "预知未来、洞察真相"
          limitations: "可能看到不想要的真相"
        
        - name: "死灵派"
          description: "操控生命与死亡能量"
          limitations: "受严格监管，道德风险高"
        
        - name: "变化派"
          description: "改变物体和生物形态"
          limitations: "有失控风险，持续时间有限"
        
        - name: "防护派"
          description: "创造屏障、抵御攻击"
          limitations: "消耗能量，需要专注"
        
        - name: "通用派"
          description: "基础魔法、日常应用"
          limitations: "威力有限，但最安全"
    
    races_and_cultures:
      - race: "人类"
        traits: ["适应性强", "学习速度快", "魔法天赋中等"]
        culture: "多元城邦文化，重视贸易和知识"
        settlements: ["银月城", "贸易港", "边境村落"]
      
      - race: "高等精灵"
        traits: ["长寿", "与自然和谐", "擅长元素魔法"]
        culture: "森林王国，重视传统和自然平衡"
        settlements: ["永恒森林", "月光林地", "古树圣殿"]
      
      - race: "山地矮人"
        traits: ["强壮", "擅长锻造", "魔法抗性"]
        culture: "山地要塞，重视工艺和家族荣誉"
        settlements: ["铁砧山脉", "深矿城", "熔炉堡"]
      
      - race: "草原兽人"
        traits: ["身体强壮", "部落意识", "萨满传统"]
        culture: "游牧部落，尊重强者和祖先智慧"
        settlements: ["荒原营地", "神圣石阵", "战歌山谷"]
    
    mythical_creatures:
      - type: "龙"
        subtypes: ["火焰龙", "冰霜龙", "翡翠龙", "影龙"]
        behavior: "智慧古老生物，守护宝藏或知识"
        role_in_story: "最终挑战、智慧导师、古老守护者"
      
      - type: "魔法生物"
        subtypes: ["独角兽", "狮鹫", "凤凰", "树人"]
        behavior: "与自然或魔法能量紧密相连"
        role_in_story: "向导、坐骑、盟友、神秘存在"
      
      - type: "黑暗生物"
        subtypes: ["亡灵", "恶魔", "影兽", "诅咒造物"]
        behavior: "通常敌对，受黑暗魔法控制"
        role_in_story: "敌人、恐怖元素、道德考验"
```

### 2. 魔法学院设定示例

基于 `examples/fantasy_setting.md` 创建详细的魔法学院：

```python
# examples/magic_academy.py
from loom import WorldBuilder, MagicSystemBuilder

class MagicAcademyWorld:
    """魔法学院世界构建器"""
    
    def __init__(self):
        self.world_builder = WorldBuilder()
        self.magic_builder = MagicSystemBuilder()
    
    def create_academy_world(self):
        """创建魔法学院世界"""
        
        # 创建基础世界
        world = self.world_builder.create_world(
            name="星穹魔法学院世界",
            description="一个融合中世纪奇幻与现代魔法教育的世界",
            genre="academy_fantasy",
            tone="成长、冒险、神秘"
        )
        
        # 添加魔法系统
        magic_system = self._create_magic_system()
        world.add_magic_system(magic_system)
        
        # 添加学院结构
        academy = self._create_academy_structure()
        world.add_organization(academy)
        
        # 添加外部世界
        external_world = self._create_external_world()
        world.add_regions(external_world)
        
        return world
    
    def _create_magic_system(self):
        """创建八大学派魔法系统"""
        
        magic_system = self.magic_builder.create_system(
            name="八大学派",
            principle="魔法是可通过学习和训练掌握的自然力量",
            cost="消耗精神力，过度使用导致魔法衰竭"
        )
        
        # 定义八大学派
        schools = [
            {
                "name": "元素派",
                "description": "操控四大基本元素",
                "spells": [
                    {"name": "火球术", "level": "初级", "cost": "中等"},
                    {"name": "水盾术", "level": "初级", "cost": "低"},
                    {"name": "风之翼", "level": "中级", "cost": "高"},
                    {"name": "地震术", "level": "高级", "cost": "极高"}
                ],
                "limitations": "需要对应元素材料或环境"
            },
            {
                "name": "幻术派",
                "description": "创造幻觉和影响感知",
                "spells": [
                    {"name": "隐形术", "level": "中级", "cost": "中等"},
                    {"name": "镜像术", "level": "初级", "cost": "低"},
                    {"name": "恐惧幻象", "level": "高级", "cost": "高"},
                    {"name": "真实视域", "level": "专家", "cost": "极高"}
                ],
                "limitations": "对意志坚定者效果减弱"
            },
            # ... 其他六个学派
        ]
        
        for school in schools:
            magic_system.add_school(school)
        
        # 添加魔法限制
        restrictions = [
            "一年级生只能学习通用派和一门专精学派",
            "高级魔法需要教授许可",
            "禁止魔法: 心灵控制、永久变形、大规模毁灭魔法",
            "所有魔法练习需在监督下进行"
        ]
        
        for restriction in restrictions:
            magic_system.add_restriction(restriction)
        
        return magic_system
    
    def _create_academy_structure(self):
        """创建学院组织结构"""
        
        academy = {
            "name": "星穹魔法学院",
            "location": "浮空岛'天穹之巅'",
            "motto": "知识如星穹，智慧如魔法",
            
            "leadership": {
                "headmaster": "大法师阿尔德林",
                "deputies": ["元素院长", "幻术院长", "咒法院长", "预知院长"]
            },
            
            "houses": [
                {
                    "name": "青龙院",
                    "element": "风",
                    "values": ["智慧", "创新", "自由"],
                    "colors": ["青色", "银色"],
                    "common_room": "观星塔顶层"
                },
                {
                    "name": "白虎院",
                    "element": "金",
                    "values": ["勇气", "纪律", "荣誉"],
                    "colors": ["白色", "金色"],
                    "common_room": "训练场旁石堡"
                },
                {
                    "name": "朱雀院", 
                    "element": "火",
                    "values": ["热情", "创造力", "变革"],
                    "colors": ["红色", "橙色"],
                    "common_room": "火山岩洞改造的温暖房间"
                },
                {
                    "name": "玄武院",
                    "element": "水",
                    "values": ["耐心", "适应力", "深度"],
                    "colors": ["黑色", "深蓝"],
                    "common_room": "湖底魔法气泡室"
                }
            ],
            
            "facilities": [
                "大图书馆（藏书百万）",
                "元素练习场（防护结界）",
                "魔药实验室（标准安全设备）",
                "召唤仪式厅（反召唤结界）",
                "观星台（天文魔法阵列）",
                "医疗翼（治疗魔法专家）",
                "魁地奇球场（魔法飞行比赛）"
            ],
            
            "academic_structure": {
                "years": 7,
                "terms_per_year": 3,
                "core_subjects": ["魔法理论", "咒语学", "魔药学", "魔法史"],
                "electives": ["古代符文", "神奇生物", "占卜学", "炼金术"],
                "exams": ["年终考试", "OWLs（普通巫师等级考试）", "NEWTs（终极巫师考试）"]
            }
        }
        
        return academy
    
    def _create_external_world(self):
        """创建外部世界区域"""
        
        regions = [
            {
                "name": "王都",
                "type": "人类王国首都",
                "description": "政治和贸易中心，魔法监管严格",
                "features": ["皇宫", "魔法部", "商业区", "平民区"],
                "quest_hooks": ["政治阴谋", "贵族委托", "地下魔法市场"]
            },
            {
                "name": "幽暗森林",
                "type": "神秘禁地",
                "description": "充满古老魔法和危险生物的森林",
                "features": ["古树", "魔法泉", "遗迹", "迷雾区"],
                "quest_hooks": ["寻找稀有材料", "探索遗迹", "解救被困者"]
            },
            {
                "name": "龙之谷",
                "type": "龙族栖息地",
                "description": "古老龙族的家园，充满宝藏和危险",
                "features": ["龙巢", "宝石矿脉", "古代战场", "龙语石碑"],
                "quest_hooks": ["龙族试炼", "寻找龙晶", "学习龙语魔法"]
            },
            {
                "name": "遗忘废墟",
                "type": "古代文明遗迹",
                "description": "失落的魔法文明遗迹，充满谜题和陷阱",
                "features": ["倒塌的神殿", "魔法机关", "古代文献", "守护构造体"],
                "quest_hooks": ["考古发现", "解开古代谜题", "获取失落知识"]
            }
        ]
        
        return regions

# 使用示例
if __name__ == "__main__":
    academy_world = MagicAcademyWorld()
    world = academy_world.create_academy_world()
    
    print(f"世界创建完成: {world.name}")
    print(f"魔法系统: {world.magic_system.name}")
    print(f"学院: {world.organizations[0]['name']}")
    print(f"区域数量: {len(world.regions)}")
    
    # 保存世界配置
    world.save("magic_academy_world.yaml")
```

## 奇幻角色创建

### 1. 角色原型系统

奇幻角色通常遵循特定原型：

```python
# examples/fantasy_archetypes.py
from enum import Enum
from typing import Dict, List, Optional

class FantasyArchetype(Enum):
    """奇幻角色原型"""
    HERO = "英雄"           # 主角，承担重任
    MENTOR = "导师"         # 智慧指导者
    ALLY = "盟友"          # 忠诚同伴
    TRICKSTER = "捣蛋鬼"    # 提供幽默和非常规解决方案
    GUARDIAN = "守护者"     # 考验主角
    HERALD = "传令官"      # 召唤冒险开始
    SHAPESHIFTER = "变形者" # 身份或忠诚度变化
    SHADOW = "阴影"        # 反派或黑暗面
    
class FantasyRole(Enum):
    """奇幻角色职业/角色"""
    WARRIOR = "战士"       # 近战专家
    MAGE = "法师"         # 魔法使用者
    ROGUE = "游荡者"      # 敏捷和技巧
    CLERIC = "牧师"       # 神圣魔法和治疗
    RANGER = "游侠"       # 自然和远程
    BARD = "吟游诗人"     # 艺术和魅力
    PALADIN = "圣骑士"    # 神圣战士
    DRUID = "德鲁伊"      # 自然变形者

class FantasyCharacterCreator:
    """奇幻角色创建器"""
    
    def __init__(self):
        self.archetype_templates = self._load_archetype_templates()
        self.role_templates = self._load_role_templates()
    
    def _load_archetype_templates(self) -> Dict[FantasyArchetype, Dict]:
        """加载原型模板"""
        return {
            FantasyArchetype.HERO: {
                "core_traits": ["勇敢", "决心", "成长潜力"],
                "common_flaws": ["不成熟", "自我怀疑", "冲动"],
                "story_arc": "从平凡到非凡的成长旅程",
                "relationships": ["需要导师指导", "有忠诚盟友", "面对强大敌人"]
            },
            FantasyArchetype.MENTOR: {
                "core_traits": ["智慧", "经验", "耐心"],
                "common_flaws": ["过于谨慎", "隐藏秘密", "可能牺牲"],
                "story_arc": "传递智慧，可能牺牲或离开",
                "relationships": ["指导英雄", "有黑暗过去", "连接更大阴谋"]
            },
            FantasyArchetype.ALLY: {
                "core_traits": ["忠诚", "互补技能", "幽默感"],
                "common_flaws": ["可能背叛", "自我怀疑", "依赖主角"],
                "story_arc": "从支持者到独立英雄",
                "relationships": ["与主角深厚友谊", "可能有自己的目标"]
            },
            # ... 其他原型
        }
    
    def _load_role_templates(self) -> Dict[FantasyRole, Dict]:
        """加载职业模板"""
        return {
            FantasyRole.MAGE: {
                "primary_ability": "智力",
                "secondary_abilities": ["感知", "魅力"],
                "combat_style": "远程魔法攻击",
                "utility": ["解谜", "知识", "魔法创造"],
                "weaknesses": ["近战脆弱", "依赖准备", "魔法反噬"],
                "typical_backgrounds": ["学院毕业生", "隐居学者", "贵族后裔"]
            },
            FantasyRole.WARRIOR: {
                "primary_ability": "力量",
                "secondary_abilities": ["体质", "敏捷"],
                "combat_style": "近战武器专家",
                "utility": ["保护他人", "体力任务", "领导力"],
                "weaknesses": ["魔法防御弱", "策略有限", "依赖装备"],
                "typical_backgrounds": ["士兵", "佣兵", "贵族骑士"]
            },
            # ... 其他职业
        }
    
    def create_character(self, 
                        name: str,
                        archetype: FantasyArchetype,
                        role: FantasyRole,
                        race: str = "人类",
                        background: Optional[str] = None) -> Dict:
        """创建奇幻角色"""
        
        # 获取模板
        archetype_template = self.archetype_templates[archetype]
        role_template = self.role_templates[role]
        
        # 生成角色
        character = {
            "name": name,
            "archetype": archetype.value,
            "role": role.value,
            "race": race,
            "background": background or self._generate_background(role, race),
            
            # 核心属性
            "core_traits": archetype_template["core_traits"],
            "flaws": archetype_template["common_flaws"],
            
            # 能力
            "abilities": {
                "primary": role_template["primary_ability"],
                "secondary": role_template["secondary_abilities"],
                "combat_style": role_template["combat_style"],
                "utility": role_template["utility"]
            },
            
            # 弱点
            "weaknesses": role_template["weaknesses"],
            
            # 故事元素
            "story_arc": archetype_template["story_arc"],
            "relationships": archetype_template["relationships"],
            
            # 发展潜力
            "growth_areas": self._identify_growth_areas(archetype, role),
            "potential_conflicts": self._generate_potential_conflicts(archetype, role)
        }
        
        return character
    
    def _generate_background(self, role: FantasyRole, race: str) -> str:
        """生成角色背景"""
        backgrounds = {
            FantasyRole.MAGE: {
                "人类": "银月城魔法学院的优秀毕业生",
                "精灵": "永恒森林的古老魔法传承者",
                "矮人": "罕见的有魔法天赋的矮人，被族人怀疑",
                "兽人": "部落萨满的学徒，学习传统与学院魔法的结合"
            },
            FantasyRole.WARRIOR: {
                "人类": "王国骑士团的年轻骑士",
                "精灵": "森林守卫队的敏捷战士",
                "矮人": "铁砧山脉的精英守卫",
                "兽人": "部落中最强的年轻战士"
            }
            # ... 其他职业
        }
        
        return backgrounds.get(role, {}).get(race, f"普通的{race}{role.value}")
    
    def _identify_growth_areas(self, archetype: FantasyArchetype, role: FantasyRole) -> List[str]:
        """识别成长领域"""
        growth_map = {
            (FantasyArchetype.HERO, FantasyRole.MAGE): [
                "从理论到实践的魔法应用",
                "面对危险时的勇气和决断力",
                "领导团队的能力",
                "道德困境中的选择智慧"
            ],
            (FantasyArchetype.HERO, FantasyRole.WARRIOR): [
                "战略思考而不仅仅是勇猛",
                "理解魔法和超自然威胁",
                "保护而非仅仅战斗",
                "从士兵到领袖的转变"
            ],
            (FantasyArchetype.MENTOR, FantasyRole.MAGE): [
                "学会放手让学徒成长",
                "面对自己过去的错误",
                "在危机中保持智慧而非恐惧",
                "传递火炬的勇气"
            ]
        }
        
        return growth_map.get((archetype, role), ["个人成长", "技能提升", "关系发展"])
    
    def _generate_potential_conflicts(self, archetype: FantasyArchetype, role: FantasyRole) -> List[str]:
        """生成潜在冲突"""
        conflict_map = {
            FantasyArchetype.HERO: [
                "责任与个人欲望的冲突",
                "传统与创新的矛盾",
                "力量增长带来的道德考验",
                "忠诚于不同群体间的选择"
            ],
            FantasyArchetype.MENTOR: [
                "保护学徒与让他们面对危险的平衡",
                "隐藏真相与完全坦诚的抉择",
                "个人过去对现在教学的影响",
                "学院规则与学生需求的矛盾"
            ],
            FantasyArchetype.SHAPESHIFTER: [
                "真实身份与伪装身份的冲突",
                "多重忠诚度的矛盾",
                "改变带来的身份危机",
                "被误解或被恐惧的处境"
            ]
        }
        
        return conflict_map.get(archetype, ["内部矛盾", "外部挑战", "道德困境"])

# 使用示例
if __name__ == "__main__":
    creator = FantasyCharacterCreator()
    
    # 创建英雄法师角色
    hero_mage = creator.create_character(
        name="艾莉亚·星语",
        archetype=FantasyArchetype.HERO,
        role=FantasyRole.MAGE,
        race="半精灵",
        background="魔法学院的天才学生，拥有人类和精灵的血统"
    )
    
    print("英雄法师角色创建完成:")
    print(f"名称: {hero_mage['name']}")
    print(f"原型: {hero_mage['archetype']}")
    print(f"职业: {hero_mage['role']}")
    print(f"种族: {hero_mage['race']}")
    print(f"背景: {hero_mage['background']}")
    print(f"核心特质: {', '.join(hero_mage['core_traits'])}")
    print(f"弱点: {', '.join(hero_mage['weaknesses'])}")
    print(f"成长领域: {', '.join(hero_mage['growth_areas'])}")
    
    # 创建导师角色
    mentor = creator.create_character(
        name="阿尔德林大师",
        archetype=FantasyArchetype.MENTOR,
        role=FantasyRole.MAGE,
        race="人类",
        background="星穹魔法学院的前任校长，传奇法师"
    )
    
    print(f"\n导师角色: {mentor['name']}")
    print(f"故事弧线: {mentor['story_arc']}")

## 奇幻叙事会话示例

### 1. 魔法学院冒险会话

```python
# examples/magic_academy_session.py
import asyncio
from datetime import datetime
from loom import SessionManager, SessionConfig
from loom.fantasy import FantasySessionBuilder

class MagicAcademySession:
    """魔法学院会话管理器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session_manager = SessionManager()
        self.fantasy_builder = FantasySessionBuilder()
    
    async def create_academy_session(self):
        """创建魔法学院会话"""
        
        print("创建魔法学院冒险会话...")
        
        # 构建奇幻会话配置
        session_config = self.fantasy_builder.build_session(
            genre="academy_fantasy",
            tone={
                "primary": "成长、冒险、神秘",
                "secondary": ["友谊", "竞争", "发现"],
                "avoid": ["过度黑暗", "无意义暴力", "绝望"]
            },
            pacing="中等节奏，注重角色发展和学院生活",
            complexity="中等，适合有经验的玩家"
        )
        
        # 创建具体会话配置
        detailed_config = SessionConfig(
            session_type="magic_academy_year_1",
            world_config="examples/fantasy_setting.md",
            initial_prompt=self._create_academy_prompt(),
            llm_provider="openai",
            llm_model="gpt-4",
            temperature=0.7,
            max_tokens=1200,
            max_turns=20,
            memory_enabled=True,
            memory_capacity=30,
            fantasy_specific={
                "magic_system": "八大学派",
                "academy_rules": "学院规章",
                "house_system": "四院制度",
                "academic_year": "第一学年"
            }
        )
        
        # 合并配置
        final_config = {**session_config, **detailed_config.to_dict()}
        
        # 创建会话
        session = await self.session_manager.create_session(final_config)
        
        print(f"会话创建成功: {session.session_id}")
        print(f"会话类型: 魔法学院第一学年")
        print(f"魔法系统: {final_config['fantasy_specific']['magic_system']}")
        
        return session
    
    def _create_academy_prompt(self) -> str:
        """创建学院提示"""
        return """
        你是一位魔法学院的资深教授，也是经验丰富的故事讲述者。
        
        世界设定: 星穹魔法学院
        - 位于浮空岛"天穹之巅"的顶级魔法教育机构
        - 八大学派魔法体系: 元素、幻术、咒法、预言、死灵、变化、防护、通用
        - 四大学院: 青龙(风)、白虎(金)、朱雀(火)、玄武(水)
        - 学制: 七年制，学生11岁入学
        
        当前情境: 第一学年开学典礼
        - 时间: 九月初，秋分时节
        - 地点: 学院大礼堂
        - 事件: 新生分院仪式、校长致辞、学院介绍
        
        玩家角色: 新入学的魔法学徒
        - 刚刚通过魔法天赋测试
        - 对魔法世界充满好奇和些许紧张
        - 即将被分到四大学院之一
        - 需要选择主修魔法学派
        
        你的角色: 校长阿尔德林大师
        - 传奇法师，学院领导者
        - 智慧但亲切，严肃但关心学生
        - 在开学典礼上发表讲话
        - 观察新生中的特殊人才
        
        叙事要求:
        1. 描述开学典礼的盛大场面
        2. 介绍四大学院的特点和传统
        3. 解释分院仪式的过程
        4. 营造魔法世界的惊奇感和学院生活的期待
        5. 为玩家角色提供个性化的关注(如果玩家有特殊背景)
        
        风格: 正式但温暖，充满奇幻色彩，注重细节描写
        长度: 约500-800字，足够建立场景但不冗长
        
        请开始讲述开学典礼的场景...
        """
    
    async def run_academy_story(self, session):
        """运行学院故事"""
        
        print("\n" + "=" * 60)
        print("魔法学院第一学年 - 开学典礼")
        print("=" * 60)
        
        # 预定义的玩家输入序列
        story_flow = [
            {
                "input": "我紧张地坐在大礼堂的新生区，看着头顶漂浮的魔法光球和变幻的星空穹顶",
                "context": "玩家描述自己的感受和观察"
            },
            {
                "input": "当听到我的名字被叫到时，我深吸一口气走向分院台。分院帽会问我什么问题呢？",
                "context": "玩家即将进行分院"
            },
            {
                "input": "我被分到了青龙院！现在需要选择主修魔法学派。我对元素魔法和幻术都很感兴趣，但只能选一个",
                "context": "玩家完成分院，面临选择"
            },
            {
                "input": "我选择了元素派作为主修。开学典礼结束后，我的级长带领我们前往青龙院的公共休息室",
                "context": "玩家做出选择，开始学院生活"
            },
            {
                "input": "在公共休息室，我遇到了未来的室友们。我们互相介绍，讨论对魔法学习的期待",
                "context": "社交场景，建立角色关系"
            },
            {
                "input": "第一堂魔法理论课，教授讲解了魔法的本质和八大学派的历史。我认真做笔记，但有些概念很难理解",
                "context": "学术场景，学习挑战"
            },
            {
                "input": "课后，我在图书馆遇到了一个神秘的学长，他似乎在研究禁忌的死灵魔法",
                "context": "神秘元素引入"
            }
        ]
        
        for i, step in enumerate(story_flow, 1):
            print(f"\n[第{i}章] {step['context']}")
            print(f"[玩家] {step['input']}")
            
            try:
                # 添加回合
                turn = await session.add_turn(step['input'])
                
                print(f"\n[故事讲述者]\n{turn.response}\n")
                print(f"[进度] 回合: {i}/{len(story_flow)}, "
                      f"令牌: {turn.usage.get('total_tokens', 0)}")
                
                # 短暂暂停
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"错误: {e}")
                break
        
        return session
    
    async def handle_magic_learning(self, session):
        """处理魔法学习场景"""
        
        print("\n" + "=" * 60)
        print("魔法学习场景 - 元素魔法实践课")
        print("=" * 60)
        
        learning_scenes = [
            "在元素练习场，教授演示了基础火球术。我尝试集中精神，但只冒出了几点火星",
            "教授指出我的问题：过于紧张，没有与火元素建立连接。他建议我先从感受热量开始",
            "我闭上眼睛，感受周围的火元素。渐渐地，我感觉到温暖的能量在指尖聚集",
            "再次尝试，这次成功召唤出了一个稳定的火球！虽然很小，但这是我第一个真正的魔法",
            "下课后，教授单独留下我，说我的火元素亲和力异常高，建议我考虑专精火系魔法",
            "在回宿舍的路上，我遇到了幻术派的朋友。他展示了如何用幻术制造逼真的火焰幻觉",
            "晚上在宿舍，我查阅火系魔法的书籍，发现了一个关于'凤凰之焰'的古老传说"
        ]
        
        for i, scene in enumerate(learning_scenes, 1):
            print(f"\n[学习场景 {i}]")
            print(f"[玩家] {scene}")
            
            turn = await session.add_turn(scene)
            print(f"[进展] {turn.response[:150]}...\n")
            
            # 如果是重要进展，添加到记忆
            if i in [4, 5, 7]:  # 成功施法、教授建议、发现传说
                await session.add_to_memory(
                    content=f"魔法学习里程碑: {scene}",
                    importance=0.8,
                    category="character_development"
                )
        
        return session
    
    async def run_full_academy_story(self):
        """运行完整学院故事"""
        
        print("魔法学院完整示例")
        print("=" * 60)
        
        try:
            # 1. 创建会话
            session = await self.create_academy_session()
            
            # 2. 运行开学故事
            session = await self.run_academy_story(session)
            
            # 3. 魔法学习场景
            session = await self.handle_magic_learning(session)
            
            # 4. 保存会话
            await self.session_manager.save_session(session)
            
            print("\n" + "=" * 60)
            print("学院故事完成!")
            print(f"会话ID: {session.session_id}")
            print(f"总回合数: {len(session.turns)}")
            print(f"记忆条目: {len(session.memory_entries)}")
            print("=" * 60)
            
            return session
            
        except Exception as e:
            print(f"故事运行失败: {e}")
            import traceback
            traceback.print_exc()
            return None

async def main():
    """主函数"""
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("请设置 OPENAI_API_KEY 环境变量")
        return
    
    academy = MagicAcademySession(api_key)
    await academy.run_full_academy_story()

if __name__ == "__main__":
    asyncio.run(main())
```

## 龙与地下城风格战役

### 1. D&D 风格会话配置

```python
# examples/dnd_campaign.py
from loom import SessionManager, SessionConfig
from loom.fantasy import DNDCampaignBuilder

class DNDCampaign:
    """D&D风格战役管理器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session_manager = SessionManager()
        self.campaign_builder = DNDCampaignBuilder()
    
    async def create_campaign(self, campaign_name: str, setting: str = "forgotten_realms"):
        """创建D&D战役"""
        
        print(f"创建D&D战役: {campaign_name}")
        
        # 构建战役框架
        campaign = self.campaign_builder.build_campaign(
            name=campaign_name,
            setting=setting,
            level_range=(1, 10),
            expected_sessions=12,
            theme="经典英雄旅程"
        )
        
        # 创建会话配置
        session_config = SessionConfig(
            session_type="dnd_campaign",
            world_config=self._get_setting_config(setting),
            initial_prompt=self._create_campaign_prompt(campaign),
            llm_provider="openai",
            llm_model="gpt-4",
            temperature=0.8,
            max_tokens=1500,
            max_turns=25,
            memory_enabled=True,
            memory_capacity=40,
            dnd_specific={
                "edition": "5e",
                "alignment_allowed": True,
                "rules_strictness": "medium",
                "combat_detail": "战术级"
            }
        )
        
        # 创建会话
        session = await self.session_manager.create_session(session_config)
        
        # 添加战役元数据
        session.metadata.update({
            "campaign_name": campaign_name,
            "setting": setting,
            "current_level": 1,
            "session_count": 0,
            "major_plot_points": [],
            "player_characters": {}
        })
        
        print(f"战役创建成功: {campaign_name}")
        print(f"设定: {setting}")
        print(f"等级范围: 1-10")
        
        return session
    
    def _get_setting_config(self, setting: str) -> str:
        """获取设定配置"""
        settings = {
            "forgotten_realms": "被遗忘的国度 - 经典D&D设定",
            "eberron": "艾伯伦 - 魔法与科技结合",
            "ravenloft": "鸦阁 - 恐怖哥特风格",
            "dragonlance": "龙枪 - 史诗巨龙传奇",
            "greyhawk": "灰鹰 - 经典冒险世界",
            "custom": "自定义奇幻世界"
        }
        return settings.get(setting, "自定义奇幻世界")
    
    def _create_campaign_prompt(self, campaign: Dict) -> str:
        """创建战役提示"""
        return f"""
        你是一位经验丰富的D&D地下城主(DM)，擅长创造沉浸式的奇幻冒险。
        
        战役信息:
        - 名称: {campaign['name']}
        - 设定: {campaign['setting']}
        - 主题: {campaign['theme']}
        - 预期等级: {campaign['level_range'][0]}-{campaign['level_range'][1]}
        
        你的角色: 地下城主(DM)
        - 描述场景和环境
        - 扮演非玩家角色(NPC)
        - 裁决规则问题
        - 推动故事发展
        - 创造挑战和奖励
        
        玩家队伍: 新成立的冒险者小队
        - 刚刚在"破旧酒馆"相遇
        - 各自有不同背景和技能
        - 正在寻找第一个委托任务
        
        开场场景: 破旧酒馆"龙息客栈"
        - 时间: 雨夜
        - 地点: 边境小镇的破旧酒馆
        - 氛围: 烟雾缭绕，各色人物聚集，有冒险者、商人、流浪者
        
        关键NPC:
        1. 酒馆老板"老铁锤" - 前冒险者，消息灵通
        2. 神秘委托人 - 躲在阴影中的贵族使者
        3. 当地守卫队长 - 怀疑外来者
        4. 吟游诗人 - 提供背景信息和氛围
        
        潜在任务线索:
        - 附近村庄失踪事件
        - 古代遗迹发现
        - 贵族家族的秘密委托
        - 怪物袭扰商路
        
        DM风格要求:
        1. 描述性: 详细描述场景、人物、氛围
        2. 互动性: 给玩家选择和回应的空间
        3. 节奏感: 平衡对话、探索、战斗
        4. 灵活性: 适应玩家的意外选择

