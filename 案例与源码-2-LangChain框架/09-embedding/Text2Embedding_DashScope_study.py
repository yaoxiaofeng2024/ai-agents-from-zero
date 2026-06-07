"""
【案例】LangChain DashScope 封装：单条与批量文本向量化

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 4.5 案例：用 LangChain 的统一接口做单条与批量向量化

知识点速览：
- 这是最贴近后续 LangChain 检索器、向量库、RAG 用法的 Embedding 案例，因为它使用的是 LangChain 统一接口。
- embed_query(text)：更偏“查询阶段”，常用于把用户问题转成向量。
- embed_documents(texts)：更偏“索引阶段”，常用于把文档片段批量转成向量。
- 返回值分别是“单个向量”和“向量列表”；向量维度由当前模型决定，建索引和查询时应保持模型一致。

模型文档链接：https://bailian.console.aliyun.com/cn-beijing/?tab=api#/api/?type=model&url=2587654
"""

# pip install langchain-community dashscope
import os
from langchain_community.embeddings import DashScopeEmbeddings
from dotenv import load_dotenv

load_dotenv()

embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key='sk-a73ee6f79ce54b7ca96f9b3e947f924e'
)

text = "This is a test document."

query_result = embeddings.embed_query(text)
print(query_result)


doc_results = embeddings.embed_documents(
    texts=[
        "Hi there!",
        "Oh, hello!",
        "What's your name?",
        "My friends call me World",
        "Hello World!",
    ]
)
print(doc_results)



