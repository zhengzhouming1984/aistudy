"""
向量存储服务模块
功能：提供向量数据库的初始化和检索功能

核心功能：
1. 向量数据库初始化：使用Chroma创建向量存储
2. 嵌入模型配置：配置OpenAI嵌入模型用于文本向量化
3. 检索器提供：返回可配置的检索器，用于RAG链
"""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import config_data as config
import os


class VectorStoreService(object):
    """
    向量存储服务类
    
    提供向量数据库的封装，包括：
    - 向量数据库初始化
    - 嵌入模型管理
    - 检索器创建
    
    Attributes:
        embedding (OpenAIEmbeddings): 嵌入模型实例
        vector_store (Chroma): Chroma向量数据库实例
    """
    
    def __init__(self, embedding):
        """
        初始化向量存储服务
        
        Args:
            embedding (OpenAIEmbeddings): 嵌入模型实例
                用于将文本转换为向量表示
        """
        # 保存嵌入模型引用
        self.embedding = embedding
        
        # 初始化Chroma向量数据库
        # collection_name: 集合名称，用于区分不同知识库
        # embedding_function: 嵌入函数，用于文本向量化
        # persist_directory: 持久化目录，数据保存位置
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )
    
    def get_retriever(self):
        """
        获取向量检索器
        
        返回一个检索器对象，可用于：
        - 在RAG链中检索相关文档
        - 直接调用进行相似度搜索
        
        Returns:
            VectorStoreRetriever: 向量检索器实例
            
        Example:
            >>> retriever = vector_store_service.get_retriever()
            >>> results = retriever.invoke("查询文本")
        """
        # k参数指定返回的结果数量
        # 这里设置为2，表示返回最相似的2个文档
        return self.vector_store.as_retriever(search_kwargs={"k": 2})


# ==================== 测试入口 ====================

if __name__ == "__main__":
    """
    模块测试入口
    
    测试内容：
    1. 初始化嵌入模型
    2. 初始化向量存储服务
    3. 获取检索器
    4. 执行检索测试
    """
    
    # 初始化嵌入模型
    # 使用配置中的API密钥和模型参数
    embedding = OpenAIEmbeddings(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
        model=config.embedding_model
    )
    
    # 初始化向量存储服务
    vector_store_service = VectorStoreService(embedding)
    
    # 获取检索器
    retriever = vector_store_service.get_retriever()
    
    # 执行检索测试
    query = "我的体重110斤，身高1米66，尺码推荐"
    print(f"查询: {query}")
    print("-" * 60)
    
    result = retriever.invoke(query)
    print("检索结果:")
    for i, doc in enumerate(result):
        print(f"\n结果 {i+1}:")
        print(f"来源: {doc.metadata.get('source', '未知')}")
        print(f"内容: {doc.page_content[:200]}...")
