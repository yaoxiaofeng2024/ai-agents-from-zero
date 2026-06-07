"""
公共工具模块：嵌入模型、LLM、Milvus 连接与补丁

使用方式：
    from common import get_embeddings, get_llm, connect_milvus

说明：
- get_embeddings() 返回 DashScopeEmbeddings 实例
- get_llm() 返回 ChatModel 实例
- connect_milvus() 自动应用补丁并建立 Milvus 连接，返回 connection_args 字典
"""

# pip install pymilvus langchain-milvus dashscope python-dotenv langchain
import os
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.chat_models import init_chat_model
from pymilvus import connections

load_dotenv()

# ==================== Milvus 连接补丁 ====================
# 解决 langchain-milvus 0.3.x 的 ConnectionNotExistException
# 参考: super_biz_agent_py/app/core/milvus_client.py::_patch_pymilvus_milvus_client_orm_alias
def _patch_pymilvus_milvus_client_orm_alias():
    """
    langchain_milvus 内部创建的 MilvusClient 会将 _using 设为 ``cm-{id}``，
    该别名未在 pymilvus.orm.connections 中注册；随后 ORM ``Collection(..., using=...)``
    会抛出 ConnectionNotExistException: should create connection first.

    在已通过 ``connections.connect(alias="default", ...)`` 建立连接后，
    强制让 MilvusClient 使用 ``default`` 别名，与 ORM 一致。
    """
    if getattr(_patch_pymilvus_milvus_client_orm_alias, "_done", False):
        return
    try:
        from pymilvus.milvus_client.milvus_client import MilvusClient
    except ImportError:
        return

    _orig_init = MilvusClient.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        self._using = "default"

    MilvusClient.__init__ = _wrapped_init
    setattr(_patch_pymilvus_milvus_client_orm_alias, "_done", True)

# 模块加载时自动应用补丁
_patch_pymilvus_milvus_client_orm_alias()
# ========================================================


def get_embeddings() -> DashScopeEmbeddings:
    """返回 DashScope 嵌入模型实例"""
    return DashScopeEmbeddings(
        model="text-embedding-v3",
        dashscope_api_key='sk-a73ee6f79ce54b7ca96f9b3e947f924e',
    )


def get_llm():
    """返回通义千问聊天模型实例"""
    return init_chat_model(
        model="qwen-plus",
        model_provider="openai",
        api_key='sk-a73ee6f79ce54b7ca96f9b3e947f924e',
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


# Milvus 默认连接配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"


def connect_milvus(
    host: str = MILVUS_HOST,
    port: str = MILVUS_PORT,
) -> dict:
    """
    连接 Milvus 服务器，返回 connection_args 字典供 Milvus VectorStore 使用。

    返回:
        dict: {"host": ..., "port": ...}
    """
    print("正在连接 Milvus 服务器...")
    try:
        connections.connect(alias="default", host=host, port=port)
        print("✅ Milvus 连接成功")
    except Exception as e:
        print(f"❌ Milvus 连接失败: {e}")
        print("\n解决方案：")
        print("1. 确保 Milvus 服务已启动: docker ps | findstr milvus")
        print("2. 或使用本地文件模式: connection_args={'uri': './milvus_demo.db'}")
        exit(1)

    return {"host": host, "port": port}
