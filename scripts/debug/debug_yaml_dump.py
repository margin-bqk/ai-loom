import yaml
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from loom.core.config_manager import AppConfig

print("1. 创建空的AppConfig...")
config = AppConfig()

print("2. 转换为字典...")
try:
    data = config.to_dict()
    print(f"   字典类型: {type(data)}")
    print(f"   字典内容: {data}")

    # 检查llm_providers
    print(f"   llm_providers: {data.get('llm_providers')}")
    print(f"   llm_providers类型: {type(data.get('llm_providers'))}")

except Exception as e:
    print(f"   to_dict失败: {e}")
    import traceback

    traceback.print_exc()

print("\n3. 尝试YAML序列化...")
try:
    yaml_str = yaml.dump(
        data, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    print(f"   YAML序列化成功")
    print(f"   YAML内容:\n{yaml_str}")
except Exception as e:
    print(f"   YAML序列化失败: {e}")
    import traceback

    traceback.print_exc()

print("\n4. 尝试写入文件...")
try:
    with open("test_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
    print(f"   文件写入成功")

    # 检查文件大小
    file_size = os.path.getsize("test_config.yaml")
    print(f"   文件大小: {file_size} 字节")

    # 读取文件内容
    with open("test_config.yaml", "r", encoding="utf-8") as f:
        content = f.read()
        print(f"   文件内容:\n{content}")

except Exception as e:
    print(f"   文件写入失败: {e}")
    import traceback

    traceback.print_exc()

# 清理
if os.path.exists("test_config.yaml"):
    os.remove("test_config.yaml")
