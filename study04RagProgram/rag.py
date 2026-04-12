"""
RAG (Retrieval-Augmented Generation) 服务模块
功能：实现检索增强生成功能，结合向量检索和大语言模型回答用户问题

核心流程：
1. 接收用户查询
2. 从知识库检索相关文档
3. 将检索结果作为上下文输入到语言模型
4. 生成基于上下文的回答
5. 维护对话历史，支持多轮对话
"""

# ==================== 导入依赖 ====================

# 导入知识库服务，用于文档检索
from knowledge_base import KnowledgeBaseService

# 导入 OpenAI 聊天模型，用于生成回答
from langchain_openai import ChatOpenAI

# 导入聊天提示模板和消息占位符
# ChatPromptTemplate: 定义对话模板
# MessagesPlaceholder: 用于插入对话历史
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入 Runnable 组件，用于构建处理链
# RunnablePassthrough: 直接传递输入数据
# RunnableLambda: 包装自定义函数
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# 导入 RunnableWithMessageHistory，用于处理对话历史
# 这是实现多轮对话的关键组件
from langchain_core.runnables.history import RunnableWithMessageHistory

# 导入字符串输出解析器，将模型输出解析为字符串
from langchain_core.output_parsers import StrOutputParser

# 导入配置文件，包含API密钥等配置
import config_data as config
import os

# 导入会话历史管理函数，用于获取/创建对话历史
from file_history_store import get_session_history


# ==================== 工具函数 ====================

def print_prompt(prompt):
    """
    打印提示信息，用于调试
    
    此函数在链式调用中插入，用于查看实际发送给模型的完整提示内容，
    便于调试和优化提示模板。
    
    Args:
        prompt: ChatPromptValue 对象，包含格式化后的提示内容
        
    Returns:
        prompt: 原样返回输入的prompt，保证链式调用继续
    """
    print("=" * 20)
    print(prompt.to_string())  # 将提示转换为字符串并打印
    print("=" * 20)
    return prompt


# ==================== RAG 服务类 ====================

class RagService:
    """
    RAG 服务类
    
    提供完整的检索增强生成功能，包括：
    - 文档检索：从知识库中检索与用户查询相关的文档
    - 上下文构建：将检索结果格式化为模型可用的上下文
    - 对话生成：使用大语言模型生成回答
    - 历史管理：维护多轮对话历史，支持上下文理解
    
    Attributes:
        knowledge_service (KnowledgeBaseService): 知识库服务实例
        prompt_template (ChatPromptTemplate): 对话提示模板
        chat_model (ChatOpenAI): 聊天模型实例
        chain (Runnable): 组合好的LangChain执行链
    """
    
    def __init__(self, knowledge_base_service=None):
        """
        初始化 RAG 服务
        
        初始化时会完成以下工作：
        1. 创建或复用知识库服务实例
        2. 设置对话提示模板（系统提示 + 历史占位符 + 用户输入）
        3. 初始化聊天模型（使用配置的API密钥和模型参数）
        4. 构建完整的处理链
        
        Args:
            knowledge_base_service (KnowledgeBaseService, optional): 
                可选的知识库服务实例。如果不提供，则自动创建新实例。
                用于在多个服务间共享知识库连接。
        """
        # 使用传入的知识库服务或创建新实例
        if knowledge_base_service:
            self.knowledge_service = knowledge_base_service
        else:
            self.knowledge_service = KnowledgeBaseService()
        
        # 初始化提示模板，定义对话的结构和风格
        # 模板包含三个部分：
        # 1. system: 设定AI助手的行为和回答风格
        # 2. MessagesPlaceholder: 插入历史对话记录
        # 3. human: 当前用户的问题
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                # 系统角色：设定回答风格和参考资料使用方式
                # {context} 会被替换为检索到的文档内容
                ("system", "以我提供的已知参考资料为主,简洁和专业的回答用户问题。\n\n参考资料：\n{context}"),
                
                # 对话历史占位符：这里会插入之前的对话记录
                # variable_name="chat_history" 对应历史消息的键名
                MessagesPlaceholder(variable_name="chat_history"),
                
                # 用户角色：当前用户的问题
                # {input} 会被替换为用户的实际查询
                ("human", "请回答用户提问:{input}")
            ]
        )
        
        # 初始化聊天模型
        # 使用配置中的API密钥、基础URL和模型名称
        self.chat_model = ChatOpenAI(
            api_key=config.openai_api_key,      # API密钥
            base_url=config.openai_base_url,    # API基础URL
            model_name=os.getenv("CHAT_MODEL", "Qwen/Qwen3-8B")          # 使用的模型名称
        )
        
        # 构建并保存处理链
        self.chain = self.get_chain()

    def get_chain(self):
        """
        构建并返回完整的RAG处理链
        
        链的结构：
        输入数据 → 检索文档 → 格式化上下文 → 构建提示 → 调用模型 → 解析输出
        
        使用 RunnableWithMessageHistory 包装，实现对话历史管理。
        
        Returns:
            Runnable: 组合好的 LangChain 执行链，可直接调用进行推理
        """
        
        # ----- 内部函数：检索相关文档 -----
        def retrieve_docs(input_dict):
            """
            从知识库检索与用户查询相关的文档
            
            Args:
                input_dict (dict): 包含用户输入的字典，格式为 {"input": "用户问题"}
                
            Returns:
                list: 检索到的文档列表，每个文档包含page_content和metadata
            """
            # 从输入字典中提取查询内容
            query = input_dict.get("input", "")
            # 调用知识库服务进行检索，返回最相关的2个文档
            return self.knowledge_service.query_knowledge_base(query, k=2)
        
        # ----- 内部函数：格式化文档 -----
        def format_document(docs):
            """
            将检索到的文档列表格式化为字符串
            
            将文档内容和元数据拼接成易于模型理解的格式，
            作为上下文信息插入到提示中。
            
            Args:
                docs (list): 检索到的文档列表，每个文档是Document对象
                
            Returns:
                str: 格式化后的文档字符串，包含内容和元数据
            """
            # 如果没有检索到文档，返回默认提示
            if not docs:
                return "无相关参考资料"
            
            # 拼接所有文档内容和元数据
            formatted_str = ""
            for doc in docs:
                # 每个文档包含：内容片段 + 元数据（来源、创建时间等）
                formatted_str += f"文档片段:{doc.page_content}\n"
                formatted_str += f"文档元数据:{doc.metadata}\n\n"
            
            return formatted_str
        
        # ----- 构建基础RAG链 -----
        # 使用字典定义并行处理的数据流
        base_chain = (
            {
                # 提取用户输入
                "input": lambda x: x["input"],
                
                # 检索并格式化文档作为上下文
                # RunnableLambda将函数包装为Runnable组件
                "context": RunnableLambda(retrieve_docs) | format_document,
                
                # 获取对话历史，如果没有则返回空列表
                "chat_history": lambda x: x.get("chat_history", [])
            }
            # 应用提示模板，将上述数据填充到模板中
            | self.prompt_template
            # 打印完整提示（调试用）
            | RunnableLambda(print_prompt)
            # 调用语言模型生成回答
            | self.chat_model
            # 将模型输出解析为字符串
            | StrOutputParser()
        )

        # ----- 包装对话历史功能 -----
        # 使用 RunnableWithMessageHistory 自动管理对话历史
        chain_with_history = RunnableWithMessageHistory(
            base_chain,                    # 基础处理链
            get_session_history,           # 获取会话历史的函数
            input_messages_key="input",    # 输入消息的键名
            history_messages_key="chat_history"  # 历史消息的键名
        )

        return chain_with_history

    def run(self, query: str, session_id: str = "default"):
        """
        运行RAG链，回答用户问题
        
        这是主要的对外接口，接收用户查询并返回生成的回答。
        会自动处理对话历史的加载和保存。
        
        Args:
            query (str): 用户的问题或查询内容
            session_id (str, optional): 会话ID，用于区分不同用户的对话。
                相同session_id的对话会共享历史记录。
                默认为 "default"。
                
        Returns:
            str: 模型生成的回答文本
            
        Example:
            >>> rag = RagService()
            >>> response = rag.run("我身高1.66米，尺码推荐")
            >>> print(response)
            "根据您的身高1.66米，建议选择尺码M。"
        """
        # 调用链进行推理
        # 输入格式为字典，包含input字段
        # config参数指定会话ID，用于历史管理
        return self.chain.invoke(
            {"input": query},                    # 用户输入
            config={"configurable": {"session_id": session_id}}  # 会话配置
        )


# ==================== 测试入口 ====================

if __name__ == "__main__":
    """
    模块测试入口
    
    当直接运行此文件时，执行以下测试：
    1. 创建RAG服务实例
    2. 发送第一个问题，测试基本RAG功能
    3. 发送跟进问题，测试对话历史功能
    
    预期结果：
    - 第一个问题能正确回答
    - 第二个问题能结合第一个问题的上下文回答
    """
    
    # 创建 RAG 服务实例
    print("=" * 50)
    print("初始化 RAG 服务...")
    print("=" * 50)
    rag_service = RagService()
    
    # ----- 测试1：基本RAG功能 -----
    print("\n【测试1】基本RAG功能")
    print("-" * 50)
    query = "我身高1.66米，尺码推荐"
    print(f"用户问题: {query}")
    
    # 调用服务获取回答
    response = rag_service.run(query)
    
    # 打印结果
    print(f"\nAI回答: {response}")
    
    # ----- 测试2：对话历史功能 -----
    print("\n" + "=" * 50)
    print("【测试2】对话历史功能（跟进问题）")
    print("-" * 50)
    follow_up_query = "那如果我体重是60公斤呢？"
    print(f"用户问题: {follow_up_query}")
    print("（这是一个跟进问题，应该结合之前的身高信息）")
    
    # 使用相同的session_id，会自动加载历史
    follow_up_response = rag_service.run(follow_up_query)
    
    # 打印结果
    print(f"\nAI回答: {follow_up_response}")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
