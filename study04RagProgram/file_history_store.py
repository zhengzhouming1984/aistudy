"""
文件聊天历史存储模块
功能：实现基于文件的对话历史存储，支持多会话管理和持久化存储
"""

import os
import json
from typing import Sequence
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

# 内存中的会话存储字典，用于缓存会话历史实例
# key: session_id, value: FileChatMessageHistory 实例
store = {}


def get_session_history(session_id: str) -> "FileChatMessageHistory":
    """
    根据会话ID获取对应的会话历史
    
    这是一个工厂函数，用于创建或获取已存在的会话历史实例。
    如果会话ID已存在，返回缓存的实例；否则创建新的实例。
    
    Args:
        session_id (str): 会话唯一标识符，用于区分不同用户的对话
        
    Returns:
        FileChatMessageHistory: 对应会话的历史消息存储实例
    """
    # 检查会话ID是否已存在于内存缓存中
    if session_id in store:
        # 如果存在，返回已有的会话历史实例（从内存中获取，提高性能）
        return store[session_id]
    
    # 如果不存在，创建新的会话历史实例
    # 文件存储路径：./chat_history/{session_id}.json
    store[session_id] = FileChatMessageHistory(
        file_path="./chat_history",  # 消息存储目录
        session_id=session_id        # 会话ID
    )
    
    # 返回新创建的会话历史实例
    return store[session_id]


class FileChatMessageHistory(BaseChatMessageHistory):
    """
    基于文件的聊天消息历史类
    
    继承自 LangChain 的 BaseChatMessageHistory，实现将对话历史
    持久化存储到 JSON 文件的功能。支持自动加载和保存消息。
    
    Attributes:
        file_path (str): 消息存储文件的完整路径
        session_id (str): 当前会话的唯一标识符
        messages (list): 内存中的消息列表
    """
    
    def __init__(self, file_path: str, session_id: str):
        """
        初始化文件聊天历史存储
        
        Args:
            file_path (str): 存储目录路径（如："./chat_history"）
            session_id (str): 会话唯一标识符
        """
        # 保存基础属性
        self.session_id = session_id
        
        # 构建完整的文件路径：目录 + 会话ID + .json 后缀
        self.file_path = os.path.join(file_path, self.session_id + ".json")
        
        # 确保存储目录存在，如果不存在则自动创建
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # 初始化消息列表（内存缓存）
        self.messages = []
        
        # 从文件加载已有的历史消息
        self.load_messages()

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """
        添加多条消息到历史记录并保存到文件
        
        此方法会将新消息追加到现有历史记录中，避免重复添加相同消息，
        然后自动保存到 JSON 文件。
        
        Args:
            messages (Sequence[BaseMessage]): 要添加的消息序列，
                通常包含用户消息和AI回复消息
        """
        # 遍历所有要添加的消息
        for message in messages:
            # 检查消息是否已存在（避免重复添加）
            if message not in self.messages:
                # 添加到内存中的消息列表
                self.messages.append(message)
        
        # 将消息对象转换为字典格式，便于JSON序列化
        # message_to_dict 将 BaseMessage 转换为可序列化的字典
        dict_messages = [message_to_dict(msg) for msg in self.messages]
        
        # 打开文件并写入JSON数据
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(dict_messages, f, ensure_ascii=False, indent=2)
            print(f"保存 {len(self.messages)} 条消息")

    def load_messages(self) -> None:
        """
        从文件加载消息历史
        
        此方法尝试从指定的文件路径加载消息历史。
        如果文件不存在、为空或包含无效的JSON，则初始化空消息列表。
        
        异常处理：
            - FileNotFoundError: 文件不存在时初始化空列表
            - json.JSONDecodeError: JSON格式错误时初始化空列表
        """
        try:
            # 尝试打开文件并读取内容
            with open(self.file_path, "r", encoding="utf-8") as f:
                # 读取文件内容并去除首尾空白字符
                content = f.read().strip()
                
                # 检查文件内容是否为空
                if content:
                    # 解析JSON内容并转换为消息对象列表
                    # messages_from_dict 将字典转换回 BaseMessage 对象
                    self.messages = messages_from_dict(json.loads(content))
                    print(f"加载 {len(self.messages)} 条消息")
                else:
                    # 文件为空，初始化空消息列表
                    print(f"文件 {self.file_path} 为空，初始化空消息列表")
                    self.messages = []
                    
        except FileNotFoundError:
            # 文件不存在（首次使用），初始化空消息列表
            print(f"文件 {self.file_path} 不存在，初始化空消息列表")
            self.messages = []
            
        except json.JSONDecodeError:
            # JSON解析错误（文件损坏），初始化空消息列表
            print(f"文件 {self.file_path} 包含无效的JSON，初始化空消息列表")
            self.messages = []

    def clear(self) -> None:
        """
        清空消息历史
        
        此方法会清空内存中的消息列表，并将空列表保存到文件，
        实现彻底删除对话历史的功能。
        """
        # 打开文件并写入空列表
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
            print(f"清空 {self.file_path}")
        
        # 同时清空内存中的消息列表
        self.messages = []


if __name__ == "__main__":
    """
    模块测试入口
    
    当直接运行此文件时，显示模块信息。
    实际使用时应在其他文件中导入 get_session_history 函数。
    """
    print("FileChatMessageHistory 模块")
    print("请在其他文件中导入使用 get_session_history 函数")
