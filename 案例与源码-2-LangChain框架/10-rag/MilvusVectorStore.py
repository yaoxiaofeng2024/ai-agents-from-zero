"""
【案例】使用 langchain_milvus 将文本写入 Milvus 向量库（add_texts）

对应教程章节：第 19 章 - RAG 检索增强生成 → 2.1.1 from_documents 与 add_texts；也可与第 18 章向量库写入案例对照阅读

知识点速览：
- 这个案例展示的是纯文本流驱动的入库路线：先创建 `Milvus` VectorStore，再通过 `add_texts()` 把字符串列表写入向量库。
- `add_texts(texts, metadata)` 会在内部调用 `embed_documents(texts)` 做批量向量化，然后把文本、向量和 metadata 一起写入 Milvus。
- 这条路线和 `from_documents(...)` 并不冲突：前者更适合你手里已经是纯文本列表，后者更适合你已经有 `Document` 列表。
- 本例里额外手动执行了一次 `embed_documents`，目的是先观察"向量长什么样、维度是多少"；真正做存储时，这一步不是必须的。
- 返回的 ids 可用于后续更新、删除或追踪；collection_name 需要和后续检索端保持一致。

重要提示：
- langchain-milvus 0.3.x 版本存在连接bug，需要先通过 pymilvus.connections.connect() 建立连接
- 参考 super_biz_agent_py 项目的正确实现方式
"""

# pip install pymilvus langchain-milvus dashscope python-dotenv
from langchain_milvus import Milvus
from langchain_community.embeddings import DashScopeEmbeddings
from pymilvus import connections
import os
from dotenv import load_dotenv

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
embeddingsModel = DashScopeEmbeddings(
    model="text-embedding-v3", dashscope_api_key='sk-a73ee6f79ce54b7ca96f9b3e947f924e'
)

# 2. 待写入的文本及（可选）元数据
texts = [
    "我喜欢吃苹果",
    "苹果是我最喜欢吃的水果",
    "我喜欢用苹果手机",
]


# 批量转成向量：这里只是为了先观察向量维度和内容；真正写入时 add_texts 内部会再次完成向量化
embeddings = embeddingsModel.embed_documents(texts)
for i, vec in enumerate(embeddings, 1):
    print(f"文本 {i}: {texts[i-1]}")
    print(f"向量长度: {len(vec)}")
    print(f"前5个向量值: {vec[:10]}\n")

# 定义每条文本对应的元数据信息
# metadata = [{"segment_id": "1"}, {"segment_id": "2"}, {"segment_id": "3"}]

# 定义每条文本对应的元数据信息；真实 RAG 中这些 metadata 往往来自 Document.metadata，也可作为来源展示或过滤条件
metadata = [{"segment_id": str(i)} for i in range(1, len(texts) + 1)]

# 3. Milvus 连接与集合名（需与检索案例一致）
# 重要：langchain-milvus 0.3.x 版本需要在创建 VectorStore 之前先建立连接
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

# 创建 Milvus 向量存储实例：此时只是"连上库 + 指定集合配置"，还没真正写入文本；真正写入发生在 add_texts()
vector_store = Milvus(
    embedding_function=embeddingsModel,
    collection_name="newsgroups",
    connection_args={
        "host": "localhost",
        "port": "19530"
    },
    auto_id=True,
)

# 4. 将文本与元数据写入向量库（add_texts 内部会调 embed_documents，无需先算向量）
ids = vector_store.add_texts(texts, metadata)

# 打印前5个存储记录的ID
print(ids[0:5])

"""
【输出示例】
文本 1: 我喜欢吃苹果
向量长度: 1024
前5个向量值: [-0.04062262922525406, 0.03663524612784386, -0.07420649379491806, 0.003861021716147661, -0.06338627636432648, -0.02864176034927368, -0.027855515480041504, 0.03684116527438164, -0.023493731394410133, -0.027892956510186195]

文本 2: 苹果是我最喜欢吃的水果
向量长度: 1024
前5个向量值: [-0.03398064523935318, 0.04141449183225632, -0.06892527639865875, 0.005737593863159418, -0.06951850652694702, -0.04560413956642151, -0.04171110317111015, 0.04508506879210472, -0.04549290984869003, -0.017945043742656708]

文本 3: 我喜欢用苹果手机
向量长度: 1024
前5个向量值: [-0.052530914545059204, 0.006213586777448654, -0.11318981647491455, -0.023480866104364395, -0.036481890827417374, -0.04383847862482071, 0.005418661516159773, 0.02874900959432125, 0.0019732017535716295, 0.01118539646267891]

正在连接 Milvus 服务器...
✅ Milvus 连接成功

[454517486254521461, 454517486254521462, 454517486254521463]
"""
