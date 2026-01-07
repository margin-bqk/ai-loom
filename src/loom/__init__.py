"""
LOOM - 基于Markdown规则的非承载式叙事引擎

五层架构：
1. 运行时核心层 (Runtime Core)
2. 规则层 (Markdown Canon)
3. 解释层 (LLM Reasoning)
4. 世界记忆层 (World Memory)
5. 玩家干预层 (Player Intervention)
"""

__version__ = "0.1.0"
__author__ = "LOOM Team"

from .core import *
from .rules import *
from .interpretation import *
from .memory import *
from .intervention import *
from .utils import *