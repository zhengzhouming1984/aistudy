# config_data.py
# 知识库配置文件

# MD5记录文件路径，用于记录已处理文件的MD5值，避免重复上传
md5_path = "md5.txt"

# 知识库名称，用于Chroma向量数据库的集合名称
knowledge_base = "rag"

# Chroma向量数据库存储路径
chroma_path = "./chroma_db"

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