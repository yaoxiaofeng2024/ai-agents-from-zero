"""
【案例】DashScope 原生调用：单句文本向量化（Hello 级）

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 4.3 案例：DashScope 原生调用，先看到“向量长什么样”

知识点速览：
- 这是本章最小的 Embedding HelloWorld，重点是先看到“文本怎样被转成向量”，暂时还不涉及相似度计算和向量库检索。
- Embedding（嵌入）是把文本变成一串数字（向量）的过程；后续做语义检索、相似度排序、RAG，底层都会用到这个结果。
- 百炼提供原生文本嵌入接口，可直接用 dashscope.TextEmbedding.call() 传入模型名和文本，返回向量结果。
- 若要单独取出向量数组，可从 output.embeddings[0].embedding 获取；向量长度由当前模型决定。

模型文档链接：https://bailian.console.aliyun.com/cn-beijing/?productCode=p_efm&tab=doc#/doc/?type=model&url=2842587
"""

import os
import dashscope
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

dashscope.api_key = 'sk-a73ee6f79ce54b7ca96f9b3e947f924e'

input_text = "衣服的质量杠杠的"

resp = dashscope.TextEmbedding.call(
    model="text-embedding-v3",
    input=input_text,
)

if resp.status_code == HTTPStatus.OK:
    print(resp)


