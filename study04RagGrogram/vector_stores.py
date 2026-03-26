from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import config_data as config
import os

class VectorStoreService(object):
    def __init__(self, embedding):
        """
        初始化向量存储服务
        
        :param embedding: 嵌入模型的传入
        """
        self.embedding = embedding
        
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )
    
    def get_retriever(self):
        """返回向量检索器,方便加入chain"""
        # k 参数应该是整数，表示返回的结果数量
        # similarity_threshold 是相似度阈值，不应该用于 k 参数
        return self.vector_store.as_retriever(search_kwargs={"k": 2})
      
if __name__ == "__main__":
    # 初始化嵌入模型

    embedding = OpenAIEmbeddings(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
        model=config.embedding_model
    )
    
    # 初始化向量存储服务
    vector_store_service = VectorStoreService(embedding)
    
    # 获取检索器
    retriever = vector_store_service.get_retriever()
    
    # 执行检索
    result = retriever.invoke("我的体重110斤，身高1米66，尺码推荐")
    print("检索结果:")
    print(result)