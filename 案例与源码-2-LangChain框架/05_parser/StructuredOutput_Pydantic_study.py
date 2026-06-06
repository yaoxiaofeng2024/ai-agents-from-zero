import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI

load_dotenv(encoding="utf-8")

class Product(BaseModel):
    """产品信息：名称、类别、简介。简介长度需 ≥ 10，由下方 validator 校验。"""
    name: str = Field(description="产品名称")
    category: str = Field(description="产品类别")
    description: str = Field(description="产品简介")

    @field_validator("description")
    def validate_description(cls, value):
        """Pydantic 校验器：description 长度必须 ≥ 10，否则抛 ValueError。"""
        if len(value) < 10:
            raise ValueError("产品简介长度必须大于等于10")
        return value

parser = PydanticOutputParser(pydantic_object=Product)

format_instructions = parser.get_format_instructions()

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个AI助手，你只能输出结构化的json数据\n{format_instructions}"),
        ("human", "请你输出标题为：{topic}的新闻内容"),
    ]
)

prompt = prompt_template.format_messages(
    topic="Macbook pro",
    format_instructions=format_instructions
)
print(prompt)

deepseek_api = 'sk-b444e6b29b344981bbd848db8fe7fe0b'
deepseek_url = 'https://api.deepseek.com'
deepseek_model = 'deepseek-v4-pro'

deepseek_client = ChatOpenAI(api_key=deepseek_api,
                                 base_url=deepseek_url,
                                 model=deepseek_model,
                                 temperature=0.7)

result = deepseek_client.invoke(prompt)
print(result)

response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info(f"结果类型: {type(response)}")


