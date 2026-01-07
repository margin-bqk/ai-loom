"""
向量存储（可选）

提供向量数据库存储接口，支持语义检索。
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
from datetime import datetime, timedelta

from .world_memory import MemoryEntity, MemoryEntityType
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    """向量存储（可选功能）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", False)
        self.embedding_model = self.config.get("embedding_model", "all-MiniLM-L6-v2")
        self.collection_name = self.config.get("collection_name", "loom_memories")
        self.persist_directory = self.config.get("persist_directory", "./chroma_db")
        self.embedding_provider = self.config.get("embedding_provider", "local")  # local, openai, huggingface
        
        # OpenAI配置
        self.openai_api_key = self.config.get("openai_api_key")
        self.openai_model = self.config.get("openai_model", "text-embedding-ada-002")
        
        # 延迟导入，因为chromadb是可选的
        self.client = None
        self.collection = None
        
        if self.enabled:
            self._initialize()
        else:
            logger.info("VectorStore disabled (optional feature)")
    
    def _initialize(self):
        """初始化向量存储"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 创建客户端
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory
            ))
            
            # 获取或创建集合
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing vector collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "LOOM memory embeddings"}
                )
                logger.info(f"Created new vector collection: {self.collection_name}")
            
            logger.info(f"VectorStore initialized successfully with provider: {self.embedding_provider}")
            
        except ImportError:
            logger.warning("chromadb not installed, VectorStore disabled")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")
            self.enabled = False
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入"""
        if not self.enabled:
            return []
        
        try:
            if self.embedding_provider == "openai":
                return self._get_openai_embedding(text)
            elif self.embedding_provider == "huggingface":
                return self._get_huggingface_embedding(text)
            else:  # local
                return self._get_local_embedding(text)
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    def _get_local_embedding(self, text: str) -> List[float]:
        """获取本地模型嵌入"""
        try:
            from sentence_transformers import SentenceTransformer
            
            if not hasattr(self, '_embedding_model'):
                self._embedding_model = SentenceTransformer(self.embedding_model)
            
            embedding = self._embedding_model.encode(text)
            return embedding.tolist()
            
        except ImportError:
            logger.warning("sentence-transformers not installed, using dummy embeddings")
            # 返回虚拟嵌入
            return [0.0] * 384
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """获取OpenAI嵌入"""
        try:
            import openai
            
            if not self.openai_api_key:
                logger.error("OpenAI API key not configured")
                return []
            
            openai.api_key = self.openai_api_key
            
            response = openai.Embedding.create(
                model=self.openai_model,
                input=text
            )
            
            return response["data"][0]["embedding"]
            
        except ImportError:
            logger.warning("openai package not installed, falling back to local embeddings")
            return self._get_local_embedding(text)
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return []
    
    def _get_huggingface_embedding(self, text: str) -> List[float]:
        """获取HuggingFace嵌入"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            import torch.nn.functional as F
            
            if not hasattr(self, '_hf_tokenizer'):
                self._hf_tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
                self._hf_model = AutoModel.from_pretrained(self.embedding_model)
            
            # 编码文本
            inputs = self._hf_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self._hf_model(**inputs)
            
            # 使用平均池化获取句子嵌入
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
            
            # 归一化
            embeddings = F.normalize(embeddings, p=2, dim=0)
            
            return embeddings.tolist()
            
        except ImportError:
            logger.warning("transformers or torch not installed, falling back to local embeddings")
            return self._get_local_embedding(text)
        except Exception as e:
            logger.error(f"HuggingFace embedding failed: {e}")
            return []
    
    def _extract_text_for_embedding(self, entity: MemoryEntity) -> str:
        """从实体提取用于嵌入的文本"""
        text_parts = []
        
        # 添加类型信息
        text_parts.append(f"类型: {entity.type.value}")
        
        # 添加内容
        if isinstance(entity.content, dict):
            for key, value in entity.content.items():
                if isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, (int, float, bool)):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    text_parts.append(f"{key}: {' '.join(str(v) for v in value[:3])}")
        else:
            text_parts.append(str(entity.content))
        
        # 添加元数据
        if entity.metadata:
            for key, value in entity.metadata.items():
                if isinstance(value, str):
                    text_parts.append(f"元数据_{key}: {value}")
        
        return " ".join(text_parts)
    
    async def store_entity(self, entity: MemoryEntity) -> bool:
        """存储实体到向量数据库"""
        if not self.enabled:
            return False
        
        # 只存储特定类型的实体
        storeable_types = [
            MemoryEntityType.FACT,
            MemoryEntityType.EVENT,
            MemoryEntityType.CHARACTER,
            MemoryEntityType.LOCATION
        ]
        
        if entity.type not in storeable_types:
            return False
        
        try:
            # 提取文本
            text = self._extract_text_for_embedding(entity)
            if not text:
                return False
            
            # 生成嵌入
            embedding = self._get_embedding(text)
            if not embedding:
                return False
            
            # 存储到向量数据库
            metadata = {
                "session_id": entity.session_id,
                "type": entity.type.value,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat()
            }
            
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
                ids=[entity.id]
            )
            
            logger.debug(f"Stored entity {entity.id} in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store entity {entity.id} in vector store: {e}")
            return False
    
    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """语义搜索"""
        if not self.enabled:
            return []
        
        try:
            # 生成查询嵌入
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            # 解析结果
            search_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i, entity_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    # 将距离转换为相似度分数（0-1）
                    similarity = 1.0 / (1.0 + distance) if distance > 0 else 1.0
                    search_results.append((entity_id, similarity))
            
            logger.debug(f"Vector search found {len(search_results)} results for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def search_by_entity(self, entity: MemoryEntity, limit: int = 5) -> List[Tuple[str, float]]:
        """基于实体搜索相似实体"""
        if not self.enabled:
            return []
        
        text = self._extract_text_for_embedding(entity)
        return await self.search(text, limit)
    
    async def delete_entity(self, entity_id: str) -> bool:
        """从向量数据库删除实体"""
        if not self.enabled:
            return False
        
        try:
            self.collection.delete(ids=[entity_id])
            logger.debug(f"Deleted entity {entity_id} from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id} from vector store: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            count = self.collection.count()
            return {
                "enabled": True,
                "collection_name": self.collection_name,
                "entity_count": count,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"enabled": False, "error": str(e)}
    
    async def sync_with_structured_store(self, structured_store, session_id: str, entity_types: Optional[List[str]] = None):
        """与结构化存储同步数据"""
        if not self.enabled:
            return False
        
        try:
            # 获取结构化存储中的实体
            from .world_memory import MemoryEntityType
            
            if entity_types:
                types_to_sync = [MemoryEntityType(t) for t in entity_types]
            else:
                types_to_sync = [
                    MemoryEntityType.FACT,
                    MemoryEntityType.EVENT,
                    MemoryEntityType.CHARACTER,
                    MemoryEntityType.LOCATION
                ]
            
            synced_count = 0
            for entity_type in types_to_sync:
                entities = await structured_store.retrieve_entities_by_type(session_id, entity_type, limit=1000)
                
                for entity in entities:
                    # 检查是否已在向量存储中
                    try:
                        # 尝试获取现有嵌入
                        existing = self.collection.get(ids=[entity.id])
                        if existing and len(existing['ids']) > 0:
                            continue  # 已存在，跳过
                    except:
                        pass
                    
                    # 存储到向量存储
                    success = await self.store_entity(entity)
                    if success:
                        synced_count += 1
            
            logger.info(f"Synced {synced_count} entities from structured store to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync with structured store: {e}")
            return False
    
    async def cleanup_old_embeddings(self, days_old: int = 30):
        """清理旧嵌入"""
        if not self.enabled:
            return False
        
        try:
            # 获取所有嵌入的元数据
            all_data = self.collection.get()
            
            if not all_data or not all_data['metadatas']:
                return True
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_ids = []
            
            for i, metadata in enumerate(all_data['metadatas']):
                if 'updated_at' in metadata:
                    try:
                        updated_at = datetime.fromisoformat(metadata['updated_at'])
                        if updated_at < cutoff_date:
                            old_ids.append(all_data['ids'][i])
                    except:
                        continue
            
            if old_ids:
                self.collection.delete(ids=old_ids)
                logger.info(f"Cleaned up {len(old_ids)} old embeddings")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old embeddings: {e}")
            return False
    
    async def cleanup(self):
        """清理向量存储"""
        if not self.enabled:
            return
        
        try:
            # 可以添加清理逻辑，如删除旧嵌入
            logger.info("VectorStore cleanup completed")
        except Exception as e:
            logger.error(f"VectorStore cleanup failed: {e}")


class DummyVectorStore(VectorStore):
    """虚拟向量存储（用于禁用向量功能时）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.enabled = False
        logger.info("Using DummyVectorStore (vector features disabled)")
    
    async def store_entity(self, entity: MemoryEntity) -> bool:
        return False
    
    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        return []
    
    async def delete_entity(self, entity_id: str) -> bool:
        return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        return {"enabled": False, "reason": "dummy_store"}