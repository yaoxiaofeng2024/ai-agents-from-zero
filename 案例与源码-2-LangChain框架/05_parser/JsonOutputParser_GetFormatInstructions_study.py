from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from loguru import logger
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

load_dotenv(encoding="utf-8")

deepseek_api = 'sk-b444e6b29b344981bbd848db8fe7fe0b'
deepseek_url = 'https://api.deepseek.com'
deepseek_model = 'deepseek-v4-pro'

deepseek_client = ChatOpenAI(api_key=deepseek_api,
                                 base_url=deepseek_url,
                                 model=deepseek_model,
                                 temperature=0.7)

class Person(BaseModel):
    """定义一条「新闻」的结构：时间、人物、事件。用于约束模型输出的 JSON 形状。"""

    time: str = Field(description="时间")
    person: str = Field(description="人物")
    event: str = Field(description="事件")


# 绑定 Pydantic 模型：主要驱动 get_format_instructions() 的 schema；invoke 后得到 dict
parser = JsonOutputParser(pydantic_object=Person)

# 获取「格式说明」：描述 Person 各字段，便于拼进提示词让模型按此输出
format_instructions = parser.get_format_instructions()

# 在 human 消息里加入 {format_instructions}，模型会看到「请按如下格式输出 JSON …」
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个AI助手，你只能输出结构化JSON数据。"),
        ("human", "请生成一个关于{topic}的新闻。{format_instructions}"),
    ]
)

prompt = chat_prompt.format_messages(
    topic="小米su7跑车",
    format_instructions=format_instructions
)
print(prompt)

result = deepseek_client.invoke(prompt)
print(result)


response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info(f"结果类型: {type(response)}")








