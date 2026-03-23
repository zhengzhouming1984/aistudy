import os,json 
from typing import Sequence 

from langchain_core.messages import message_to_dict, messages_from_dict, HumanMessage, AIMessage, BaseMessage 
from langchain_core.chat_history import BaseChatMessageHistory 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from openai import OpenAI


class FileChatMessageHistory(BaseChatMessageHistory): 
    def __init__(self, file_path: str, session_id: str): 
        self.file_path = file_path 
        self.session_id = session_id 
        self.file_path = os.path.join(self.file_path, self.session_id + ".json") 
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True) 
        self.messages = []  # 初始化messages属性
        self.load_messages()  # 加载现有消息

    def add_messages(self, messages: Sequence[BaseMessage]) -> None: 
        """
        添加多条消息到历史记录
        
        Args:
            messages (Sequence[BaseMessage]): 要添加的消息序列
        """
        # 检查并添加新消息，避免重复
        for message in messages:
            if message not in self.messages:
                self.messages.append(message)
        
        # 转换为字典并保存
        dict_messages = [message_to_dict(msg) for msg in self.messages]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(dict_messages, f, ensure_ascii=False, indent=2)
            print(f"保存 {len(self.messages)} 条消息")
    def load_messages(self) -> None:
        """
        从文件加载消息历史
        
        此方法尝试从指定的文件路径加载消息历史，如果文件不存在、为空或包含无效的JSON，
        则初始化空消息列表。
        """
        try: 
            # 尝试打开文件并读取内容
            with open(self.file_path, "r", encoding="utf-8") as f: 
                # 读取文件内容并去除首尾空白
                content = f.read().strip()
                
                # 检查文件是否为空
                if content:
                    # 解析JSON内容并转换为消息对象
                    self.messages = messages_from_dict(json.loads(content)) 
                    print(f"加载 {len(self.messages)} 条消息") 
                else:
                    # 文件为空，初始化空消息列表
                    print(f"文件 {self.file_path} 为空，初始化空消息列表") 
                    self.messages = []
        except FileNotFoundError: 
            # 文件不存在，初始化空消息列表
            print(f"文件 {self.file_path} 不存在，初始化空消息列表") 
            self.messages = []
        except json.JSONDecodeError: 
            # JSON解析错误，文件内容不是有效的JSON格式
            print(f"文件 {self.file_path} 包含无效的JSON，初始化空消息列表") 
            self.messages = []

    def clear(self) -> None: 
        """
        清空消息历史
        """
        with open(self.file_path, "w", encoding="utf-8") as f: 
            json.dump([], f) 
            print(f"清空 {self.file_path}")
        self.messages = []  # 同时清空内存中的消息


# 初始化 OpenAI 客户端，配置 API 密钥和基础 URL
# 使用 SiliconFlow API 作为后端
client = OpenAI(
    api_key="sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw",  # API 密钥
    base_url="https://api.siliconflow.cn/v1"  # SiliconFlow API 基础 URL
)

# 初始化 LangChain 的 ChatOpenAI 模型
model = ChatOpenAI(
    api_key="sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw",
    base_url="https://api.siliconflow.cn/v1",
    model_name="Qwen/Qwen3-8B"
)

# 创建提示模板
# prompt = PromptTemplate.from_template("你需要根据会话历史回应用户问题。对话历史:{chat_history},用户提问:{input},请仔细分析对话历史中的所有信息，准确回答用户问题。")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你需要根据会话历史回应用户问题。用户提问:{input},请仔细分析对话历史中的所有信息，准确回答用户问题。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# 创建输出解析器
strOutput = StrOutputParser()


def print_prompt(full_prompt):
    print("=" * 10, full_prompt.to_string(), "=" * 10)
    return full_prompt


# 创建基础链
base_chain = prompt | print_prompt | model | strOutput

# 存储会话历史的字典，键为会话ID，值为对应的InMemoryChatMessageHistory实例
store = {}


# 获取会话历史的函数 
def get_session_history(session_id): 
    """
    根据会话ID获取对应的会话历史

    Args:
        session_id (str): 会话唯一标识符

    Returns:
        FileChatMessageHistory: 对应会话的历史消息存储实例
    """
    # 检查会话ID是否已存在
    if session_id in store:
        # 如果存在，返回已有的会话历史
        return store[session_id]
    # 如果不存在，创建新的会话历史实例并存储
    store[session_id] = FileChatMessageHistory(
        file_path="./chat_history",  # 消息存储目录
        session_id=session_id  # 会话ID
    )
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


    for chunk in conversation_chain.stream({"input": "我有一只狗"}, config=session_config):
        print(chunk, end="", flush=True)
    print()
    print()


    for chunk in conversation_chain.stream({"input": "我还有两只猫"}, config=session_config):
        print(chunk, end="", flush=True)
    print()
    print()


    for chunk in conversation_chain.stream({"input": "我有几只宠物"}, config=session_config):
        print(chunk, end="", flush=True)
    print()
    print()