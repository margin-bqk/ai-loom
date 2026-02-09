# Sci Fi Example

## 概述

本文档提供 LOOM 科幻叙事功能的完整示例，展示如何创建和管理科幻世界、先进科技系统、外星文明和太空歌剧叙事。通过本示例，您将学习如何：

1. 构建硬科幻和太空歌剧世界
2. 设计合理的未来科技系统
3. 创建有深度的外星文明和文化
4. 管理星际政治和冲突
5. 处理科幻特有的叙事元素（AI、基因工程、太空旅行等）

## 科幻世界构建

### 1. 核心科幻元素

基于 `examples/sci_fi_world.md` 的科幻世界：

```yaml
# examples/sci_fi_world.md 的 YAML 表示
sci_fi_world:
  name: "星海联邦宇宙"
  genre: "太空歌剧、硬科幻元素"
  time_period: "公元25世纪"
  
  core_elements:
    ftl_travel:
      system: "跃迁门网络"
      description: "通过固定的跃迁门进行超光速旅行"
      limitations: "需要建立和维护跃迁门，无法随意跃迁"
      scientific_basis: "基于阿尔库贝利度规的扭曲驱动理论"
    
    artificial_intelligence:
      levels:
        - level: "弱AI"
          description: "专用人工智能，无自我意识"
          examples: ["飞船导航AI", "医疗诊断系统", "资源管理AI"]
          restrictions: "无"
        
        - level: "强AI"
          description: "通用人工智能，有自我意识"
          examples: ["星舰主脑", "科研AI", "军事战略AI"]
          restrictions: "受'AI三定律'严格限制，需要定期伦理审查"
        
        - level: "超AI"
          description: "超越人类理解的人工智能"
          examples: ["古代文明遗留AI", "实验性量子AI"]
          restrictions: "禁止创造，现存个体受严密监控"
    
    bio_engineering:
      technologies:
        - name: "基因优化"
          description: "消除遗传疾病，增强基础能力"
          ethical_status: "普遍接受，有监管"
        
        - name: "基因定制"
          description: "定制外貌、能力、寿命"
          ethical_status: "有争议，受阶级限制"
        
        - name: "基因武器"
          description: "针对特定基因的生化武器"
          ethical_status: "严格禁止，战争罪"
        
        - name: "意识上传"
          description: "将意识数字化"
          ethical_status: "实验阶段，法律地位未定"
    
    alien_civilizations:
      - name: "瓦肯人"
        type: "类人外星文明"
        traits: ["逻辑至上", "情感抑制", "铜基血液"]
        technology: ["先进理论物理", "医疗科技", "精神感应"]
        culture: "重视证据和逻辑，社会高度结构化"
        relationship: "联邦盟友，科技共享伙伴"
      
      - name: "克里格虫族"
        type: "昆虫类集体意识文明"
        traits: ["蜂巢思维", "快速进化", "扩张主义"]
        technology: ["生物科技", "有机舰船", "群体战术"]
        culture: "无个体概念，完全为集体服务"
        relationship: "潜在威胁，边境冲突"
      
      - name: "以太族"
        type: "能量生命体"
        traits: ["非物质形态", "神秘莫测", "时间感知不同"]
        technology: ["能量操控", "维度旅行", "现实扭曲"]
        culture: "难以理解，交流困难"
        relationship: "中立观察者，偶尔干预"

    major_factions:
      - name: "星海联邦"
        type: "民主政体"
        territory: "核心世界数百光年"
        ideology: "多元文化、科技共享、和平扩张"
        strengths: ["科技先进", "文化包容", "外交灵活"]
        weaknesses: ["官僚主义", "决策缓慢", "军事分散"]
      
      - name: "企业联盟"
        type: "企业统治政体"
        territory: "资源丰富星区"
        ideology: "资本主义极致、利润至上"
        strengths: ["经济实力", "效率", "技术创新"]
        weaknesses: ["社会不平等", "环境破坏", "道德模糊"]
      
      - name: "自由边境"
        type: "无政府区域"
        territory: "法律薄弱星区"
        ideology: "生存主义、机会主义"
        strengths: ["自由度高", "机会多", "适应力强"]
        weaknesses: ["危险", "不稳定", "缺乏保护"]

    important_locations:
      - name: "地球"
        type: "人类母星"
        status: "政治文化中心，历史象征"
        features: ["联合国总部", "历史档案馆", "地球化示范区"]
      
      - name: "火星"
        type: "完全地球化行星"
        status: "科技研发中心，工业基地"
        features: ["轨道电梯", "地下城市", "量子计算中心"]
      
      - name: "泰坦空间站"
        type: "最大贸易枢纽"
        status: "文化熔炉，经济中心"
        features: ["环形居住区", "零重力市场", "多元文化区"]
      
      - name: "深渊前哨"
        type: "军事科研前哨"
        status: "对抗虫族最前线"
        features: ["防御平台", "科研设施", "难民收容所"]
```

### 2. 科幻世界构建器

```python
# examples/sci_fi_world_builder.py
from loom import WorldBuilder, TechSystemBuilder, AlienCivilizationBuilder

class SciFiWorldBuilder:
    """科幻世界构建器"""
    
    def __init__(self):
        self.world_builder = WorldBuilder()
        self.tech_builder = TechSystemBuilder()
        self.alien_builder = AlienCivilizationBuilder()
    
    def create_star_federation_world(self):
        """创建星海联邦世界"""
        
        print("构建星海联邦科幻世界...")
        
        # 创建基础世界
        world = self.world_builder.create_world(
            name="星海联邦宇宙",
            description="公元25世纪，人类建立横跨数百光年的星际文明",
            genre="space_opera",
            tone="探索、生存、道德挑战"
        )
        
        # 添加科技系统
        tech_systems = self._create_tech_systems()
        for system in tech_systems:
            world.add_tech_system(system)
        
        # 添加外星文明
        alien_civs = self._create_alien_civilizations()
        for civ in alien_civs:
            world.add_civilization(civ)
        
        # 添加主要势力
        factions = self._create_factions()
        for faction in factions:
            world.add_faction(faction)
        
        # 添加重要地点
        locations = self._create_locations()
        for location in locations:
            world.add_location(location)
        
        print(f"世界构建完成: {world.name}")
        print(f"科技系统: {len(tech_systems)}个")
        print(f"外星文明: {len(alien_civs)}个")
        print(f"主要势力: {len(factions)}个")
        print(f"重要地点: {len(locations)}个")
        
        return world
    
    def _create_tech_systems(self):
        """创建科技系统"""
        
        systems = []
        
        # 1. 跃迁技术
        ftl_system = self.tech_builder.create_system(
            name="跃迁门网络",
            category="交通",
            description="通过固定的跃迁门进行超光速旅行",
            scientific_basis="阿尔库贝利度规扭曲驱动",
            limitations=["需要建立和维护跃迁门", "无法随意跃迁", "有微小失败风险"],
            societal_impact="实现星际文明，改变时空观念"
        )
        systems.append(ftl_system)
        
        # 2. 人工智能
        ai_system = self.tech_builder.create_system(
            name="人工智能体系",
            category="计算",
            description="从弱AI到强AI的多层次人工智能",
            scientific_basis="神经网络、量子计算、意识模拟",
            limitations=["强AI受三定律限制", "超AI禁止创造", "需要伦理审查"],
            societal_impact="劳动力变革、伦理挑战、存在风险"
        )
        systems.append(ai_system)
        
        # 3. 基因工程
        bio_system = self.tech_builder.create_system(
            name="基因工程技术",
            category="生物",
            description="从基因优化到意识上传的生物科技",
            scientific_basis="CRISPR、神经科学、意识数字化",
            limitations=["伦理争议", "阶级分化风险", "不可预知副作用"],
            societal_impact="寿命延长、能力增强、身份重新定义"
        )
        systems.append(bio_system)
        
        # 4. 纳米技术
        nano_system = self.tech_builder.create_system(
            name="纳米制造技术",
            category="制造",
            description="原子级精确制造和修复",
            scientific_basis="分子组装、自复制纳米机器",
            limitations=["灰色粘质风险", "能量需求高", "严格管控"],
            societal_impact="物质极大丰富、医疗革命、环境修复"
        )
        systems.append(nano_system)
        
        return systems
    
    def _create_alien_civilizations(self):
        """创建外星文明"""
        
        civilizations = []
        
        # 1. 瓦肯人
        vulcans = self.alien_builder.create_civilization(
            name="瓦肯人",
            type="类人文明",
            homeworld="瓦肯星",
            biology={
                "physiology": "类人外形，尖耳，铜基血液",
                "lifespan": "平均200地球年",
                "special_abilities": ["精神感应", "情感抑制", "逻辑思维"]
            },
            culture={
                "values": ["逻辑", "证据", "和平"],
                "social_structure": "高度结构化，基于逻辑的 meritocracy",
                "art_science": "重视科学和哲学，艺术形式抽象"
            },
            technology_level="先进",
            relationship_status="盟友"
        )
        civilizations.append(vulcans)
        
        # 2. 克里格虫族
        krieg = self.alien_builder.create_civilization(
            name="克里格虫族",
            type="昆虫类集体意识",
            homeworld="克里格母巢",
            biology={
                "physiology": "昆虫外形，几丁质外骨骼，多形态",
                "lifespan": "个体短暂，集体永恒",
                "special_abilities": ["蜂巢思维", "快速进化", "生物科技"]
            },
            culture={
                "values": ["集体生存", "扩张", "效率"],
                "social_structure": "完全集体主义，无个体概念",
                "art_science": "实用主义，无艺术，高效科技"
            },
            technology_level="特殊化（生物科技）",
            relationship_status="潜在威胁"
        )
        civilizations.append(krieg)
        
        # 3. 以太族
        etherians = self.alien_builder.create_civilization(
            name="以太族",
            type="能量生命体",
            homeworld="未知",
            biology={
                "physiology": "纯能量形态，无固定形状",
                "lifespan": "可能永恒",
                "special_abilities": ["能量操控", "维度旅行", "现实感知"]
            },
            culture={
                "values": ["未知", "神秘", "观察"],
                "social_structure": "无法理解",
                "art_science": "超越人类理解"
            },
            technology_level="超越性",
            relationship_status="中立观察者"
        )
        civilizations.append(etherians)
        
        return civilizations
    
    def _create_factions(self):
        """创建主要势力"""
        
        factions = [
            {
                "name": "星海联邦",
                "type": "民主政体",
                "ideology": "多元文化、科技共享、和平扩张",
                "territory": "核心世界数百光年",
                "government": "联邦制，各星球高度自治",
                "military": "联邦舰队，防御为主",
                "economy": "混合经济，注重可持续发展",
                "culture": "多元融合，尊重差异",
                "goals": ["维护和平", "促进发展", "探索未知"],
                "internal_conflicts": ["中央与地方权力", "资源分配", "文化融合挑战"]
            },
            {
                "name": "企业联盟",
                "type": "企业统治",
                "ideology": "利润至上、效率优先、自由市场",
                "territory": "资源丰富星区",
                "government": "企业董事会统治，股东民主",
                "military": "企业安保部队，雇佣兵",
                "economy": "完全资本主义，垄断常见",
                "culture": "消费主义，个人成功崇拜",
                "goals": ["利润最大化", "市场扩张", "技术垄断"],
                "internal_conflicts": ["劳资矛盾", "环境代价", "道德底线"]
            },
            {
                "name": "自由边境",
                "type": "无政府区域",
                "ideology": "生存主义、机会主义、个人自由",
                "territory": "法律薄弱星区",
                "government": "无中央政权，地方强人统治",
                "military": "民兵、海盗、私人武装",
                "economy": "黑市、走私、资源掠夺",
                "culture": "实用主义，尊重强者",
                "goals": ["生存", "发财", "逃避法律"],
                "internal_conflicts": ["暴力循环", "资源争夺", "缺乏安全保障"]
            }
        ]
        
        return factions
    
    def _create_locations(self):
        """创建重要地点"""
        
        locations = [
            {
                "name": "地球",
                "type": "母星",
                "status": "政治文化中心",
                "description": "人类起源星球，经过生态恢复和历史保护",
                "features": [
                    "联合国星际总部",
                    "人类历史档案馆",
                    "地球化技术示范区",
                    "文化遗产保护区"
                ],
                "significance": "象征意义大于实际权力，精神家园",
                "quest_hooks": ["政治阴谋", "历史发现", "生态危机"]
            },
            {
                "name": "火星",
                "type": "地球化行星",
                "status": "科技工业中心",
                "description": "完全地球化的红色星球，联邦科技心脏",
                "features": [
                    "轨道电梯'天梯'",
                    "地下城市网络",
                    "量子计算中心",
                    "星际船坞"
                ],
                "significance": "联邦实际权力中心，科技引擎",
                "quest_hooks": ["科技突破", "工业间谍", "资源危机"]
            },
            {
                "name": "泰坦空间站",
                "type": "贸易枢纽",
                "status": "经济文化中心",
                "description": "土卫六轨道上的巨型空间站，星际贸易和文化中心",
                "features": [
                    "环形居住区（模拟重力）",
                    "零重力自由贸易区",
                    "多元文化使馆区",
                    "黑市和情报交易所"
                ],
                "significance": "经济命脉，情报中心，文化熔炉",
                "quest_hooks": ["贸易纠纷", "外交危机", "情报操作"]
            },
            {
                "name": "深渊前哨",
                "type": "军事科研站",
                "status": "边境防线",
                "description": "位于虫族边境的军事科研前哨，联邦最前线",
                "features": [
                    "多层防御平台",
                    "生物威胁研究设施",
                    "难民收容所",
                    "秘密武器实验室"
                ],
                "significance": "生存防线，科研前沿，道德考验场",
                "quest_hooks": ["军事冲突", "科研突破", "人道危机"]
            }
        ]
        
        return locations

# 使用示例
if __name__ == "__main__":
    builder = SciFiWorldBuilder()
    world = builder.create_star_federation_world()
    
    # 保存世界配置
    world.save("star_federation_world.yaml")
    
    # 输出摘要
    print("\n世界摘要:")
    print(f"名称: {world.name}")
    print(f"时代: 公元25世纪")
    print(f"核心科技: {', '.join([ts.name for ts in world.tech_systems])}")
    print(f"主要文明: {', '.join([civ.name for civ in world.civilizations])}")
    print(f"势力格局: {', '.join([faction['name'] for faction in world.factions])}")
```

## 科幻叙事会话示例

### 1. 星际探索会话

```python
# examples/starfleet_exploration.py
import asyncio
from loom import SessionManager, SessionConfig
from loom.sci_fi import SciFiSessionBuilder

class StarfleetExplorationSession:
    """星际探索会话管理器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session_manager = SessionManager()
        self.sci_fi_builder = SciFiSessionBuilder()
    
    async def create_exploration_session(self, ship_name: str = "进取号"):
        """创建星际探索会话"""
        
        print(f"创建星际探索会话 - 星舰: {ship_name}")
        
        # 构建科幻会话配置
        session_config = self.sci_fi_builder.build_session(
            genre="space_exploration",
            subgenre="hard_sci_fi",
            tone={
                "primary": "探索、惊奇、科学",
                "secondary": ["冒险", "道德", "团队合作"],
                "avoid": ["无科学依据", "过度奇幻", "简单化复杂问题"]
            },
            tech_level="advanced_25th_century",
            scientific_accuracy="high"
        )
        
        # 创建具体会话配置
        detailed_config = SessionConfig(
            session_type="starfleet_exploration",
            world_config="examples/sci_fi_world.md",
            initial_prompt=self._create_exploration_prompt(ship_name),
            llm_provider="openai",
            llm_model="gpt-4",
            temperature=0.7,
            max_tokens=1500,
            max_turns=15,
            memory_enabled=True,
            memory_capacity=35,
            sci_fi_specific={
                "ship_class": "探索舰",
                "mission_type
