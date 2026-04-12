import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端，配置 API 密钥和基础 URL
# 使用 SiliconFlow API 作为后端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw"),  # API 密钥
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")  # SiliconFlow API 基础 URL
)

# 初始化 LangChain 的 ChatOpenAI 模型
model = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1"),
    model_name=os.getenv("CHAT_MODEL", "Qwen/Qwen3-8B")
)

# 创建提示模板
# prompt = PromptTemplate.from_template("你需要根据会话历史回应用户问题。对话历史:{chat_history},用户提问:{input},请仔细分析对话历史中的所有信息，准确回答用户问题。")

prompt = ChatPromptTemplate.from_messages([
    ("system","你需要根据会话历史回应用户问题。用户提问:{input},请仔细分析对话历史中的所有信息，准确回答用户问题。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# 创建输出解析器
strOutput = StrOutputParser()

def print_prompt(full_prompt):
    print("="*10, full_prompt.to_string(), "="*10)
    return full_prompt

# 创建基础链
base_chain = prompt | print_prompt | model | strOutput

# 存储会话历史的字典，键为会话ID，值为对应的InMemoryChatMessageHistory实例
store={}

# 获取会话历史的函数
def get_session_history(session_id):
    """
    根据会话ID获取对应的会话历史
    
    Args:
        session_id (str): 会话唯一标识符
    
    Returns:
        InMemoryChatMessageHistory: 对应会话的历史消息存储实例
    """
    # 检查会话ID是否已存在
    if session_id in store:
        # 如果存在，返回已有的会话历史
        return store[session_id]
    # 如果不存在，创建新的会话历史实例并存储
    store[session_id] = InMemoryChatMessageHistory()
    # 返回新创建的会话历史
    return store[session_id]

# 创建带消息历史的链
conversation_chain = RunnableWithMessageHistory(
    runnable=base_chain,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

if __name__ == '__main__':
    session_config = {
        "configurable": {
            "session_id": "user_001"
        }
    }
    
    # 流式输出第一个问题

    for chunk in conversation_chain.stream({"input": "我有一只狗"}, config=session_config):
        print(chunk, end="", flush=True)
    print()
    print()

    # 流式输出第二个问题

    for chunk in conversation_chain.stream({"input": "我还有两只猫"}, config=session_config):
        print(chunk, end="", flush=True)
    print()
    print()

    # 流式输出第三个问题

    for chunk in conversation_chain.stream({"input": "我有几只宠物"}, config=session_config):
        print(chunk, end="", flush=True)
    print()
    print()