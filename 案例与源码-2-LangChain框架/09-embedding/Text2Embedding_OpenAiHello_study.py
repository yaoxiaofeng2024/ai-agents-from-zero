"""
【案例】OpenAI 兼容接口调用阿里百炼 Embedding（Hello 级）

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 4.4 案例：OpenAI 兼容写法，理解“同一能力，不同接法”

知识点速览：
- 这个案例演示的是“同一类 Embedding 能力，可以通过 OpenAI 兼容协议来调用”，重点不在 SDK 名字，而在兼容接口思想。
- 对真实项目来说，这种写法很常见，因为保留同一套调用方式后，切换厂商时通常只需要调整 base_url、api_key、model。
- client.embeddings.create() 的 input 可以是单字符串或字符串列表；返回结果中的 data[i].embedding 就是向量。
- 若平台存在不同地域或不同网关，base_url 与对应 API Key 需要保持匹配。
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

input_text = "衣服的质量杠杠的"

client = OpenAI(
    api_key='sk-a73ee6f79ce54b7ca96f9b3e947f924e',
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.embeddings.create(
    model='text-embedding-v3',
    input=input_text,
)

print(completion.model_dump_json())






