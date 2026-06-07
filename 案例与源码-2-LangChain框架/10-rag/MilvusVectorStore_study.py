from langchain_milvus import Milvus
from common import get_embeddings, connect_milvus

# 1. 初始化嵌入模型
embeddingsModel = get_embeddings()

# 2. 待写入的文本及（可选）元数据
texts = [
    "我喜欢吃苹果",
    "苹果是我最喜欢吃的水果",
    "我喜欢用苹果手机",
]

embeddings = embeddingsModel.embed_documents(texts)
for i, vec in enumerate(embeddings, 1):
    print(f"文本 {i}：{texts[i-1]}")
    print(f"向量长度：{len(vec)}")
    print(f"前5个向量值：{vec[:10]}\n")

# 定义每条文本对应的元数据信息
# metadata = [{"segment_id": "1"}, {"segment_id": "2"}, {"segment_id": "3"}]

# 定义每条文本对应的元数据信息；真实 RAG 中这些 metadata 往往来自 Document.metadata，也可作为来源展示或过滤条件
metadata = [{"segment_id": str(i)} for i in range(1, len(texts) + 1)]

# 3. Milvus 连接与集合名（需与检索案例一致）
# 重要：langchain-milvus 0.3.x 版本需要在创建 VectorStore 之前先建立连接
connection_args = connect_milvus()

# 创建 Milvus 向量存储实例：此时只是"连上库 + 指定集合配置"，还没真正写入文本；真正写入发生在 add_texts()
vector_store = Milvus(
    embedding_function=embeddingsModel,
    collection_name="newsgroups",
    connection_args=connection_args,
    auto_id=True,
)

ids = vector_store.add_texts(texts, metadatas=metadata)
print(ids)




