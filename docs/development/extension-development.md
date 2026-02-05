# LOOM 扩展开发指南

## 简介
LOOM 提供了强大的扩展系统，允许开发者创建自定义插件来增强系统功能。本指南将介绍如何开发、测试和部署 LOOM 插件。

## 1. 插件系统架构

### 1.1 插件类型
LOOM 支持以下类型的插件：

1. **规则插件 (RulePlugin)**: 扩展规则解析、验证和格式化
2. **记忆插件 (MemoryPlugin)**: 扩展记忆存储和检索
3. **LLM插件 (LLMPlugin)**: 添加新的 LLM 提供商
4. **导出插件 (ExportPlugin)**: 添加新的导出格式

### 1.2 插件生命周期
```
初始化 → 注册 → 使用 → 清理
    ↓        ↓       ↓       ↓
initialize() → 添加到管理器 → 处理请求 → cleanup()
```

## 2. 开发第一个插件

### 2.1 创建插件类
```python
from src.loom.plugins import RulePlugin
from typing import Dict, Any

class MyCustomRuleFormatter(RulePlugin):
    """自定义规则格式化插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "MyCustomRuleFormatter"
        self.version = "1.0.0"
        self.description = "自定义规则格式化器"
        
    def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化插件: {self.name}")
        return True
        
    def cleanup(self):
        """清理插件资源"""
        print(f"清理插件: {self.name}")
        
    def preprocess_rule(self, rule_text: str) -> str:
        """预处理规则文本"""
        # 在这里实现预处理逻辑
        return rule_text.strip()
        
    def postprocess_rule(self, rule_text: str, parsed_rule: Dict[str, Any]) -> Dict[str, Any]:
        """后处理解析后的规则"""
        # 添加自定义元数据
        parsed_rule["processed_by"] = self.name
        return parsed_rule
        
    def validate_rule(self, rule_text: str) -> bool:
        """验证规则有效性"""
        # 实现验证逻辑
        return "rule:" in rule_text and "description:" in rule_text
```

### 2.2 注册插件
```python
from src.loom.plugins import register_plugin

# 创建插件实例
plugin = MyCustomRuleFormatter()

# 注册插件
if register_plugin(plugin):
    print("插件注册成功")
else:
    print("插件注册失败")
```

### 2.3 使用插件
```python
from src.loom.plugins import get_plugin_manager

# 获取插件管理器
manager = get_plugin_manager()

# 获取特定类型的插件
rule_plugins = manager.get_plugins_by_type("rule")

# 使用插件
for plugin in rule_plugins:
    if plugin.name == "MyCustomRuleFormatter":
        result = plugin.preprocess_rule("rule: test")
        print(f"处理结果: {result}")
```

## 3. 插件开发最佳实践

### 3.1 错误处理
```python
class RobustPlugin(RulePlugin):
    def preprocess_rule(self, rule_text: str) -> str:
        try:
            # 业务逻辑
            if not rule_text:
                raise ValueError("规则文本不能为空")
            return rule_text.strip()
        except Exception as e:
            # 记录错误并返回默认值
            logger.error(f"预处理规则时出错: {e}")
            return rule_text  # 返回原始文本
```

### 3.2 配置管理
```python
class ConfigurablePlugin(RulePlugin):
    def __init__(self, config_file: str = None):
        super().__init__()
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "enabled": True,
            "max_length": 1000,
            "strip_comments": True
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
```

### 3.3 性能优化
```python
class CachedPlugin(RulePlugin):
    def __init__(self):
        super().__init__()
        self.cache = {}
        
    def preprocess_rule(self, rule_text: str) -> str:
        # 使用缓存提高性能
        cache_key = hash(rule_text)
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        # 计算密集型操作
        result = self._expensive_processing(rule_text)
        self.cache[cache_key] = result
        return result
        
    def _expensive_processing(self, text: str) -> str:
        # 模拟计算密集型操作
        import time
        time.sleep(0.1)  # 模拟耗时操作
        return text.upper()
```

## 4. 测试插件

### 4.1 单元测试
```python
import pytest
from src.loom.plugins.example_plugins import MarkdownRuleFormatter

class TestMarkdownRuleFormatter:
    def setup_method(self):
        self.plugin = MarkdownRuleFormatter()
        
    def test_initialization(self):
        """测试插件初始化"""
        assert self.plugin.name == "MarkdownRuleFormatter"
        assert self.plugin.version == "1.1.0"
        
    def test_preprocess_rule(self):
        """测试规则预处理"""
        input_text = "  rule: test  \n\n  description: test  "
        expected = "rule: test\ndescription: test"
        result = self.plugin.preprocess_rule(input_text)
        assert result == expected
        
    def test_validate_rule(self):
        """测试规则验证"""
        valid_rule = "rule: test\ndescription: test\ncondition: when\neffect: then"
        invalid_rule = "just some text"
        
        assert self.plugin.validate_rule(valid_rule) == True
        assert self.plugin.validate_rule(invalid_rule) == False
```

### 4.2 集成测试
```python
import asyncio
from src.loom.plugins import get_plugin_manager

class TestPluginIntegration:
    async def test_plugin_registration(self):
        """测试插件注册和初始化"""
        manager = get_plugin_manager()
        
        # 注册插件
        plugin = MarkdownRuleFormatter()
        assert manager.register_plugin(plugin) == True
        
        # 初始化插件
        results = manager.initialize_all()
        assert results["MarkdownRuleFormatter"] == True
        
        # 清理插件
        manager.cleanup_all()
```

## 5. 插件打包和分发

### 5.1 项目结构
```
my_loom_plugin/
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       ├── core.py          # 插件核心逻辑
│       └── utils.py         # 工具函数
├── tests/
│   ├── __init__.py
│   └── test_plugin.py
├── pyproject.toml          # 项目配置
├── README.md              # 项目说明
└── setup.py              # 安装脚本（可选）
```

### 5.2 pyproject.toml 配置
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-loom-plugin"
version = "1.0.0"
description = "自定义 LOOM 插件"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "loom-core>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "black", "mypy"]
test = ["pytest", "pytest-asyncio"]

[project.entry-points."loom.plugins"]
my_plugin = "my_plugin.core:MyCustomRuleFormatter"
```

### 5.3 安装和使用
```bash
# 本地安装
pip install -e .

# 使用插件
from my_plugin.core import MyCustomRuleFormatter
from src.loom.plugins import register_plugin

plugin = MyCustomRuleFormatter()
register_plugin(plugin)
```

## 6. 高级插件开发

### 6.1 插件间通信
```python
class CommunicatingPlugin(RulePlugin):
    def __init__(self, plugin_manager):
        super().__init__()
        self.plugin_manager = plugin_manager
        
    def process_with_other_plugins(self, rule_text: str) -> str:
        """与其他插件协作处理"""
        # 获取所有规则插件
        rule_plugins = self.plugin_manager.get_plugins_by_type("rule")
        
        # 按顺序应用所有插件
        result = rule_text
        for plugin in rule_plugins:
            if plugin != self:  # 排除自己
                result = plugin.preprocess_rule(result)
                
        return result
```

### 6.2 动态配置
```python
class DynamicPlugin(RulePlugin):
    def __init__(self):
        super().__init__()
        self.config_handlers = {
            "enable_feature": self._enable_feature,
            "set_threshold": self._set_threshold,
        }
        
    def update_config(self, config: Dict[str, Any]):
        """动态更新配置"""
        for key, value in config.items():
            if key in self.config_handlers:
                self.config_handlers[key](value)
                
    def _enable_feature(self, enabled: bool):
        self.feature_enabled = enabled
        
    def _set_threshold(self, threshold: float):
        self.threshold = threshold
```

### 6.3 插件钩子
```python
class HookedPlugin(RulePlugin):
    def __init__(self):
        super().__init__()
        self.hooks = {
            "pre_process": [],
            "post_process": [],
        }
        
    def add_hook(self, hook_name: str, callback):
        """添加钩子函数"""
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)
            
    def preprocess_rule(self, rule_text: str) -> str:
        """执行预处理钩子"""
        # 执行前置钩子
        for hook in self.hooks["pre_process"]:
            rule_text = hook(rule_text)
            
        # 主要处理逻辑
        result = self._actual_processing(rule_text)
        
        # 执行后置钩子
        for hook in self.hooks["post_process"]:
            result = hook(result)
            
        return result
```

## 7. 调试和故障排除

### 7.1 日志记录
```python
import logging

logger = logging.getLogger(__name__)

class LoggedPlugin(RulePlugin):
    def preprocess_rule(self, rule_text: str) -> str:
        logger.debug(f"开始预处理规则，长度: {len(rule_text)}")
        
        try:
            result = self._process(rule_text)
            logger.info(f"规则预处理成功，结果长度: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"规则预处理失败: {e}", exc_info=True)
            raise
```

### 7.2 性能分析
```python
import time
from functools import wraps

def profile(func):
    """性能分析装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        logger.info(f"{func.__name__} 执行时间: {elapsed:.3f}秒")
        return result
    return wrapper

class ProfiledPlugin(RulePlugin):
    @profile
    def preprocess_rule(self, rule_text: str) -> str:
        # 业务逻辑
        return rule_text.strip()
```

### 7.3 常见问题
1. **插件未注册**: 检查插件类是否继承自正确的基类
2. **初始化失败**: 检查 `initialize()` 方法是否返回 `True`
3. **内存泄漏**: 确保 `cleanup()` 方法正确释放资源
4. **性能问题**: 使用缓存和异步处理优化性能

## 8. 社区贡献

### 8.1 贡献指南
1. Fork 项目仓库
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request
5. 等待代码审查

### 8.2 代码规范
- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写完整的文档字符串
- 添加单元测试

### 8.3 发布流程
1. 更新版本号
2. 更新 CHANGELOG.md
3. 运行测试套件
4. 构建和发布包

## 9. 资源

### 9.1 示例插件
- [官方示例插件](src/loom/plugins/example_plugins.py)
- [社区插件仓库](https://github.com/loom-community/plugins)

### 9.2 文档
- [API 参考](docs/API_REFERENCE.md)
- [插件系统文档](docs/PLUGIN_SYSTEM.md)
- [开发博客](https://blog.loom.dev)

### 9.3 支持
- [GitHub Issues](https://github.com/loom-project/loom/issues)
- [Discord 社区](https://discord.gg/loom)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/loom)

---

*本指南将持续更新。如有问题或建议，请通过 GitHub Issues 提交反馈。*