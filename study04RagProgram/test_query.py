from knowledge_base import KnowledgeBaseService

# 创建知识库服务实例
server = KnowledgeBaseService()

# 测试查询
query = "我身高1.66米，尺码推荐"
results = server.query_knowledge_base(query, k=2)

print('查询结果数量:', len(results))
for i, doc in enumerate(results):
    print(f'结果 {i+1}:')
    print(f'来源: {doc.metadata["source"]}')
    print(f'内容: {doc.page_content[:150]}...')
    print()

# 测试其他查询
print("\n测试其他查询:")
queries = ["羊绒衫如何洗涤", "春季服装颜色推荐"]
for q in queries:
    print(f'\n查询: {q}')
    results = server.query_knowledge_base(q, k=2)
    print(f'结果数量: {len(results)}')
    for i, doc in enumerate(results):
        print(f'结果 {i+1}:')
        print(f'来源: {doc.metadata["source"]}')
        print(f'内容: {doc.page_content[:150]}...')
