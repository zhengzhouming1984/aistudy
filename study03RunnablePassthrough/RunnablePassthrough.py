import os
from dotenv import load_dotenv
from langchain_core.vectorstores import InMemoryVectorStore
from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端，配置 API 密钥和基础 URL
# 使用 SiliconFlow API 作为后端
api_key = os.getenv("OPENAI_API_KEY", "sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

client = OpenAI(
    api_key=api_key,  # API 密钥
    base_url=base_url  # SiliconFlow API 基础 URL
)

# 初始化 LangChain 的 ChatOpenAI 模型
model = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,
    model_name=os.getenv("CHAT_MODEL", "Qwen/Qwen3-8B")
)

# 初始化嵌入模型
from langchain_openai import OpenAIEmbeddings
qwen_embeddings = OpenAIEmbeddings(
    api_key=api_key,
    base_url=base_url,
    model=os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
)

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "以我提供的已知参考资料为主，简洁和专业的回答用户问题。参考资料:{context}"),
    ("user", "用户提问：{input}")
])

# 创建输出解析器
strOutput = StrOutputParser()


def print_prompt(full_prompt):
    print("=" * 10, full_prompt.to_string(), "=" * 10)
    return full_prompt

# 初始化向量存储
vector_store = InMemoryVectorStore(embedding=qwen_embeddings)
vector_store.add_texts(["减肥就是要少吃多练","在减脂期间吃东西很重要,清淡少油控制卡路里摄入并运动起来","跑步是很好的运动哦"])

# 构建完整的处理链
chain = (
    # 接收输入并添加上下文
    RunnablePassthrough.assign(
        context=lambda input_data: [doc.page_content for doc in vector_store.similarity_search(input_data["input"], k=2)]
    )
    # 构建提示
    | prompt
    # 打印提示
    | print_prompt
    # 调用模型
    | model
    # 解析输出
    | strOutput
)

# 测试链
if __name__ == '__main__':
    # 测试减肥问题
    result = chain.invoke({"input": "怎么减肥？"})
    print("回答:", result)
    
    # 测试其他问题
    result = chain.invoke({"input": "跑步有什么好处？"})
    print("回答:", result)