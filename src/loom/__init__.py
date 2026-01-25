"""
LOOM - Language-Oriented Open Mythos
语言驱动的开放叙事解释器运行时

五层架构：
1. 运行时核心层 (Runtime Core)
2. 规则层 (Markdown规则)
3. 解释层 (LLM推理)
4. 世界记忆层 (世界记忆)
5. 玩家干预层 (玩家干预)
"""

__version__ = "0.10.0"
__author__ = "LOOM Team"

from .core import *
from .rules import *
from .interpretation import *
from .memory import *
from .intervention import *
from .utils import *