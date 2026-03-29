from knowledge_base import KnowledgeBaseService

# 创建知识库服务实例
server = KnowledgeBaseService()

# 获取所有文档
all_docs = server.chroma.get()

print("文档数量:", len(all_docs['ids']))

# 打印每个文档的来源和内容预览
for i, doc in enumerate(all_docs['documents']):
    print(f"\n文档 {i+1}:")
    print("来源:", all_docs['metadatas'][i]['source'])
    print("内容预览:", doc[:100], "...")
