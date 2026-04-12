"""
配置文件
功能：集中管理项目的所有配置参数

配置内容包括：
1. OpenAI API配置（密钥、基础URL、模型）
2. 向量数据库配置（路径、集合名称）
3. 文本分割配置（块大小、重叠、分隔符）
4. MD5记录配置（去重文件路径）
5. 语义切片配置（阈值、目标大小）
"""

import os

# ==================== 基础路径配置 ====================

# 获取当前文件所在目录的绝对路径
# 用于构建其他文件的相对路径，确保路径正确性
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==================== OpenAI API配置 ====================

# OpenAI API密钥
# 优先从环境变量读取，如果不存在则使用默认值
# 注意：生产环境应该使用环境变量，避免硬编码密钥
openai_api_key = os.getenv("OPENAI_API_KEY", "sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw")

# OpenAI API基础URL
# 默认使用SiliconFlow的API服务
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

# 嵌入模型名称
# 使用Qwen的嵌入模型，用于文本向量化和语义切片
embedding_model = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")


# ==================== MD5去重配置 ====================

# MD5记录文件路径
# 用于记录已处理文件的MD5值，避免重复上传相同内容
# 文件位置：项目根目录下的md5.txt
md5_path = os.path.join(BASE_DIR, "md5.txt")


# ==================== 知识库配置 ====================

# 知识库名称
# 用于标识知识库，与collection_name保持一致
knowledge_base = "rag"

# Chroma向量数据库存储路径
# 向量数据库文件将保存在此目录下
chroma_path = os.path.join(BASE_DIR, "./chroma_db")

# 向量数据库集合名称
# 用于Chroma数据库中的集合标识
# 应与knowledge_base保持一致
collection_name = "rag"

# 向量数据库持久化目录
# 与chroma_path保持一致，确保数据保存位置正确
persist_directory = os.path.join(BASE_DIR, "./chroma_db")


# ==================== 文本分割配置（递归字符切片） ====================

# 文本分割的块大小（字符数）
# 每个文本块的最大长度，超过此长度将进行分割
chunk_size = 1000

# 文本分割的重叠部分大小（字符数）
# 相邻文本块之间的重叠字符数，用于保持上下文连贯性
chunk_overlap = 100

# 计算文本长度的函数
# 使用Python内置的len函数计算字符数
length_function = len

# 文本分割的分隔符列表，按优先级从高到低排列
# 分割时会优先尝试使用排在前面的分隔符
# 顺序：段落 > 行 > 空格 > 字符 > 标点
separators = ["\n\n", "\n", " ", "", ".", "!", "?"]

# 最大分割字符数
# 用于控制文本分割的粒度，防止产生过大的文本块
max_split_char_number = 1000


# ==================== 向量检索配置 ====================

# 相似度阈值
# 用于过滤检索结果，只返回相似度高于此阈值的结果
# 范围：0-1，值越大表示相似度要求越高
similarity_threshold = 0.5


# ==================== 语义切片配置 ====================

# 是否使用语义切片
# True: 使用SemanticChunker进行语义切片
# False: 使用RecursiveCharacterTextSplitter进行递归字符切片
semantic_chunking = True

# 语义相似度阈值
# 值越小切片越细，值越大切片越粗
# 范围：0-1，建议根据文本特点调整
semantic_threshold = 0.5

# 语义切片的目标大小（字符数）
# 语义切片器会尽量保持每个切片接近此大小
semantic_chunk_size = 500

# 语义切片的重叠大小（字符数）
# 相邻语义切片之间的重叠字符数
semantic_chunk_overlap = 50
