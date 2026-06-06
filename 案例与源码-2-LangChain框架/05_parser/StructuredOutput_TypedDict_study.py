import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv(encoding="utf-8")

deepseek_api = 'sk-b444e6b29b344981bbd848db8fe7fe0b'
deepseek_url = 'https://api.deepseek.com'
deepseek_model = 'deepseek-v4-pro'

deepseek_client = ChatOpenAI(api_key=deepseek_api,
                                 base_url=deepseek_url,
                                 model=deepseek_model,
                                 temperature=0.7)


# 使用 Pydantic 模型定义结构（比 TypedDict 更稳定）
class Animal(BaseModel):
    animal: str = Field(description="动物名称")
    emoji: str = Field(description="对应的表情符号")


class AnimalList(BaseModel):
    animals: list[Animal] = Field(description="动物与表情列表")


# 创建 JSON 输出解析器
parser = JsonOutputParser(pydantic_object=AnimalList)

# 获取格式说明
format_instructions = parser.get_format_instructions()

# 创建提示模板
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个AI助手，请严格按照指定的JSON格式输出。"),
    ("human", "任意生成三种动物，以及他们的 emoji 表情。{format_instructions}")
])

# 格式化提示
prompt = chat_prompt.format_messages(format_instructions=format_instructions)

# 调用模型
result = deepseek_client.invoke(prompt)
print("原始响应:", result.content)

# 解析结果
response = parser.invoke(result)
print("\n解析后的结构化结果:")
print(response)
print(f"\n结果类型: {type(response)}")

