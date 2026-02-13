"""
API密钥管理器

支持BYOK（Bring Your Own Key）功能，提供安全的API密钥管理。
支持环境变量、配置文件、密钥环等多种密钥存储方式。
"""

import os
import json
import hashlib
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import keyring
import keyring.errors

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class APIKeyInfo:
    """API密钥信息"""

    provider: str
    key_id: str
    key_value: str
    key_type: str = "api_key"  # api_key, bearer_token, etc.
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mask_key(self) -> str:
        """掩码密钥（用于日志）"""
        if len(self.key_value) <= 8:
            return "***"
        return f"{self.key_value[:4]}...{self.key_value[-4:]}"

    def to_dict(self, mask: bool = True) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider": self.provider,
            "key_id": self.key_id,
            "key_value": self.mask_key() if mask else self.key_value,
            "key_type": self.key_type,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }


class KeyManager:
    """API密钥管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "./config/keys")
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 密钥存储
        self._keys: Dict[str, APIKeyInfo] = {}
        self._keyring_service = "loom-ai"

        # 加载现有密钥
        self._load_keys()

        logger.info(f"KeyManager initialized with config directory: {self.config_dir}")

    def _load_keys(self):
        """从文件加载密钥"""
        key_file = self.config_dir / "keys.json"
        if key_file.exists():
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for key_data in data.get("keys", []):
                    try:
                        key_info = APIKeyInfo(
                            provider=key_data["provider"],
                            key_id=key_data["key_id"],
                            key_value=key_data["key_value"],
                            key_type=key_data.get("key_type", "api_key"),
                            created_at=datetime.fromisoformat(key_data["created_at"]),
                            last_used=(
                                datetime.fromisoformat(key_data["last_used"])
                                if key_data.get("last_used")
                                else None
                            ),
                            usage_count=key_data.get("usage_count", 0),
                            is_active=key_data.get("is_active", True),
                            metadata=key_data.get("metadata", {}),
                        )
                        self._keys[key_info.key_id] = key_info
                    except Exception as e:
                        logger.error(
                            f"Failed to load key {key_data.get('key_id', 'unknown')}: {e}"
                        )

                logger.info(f"Loaded {len(self._keys)} keys from {key_file}")

            except Exception as e:
                logger.error(f"Failed to load keys from {key_file}: {e}")

    def _save_keys(self):
        """保存密钥到文件"""
        key_file = self.config_dir / "keys.json"
        try:
            data = {
                "keys": [
                    key_info.to_dict(mask=False) for key_info in self._keys.values()
                ],
                "updated_at": datetime.now().isoformat(),
            }

            with open(key_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 设置文件权限（仅所有者可读写）
            key_file.chmod(0o600)

            logger.debug(f"Saved {len(self._keys)} keys to {key_file}")

        except Exception as e:
            logger.error(f"Failed to save keys to {key_file}: {e}")

    def _generate_key_id(self, provider: str, key_value: str) -> str:
        """生成密钥ID"""
        content = f"{provider}:{key_value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def add_key(
        self,
        provider: str,
        key_value: str,
        key_type: str = "api_key",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """添加API密钥"""
        # 验证密钥格式
        if not key_value or not key_value.strip():
            raise ValueError("Key value cannot be empty")

        # 生成密钥ID
        key_id = self._generate_key_id(provider, key_value)

        # 检查是否已存在
        if key_id in self._keys:
            logger.warning(f"Key for provider {provider} already exists, updating")
            existing_key = self._keys[key_id]
            existing_key.key_value = key_value
            existing_key.last_used = datetime.now()
            existing_key.is_active = True
            existing_key.metadata.update(metadata or {})
        else:
            # 创建新密钥
            key_info = APIKeyInfo(
                provider=provider,
                key_id=key_id,
                key_value=key_value,
                key_type=key_type,
                metadata=metadata or {},
            )
            self._keys[key_id] = key_info

        # 保存到文件
        self._save_keys()

        # 可选：保存到系统密钥环
        self._save_to_keyring(provider, key_value)

        logger.info(f"Added key for provider {provider} (ID: {key_id[:8]}...)")
        return key_id

    def _save_to_keyring(self, provider: str, key_value: str):
        """保存到系统密钥环"""
        try:
            keyring.set_password(self._keyring_service, provider, key_value)
            logger.debug(f"Saved key for {provider} to system keyring")
        except keyring.errors.KeyringError as e:
            logger.warning(f"Failed to save key to system keyring: {e}")

    def get_key(self, provider: str, key_id: Optional[str] = None) -> Optional[str]:
        """获取API密钥"""
        # 首先尝试从环境变量获取
        env_key = f"{provider.upper()}_API_KEY"
        if env_key in os.environ:
            key_value = os.environ[env_key]
            if key_value:
                logger.debug(f"Using key for {provider} from environment variable")
                return key_value

        # 从存储的密钥中查找
        matching_keys = []
        for key_info in self._keys.values():
            if key_info.provider == provider and key_info.is_active:
                if key_id is None or key_info.key_id == key_id:
                    matching_keys.append(key_info)

        if not matching_keys:
            # 尝试从系统密钥环获取
            try:
                key_value = keyring.get_password(self._keyring_service, provider)
                if key_value:
                    logger.debug(f"Using key for {provider} from system keyring")
                    return key_value
            except keyring.errors.KeyringError:
                pass

            logger.warning(f"No active key found for provider {provider}")
            return None

        # 选择最近使用的密钥
        selected_key = max(matching_keys, key=lambda k: k.last_used or k.created_at)

        # 更新使用统计
        selected_key.last_used = datetime.now()
        selected_key.usage_count += 1
        self._save_keys()

        logger.debug(f"Using key for {provider} (ID: {selected_key.key_id[:8]}...)")
        return selected_key.key_value

    def get_key_info(
        self, provider: str, key_id: Optional[str] = None
    ) -> Optional[APIKeyInfo]:
        """获取密钥信息"""
        for key_info in self._keys.values():
            if key_info.provider == provider and key_info.is_active:
                if key_id is None or key_info.key_id == key_id:
                    return key_info
        return None

    def list_keys(self, provider: Optional[str] = None) -> List[APIKeyInfo]:
        """列出所有密钥"""
        keys = list(self._keys.values())
        if provider:
            keys = [k for k in keys if k.provider == provider]
        return sorted(keys, key=lambda k: k.last_used or k.created_at, reverse=True)

    def disable_key(self, key_id: str) -> bool:
        """禁用密钥"""
        if key_id in self._keys:
            self._keys[key_id].is_active = False
            self._save_keys()
            logger.info(f"Disabled key {key_id[:8]}...")
            return True
        return False

    def enable_key(self, key_id: str) -> bool:
        """启用密钥"""
        if key_id in self._keys:
            self._keys[key_id].is_active = True
            self._save_keys()
            logger.info(f"Enabled key {key_id[:8]}...")
            return True
        return False

    def delete_key(self, key_id: str) -> bool:
        """删除密钥"""
        if key_id in self._keys:
            provider = self._keys[key_id].provider
            del self._keys[key_id]
            self._save_keys()

            # 从系统密钥环删除
            try:
                keyring.delete_password(self._keyring_service, provider)
            except keyring.errors.KeyringError:
                pass

            logger.info(f"Deleted key {key_id[:8]}...")
            return True
        return False

    def rotate_key(self, provider: str, new_key_value: str) -> str:
        """轮换密钥（添加新密钥并禁用旧密钥）"""
        # 添加新密钥
        new_key_id = self.add_key(provider, new_key_value)

        # 禁用所有旧密钥
        for key_info in self._keys.values():
            if key_info.provider == provider and key_info.key_id != new_key_id:
                key_info.is_active = False

        self._save_keys()
        logger.info(
            f"Rotated key for provider {provider}, new key ID: {new_key_id[:8]}..."
        )
        return new_key_id

    def validate_key(
        self, provider: str, key_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证密钥有效性"""
        if key_value is None:
            key_value = self.get_key(provider)
            if key_value is None:
                return {
                    "valid": False,
                    "error": "No key available",
                    "provider": provider,
                }

        # 基本验证
        if not key_value or len(key_value) < 10:
            return {"valid": False, "error": "Key too short", "provider": provider}

        # Provider特定验证
        if provider == "openai":
            # OpenAI密钥以'sk-'开头
            if not key_value.startswith("sk-"):
                return {
                    "valid": False,
                    "error": "Invalid OpenAI key format",
                    "provider": provider,
                }
        elif provider == "anthropic":
            # Anthropic密钥格式
            pass  # 没有固定格式

        return {
            "valid": True,
            "provider": provider,
            "key_length": len(key_value),
            "key_prefix": key_value[:4] + "..." if len(key_value) > 8 else "***",
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_keys = len(self._keys)
        active_keys = sum(1 for k in self._keys.values() if k.is_active)

        # 按Provider统计
        provider_stats = {}
        for key_info in self._keys.values():
            provider = key_info.provider
            if provider not in provider_stats:
                provider_stats[provider] = {"total": 0, "active": 0, "usage_count": 0}

            provider_stats[provider]["total"] += 1
            if key_info.is_active:
                provider_stats[provider]["active"] += 1
            provider_stats[provider]["usage_count"] += key_info.usage_count

        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "providers": provider_stats,
            "last_updated": datetime.now().isoformat(),
        }

    def export_keys(self, include_values: bool = False) -> Dict[str, Any]:
        """导出密钥（谨慎使用）"""
        keys = []
        for key_info in self._keys.values():
            key_data = key_info.to_dict(mask=not include_values)
            keys.append(key_data)

        return {
            "keys": keys,
            "exported_at": datetime.now().isoformat(),
            "warning": (
                "Keep this data secure!"
                if include_values
                else "Keys are masked for security"
            ),
        }

    def import_keys(self, data: Dict[str, Any], overwrite: bool = False) -> int:
        """导入密钥"""
        imported_count = 0

        for key_data in data.get("keys", []):
            try:
                key_id = key_data["key_id"]

                if key_id in self._keys and not overwrite:
                    logger.debug(f"Key {key_id[:8]}... already exists, skipping")
                    continue

                key_info = APIKeyInfo(
                    provider=key_data["provider"],
                    key_id=key_id,
                    key_value=key_data["key_value"],
                    key_type=key_data.get("key_type", "api_key"),
                    created_at=datetime.fromisoformat(key_data["created_at"]),
                    last_used=(
                        datetime.fromisoformat(key_data["last_used"])
                        if key_data.get("last_used")
                        else None
                    ),
                    usage_count=key_data.get("usage_count", 0),
                    is_active=key_data.get("is_active", True),
                    metadata=key_data.get("metadata", {}),
                )

                self._keys[key_id] = key_info
                imported_count += 1

            except Exception as e:
                logger.error(f"Failed to import key: {e}")

        if imported_count > 0:
            self._save_keys()

        logger.info(f"Imported {imported_count} keys")
        return imported_count


# 全局KeyManager实例
_global_key_manager: Optional[KeyManager] = None


def get_key_manager(config_dir: Optional[str] = None) -> KeyManager:
    """获取全局KeyManager实例"""
    global _global_key_manager
    if _global_key_manager is None:
        _global_key_manager = KeyManager(config_dir)
    return _global_key_manager


def get_provider_key(provider: str, key_id: Optional[str] = None) -> Optional[str]:
    """便捷函数：获取Provider密钥"""
    return get_key_manager().get_key(provider, key_id)


def add_provider_key(provider: str, key_value: str, **kwargs) -> str:
    """便捷函数：添加Provider密钥"""
    return get_key_manager().add_key(provider, key_value, **kwargs)
