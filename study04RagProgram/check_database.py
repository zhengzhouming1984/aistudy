"""
数据库检查工具
功能：检查知识库中存储的文档数量和内容

此脚本用于：
1. 连接到Chroma向量数据库
2. 获取所有存储的文档
3. 显示文档数量
4. 打印每个文档的来源和内容预览

使用方法：
    python check_database.py

注意事项：
- 此脚本需要KnowledgeBaseService类正确配置
- 会连接到配置的Chroma向量数据库
- 适用于检查知识库的当前状态
"""

# 导入知识库服务
# KnowledgeBaseService提供了与向量数据库交互的方法
from knowledge_base import KnowledgeBaseService

# 创建知识库服务实例
# 这会初始化Chroma向量数据库连接
# 内部会使用配置文件中的设置（如数据库路径、嵌入模型等）
server = KnowledgeBaseService()

# 获取所有文档
# 调用Chroma的get()方法获取所有存储的文档
# 返回包含以下键的字典：
# - 'ids': 文档的唯一标识符列表
# - 'documents': 文档内容列表
# - 'metadatas': 文档元数据列表（包含source、create_time等信息）
all_docs = server.chroma.get()

# 打印文档数量
# 通过获取ids列表的长度来计算文档总数
print("文档数量:", len(all_docs['ids']))

# 打印每个文档的详细信息
# 使用enumerate()同时获取索引和文档内容
for i, doc in enumerate(all_docs['documents']):
    print(f"\n文档 {i+1}:")
    # 打印文档来源（文件名）
    # 从对应的元数据中获取source字段
    print("来源:", all_docs['metadatas'][i]['source'])
    # 打印文档内容预览（前100个字符）
    # 使用切片操作获取文档前100个字符，然后添加省略号
    print("内容预览:", doc[:100], "...")

# 执行完成后，脚本会自动退出
# 此脚本主要用于手动检查知识库状态，不是生产环境的一部分
