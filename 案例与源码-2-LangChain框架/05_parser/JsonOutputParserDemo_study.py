from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from loguru import logger
from langchain_openai import ChatOpenAI

load_dotenv(encoding="utf-8")

chat_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个{role}，请简短回答我提出的问题，结果返回json格式，q字段表示问题，a字段表示答案。",
        ),
        ("human", "请回答：{question}")
    ]
)

prompt = chat_prompt.invoke(
    {"role": "AI助手", "question": "什么是LangChai，简洁回答100字以内"}
)
logger.info(prompt)

deepseek_api = 'sk-b444e6b29b344981bbd848db8fe7fe0b'
deepseek_url = 'https://api.deepseek.com'
deepseek_model = 'deepseek-v4-pro'

deepseek_client = ChatOpenAI(api_key=deepseek_api,
                                 base_url=deepseek_url,
                                 model=deepseek_model,
                                 temperature=0.7)

result = deepseek_client.invoke(prompt)
print(result)

parser = JsonOutputParser()
response = parser.invoke(result)
print(response)

