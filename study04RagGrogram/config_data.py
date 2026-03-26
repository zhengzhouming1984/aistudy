# config_data.py
# 知识库配置文件
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# OpenAI 配置
openai_api_key = os.getenv("OPENAI_API_KEY", "sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw")
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
embedding_model = "Qwen/Qwen3-Embedding-0.6B"

# MD5 记录文件路径，用于记录已处理文件的 MD5 值，避免重复上传
md5_path = os.path.join(BASE_DIR, "md5.txt")

# 知识库名称，用于Chroma向量数据库的集合名称
knowledge_base = "rag"

# Chroma 向量数据库存储路径
chroma_path = os.path.join(BASE_DIR, "./chroma_db")

# 文本分割的块大小，单位为字符数
chunk_size = 1000

# 文本分割的重叠部分大小，单位为字符数
chunk_overlap = 100

# 计算文本长度的函数
length_function = len

# 文本分割的分隔符列表，按优先级从高到低排列
separators = ["\n\n", "\n", " ", "", ".", "!", "?"]

# 最大分割字符数，用于控制文本分割的粒度
max_split_char_number = 1000

# 向量数据库配置
collection_name = "rag"  # 集合名称，与 knowledge_base 保持一致
persist_directory = os.path.join(BASE_DIR, "./chroma_db")  # 持久化目录，与 chroma_path 保持一致

# 相似度阈值
similarity_threshold = 0.5

# 语义切片配置
# semantic_chunking = True  # 是否使用语义切片
# semantic_threshold = 0.3  # 语义相似度阈值，值越小切片越细
# semantic_chunk_size = 1000  # 语义切片的目标大小
# semantic_chunk_overlap = 100  # 语义切片的重叠大小
semantic_chunking = True  # 是否使用语义切片
semantic_threshold = 0.1  # 语义相似度阈值，值越小切片越细
semantic_chunk_size = 500  # 语义切片的目标大小
semantic_chunk_overlap = 50  # 语义切片的重叠大小