"""
【案例】将 Document 列表向量化并写入 Milvus（langchain_milvus）

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 6.2 案例：把 Document 列表写入 Milvus，再用检索器取回结果

知识点速览：
- 这是本章最贴近"向量库实战入口"的案例，演示的是：先准备 Document，再向量化，再写入 Milvus，最后按相似度检索。
- Milvus.from_documents() 会自动读取每个 Document 的 page_content，调用 embedding 做向量化，并把原文、向量、metadata 一起写入 Milvus。
- as_retriever() 得到的是检索器；invoke(查询文本) 时，LangChain 会先把查询文本转成向量，再去库里找最相关的 Document。
- 这个案例是 RAG 的底层能力演示，不包含文档加载器、文本分割器和"检索后交给大模型生成答案"的完整流程。
- connection_args 要与本地环境一致；如果要复用已有集合，查询端也必须使用同一个 collection_name。

重要提示：
- langchain-milvus 0.3.x 版本存在连接bug，需要先通过 pymilvus.connections.connect() 建立连接
- 参考 super_biz_agent_py 项目的正确实现方式
"""

# pip install pymilvus langchain-milvus dashscope python-dotenv
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import Milvus
from langchain_core.documents import Document
from dotenv import load_dotenv
from pymilvus import connections

load_dotenv()

# ==================== 重要补丁 ====================
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

# 应用补丁
_patch_pymilvus_milvus_client_orm_alias()
# ===============================================

# 1. 初始化嵌入模型
embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key='sk-a73ee6f79ce54b7ca96f9b3e947f924e'
)

# 2. 构造 Document 列表：page_content 是正文，metadata 是附加信息
# 在完整 RAG 中，这些 Document 往往来自“加载器 + 分割器”；本案例先用手写数据聚焦理解向量库存取流程
texts = [
    "通义千问是阿里巴巴研发的大语言模型。",
    "Redis 是一个高性能的键值存储系统，支持向量检索。",
    "LangChain 可以轻松集成各种大模型和向量数据库。",
]

documents = [
    Document(page_content=text, metadata={"source": "manual"}) for text in texts
]

# 3. 一次性写入 Milvus：内部会对每个 Document 的 page_content 做向量化，并建立可检索索引
# 重要：langchain-milvus 0.3.x 版本需要在创建 VectorStore 之前先建立连接
# 参考 super_biz_agent_py 项目的正确实现方式

# 步骤1：先通过 pymilvus 建立连接（解决 ConnectionNotExistException）
print("正在连接 Milvus 服务器...")
try:
    connections.connect(
        alias="default",
        host="localhost",
        port="19530"
    )
    print("✅ Milvus 连接成功")
except Exception as e:
    print(f"❌ Milvus 连接失败: {e}")
    print("\n解决方案：")
    print("1. 确保 Milvus 服务已启动: docker ps | findstr milvus")
    print("2. 或使用本地文件模式: connection_args={'uri': './milvus_demo.db'}")
    exit(1)

# 步骤2：创建 LangChain Milvus VectorStore
# 注意：必须在 connections.connect() 之后才能创建
vector_store = Milvus.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name="my_collection_2",
    connection_args={
        "host": "localhost",
        "port": "19530"
    },
    auto_id=True,
    drop_old=False
)

# 4. 得到检索器：当你 invoke 查询文本时，LangChain 会先把问题向量化，再在库中做相似度检索
retriever = vector_store.as_retriever(search_kwargs={"k": 2})
results = retriever.invoke("LangChain 和 Redis 怎么结合？")
for res in results:
    print(res.page_content)














